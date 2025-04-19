# Documentation Technique du Dashboard - Le Vieux Moulin

Cette documentation détaille l'architecture, les fonctionnalités et l'utilisation du module dashboard pour le restaurant "Le Vieux Moulin".

## Architecture du module

Le dashboard utilise une architecture moderne combinant un frontend React avec un backend Node.js :

- **Frontend** : Application React utilisant Material-UI et Recharts
- **Backend** : Serveur Node.js/Express servant d'agrégateur de données
- **Communication** : API REST pour les données historiques, WebSockets pour le temps réel

## Technologies utilisées

### Frontend
- React 18
- Redux Toolkit
- Material-UI
- Recharts
- Axios
- Socket.io Client

### Backend
- Node.js
- Express
- Socket.io
- Winston (logs)
- Joi (validation)

## Communication avec les autres modules

Le dashboard s'intègre avec tous les modules existants du système :

### Module IoT
- Affichage en temps réel des niveaux de stock
- Surveillance des équipements (friteuses, etc.)
- Alertes sur niveaux bas et équipements

### Module IA/ML
- Visualisation des prédictions de vente
- Affichage des suggestions de recettes
- Détection d'anomalies

### Module Marketing
- Suivi des campagnes marketing
- Métriques d'engagement sur réseaux sociaux
- Efficacité des promotions

### Module Comptabilité
- Synthèse des indicateurs financiers
- Analyse des revenus et dépenses
- Visualisation des marges par produit

## Composants principaux

### Vue d'ensemble
- KPI essentiels (CA, ticket moyen, etc.)
- Alertes importantes
- Aperçu des stocks et ventes

### Monitoring IoT & Stocks
- Niveaux d'ingrédients en temps réel
- État des équipements
- Prévisions de rupture

### Analyse des ventes
- Évolution temporelle
- Répartition par produit
- Comparaison historique

### Suivi marketing
- Performance des campagnes
- Engagement sur réseaux sociaux
- Efficacité des promotions

### Données financières
- Chiffre d'affaires par période
- Analyse des coûts
- Marges et rentabilité

### Gestion RH
- Planning du personnel
- Analyse de la performance
- Optimisation des horaires

## Sécurité

- Authentification JWT
- Autorisation basée sur les rôles
- Communications HTTPS/WSS
- Journalisation des actions sensibles

## Guide d'utilisation

### Personnalisation
Le dashboard est personnalisable via l'interface d'administration :
- Ajout/suppression de widgets
- Configuration des alertes
- Personnalisation des périodes d'analyse

### Exportation des données
Toutes les visualisations peuvent être exportées en différents formats :
- CSV pour analyse externe
- PDF pour rapports
- Images pour présentations