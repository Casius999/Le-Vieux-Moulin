# Module d'Optimisation des Plannings - Le Vieux Moulin

Ce module fournit un système automatisé d'optimisation et de gestion des plannings du personnel pour le restaurant "Le Vieux Moulin", basé sur les prévisions d'affluence, les données historiques et les contraintes du personnel.

## Fonctionnalités

- **Génération automatique de plannings** en fonction des prévisions d'affluence
- **Optimisation des ressources humaines** selon les compétences et disponibilités
- **Prise en compte des contraintes légales** (temps de repos, heures maximum)
- **Interface pour ajustements manuels** par les gestionnaires
- **Notifications automatiques** aux employés lors de la création/modification des plannings
- **Visualisation des plannings** par jour, semaine ou mois
- **Exportation aux formats** standard (PDF, CSV, iCal)
- **Optimisation basée sur le Machine Learning** utilisant les données historiques

## Nouveautés - Optimisation ML

Le module intègre désormais un système d'optimisation avancé basé sur le Machine Learning :

- **Apprentissage à partir des plannings historiques** pour identifier les configurations performantes
- **Analyse des performances individuelles** des employés sur différents postes et horaires
- **Prédiction de la performance** des plannings générés
- **Insights et recommandations** pour améliorer la planification
- **Adaptation intelligente** aux spécificités du restaurant et de son équipe

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/integration/staffing_scheduler
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer les paramètres dans `config.py` selon votre environnement

## Utilisation

### Ligne de commande

Générer un planning pour la semaine prochaine :
```bash
python -m staffing_scheduler.cli generate --start-date 2025-04-21 --days 7
```

Générer un planning avec l'optimiseur ML :
```bash
python -m staffing_scheduler.cli generate-ml --start-date 2025-04-21 --days 7 --model-path models/optimized_model.json
```

### API REST

Le module expose une API REST pour l'intégration avec d'autres systèmes :

```bash
python -m staffing_scheduler.api.server
```

Voir la documentation Swagger à l'adresse : http://localhost:5002/docs

### Interface Web

Un tableau de bord web est disponible pour les gestionnaires :

```bash
python -m staffing_scheduler.webapp
```

## Structure du Projet

- `api/` - API REST pour intégration externe
- `examples/` - Exemples d'utilisation du module
- `integration/` - Intégration avec d'autres modules du système
- `models/` - Modèles pour la représentation des données
- `scheduler/` - Algorithmes d'optimisation des plannings
  - `optimizer.py` - Optimiseur génétique standard
  - `ml_optimizer.py` - Optimiseur basé sur le Machine Learning
- `tests/` - Tests unitaires et d'intégration
- `webapp/` - Interface web pour les gestionnaires

## Modèles d'Optimisation

Le module propose deux types d'algorithmes d'optimisation :

### Optimiseur Standard (Génétique)

L'optimiseur standard utilise un algorithme génétique multi-contraintes pour générer des plannings efficaces :
```python
from staffing_scheduler.scheduler.optimizer import ScheduleOptimizer

optimizer = ScheduleOptimizer(config={
    "population_size": 100,
    "generations": 50,
    "mutation_rate": 0.1
})

schedule = optimizer.generate_schedule(
    start_date=start_date,
    end_date=end_date,
    employees=employees,
    staffing_needs=needs
)
```

### Optimiseur ML

L'optimiseur ML enrichit l'algorithme génétique avec des capacités d'apprentissage à partir des données historiques :
```python
from staffing_scheduler.scheduler.ml_optimizer import MLScheduleOptimizer

# Créer l'optimiseur
ml_optimizer = MLScheduleOptimizer()

# Charger les données historiques
ml_optimizer.load_historical_data(historical_schedules, metrics)

# Entraîner le modèle
ml_optimizer.train_model()

# Générer un planning optimisé
schedule = ml_optimizer.generate_schedule(
    start_date=start_date,
    end_date=end_date,
    employees=employees,
    staffing_needs=needs
)

# Obtenir des insights
insights = ml_optimizer.analyze_optimization_results(schedule)
```

## Exemple d'Utilisation

Un exemple complet est disponible dans `examples/ml_scheduler_demo.py` :

```bash
python -m staffing_scheduler.examples.ml_scheduler_demo
```

Cet exemple démontre :
- La création et l'entraînement d'un modèle ML
- La génération de plannings optimisés
- L'analyse des résultats d'optimisation
- L'export et l'import des modèles pour réutilisation

## Intégration

Ce module s'intègre avec :
- Le **module de prédiction** pour obtenir les prévisions d'affluence
- Le **système de réservation** pour ajuster les plannings en fonction des réservations
- Le **module de comptabilité** pour le suivi des coûts de personnel

Voir [INTEGRATION.md](./INTEGRATION.md) pour les détails d'intégration.

## Configuration

Les paramètres de configuration sont définis dans `config.py`. Les options principales incluent :
- Règles d'optimisation des plannings
- Contraintes légales
- Paramètres de connexion à la base de données
- Configuration de l'optimiseur ML

Pour une description détaillée des méthodes d'optimisation, consultez [STAFFING.md](./STAFFING.md).

## Tests

Exécuter les tests unitaires :
```bash
python -m unittest discover -s tests
```

## Licence

Voir la licence principale du projet Le Vieux Moulin.
