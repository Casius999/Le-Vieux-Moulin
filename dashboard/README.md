# Dashboard de Pilotage - Restaurant "Le Vieux Moulin"

Ce module fournit un tableau de bord de pilotage interactif pour le système de gestion intelligente du restaurant "Le Vieux Moulin". Il centralise et visualise en temps réel les principales données et indicateurs de performance provenant de tous les autres modules du système.

## Fonctionnalités

- **Vue d'ensemble** : Synthèse des KPIs essentiels à l'activité du restaurant
- **Monitoring IoT & Stocks** : Suivi en temps réel des niveaux de stock et des équipements
- **Analyse des Ventes** : Visualisation des tendances de vente et des prévisions générées par les modèles IA/ML
- **Suivi Marketing** : Tableau de bord des campagnes marketing et des actions de communication
- **Données Financières** : Rapports issus du module de comptabilité (revenus, dépenses, marges)
- **Gestion RH** : Analyse de l'affluence et indicateurs de performance du personnel

## Installation

```bash
# Installer les dépendances frontend
cd dashboard/frontend
npm install

# Installer les dépendances backend
cd ../backend
npm install

# Configuration
cp .env.example .env
# Éditer le fichier .env avec les paramètres spécifiques
```

## Développement

```bash
# Lancer le serveur de développement frontend (port 3000)
cd frontend
npm start

# Lancer le serveur de développement backend (port 5000)
cd backend
npm run dev
```

## Production

```bash
# Build frontend
cd frontend
npm run build

# Lancer en production
cd ../backend
npm start
```

## Documentation

Pour plus de détails, consultez le fichier [DASHBOARD.md](./DASHBOARD.md) qui contient la documentation technique complète du module.