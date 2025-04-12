# Guide d'Utilisation - Module de Prédiction "Le Vieux Moulin"

Ce guide présente comment installer, configurer et utiliser le module de prédiction IA/ML pour le restaurant "Le Vieux Moulin". Il est destiné aux développeurs et aux opérateurs du système qui souhaitent intégrer ou exploiter les fonctionnalités prédictives.

## Table des matières

1. [Installation](#1-installation)
2. [Architecture du Module](#2-architecture-du-module)
3. [Utilisation des Modèles](#3-utilisation-des-modèles)
4. [Entraînement des Modèles](#4-entraînement-des-modèles)
5. [API de Prédiction](#5-api-de-prédiction)
6. [Évaluation des Performances](#6-évaluation-des-performances)
7. [Intégration avec le Serveur Central](#7-intégration-avec-le-serveur-central)
8. [Déploiement avec Docker](#8-déploiement-avec-docker)
9. [Maintenance et Mise à Jour](#9-maintenance-et-mise-à-jour)
10. [Résolution des Problèmes](#10-résolution-des-problèmes)

## 1. Installation

### Prérequis

- Python 3.9 ou supérieur
- pip (gestionnaire de paquets Python)
- Environnement virtuel (recommandé)

### Installation depuis le dépôt

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/ml

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sous Linux/macOS
# ou
venv\Scripts\activate  # Sous Windows

# Installer les dépendances
pip install -r prediction_module/requirements.txt
```

### Installation comme package Python

Il est également possible d'installer le module comme un package Python standard :

```bash
cd Le-Vieux-Moulin/ml
pip install -e .
```

## 2. Architecture du Module

Le module de prédiction est organisé de manière modulaire avec les composants suivants :

- **models/** : Implémentation des trois modèles principaux
  - **stock_forecaster.py** : Prévision des besoins en matières premières
  - **recipe_recommender.py** : Recommandation de recettes
  - **financial_forecaster.py** : Prévisions financières

- **data_processing/** : Prétraitement et normalisation des données
  - **preprocessor.py** : Classe principale pour le prétraitement

- **training/** : Scripts d'entraînement des modèles
  - **train_models.py** : Script principal d'entraînement

- **evaluation/** : Outils d'évaluation des performances
  - **model_evaluator.py** : Évaluation des différents modèles

- **api/** : Interface REST pour les services de prédiction
  - **server.py** : Serveur FastAPI

- **utils/** : Utilitaires communs
  - **common.py** : Fonctions et classes utilitaires

- **tests/** : Tests unitaires et d'intégration

## 3. Utilisation des Modèles

### Prévision des Stocks

```python
from prediction_module.models.stock_forecaster import StockForecaster
import pandas as pd

# Charger les données historiques
historical_data = pd.read_csv('data/stock_history.csv', parse_dates=['date'])

# Initialiser le modèle (avec ou sans modèle préentraîné)
forecaster = StockForecaster(model_path='models/stock/stock_lstm_v1.h5')

# Générer des prédictions pour les 7 prochains jours
predictions = forecaster.predict(
    historical_data=historical_data,
    days_ahead=7,
    ingredients=['farine', 'tomate', 'mozzarella']
)

# Afficher les prédictions
for date, values in predictions.items():
    print(f"Prévisions pour {date}:")
    for ingredient, data in values.items():
        print(f"  - {ingredient}: {data['mean']:.2f} {data['unit']} (±{data['confidence_interval']:.2f})")
```

### Recommandation de Recettes

```python
from prediction_module.models.recipe_recommender import RecipeRecommender
from datetime import datetime

# Initialiser le recommandeur
recommender = RecipeRecommender(recipe_db_path='data/recipes.csv')

# Ingrédients disponibles (en stock)
available_ingredients = {
    'farine': 10.0,  # kg
    'tomate': 15.0,  # kg
    'mozzarella': 8.0,  # kg
    'basilic': 0.5,  # kg
    'huile_olive': 3.0  # L
}

# Ingrédients en promotion
promotions = {
    'mozzarella': 0.15,  # 15% de réduction
    'basilic': 0.20      # 20% de réduction
}

# Obtenir des suggestions
suggestions = recommender.generate_suggestions(
    count=3,  # Nombre de suggestions
    recipe_type='pizza',  # Type de recette
    available_ingredients=available_ingredients,
    promotions=promotions,
    current_date=datetime.now()
)

# Afficher les suggestions
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion['name']}")
    print(f"   {suggestion['explanation']}")
```

### Prévision Financière

```python
from prediction_module.models.financial_forecaster import FinancialForecaster
import pandas as pd

# Charger les données financières historiques
financial_data = pd.read_csv('data/financial_history.csv', parse_dates=['date'])

# Initialiser le forecaster
forecaster = FinancialForecaster(models_dir='models/financial')
forecaster.financial_data = financial_data

# Générer des prévisions
forecast = forecaster.predict(
    metrics=['chiffre_affaires', 'couts_ingredients', 'marge_brute'],
    days_ahead=30,
    include_components=True
)

# Afficher les résultats
for metric, data in forecast.items():
    print(f"\nPrévisions pour {metric}:")
    print(f"  - Total sur 30 jours: {sum(data['values']):.2f} €")
    print(f"  - Moyenne journalière: {sum(data['values'])/30:.2f} €")
```

## 4. Entraînement des Modèles

Le module fournit un script d'entraînement unifié qui permet d'entraîner un ou plusieurs modèles à la fois.

### En ligne de commande

```bash
# Entraîner tous les modèles
python -m prediction_module train --all

# Entraîner un modèle spécifique
python -m prediction_module train --stock

# Personnaliser les répertoires
python -m prediction_module train --financial --data_dir=./custom_data --models_dir=./custom_models
```

### Configuration de l'entraînement

L'entraînement peut être personnalisé via un fichier de configuration JSON :

```json
{
  "stock_data": "stock_history.csv",
  "recipe_data": "recipes.csv",
  "financial_data": "financial_history.csv",
  "sales_data": "sales_history.csv",
  
  "stock_config": {
    "lookback_days": 30,
    "lstm_units": 128,
    "dropout_rate": 0.2,
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100
  },
  
  "recipe_config": {
    "embedding_dim": 64
  },
  
  "financial_config": {
    "prophet_params": {
      "changepoint_prior_scale": 0.05,
      "seasonality_prior_scale": 10
    },
    "xgboost_params": {
      "max_depth": 6,
      "learning_rate": 0.1,
      "n_estimators": 100
    }
  }
}
```

## 5. API de Prédiction

Le module inclut un serveur API FastAPI qui expose les fonctionnalités de prédiction via une interface REST.

### Démarrage du serveur

```bash
# Démarrer le serveur avec les paramètres par défaut
python -m prediction_module serve

# Personnaliser l'hôte et le port
python -m prediction_module serve --host 0.0.0.0 --port 8080

# Activer le mode debug (rechargement automatique)
python -m prediction_module serve --debug
```

### Points d'accès API

#### Prévision des Stocks

**Endpoint**: `/api/stock/forecast`

**Méthode**: POST

**Corps de la requête**:
```json
{
  "days_ahead": 7,
  "ingredients": ["farine", "tomate", "mozzarella"],
  "include_confidence": true
}
```

#### Recommandation de Recettes

**Endpoint**: `/api/recipes/suggest`

**Méthode**: POST

**Corps de la requête**:
```json
{
  "count": 3,
  "recipe_type": "pizza",
  "available_ingredients": {
    "farine": 10.0,
    "tomate": 15.0,
    "mozzarella": 8.0
  },
  "promotions": {
    "mozzarella": 0.15
  }
}
```

#### Prévision Financière

**Endpoint**: `/api/finance/forecast`

**Méthode**: POST

**Corps de la requête**:
```json
{
  "metrics": ["chiffre_affaires", "couts_ingredients", "marge_brute"],
  "days_ahead": 30,
  "include_components": true,
  "detect_anomalies": false
}
```

## 6. Évaluation des Performances

Le module inclut des outils pour évaluer les performances des modèles entraînés.

### En ligne de commande

```bash
# Évaluer tous les modèles
python -m prediction_module evaluate --all

# Évaluer un modèle spécifique
python -m prediction_module evaluate --recipe

# Personnaliser les répertoires
python -m prediction_module evaluate --financial --models_dir=./custom_models --data_dir=./test_data
```

### Rapports d'évaluation

Les rapports d'évaluation sont générés dans le répertoire `evaluation/reports/` au format JSON et Markdown. Des graphiques de performance sont également générés dans `evaluation/plots/`.

## 7. Intégration avec le Serveur Central

Le module de prédiction est conçu pour être intégré facilement avec le serveur central du système "Le Vieux Moulin".

### Configuration de l'intégration

Dans la configuration du serveur central, définir les paramètres d'accès à l'API de prédiction :

```yaml
prediction_module:
  api_url: "http://localhost:8000"
  timeout: 30  # secondes
  retry_attempts: 3
```

### Exemple d'intégration

```python
import requests
import json

# Configuration
api_url = "http://localhost:8000"

# Prévision des stocks
def get_stock_forecast(ingredients, days_ahead=7):
    response = requests.post(
        f"{api_url}/api/stock/forecast",
        json={
            "ingredients": ingredients,
            "days_ahead": days_ahead
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erreur API: {response.status_code} - {response.text}")

# Intégration dans le serveur central
def update_inventory_orders():
    # Obtenir les prévisions
    forecast = get_stock_forecast(["farine", "tomate", "mozzarella"], days_ahead=14)
    
    # Traiter les prévisions et générer des commandes
    for date, ingredients in forecast.items():
        for ingredient, values in ingredients.items():
            if values["mean"] < STOCK_THRESHOLD[ingredient]:
                # Générer une commande
                create_order(ingredient, calculate_order_quantity(values["mean"]))
```

## 8. Déploiement avec Docker

Le module peut être déployé facilement dans un conteneur Docker.

### Construction de l'image

```bash
# À partir du répertoire ml/prediction_module
docker build -t levieuxmoulin/prediction:latest -f Dockerfile .
```

### Exécution du conteneur

```bash
# Démarrer le serveur API
docker run -p 8000:8000 -v /chemin/local/models:/app/models levieuxmoulin/prediction:latest

# Entraîner les modèles
docker run -v /chemin/local/data:/app/data -v /chemin/local/models:/app/models levieuxmoulin/prediction:latest python -m prediction_module train --all

# Évaluer les performances
docker run -v /chemin/local/data:/app/data -v /chemin/local/models:/app/models -v /chemin/local/output:/app/output levieuxmoulin/prediction:latest python -m prediction_module evaluate --all
```

### Docker Compose

Un exemple de configuration Docker Compose pour intégrer le module avec d'autres services :

```yaml
version: '3'

services:
  prediction_api:
    image: levieuxmoulin/prediction:latest
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - MODELS_DIR=/app/models
    restart: unless-stopped
    
  central_server:
    image: levieuxmoulin/central:latest
    ports:
      - "80:80"
    depends_on:
      - prediction_api
      - database
    environment:
      - PREDICTION_API_URL=http://prediction_api:8000
    
  database:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_USER=levieuxmoulin
      - POSTGRES_DB=restaurant

volumes:
  postgres_data:
```

## 9. Maintenance et Mise à Jour

### Réentraînement périodique

Pour maintenir la pertinence des modèles, il est recommandé de les réentraîner régulièrement :

```bash
# Script de réentraînement (à exécuter via cron ou autre planificateur)
#!/bin/bash
cd /chemin/vers/prediction_module
source venv/bin/activate
python -m prediction_module train --all
```

Configuration cron pour un réentraînement hebdomadaire :
```
0 2 * * 1 /chemin/vers/scripts/retrain.sh >> /var/log/retrain.log 2>&1
```

### Gestion des versions

Les modèles suivent un versionnement sémantique (MAJOR.MINOR.PATCH) :
- MAJOR : Changements incompatibles dans l'API ou les prédictions
- MINOR : Ajout de fonctionnalités rétrocompatibles
- PATCH : Corrections de bugs et améliorations mineures

### Sauvegarde des modèles

Il est recommandé de sauvegarder régulièrement les modèles entraînés :

```bash
# Script de sauvegarde
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/chemin/vers/backups/models_$TIMESTAMP"

mkdir -p $BACKUP_DIR
cp -r /chemin/vers/models/* $BACKUP_DIR/

# Optionnel: Compression
tar -czf "$BACKUP_DIR.tar.gz" $BACKUP_DIR
rm -rf $BACKUP_DIR
```

## 10. Résolution des Problèmes

### Problèmes courants et solutions

**Problème**: Le module ne trouve pas les modèles entraînés.
**Solution**: Vérifier la variable d'environnement `MODELS_DIR` ou le chemin fourni à l'initialisation des modèles.

**Problème**: Erreurs lors du prétraitement des données.
**Solution**: Vérifier le format des données d'entrée, notamment les colonnes de date et les types de données.

**Problème**: L'API renvoie des erreurs 500.
**Solution**: Consulter les logs du serveur dans le fichier `logs/api_server.log` pour identifier la cause.

**Problème**: Performances de prédiction dégradées.
**Solution**: Réentraîner les modèles avec des données plus récentes, ou ajuster les hyperparamètres dans le fichier de configuration.

### Journaux (logs)

Les journaux sont essentiels pour diagnostiquer les problèmes :

- **Journal API**: `logs/api_server.log`
- **Journal d'entraînement**: `logs/training.log`
- **Journal d'évaluation**: `logs/evaluation.log`

### Support et contact

Pour toute question ou problème, veuillez :
1. Consulter la documentation complète dans le dossier `docs/`
2. Vérifier les issues ouvertes sur le dépôt GitHub
3. Contacter l'équipe technique à support@levieuxmoulin.fr

---

Ce guide est maintenu par l'équipe technique du restaurant "Le Vieux Moulin". Pour les dernières mises à jour, consultez le dépôt GitHub du projet.
