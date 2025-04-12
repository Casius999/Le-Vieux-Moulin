# Documentation Détaillée des Modèles IA/ML - Le Vieux Moulin

Ce document décrit en détail l'architecture des modèles d'intelligence artificielle et d'apprentissage automatique utilisés dans le module de prédiction du restaurant "Le Vieux Moulin". Il couvre les choix techniques, les algorithmes, les hyperparamètres, les étapes d'entraînement et les procédures de déploiement.

## Table des matières

1. [Architecture des modèles](#1-architecture-des-modèles)
2. [Choix techniques](#2-choix-techniques)
3. [Prétraitement des données](#3-prétraitement-des-données)
4. [Entraînement des modèles](#4-entraînement-des-modèles)
5. [Évaluation des performances](#5-évaluation-des-performances)
6. [Déploiement et intégration](#6-déploiement-et-intégration)
7. [Maintenance et mise à jour](#7-maintenance-et-mise-à-jour)

## 1. Architecture des modèles

Le module de prédiction repose sur trois modèles principaux interconnectés:

### 1.1. Modèle de prévision des besoins en matières premières

**Architecture**: Réseau de neurones récurrents (LSTM)

- **Couche d'entrée**: Variables temporelles (jour, mois, saison, vacances, événements locaux) + historique des ventes et stocks (7-30 jours)
- **Couches cachées**: 2 couches LSTM bidirectionnelles (128 unités chacune)
- **Couche de sortie**: Prédiction des besoins pour les 7 prochains jours par ingrédient

Le modèle utilise une architecture encoder-decoder avec un mécanisme d'attention pour donner plus de poids aux jours similaires dans l'historique.

### 1.2. Modèle de recommandation de recettes

**Architecture**: Système hybride combinant:

- **Filtrage collaboratif**: Matrice de factorisation pour capturer les préférences clients
- **Recommandation basée sur le contenu**: Réseau de neurones feed-forward pour analyser les attributs des recettes
- **Module contextuel**: Intégration des données contextuelles (saison, météo, stock disponible, promotions)

### 1.3. Modèle de prévision financière

**Architecture**: Ensemble d'algorithmes

- **Tendances à long terme**: Modèle Prophet (Facebook) pour la décomposition des séries temporelles
- **Variations à court terme**: XGBoost pour la prédiction des écarts par rapport à la tendance
- **Détection d'anomalies**: Isolation Forest pour identifier les transactions inhabituelles

## 2. Choix techniques

### 2.1. Frameworks et bibliothèques

- **TensorFlow 2.11+**: Entraînement et déploiement des modèles de deep learning
- **PyTorch 1.13+**: Prototypage rapide et expérimentation
- **scikit-learn 1.2+**: Algorithmes classiques de ML et prétraitement
- **Prophet**: Modélisation de séries temporelles avec décomposition des tendances
- **XGBoost**: Modèles d'arbres boostés pour la haute précision
- **Pandas & NumPy**: Manipulation et prétraitement des données
- **FastAPI**: API REST pour servir les prédictions en temps réel

### 2.2. Justification des choix algorithmiques

- **LSTM pour les prévisions de stock**: Capacité à modéliser des dépendances temporelles complexes et à capturer les motifs saisonniers dans les données de vente.
- **Système hybride pour les recommandations**: Combine les avantages du filtrage collaboratif (préférences similaires entre clients) et des approches basées sur le contenu (caractéristiques des recettes).
- **Ensemble pour les prévisions financières**: Robustesse face au bruit dans les données financières et capacité à modéliser différentes échelles temporelles.

### 2.3. Hyperparamètres clés

**Modèle de prévision des stocks**:
- Taille de batch: 32
- Taux d'apprentissage: 0.001 avec décroissance exponentielle
- Dropout: 0.2
- Fonction d'activation: ReLU (couches internes) et linéaire (couche de sortie)
- Optimiseur: Adam

**Modèle de recommandation**:
- Dimensions latentes: 64
- Régularisation L2: 0.01
- Nombre de couches cachées: 3 (128, 64, 32 unités)
- Taux d'apprentissage: 0.005

**Modèle financier**:
- XGBoost: max_depth=6, learning_rate=0.1, n_estimators=100
- Prophet: changepoint_prior_scale=0.05, seasonality_prior_scale=10
- Isolation Forest: contamination=0.02

## 3. Prétraitement des données

### 3.1. Sources de données

- **Données de vente**: Historique des commandes, plats vendus, chiffre d'affaires
- **Données de stock**: Niveaux d'inventaire, commandes fournisseurs, délais de livraison
- **Données contextuelles**: Météo, jours fériés, événements locaux, promotions
- **Données client**: Historique des préférences, fréquence des visites (anonymisées)
- **Données fournisseurs**: Prix, disponibilité, promotions en cours

### 3.2. Pipeline de prétraitement

1. **Nettoyage des données**:
   - Détection et gestion des valeurs manquantes
   - Identification et traitement des valeurs aberrantes
   - Standardisation des formats (dates, montants, unités)

2. **Feature engineering**:
   - Extraction de caractéristiques temporelles (jour de semaine, mois, saison, etc.)
   - Création d'indicateurs pour les événements spéciaux et périodes de forte affluence
   - Calcul de métriques dérivées (taux de rotation, marge par produit, etc.)
   - Création de variables retardées (lag features) pour capturer les tendances

3. **Normalisation et scaling**:
   - StandardScaler pour les variables continues
   - Encodage one-hot pour les variables catégorielles
   - Normalisation MinMax pour les entrées des réseaux de neurones

4. **Segmentation des données**:
   - Division chronologique pour l'entraînement, la validation et le test
   - Stratification pour préserver la distribution des variables critiques

## 4. Entraînement des modèles

### 4.1. Préparation des données d'entraînement

- **Horizon de prévision**: 7 jours pour les stocks, 30 jours pour les finances
- **Fenêtre d'historique**: 30 jours glissants pour les modèles LSTM
- **Ratio de division**: 70% entraînement, 15% validation, 15% test

### 4.2. Procédure d'entraînement

1. **Initialisation**: Chargement et prétraitement des données historiques
2. **Partitionnement**: Division des données en ensembles d'entraînement, validation et test
3. **Recherche d'hyperparamètres**: Utilisation de validation croisée et Bayesian Optimization
4. **Entraînement**: 
   - Entraînement par lots (batch) avec sauvegarde des meilleurs modèles
   - Early stopping basé sur l'erreur de validation
   - Réglage fin sur les données les plus récentes
5. **Validation**: Évaluation sur des données non vues durant l'entraînement
6. **Test final**: Vérification des performances sur l'ensemble de test

### 4.3. Stratégies d'optimisation

- **Augmentation des données**: Génération de scénarios synthétiques pour les cas rares
- **Transfer learning**: Pré-entraînement sur des données génériques de restauration
- **Fine-tuning**: Adaptation aux spécificités du restaurant avec les données locales
- **Ensembling**: Combinaison de plusieurs modèles pour améliorer la robustesse

## 5. Évaluation des performances

### 5.1. Métriques d'évaluation

**Modèle de prévision des stocks**:
- MAE (Mean Absolute Error): Erreur moyenne en unités d'ingrédients
- MAPE (Mean Absolute Percentage Error): Erreur relative en pourcentage
- RMSE (Root Mean Square Error): Sensibilité aux grandes erreurs

**Modèle de recommandation**:
- Précision: Proportion de suggestions effectivement adoptées
- Rappel: Capacité à identifier toutes les options pertinentes
- NDCG (Normalized Discounted Cumulative Gain): Qualité du classement des suggestions

**Modèle financier**:
- R² (coefficient de détermination): Variance expliquée par le modèle
- MAE (Mean Absolute Error): Erreur moyenne en euros
- Intervalle de confiance (90%): Plage de prévision pour la gestion des risques

### 5.2. Benchmarks et objectifs

| Modèle | Métrique | Objectif | État actuel |
|--------|----------|----------|-------------|
| Stocks | MAPE | < 15% | 18% |
| Stocks | MAE | < 5 unités | 6.2 unités |
| Recettes | Précision@5 | > 80% | 75% |
| Financier | MAPE mensuel | < 5% | 7% |

### 5.3. Tests A/B

Des tests A/B seront réalisés pour comparer les performances des nouvelles versions de modèles avec celles actuellement en production:
- 30% des prédictions utiliseront le nouveau modèle
- 70% utiliseront le modèle existant
- Les métriques commerciales (réduction du gaspillage, augmentation des ventes) seront mesurées

## 6. Déploiement et intégration

### 6.1. Architecture de déploiement

```
+-------------------+     +--------------------+     +------------------+
| Serveur central   |     | Service ML         |     | Stockage modèles |
| (API Gateway)     |<--->| (Conteneur Docker) |<--->| (MinIO/S3)       |
+-------------------+     +--------------------+     +------------------+
        ^                          ^
        |                          |
        v                          v
+-------------------+     +--------------------+
| Base de données   |     | Serveur de logs    |
| (PostgreSQL)      |     | (ELK Stack)        |
+-------------------+     +--------------------+
```

### 6.2. Pipeline de déploiement

1. Entraînement des modèles sur l'infrastructure de développement
2. Evaluation des performances sur des données de test
3. Exportation des modèles au format approprié (SavedModel, ONNX)
4. Tests d'intégration avec des données fictives
5. Déploiement en préproduction pour les tests utilisateurs
6. Déploiement progressif en production (Canary release)
7. Surveillance continue des performances

### 6.3. Intégration avec le serveur central

- **API REST** avec documentation OpenAPI
- **Endpoints principaux**:
  - `/api/predictions/stock?horizon=7&ingredients=all`
  - `/api/suggestions/recipes?count=5&constraints=in_stock`
  - `/api/predictions/finance?horizon=30&metrics=revenue,costs`
- **Authentification**: JWT avec permissions granulaires
- **Gestion d'erreurs**: Fallback vers des prédictions de base en cas d'échec

### 6.4. Monitoring et observabilité

- Journalisation des prédictions et des entrées associées
- Suivi de la dérive des données (data drift)
- Alertes en cas de dégradation des performances
- Tableaux de bord pour visualiser les métriques clés

## 7. Maintenance et mise à jour

### 7.1. Réentraînement des modèles

- **Fréquence**: Hebdomadaire pour la mise à jour incrémentale, mensuelle pour le réentraînement complet
- **Déclencheurs**: Automatique (planifié) ou manuel (après changements significatifs)
- **Validation**: Tests automatisés avant déploiement

### 7.2. Gestion des versions

- Versionnage sémantique pour les modèles (MAJOR.MINOR.PATCH)
- Conservation de l'historique des modèles pour rollback
- Documentation des changements dans un CHANGELOG

### 7.3. Amélioration continue

- Analyse des erreurs de prédiction pour identifier les axes d'amélioration
- Expérimentation avec de nouvelles architectures et algorithmes
- Intégration de nouvelles sources de données (réseaux sociaux, avis clients, etc.)
- Optimisation des performances et de l'utilisation des ressources

---

## Annexes

### A. Diagrammes d'architecture des modèles

*Les diagrammes détaillés seront ajoutés dans le dossier `docs/diagrams/`*

### B. Exemples de code d'utilisation

```python
# Exemple d'utilisation du modèle de prévision des stocks
from prediction_module.models.stock_forecaster import StockForecaster

# Initialiser le modèle
forecaster = StockForecaster(model_path='models/stock_lstm_v2.h5')

# Obtenir les prévisions pour les 7 prochains jours
predictions = forecaster.predict(
    days_ahead=7,
    ingredients=['farine', 'tomate', 'mozzarella', 'huile_olive'],
    include_confidence=True
)

# Afficher les résultats
for day, items in predictions.items():
    print(f"Prévisions pour {day}:")
    for ingredient, amount in items.items():
        print(f"  - {ingredient}: {amount['mean']:.2f} {amount['unit']} (±{amount['confidence_interval']:.2f})")
```

### C. Références et publications

- LSTMs pour la prévision des séries temporelles: Hochreiter, S., & Schmidhuber, J. (1997)
- Systèmes de recommandation hybrides: Burke, R. (2002)
- XGBoost: Chen, T., & Guestrin, C. (2016)
- Prophet: Taylor, S. J., & Letham, B. (2018)
