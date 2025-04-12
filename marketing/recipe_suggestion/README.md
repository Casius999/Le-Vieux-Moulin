# Module de Suggestion de Recettes Dynamiques - Le Vieux Moulin

Ce module analyse les promotions des fournisseurs et les tendances des données clients pour générer automatiquement des suggestions de recettes adaptées et des offres promotionnelles pour le restaurant "Le Vieux Moulin".

## Fonctionnalités

- Récupération et analyse des promotions fournisseurs en temps réel
- Analyse des tendances locales et préférences clients
- Génération automatique de suggestions de recettes (pizza du jour, plat spécial)
- Création d'offres promotionnelles personnalisées
- Intégration avec les systèmes de vente et de marketing

## Structure du Module

```
recipe_suggestion/
├── README.md                 # Ce fichier
├── RECIPE_STRATEGY.md        # Documentation détaillée de l'algorithme
├── src/                      # Code source
│   ├── api_connectors/       # Connecteurs API pour les fournisseurs
│   ├── trend_analyzer/       # Analyse des tendances et préférences
│   ├── recipe_generator/     # Générateur de recettes
│   └── promotion_manager/    # Gestionnaire de promotions
├── config/                   # Fichiers de configuration
│   ├── providers.json        # Configuration des fournisseurs
│   ├── recipes_base.json     # Base de recettes disponibles
│   └── settings.json         # Paramètres généraux
├── tests/                    # Tests unitaires et d'intégration
└── examples/                 # Exemples d'utilisation
```

## Installation

### Prérequis

- Python 3.9+ ou Node.js 16+
- Accès aux API des fournisseurs configurés
- Connexion à la base de données centrale du restaurant

### Installation

```bash
# Création d'un environnement virtuel (Python)
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows

# Installation des dépendances
pip install -r requirements.txt

# Configuration initiale
python src/setup.py
```

## Configuration

1. Modifiez le fichier `config/settings.json` pour définir les paramètres généraux
2. Configurez les accès aux API fournisseurs dans `config/providers.json`
3. Adaptez les recettes de base dans `config/recipes_base.json` selon les spécialités du restaurant

## Utilisation

### Démarrage du service

```bash
# Démarrer le service de suggestion de recettes
python src/main.py

# Mode développement avec rechargement automatique
python src/main.py --dev
```

### Exemples d'utilisation

#### Génération manuelle d'une suggestion

```python
from recipe_suggestion.src.recipe_generator import generate_suggestion

# Générer une suggestion de pizza
suggestion = generate_suggestion(
    meal_type="pizza", 
    constraints={"vegetarian": False, "spicy": True}
)
print(suggestion)
```

#### Intégration avec le système de menus

```python
from recipe_suggestion.src.api import get_daily_special

# Obtenir la suggestion du jour pour le menu
daily_special = get_daily_special()
print(f"Plat du jour: {daily_special['name']}")
print(f"Prix: {daily_special['price']}€")
print(f"Ingrédients: {', '.join(daily_special['ingredients'])}")
```

## Intégration avec les Autres Modules

### Module de ML/IA

Le module de recettes interagit avec le module d'intelligence artificielle (`/ml/prediction_module`) pour améliorer ses suggestions:

- Il utilise les prévisions de consommation pour anticiper les tendances
- Il réutilise les modèles de recommandation pour affiner les suggestions
- Il partage ses données avec le module ML pour entraînement continu

Interface principale: `/ml/prediction_module/api/recommendation_endpoint`

### Module Marketing

Le module s'intègre au système marketing global:

- Il fournit des suggestions pour les campagnes de promotion
- Il reçoit des données sur l'efficacité des promotions précédentes
- Il peut déclencher automatiquement des campagnes selon les ingrédients à écouler

### Module UI

Les suggestions sont exposées à l'interface utilisateur via:

- Une API REST (documentation dans `/api/README.md`)
- Des webhooks pour les mises à jour en temps réel
- Des exports de données formatées pour l'affichage

## Monitoring et Performances

Le module inclut un tableau de bord de surveillance accessible à:
`http://localhost:5000/dashboard`

Métriques clés:
- Taux d'adoption des suggestions (% de suggestions qui deviennent des commandes)
- Temps de génération des suggestions
- ROI des promotions suggérées
- Satisfaction client (si intégré au système de feedback)

## Dépannage

### Problèmes courants

- **Pas de suggestions générées**: Vérifiez les accès API des fournisseurs
- **Suggestions peu pertinentes**: Assurez-vous que la base de données des préférences clients est à jour
- **Erreurs d'intégration**: Vérifiez les logs dans `/var/log/recipe_suggestion/`

## Roadmap

- [ ] Intégration des données météorologiques pour ajuster les suggestions
- [ ] Système de notation interne des suggestions
- [ ] Interface d'administration pour ajuster manuellement les paramètres
- [ ] Module d'analyse visuelle des ingrédients disponibles

## Licence

© 2025 Le Vieux Moulin - Tous droits réservés