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

- `algorithm/` - Algorithmes d'optimisation des plannings
- `api/` - API REST pour intégration externe
- `cli/` - Interface en ligne de commande
- `data/` - Modèles de données et accès à la base de données 
- `models/` - Modèles pour la représentation des données
- `tests/` - Tests unitaires et d'intégration
- `utils/` - Utilitaires divers
- `webapp/` - Interface web pour les gestionnaires

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

## Licence

Voir la licence principale du projet Le Vieux Moulin.
