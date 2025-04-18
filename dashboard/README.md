# Dashboard de Pilotage - Le Vieux Moulin

Ce module fournit un dashboard de pilotage complet pour le système de gestion intelligente du restaurant "Le Vieux Moulin". Il permet de visualiser en temps réel les principales données et indicateurs de performance provenant de tous les autres modules du système.

## Fonctionnalités

- **Vue d'ensemble** : Indicateurs clés de performance (KPI) globaux
- **Module IoT & Stocks** : Suivi en temps réel des niveaux de stock et des équipements
- **Ventes & Prédictions** : Analyses des ventes et prévisions générées par les modèles IA/ML
- **Marketing & Communication** : Suivi des campagnes marketing et des actions de communication
- **Finance & Comptabilité** : Rapports financiers, revenus et dépenses
- **Personnel & Plannings** : Analyse de l'affluence et de la performance du personnel

## Architecture

Le dashboard est basé sur une architecture moderne utilisant :

- **Frontend** : React.js avec Material-UI pour l'interface utilisateur
- **État global** : Redux pour la gestion d'état
- **Visualisations** : Recharts pour les graphiques et visualisations
- **Communication** : Axios pour les appels API REST et Socket.io pour les mises à jour en temps réel

## Structure du projet

```
/dashboard/
│
├── frontend/                 # Application React frontend
│   ├── public/               # Fichiers statiques publics
│   ├── src/                  # Code source
│   │   ├── components/       # Composants réutilisables
│   │   ├── views/            # Pages principales (vues)
│   │   ├── store/            # Configuration Redux
│   │   ├── services/         # Services API et WebSocket
│   │   ├── utils/            # Fonctions utilitaires
│   │   └── App.js            # Composant racine de l'application
│   ├── package.json          # Dépendances et scripts
│   └── README.md             # Documentation frontend
│
├── backend/                  # Serveur backend (API et WebSockets)
│   ├── controllers/          # Contrôleurs API
│   ├── middleware/           # Middleware Express
│   ├── routes/               # Définition des routes API
│   ├── services/             # Services métier
│   ├── utils/                # Fonctions utilitaires
│   ├── app.js                # Application Express
│   ├── server.js             # Point d'entrée du serveur
│   ├── package.json          # Dépendances et scripts
│   └── README.md             # Documentation backend
│
├── config/                   # Configuration globale
│   ├── default.json          # Configuration par défaut
│   ├── development.json      # Configuration de développement
│   └── production.json       # Configuration de production
│
├── test/                     # Tests automatisés
│   ├── unit/                 # Tests unitaires
│   └── integration/          # Tests d'intégration
│
├── docs/                     # Documentation supplémentaire
│   ├── architecture/         # Diagrammes d'architecture
│   ├── api/                  # Documentation API
│   └── user-guide/           # Guide utilisateur
│
├── .env.example              # Exemple de fichier d'environnement
├── .gitignore                # Fichiers ignorés par Git
├── docker-compose.yml        # Configuration Docker Compose
├── Dockerfile                # Instructions de build Docker
├── DASHBOARD.md              # Documentation principale du dashboard
└── README.md                 # Ce fichier
```

## Installation et déploiement

### Prérequis

- Node.js 18.x ou supérieur
- npm 8.x ou supérieur
- MongoDB (optionnel, pour le cache et les logs)
- Accès au serveur central via API

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/dashboard

# Installation des dépendances frontend
cd frontend
npm install

# Installation des dépendances backend
cd ../backend
npm install

# Configuration
cp .env.example .env
# Éditer le fichier .env avec les paramètres spécifiques
```

### Développement

```bash
# Lancer le serveur de développement frontend (port 3000)
cd frontend
npm start

# Lancer le serveur de développement backend (port 5000)
cd backend
npm run dev
```

### Production

```bash
# Build frontend
cd frontend
npm run build

# Lancer en production
cd ../backend
npm start
```

### Docker

```bash
# Construire et lancer avec Docker Compose
docker-compose up -d
```

## Connexion aux services internes

Le dashboard communique avec plusieurs services du système :

- **API Centrale** : Récupération des données consolidées
- **WebSockets** : Mises à jour en temps réel des données IoT et ventes
- **API ML** : Accès aux prédictions et recommandations
- **API Comptabilité** : Récupération des données financières

La configuration de ces connexions se fait dans le fichier `.env` ou dans les fichiers de configuration appropriés dans le dossier `/config`.

## Personnalisation

Le dashboard est entièrement personnalisable :

1. Accédez à l'interface d'administration (accessible via le menu utilisateur)
2. Naviguez vers "Configuration du dashboard"
3. Sélectionnez les widgets à afficher sur chaque page
4. Configurez les seuils d'alerte et les indicateurs clés
5. Ajustez les périodes de rafraîchissement des données

## Sécurité

- **Authentification** : JWT pour sécuriser les appels API
- **Autorisation** : Système de rôles pour contrôler l'accès aux différentes sections
- **Protection des données** : Chiffrement des communications et des données sensibles
- **Audit** : Journalisation des actions utilisateur

## Documentation supplémentaire

Pour plus de détails, consultez :

- [DASHBOARD.md](./DASHBOARD.md) - Documentation technique complète
- [frontend/README.md](./frontend/README.md) - Guide du développement frontend
- [backend/README.md](./backend/README.md) - Guide du développement backend
- [docs/](./docs/) - Documentation utilisateur et diagrammes d'architecture

## Contribution

Pour contribuer au développement du dashboard, veuillez consulter le fichier [CONTRIBUTING.md](../CONTRIBUTING.md) à la racine du dépôt principal.

## Licence

© 2025 Le Vieux Moulin - Tous droits réservés
