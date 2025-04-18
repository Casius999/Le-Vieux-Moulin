# Documentation Technique du Dashboard - Le Vieux Moulin

## Table des matières

1. [Architecture détaillée](#architecture-détaillée)
   - [Architecture Frontend](#architecture-frontend)
   - [Architecture Backend](#architecture-backend)
   - [Flux de données](#flux-de-données)

2. [Technologies utilisées](#technologies-utilisées)
   - [Frontend](#frontend)
   - [Backend](#backend)
   - [Outils de développement](#outils-de-développement)

3. [Installation et configuration](#installation-et-configuration)
   - [Prérequis](#prérequis)
   - [Configuration du frontend](#configuration-du-frontend)
   - [Configuration du backend](#configuration-du-backend)
   - [Variables d'environnement](#variables-denvironnement)

4. [Communication avec les modules du système](#communication-avec-les-modules-du-système)
   - [Module IoT](#module-iot)
   - [Module IA/ML](#module-iaml)
   - [Module intégration API](#module-intégration-api)
   - [Module marketing](#module-marketing)
   - [Module comptabilité](#module-comptabilité)

5. [Structure des données](#structure-des-données)
   - [Modèles de données](#modèles-de-données)
   - [Endpoints API](#endpoints-api)
   - [Schéma des événements WebSocket](#schéma-des-événements-websocket)

6. [Composants du dashboard](#composants-du-dashboard)
   - [Vue d'ensemble](#vue-densemble)
   - [Monitoring des stocks](#monitoring-des-stocks)
   - [Analyse des ventes](#analyse-des-ventes)
   - [Suivi marketing](#suivi-marketing)
   - [Rapports financiers](#rapports-financiers)
   - [Gestion du personnel](#gestion-du-personnel)

7. [Sécurité](#sécurité)
   - [Authentification et autorisation](#authentification-et-autorisation)
   - [Sécurisation des communications](#sécurisation-des-communications)
   - [Protection des données](#protection-des-données)

8. [Tests](#tests)
   - [Tests unitaires](#tests-unitaires)
   - [Tests d'intégration](#tests-dintégration)
   - [Tests de performance](#tests-de-performance)

9. [Déploiement](#déploiement)
   - [Déploiement manuel](#déploiement-manuel)
   - [Déploiement avec Docker](#déploiement-avec-docker)
   - [CI/CD](#cicd)

10. [Maintenance et mise à jour](#maintenance-et-mise-à-jour)
    - [Logs et surveillance](#logs-et-surveillance)
    - [Stratégie de mise à jour](#stratégie-de-mise-à-jour)
    - [Sauvegarde et restauration](#sauvegarde-et-restauration)

11. [Cas d'utilisation et exemples](#cas-dutilisation-et-exemples)
    - [Scénarios courants](#scénarios-courants)
    - [Interprétation des visualisations](#interprétation-des-visualisations)
    - [Prise de décision basée sur les données](#prise-de-décision-basée-sur-les-données)

12. [Résolution des problèmes](#résolution-des-problèmes)
    - [Problèmes courants](#problèmes-courants)
    - [FAQ](#faq)

## Architecture détaillée

### Architecture Frontend

L'architecture frontend du dashboard suit le modèle React avec Redux pour la gestion d'état. Voici les composants principaux :

- **App.js** : Point d'entrée principal de l'application React
- **Routes.js** : Configuration des routes de l'application
- **Store** : Configuration du store Redux avec les reducers et middleware
- **Views** : Composants de page pour chaque section du dashboard
- **Components** : Composants réutilisables (graphiques, tableaux, etc.)
- **Services** : Services pour la communication avec l'API et les WebSockets
- **Utils** : Fonctions utilitaires pour le formatage, les calculs, etc.

Le frontend implémente les principes suivants :
- **Composants fonctionnels** avec Hooks React
- **Lazy loading** pour optimiser le chargement des modules
- **Responsive design** pour s'adapter à différentes tailles d'écran
- **Thème personnalisable** avec support du mode sombre
- **Internationalisation** pour supporter plusieurs langues

### Architecture Backend

Le backend agit comme une couche d'abstraction entre le frontend et les différents modules du système "Le Vieux Moulin". Il suit une architecture Express.js :

- **server.js** : Point d'entrée du serveur
- **app.js** : Configuration de l'application Express
- **routes** : Définition des routes API
- **controllers** : Logique de traitement des requêtes
- **services** : Services métier et intégration avec les modules externes
- **middleware** : Middlewares pour l'authentification, la journalisation, etc.
- **utils** : Fonctions utilitaires
- **socketHandlers** : Gestion des communications WebSocket

Le backend sert plusieurs objectifs :
- **Aggregation** : Combine les données de plusieurs sources
- **Mise en cache** : Cache les données fréquemment demandées
- **Transformation** : Adapte les données aux besoins du frontend
- **Sécurité** : Applique les contrôles d'accès et filtre les données sensibles

### Flux de données

1. **Collecte** : Les données sont collectées par les différents modules du système (IoT, ML, API, etc.)
2. **Traitement** : Le backend agrège et transforme ces données
3. **Stockage** : Certaines données peuvent être mises en cache ou stockées pour analyse
4. **Distribution** :
   - Les données statiques/historiques sont fournies via l'API REST
   - Les mises à jour en temps réel sont envoyées via WebSockets
5. **Présentation** : Le frontend affiche les données sous forme de graphiques, tableaux, etc.
6. **Interaction** : L'utilisateur interagit avec les visualisations et peut déclencher des actions

```
┌────────────┐   REST API   ┌────────────┐   WebSockets   ┌────────────┐
│  Modules   │ ──────────> │  Backend   │ ──────────────>│  Frontend  │
│  externes  │ <─────────  │  Dashboard │ <──────────────│  Dashboard │
└────────────┘   Webhooks   └────────────┘   REST API     └────────────┘
     │                            │                            │
     │                            │                            │
     ▼                            ▼                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Base de données principale                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Technologies utilisées

### Frontend

- **React 18** : Bibliothèque JavaScript pour construire l'interface utilisateur
- **Redux Toolkit** : Gestion d'état avancée
- **Material-UI v5** : Framework de composants UI
- **Recharts** : Bibliothèque de visualisation de données
- **Axios** : Client HTTP pour les requêtes API
- **Socket.io Client** : Communication WebSocket
- **i18next** : Internationalisation
- **date-fns** : Manipulation des dates
- **react-router-dom** : Routage
- **formik** : Gestion des formulaires
- **yup** : Validation des schémas

### Backend

- **Node.js 18+** : Environnement d'exécution JavaScript
- **Express.js** : Framework web
- **Socket.io** : Communication WebSocket
- **Mongoose** (optionnel) : ORM pour MongoDB
- **Redis** (optionnel) : Pour la mise en cache et la gestion des sessions
- **JWT** : Authentification basée sur tokens
- **winston** : Journalisation
- **joi** : Validation des données
- **helmet** : Sécurisation des en-têtes HTTP
- **cors** : Gestion du partage de ressources entre origines
- **compression** : Compression des réponses HTTP

### Outils de développement

- **ESLint** : Linter JavaScript
- **Prettier** : Formattage du code
- **Jest** : Framework de test
- **Testing Library** : Test des composants React
- **Supertest** : Test des API REST
- **Webpack** : Bundling et optimisation
- **Babel** : Transpilation du code
- **nodemon** : Rechargement automatique du serveur en développement
- **Docker** : Conteneurisation pour le déploiement
- **Swagger** : Documentation API
- **Storybook** : Développement et documentation des composants UI

## Installation et configuration

### Prérequis

- Node.js 18.x ou supérieur
- npm 8.x ou supérieur ou yarn 1.22.x ou supérieur
- Git
- Accès aux API du système "Le Vieux Moulin"
- (Optionnel) MongoDB pour le stockage local
- (Optionnel) Redis pour la mise en cache

### Configuration du frontend

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/dashboard/frontend

# Installer les dépendances
npm install

# Configurer les variables d'environnement
cp .env.example .env.local
# Éditer le fichier .env.local selon votre environnement

# Lancer en mode développement
npm start

# Compiler pour la production
npm run build
```

### Configuration du backend

```bash
# Se déplacer dans le dossier backend
cd ../backend

# Installer les dépendances
npm install

# Configurer les variables d'environnement
cp .env.example .env
# Éditer le fichier .env selon votre environnement

# Lancer en mode développement
npm run dev

# Lancer en mode production
npm start
```

### Variables d'environnement

#### Frontend (.env.local)

```
# API Backend
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SOCKET_URL=http://localhost:5000

# Configuration
REACT_APP_REFRESH_INTERVAL=60000  # Intervalle de rafraîchissement en ms
REACT_APP_DEFAULT_LANGUAGE=fr     # Langue par défaut
REACT_APP_THEME=light             # Thème par défaut (light/dark)

# Fonctionnalités
REACT_APP_ENABLE_NOTIFICATIONS=true
REACT_APP_ENABLE_OFFLINE_MODE=true
```

#### Backend (.env)

```
# Serveur
PORT=5000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000

# Sécurité
JWT_SECRET=your_jwt_secret_key
JWT_EXPIRATION=1d

# API Centrale
CENTRAL_API_URL=http://localhost:8000/api
CENTRAL_API_KEY=your_api_key

# Base de données (optionnel)
MONGODB_URI=mongodb://localhost:27017/dashboard
REDIS_URL=redis://localhost:6379
SESSION_SECRET=your_session_secret

# Logging
LOG_LEVEL=info
LOG_FILE=logs/app.log
```

## Communication avec les modules du système

### Module IoT

Le dashboard communique avec le module IoT pour récupérer :
- Niveaux de stock en temps réel
- État des équipements (température four, friteuse, etc.)
- Historique des mesures pour analyse de tendances

**Méthode de communication** :
- API REST pour les données historiques
- WebSockets (MQTT sur WebSocket) pour les mises à jour en temps réel

**Exemple de données reçues** :
```json
{
  "timestamp": 1649247668.453,
  "device_id": "cuisine_principale",
  "type": "weight_sensors",
  "data": {
    "bac_farine": 2450.5,
    "bac_sucre": 1230.8
  }
}
```

### Module IA/ML

Le dashboard intègre les prédictions et recommandations du module IA/ML :
- Prévisions des niveaux de stock nécessaires
- Recommandations pour l'optimisation du menu
- Détection d'anomalies dans la consommation

**Méthode de communication** :
- API REST pour récupérer les dernières prédictions
- Webhooks pour les alertes et notifications

**Exemple d'intégration dans le frontend** :
```javascript
// services/predictionService.js
import axios from 'axios';

export const fetchStockPredictions = async (itemId, days = 7) => {
  try {
    const response = await axios.get(`/api/predictions/stock/${itemId}`, {
      params: { days }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching stock predictions:', error);
    throw error;
  }
};
```

### Module intégration API

Le dashboard utilise le module d'intégration API pour :
- Afficher les transactions des caisses enregistreuses
- Suivre les commandes fournisseurs
- Visualiser les réservations
- Analyser les données clients

**Points d'intégration principaux** :
- Données POS (Point of Sale)
- État des commandes fournisseurs
- Calendrier des réservations
- Profils clients et programme de fidélité

### Module marketing

Le dashboard présente les données du module marketing :
- Performance des campagnes en cours
- Engagement sur les réseaux sociaux
- Efficacité des promotions
- Suggestions de recettes populaires

**Visualisations principales** :
- Tableau de bord des campagnes marketing
- Analyse des canaux de communication
- Suivi des promotions et offres spéciales
- Impact des publications sur les réseaux sociaux

### Module comptabilité

Le dashboard intègre les rapports financiers du module comptabilité :
- Revenus et dépenses
- Marges par produit et service
- Indicateurs financiers clés (KPI)
- Prévisions financières

**Fonctionnalités spécifiques** :
- Comparaison avec les périodes précédentes
- Analyse des coûts et revenus par catégorie
- Tableau de bord financier pour la direction
- Export de rapports pour la comptabilité externe

## Structure des données

### Modèles de données

#### Stock

```typescript
interface StockItem {
  id: string;
  name: string;
  category: string;
  currentLevel: number;
  unit: string;
  minLevel: number;
  maxLevel: number;
  criticalLevel: number;
  lastUpdated: Date;
  predictions: {
    date: Date;
    predictedLevel: number;
  }[];
}
```

#### Vente

```typescript
interface Sale {
  id: string;
  date: Date;
  total: number;
  paymentMethod: 'cash' | 'card' | 'mobile' | 'other';
  items: {
    id: string;
    name: string;
    quantity: number;
    unitPrice: number;
    total: number;
  }[];
  customer?: {
    id: string;
    name: string;
    loyaltyPoints: number;
  };
}
```

#### Campagne marketing

```typescript
interface MarketingCampaign {
  id: string;
  name: string;
  type: 'social' | 'email' | 'sms' | 'flyer' | 'other';
  startDate: Date;
  endDate: Date;
  status: 'planned' | 'active' | 'completed' | 'cancelled';
  budget: number;
  spent: number;
  metrics: {
    impressions: number;
    clicks: number;
    conversions: number;
    roi: number;
  };
  content: {
    title: string;
    description: string;
    imageUrl?: string;
    targetUrl?: string;
  };
}
```

#### Rapport financier

```typescript
interface FinancialReport {
  id: string;
  period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  startDate: Date;
  endDate: Date;
  revenue: {
    total: number;
    byCategory: Record<string, number>;
    byPaymentMethod: Record<string, number>;
  };
  expenses: {
    total: number;
    byCategory: Record<string, number>;
  };
  profit: number;
  margin: number;
  taxes: number;
  comparisons: {
    previousPeriod: {
      revenue: number;
      expenses: number;
      profit: number;
      revenueChange: number;
      expensesChange: number;
      profitChange: number;
    };
    sameLastYear?: {
      revenue: number;
      expenses: number;
      profit: number;
      revenueChange: number;
      expensesChange: number;
      profitChange: number;
    };
  };
}
```

### Endpoints API

Le backend expose les endpoints API suivants :

#### Authentification

- `POST /api/auth/login` - Authentification utilisateur
- `POST /api/auth/refresh` - Rafraîchissement du token JWT
- `POST /api/auth/logout` - Déconnexion

#### Stocks

- `GET /api/stocks` - Liste des niveaux de stock
- `GET /api/stocks/:id` - Détails d'un item spécifique
- `GET /api/stocks/categories` - Liste des catégories de stock
- `GET /api/stocks/alerts` - Alertes de stock (niveaux bas, expiration)

#### Ventes

- `GET /api/sales` - Données de vente (avec filtres période, produit)
- `GET /api/sales/summary` - Résumé des ventes (totaux, moyennes)
- `GET /api/sales/products` - Analyse des ventes par produit
- `GET /api/sales/hourly` - Répartition horaire des ventes
- `GET /api/sales/trends` - Tendances des ventes sur la période

#### Marketing

- `GET /api/marketing/campaigns` - Liste des campagnes marketing
- `GET /api/marketing/campaigns/:id` - Détails d'une campagne
- `GET /api/marketing/social` - Métriques des réseaux sociaux
- `GET /api/marketing/promotions` - Promotions en cours et planifiées

#### Finance

- `GET /api/finance/summary` - Résumé financier
- `GET /api/finance/reports` - Rapports financiers
- `GET /api/finance/expenses` - Analyse des dépenses
- `GET /api/finance/revenue` - Analyse des revenus
- `GET /api/finance/predictions` - Prévisions financières

#### Personnel

- `GET /api/staff/schedule` - Planning du personnel
- `GET /api/staff/performance` - Analyse des performances
- `GET /api/staff/hours` - Heures travaillées
- `GET /api/staff/costs` - Coûts de personnel

#### Dashboard

- `GET /api/dashboard/overview` - Vue d'ensemble pour la page d'accueil
- `GET /api/dashboard/kpi` - Indicateurs clés de performance
- `GET /api/dashboard/alerts` - Alertes et notifications
- `GET /api/dashboard/config` - Configuration personnalisée du dashboard

### Schéma des événements WebSocket

Le dashboard utilise Socket.io pour les mises à jour en temps réel. Voici les principaux événements :

#### Stocks

```javascript
// Mise à jour du niveau de stock
socket.on('stock:update', (data) => {
  /* 
  {
    itemId: string,
    currentLevel: number,
    timestamp: Date,
    change: number,
    reason: string
  }
  */
});

// Alerte de stock
socket.on('stock:alert', (data) => {
  /* 
  {
    itemId: string,
    alertType: 'low' | 'critical' | 'expiring' | 'expired',
    level: number,
    timestamp: Date
  }
  */
});
```

#### Ventes

```javascript
// Nouvelle vente
socket.on('sale:new', (data) => {
  /* 
  {
    saleId: string,
    total: number,
    items: number,
    timestamp: Date
  }
  */
});

// Mise à jour des KPI de vente
socket.on('sale:kpi_update', (data) => {
  /* 
  {
    dailyTotal: number,
    averageTicket: number,
    customerCount: number,
    timestamp: Date
  }
  */
});
```

#### Équipements

```javascript
// État des équipements
socket.on('equipment:status', (data) => {
  /* 
  {
    equipmentId: string,
    status: 'normal' | 'warning' | 'critical',
    metrics: {
      temperature?: number,
      power?: number,
      // autres métriques spécifiques
    },
    timestamp: Date
  }
  */
});
```

#### Système

```javascript
// Notifications générales
socket.on('system:notification', (data) => {
  /* 
  {
    id: string,
    type: 'info' | 'warning' | 'error' | 'success',
    message: string,
    details?: any,
    timestamp: Date
  }
  */
});
```

## Composants du dashboard

### Vue d'ensemble

La page d'accueil du dashboard présente une vue d'ensemble du restaurant avec les indicateurs clés :

- **KPI principaux** : Chiffre d'affaires du jour, nombre de clients, ticket moyen
- **État des stocks** : Aperçu rapide avec code couleur
- **Ventes en direct** : Graphique en temps réel des ventes
- **Alertes** : Notifications importantes nécessitant une attention
- **Réservations du jour** : Aperçu des réservations à venir
- **Suggestions du jour** : Recommandations générées par l'IA

### Monitoring des stocks

Cette section offre une vision détaillée des stocks :

- **Tableau des stocks** : Liste complète avec niveaux actuels, minimums et statuts
- **Graphiques d'évolution** : Tendances de consommation sur différentes périodes
- **Alertes de rupture** : Prédiction des ruptures de stock potentielles
- **État des équipements** : Surveillance des friteuses, fours et autres équipements
- **Commandes en cours** : Suivi des commandes fournisseurs
- **Suggestions de commande** : Recommandations générées par le module IA/ML

### Analyse des ventes

L'analyse des ventes permet d'explorer les données de vente en détail :

- **Évolution des ventes** : Graphiques par jour, semaine, mois, année
- **Répartition par produit** : Analyse des produits les plus vendus
- **Heatmap horaire** : Visualisation des moments de forte affluence
- **Analyse des ingrédients** : Consommation d'ingrédients par type de plat
- **Comparaison avec prévisions** : Écart entre les ventes réelles et prévues
- **Impact des promotions** : Corrélation entre promotions et ventes

### Suivi marketing

Le suivi marketing permet de mesurer l'efficacité des actions marketing :

- **Performance des campagnes** : Métriques clés par campagne
- **Engagement réseaux sociaux** : Statistiques de likes, partages, commentaires
- **Impact des promotions** : Taux de conversion et ROI
- **Calendrier marketing** : Planning des actions futures
- **Analyse des avis clients** : Synthèse des commentaires et évaluations
- **Recommandations** : Suggestions pour améliorer l'efficacité marketing

### Rapports financiers

Cette section présente les données financières essentielles :

- **Tableau de bord comptable** : Synthèse financière pour la direction
- **Analyse des revenus** : Décomposition par catégorie, produit, période
- **Analyse des coûts** : Répartition des dépenses avec détail
- **Marge et rentabilité** : Calcul des marges par produit et service
- **Prévisions financières** : Projections basées sur les données historiques
- **Exporter les rapports** : Génération de rapports PDF pour la comptabilité

### Gestion du personnel

Cette section aide à optimiser la gestion des ressources humaines :

- **Planning des équipes** : Visualisation des horaires et couverture
- **Analyse de la performance** : Productivité et efficacité
- **Pic d'activité** : Correspondance entre affluence et personnel
- **Coût du personnel** : Analyse des coûts par service, rôle, période
- **Suggestions d'optimisation** : Recommandations pour améliorer l'efficience
- **Satisfaction équipe** : Suivi du bien-être et feedback des employés

## Sécurité

### Authentification et autorisation

Le système utilise JWT (JSON Web Tokens) pour l'authentification :

- **Authentification** : Vérification de l'identité par identifiant/mot de passe
- **Autorisation** : Contrôle d'accès basé sur des rôles définis
- **Sessions** : Gestion des sessions avec expiration et rafraîchissement
- **Protection CSRF** : Contre les attaques Cross-Site Request Forgery

Les rôles principaux sont :
- **Admin** : Accès complet à toutes les fonctionnalités
- **Manager** : Accès aux rapports financiers et gestion du personnel
- **Staff** : Accès aux stocks et ventes uniquement
- **Comptable** : Accès aux rapports financiers uniquement

### Sécurisation des communications

Toutes les communications sont sécurisées par :

- **HTTPS** : Chiffrement TLS pour toutes les communications HTTP
- **WSS** : WebSockets sécurisés par TLS
- **En-têtes de sécurité** : Configuration avec Helmet.js
- **CORS** : Contrôle d'accès aux ressources entre origines

### Protection des données

La protection des données est assurée par :

- **Validation des entrées** : Validation stricte de toutes les données entrantes
- **Sanitization** : Nettoyage des données pour éviter les injections
- **Logs d'audit** : Journalisation des accès et modifications
- **Limitation de débit** : Protection contre les attaques par force brute
- **Masquage** : Protection des données sensibles dans les logs et l'interface

## Tests

### Tests unitaires

Les tests unitaires couvrent :

- **Composants React** : Tests de rendu et comportement
- **Reducers Redux** : Tests des transformations d'état
- **Services** : Tests des appels API et WebSocket
- **Utilitaires** : Tests des fonctions helpers

Exemple de test de composant React :

```javascript
import { render, screen } from '@testing-library/react';
import StockLevelCard from './StockLevelCard';

test('renders stock level correctly', () => {
  const stockItem = {
    name: 'Farine',
    currentLevel: 75,
    maxLevel: 100,
    criticalLevel: 20,
    unit: 'kg'
  };
  
  render(<StockLevelCard item={stockItem} />);
  
  expect(screen.getByText('Farine')).toBeInTheDocument();
  expect(screen.getByText('75 kg')).toBeInTheDocument();
  expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '75');
});
```

### Tests d'intégration

Les tests d'intégration vérifient :

- **Flux de données complets** : De l'API au rendu UI
- **Interactions entre composants** : Communication et état partagé
- **Intégration WebSocket** : Émission et réception d'événements

### Tests de performance

Les tests de performance mesurent :

- **Temps de chargement** : Performance initiale et navigation
- **Utilisation mémoire** : Fuites mémoire et optimisation
- **Réactivité** : Temps de réponse aux interactions
- **Charge serveur** : Capacité de traitement en charge élevée

## Déploiement

### Déploiement manuel

Instructions pour un déploiement manuel :

1. Build du frontend :
   ```bash
   cd frontend
   npm run build
   ```

2. Copie des fichiers statiques vers le dossier public du backend :
   ```bash
   cp -r build/* ../backend/public/
   ```

3. Configuration du backend pour la production :
   ```bash
   cd ../backend
   cp .env.example .env.production
   # Éditer .env.production avec les paramètres de production
   ```

4. Démarrage du serveur backend :
   ```bash
   NODE_ENV=production npm start
   ```

### Déploiement avec Docker

Le projet inclut des fichiers Docker pour faciliter le déploiement :

1. Construction des images :
   ```bash
   docker-compose build
   ```

2. Démarrage des conteneurs :
   ```bash
   docker-compose up -d
   ```

Le fichier `docker-compose.yml` définit les services suivants :
- **dashboard-backend** : Serveur Node.js
- **dashboard-frontend** : Serveur Nginx pour les fichiers statiques (en développement)
- **dashboard-db** (optionnel) : MongoDB pour le stockage
- **dashboard-redis** (optionnel) : Redis pour le cache et les sessions

### CI/CD

Le projet est configuré pour l'intégration et le déploiement continus :

1. **Tests automatisés** lors des pull requests
2. **Analyse de code** avec ESLint et SonarQube
3. **Build automatique** lors des fusions sur la branche principale
4. **Déploiement automatique** vers l'environnement de staging
5. **Déploiement manuel** vers la production après validation

## Maintenance et mise à jour

### Logs et surveillance

Le système utilise Winston pour la journalisation :

- **Logs applicatifs** : Informations, avertissements, erreurs
- **Logs d'accès** : Requêtes HTTP et WebSocket
- **Logs d'audit** : Actions utilisateur importantes
- **Logs de performance** : Métriques de performance

Les logs peuvent être configurés pour être envoyés vers :
- Fichiers locaux avec rotation
- Console (développement)
- Service externe (ELK, Graylog)

### Stratégie de mise à jour

Les mises à jour suivent le processus suivant :

1. **Développement** sur branches de fonctionnalités
2. **Revue de code** et validation par l'équipe
3. **Tests automatisés** et manuels
4. **Déploiement sur staging** pour validation
5. **Déploiement en production** avec possibilité de rollback
6. **Surveillance post-déploiement** pour détecter les problèmes

### Sauvegarde et restauration

Le système inclut des procédures de sauvegarde et restauration :

- **Sauvegarde quotidienne** des données de configuration
- **Sauvegarde automatique** avant chaque mise à jour majeure
- **Procédure de restauration** documentée pour différents scénarios
- **Tests de restauration** périodiques pour valider les sauvegardes

## Cas d'utilisation et exemples

### Scénarios courants

1. **Début de journée** : Vérification des stocks, planning du personnel, réservations du jour
2. **Pendant le service** : Suivi en temps réel des ventes, alertes de stock
3. **Fin de journée** : Bilan des ventes, analyse des performances, préparation des commandes
4. **Fin de semaine** : Analyse hebdomadaire, planification marketing, optimisation des stocks
5. **Fin de mois** : Rapports financiers, analyse de rentabilité, décisions stratégiques

### Interprétation des visualisations

Chaque visualisation du dashboard est conçue pour faciliter l'analyse :

- **Graphiques d'évolution** : Tendances et saisonnalité
- **Diagrammes en barres** : Comparaisons entre catégories
- **Camemberts** : Répartition et proportions
- **Heatmaps** : Identification des points chauds (horaires, produits)
- **Jauges** : Indicateurs de performance par rapport aux objectifs

### Prise de décision basée sur les données

Le dashboard aide à prendre des décisions informées :

- **Optimisation des stocks** : Éviter les ruptures et le gaspillage
- **Planification du personnel** : Adapter les équipes à l'affluence
- **Ajustement de la carte** : Mettre en avant les produits populaires
- **Ciblage marketing** : Concentrer les efforts sur les canaux efficaces
- **Optimisation des coûts** : Identifier les postes de dépense à optimiser

## Résolution des problèmes

### Problèmes courants

Solutions aux problèmes les plus fréquents :

1. **Problèmes de connexion API** :
   - Vérifier les paramètres de connexion dans `.env`
   - Vérifier que les services externes sont actifs
   - Consulter les logs pour les erreurs détaillées

2. **Données manquantes ou incorrectes** :
   - Vérifier la synchronisation avec les modules sources
   - Consulter les logs pour les erreurs de transformation
   - Vérifier les permissions d'accès aux données

3. **Lenteurs d'affichage** :
   - Vérifier la configuration de mise en cache
   - Optimiser les requêtes API volumineuses
   - Vérifier la pagination des résultats

4. **Problèmes WebSocket** :
   - Vérifier la connexion réseau
   - Consulter les logs côté serveur
   - Vérifier la configuration CORS et pare-feu

### FAQ

**Q: Comment ajouter un nouveau widget au dashboard ?**
R: Créez un nouveau composant React dans le dossier `components/widgets`, puis ajoutez-le dans le fichier de configuration du dashboard.

**Q: Comment configurer l'accès à un nouveau module du système ?**
R: Ajoutez la configuration dans le fichier `.env` et créez un nouveau service dans le dossier `services/`.

**Q: Comment personnaliser les seuils d'alerte ?**
R: Les seuils sont configurables dans l'interface d'administration, section "Configuration des alertes".

**Q: Comment gérer plusieurs établissements ?**
R: Sélectionnez l'établissement dans le sélecteur en haut de l'interface. Chaque établissement a sa propre configuration et ses propres données.

**Q: Comment exporter les données pour analyse externe ?**
R: Utilisez les boutons d'export disponibles sur chaque graphique et tableau, ou utilisez l'option "Exporter les données" dans le menu principal.
