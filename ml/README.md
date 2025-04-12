# Module IA/ML - Le Vieux Moulin

Ce répertoire contient tous les modèles d'intelligence artificielle et de machine learning utilisés dans le système de gestion intelligente du restaurant "Le Vieux Moulin". Les modèles sont conçus pour optimiser les opérations, prévoir les besoins en stocks, générer des suggestions culinaires et fournir des analyses pour le module de comptabilité avancé.

## Structure du Répertoire

- **/models/** - Modèles entraînés et prêts à être déployés
- **/training/** - Scripts et notebooks pour l'entraînement des modèles
- **/data_processing/** - Outils de prétraitement et nettoyage des données
- **/inference/** - API et services d'inférence
- **/evaluation/** - Métriques et outils d'évaluation des modèles

## Modèles Implémentés

### 1. Prévision de Consommation
- **Objectif** : Prévoir les besoins en ingrédients basés sur l'historique, la saisonnalité et les événements spéciaux
- **Algorithmes** : ARIMA, Prophet, LSTM
- **Données d'entrée** : Historique des ventes, stocks, réservations, météo, événements locaux
- **Performances** : MAPE < 15% sur 7 jours, < 20% sur 14 jours

```python
# Exemple d'utilisation du modèle de prévision
from models.forecasting import StockForecaster

# Initialiser le modèle
forecaster = StockForecaster(model_path='models/stock_lstm_v2.h5')

# Obtenir les prévisions pour les 7 prochains jours par ingrédient
predictions = forecaster.predict(
    days_ahead=7,
    ingredients=['farine', 'tomate', 'mozzarella', 'huile_olive'],
    include_confidence=True
)

print(predictions)
```

### 2. Détection d'Anomalies
- **Objectif** : Identifier les anomalies dans la consommation ou le fonctionnement des équipements
- **Algorithmes** : Isolation Forest, Autoencoders, DBSCAN
- **Données d'entrée** : Séries temporelles des capteurs, consommation des ingrédients
- **Performances** : Précision > 92%, Rappel > 85%

### 3. Recommandation de Recettes
- **Objectif** : Suggérer des plats spéciaux basés sur les stocks, les tendances et les préférences clients
- **Algorithmes** : Systèmes de recommandation, NLP pour analyse des tendances
- **Données d'entrée** : Stocks actuels, popularité des plats, tendances gastronomiques, saison
- **Performances** : Taux d'adoption > 75% pour les suggestions

### 4. Optimisation des Stocks
- **Objectif** : Minimiser le gaspillage tout en évitant les ruptures de stock
- **Algorithmes** : Algorithmes génétiques, Optimisation multi-objectifs
- **Données d'entrée** : Prévisions de consommation, contraintes de stockage, délais fournisseurs
- **Performances** : Réduction du gaspillage > 25%, Taux de rupture de stock < 2%

### 5. Analyse Financière
- **Objectif** : Fournir des analyses pour le module de comptabilité et détecter les anomalies financières
- **Algorithmes** : Régression, Clustering, Détection d'anomalies
- **Données d'entrée** : Historique financier, transactions de caisse, coûts des matières premières
- **Performances** : Précision des prévisions financières > 90%

## Environnement et Dépendances

### Environnement de développement
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\\Scripts\\activate sous Windows

# Installer les dépendances
pip install -r requirements.txt
```

### Dépendances principales
- Python 3.9+
- TensorFlow 2.8+
- PyTorch 1.12+
- scikit-learn 1.0+
- Pandas 1.4+
- NumPy 1.21+
- Prophet 1.0+
- XGBoost 1.5+

## Entraînement des Modèles

Tous les modèles peuvent être entraînés à partir des scripts dans le dossier `/training/`. Exemple:

```bash
# Entraîner le modèle de prévision de consommation
cd training
python train_forecasting_model.py --data ../data/processed/sales_history.csv --epochs 100 --batch_size 32
```

Chaque script d'entraînement accepte plusieurs paramètres pour personnaliser le processus:
- Source de données
- Hyperparamètres du modèle
- Configuration de l'entraînement
- Chemin de sauvegarde

## Déploiement des Modèles

Les modèles entraînés sont exportés au format standard (TensorFlow SavedModel, ONNX, etc.) et peuvent être déployés via l'API d'inférence:

```bash
# Démarrer le service d'inférence
cd inference
python inference_server.py --models_dir ../models/ --port 5000
```

L'API expose des endpoints RESTful pour chaque modèle:
- `/api/forecast` - Pour les prévisions de consommation
- `/api/anomalies` - Pour la détection d'anomalies
- `/api/recipes` - Pour les suggestions de recettes
- `/api/optimize` - Pour l'optimisation des stocks
- `/api/finance` - Pour l'analyse financière

## Évaluation et Surveillance

Les performances des modèles sont évaluées en continu et peuvent être visualisées via le dashboard:

```bash
# Lancer le dashboard d'évaluation
cd evaluation
python metrics_dashboard.py
```

Le système garde également une trace des prédictions et résultats pour améliorer continuellement les modèles.

## Intégration Multi-Établissements

Les modèles sont conçus pour prendre en charge plusieurs établissements:
- Modèles partagés avec paramètres spécifiques par établissement
- Transfert d'apprentissage entre établissements
- Modèles globaux enrichis par les données locales

## Mise à Jour et Maintenance

Les modèles sont réentraînés périodiquement:
- Automatiquement chaque semaine avec les nouvelles données
- Manuellement après des changements significatifs (menu, équipement, etc.)
- Version des modèles suivant le format `{type}_{algorithme}_v{version}`

---

Pour plus d'informations sur l'utilisation et le développement des modèles, consultez la documentation complète ou contactez l'équipe data science.
