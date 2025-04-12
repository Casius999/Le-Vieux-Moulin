# Module de Prédiction IA/ML - Le Vieux Moulin

Ce module utilise l'intelligence artificielle et le machine learning pour prédire les besoins du restaurant, optimiser la gestion des stocks et générer des suggestions de recettes basées sur les données disponibles.

## Fonctionnalités principales

- Prévision des besoins en matières premières et optimisation des stocks
- Génération automatique de suggestions de recettes (plat du jour, pizza spéciale)
- Production de prévisions financières pour le module de comptabilité avancé

## Structure du module

- `/models/` - Modèles entraînés et prêts à l'emploi
- `/data_processing/` - Outils de prétraitement des données
- `/training/` - Scripts d'entraînement des modèles
- `/utils/` - Fonctions utilitaires communes
- `/evaluation/` - Outils d'évaluation des performances des modèles
- `/api/` - Interface API pour l'intégration avec le serveur central
- `/tests/` - Tests unitaires et d'intégration

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\\Scripts\\activate sous Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

Consultez les sections spécifiques de la documentation pour:
- L'entraînement des modèles (`training/README.md`)
- L'évaluation des performances (`evaluation/README.md`)
- L'utilisation de l'API (`api/README.md`)
- La structure des données attendues (`data_processing/README.md`)

## Documentation complète

Veuillez consulter le fichier `MODEL_DOC.md` pour une description détaillée de l'architecture des modèles, des choix techniques, des étapes d'entraînement et des procédures de déploiement.
