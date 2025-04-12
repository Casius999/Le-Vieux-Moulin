# Système de Gestion Intelligente - "Le Vieux Moulin"

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Status](https://img.shields.io/badge/status-In%20Development-yellow.svg)

## Présentation

Ce dépôt contient l'intégralité du système de gestion intelligente développé pour le restaurant "Le Vieux Moulin" (Pizzeria Bar du Vieux Moulin) situé à Vensac en Gironde. Le système intègre des capteurs IoT, de l'intelligence artificielle, des interfaces de commande vocale, et un module de comptabilité avancé pour optimiser toutes les opérations du restaurant.

### Restaurant "Le Vieux Moulin"
- **Localisation** : Camping 3 étoiles à Vensac, Gironde, France
- **Contact** : +33 7 79 43 17 29
- **Fiche Google** : [Le Vieux Moulin](https://g.co/kgs/ua1rt2j)
- **Capacité** : 60 couverts le midi, 80 le soir
- **Spécialités** : Pizzas, salades, frites, magret, et autres spécialités locales

## Fonctionnalités Principales

- **Gestion des Stocks IoT** : Capteurs reliés aux bacs d'ingrédients et équipements (friteuse, etc.)
- **Commande Vocale** : Interface vocale pour le personnel via tablettes murales
- **Intelligence Artificielle** : Prévisions de consommation, optimisation des commandes, détection d'anomalies
- **Intégration API** : Connexion avec caisse enregistreuse, fournisseurs, système de réservation, CRM
- **Marketing Automatisé** : Gestion des réseaux sociaux, campagnes publicitaires, suggestions culinaires
- **Comptabilité Avancée** : Rapports automatisés, suivi financier en temps réel, préparation des données fiscales

## Structure du Dépôt

Le projet est organisé en plusieurs modules, chacun avec sa propre documentation détaillée :

- **[/ARCHITECTURE/](./ARCHITECTURE/)** : Schémas et diagrammes du système
  - [`system_architecture.svg`](./ARCHITECTURE/system_architecture.svg) - Diagramme complet de l'architecture
  - [`architecture_description.md`](./ARCHITECTURE/architecture_description.md) - Description détaillée de l'architecture

- **[/docs/](./docs/)** : Documentation complète du projet
  - Guides utilisateur, manuels d'exploitation, spécifications techniques

- **[/iot/](./iot/)** : Module de gestion des capteurs IoT
  - [/sensor_module/](./iot/sensor_module/) - Bacs avec cellules de charge, sonde friteuse, etc.
  - Configuration et gestion des capteurs, passerelle IoT

- **[/ml/](./ml/)** : Modèles d'intelligence artificielle et d'analyse prédictive
  - Prévisions des besoins, optimisation des stocks, suggestions de recettes

- **[/ui/](./ui/)** : Interface utilisateur
  - Tablettes murales, module de commande vocale, tableaux de bord

- **[/integration/](./integration/)** : Intégrations API externes
  - Caisse enregistreuse, fournisseurs, système de réservation, CRM

- **[/marketing/](./marketing/)** : Module marketing et communication
  - Gestion réseaux sociaux, campagnes publicitaires, notifications automatisées

- **[/accounting/](./accounting/)** : Module de comptabilité avancé
  - Rapports exhaustifs, suivi financier temps réel, gestion TVA

- **[/REQUIREMENTS.md](./REQUIREMENTS.md)** : Spécifications détaillées du projet

## Architecture et Approche Technique

Le système est conçu selon les principes fondamentaux suivants :

- **Modularité** : Chaque composant est indépendant et peut être développé, testé et mis à jour séparément
- **Granularité** : Décomposition en micro-tâches dédiées pour une maintenance facilitée
- **Évolutivité** : Architecture permettant la duplication ou l'extension pour un deuxième établissement prévu
- **Sécurité** : Authentification forte, chiffrement des communications, protection des données

Le système suit une architecture microservices modern, où :
- Chaque service possède sa propre base de données ou son propre espace de stockage
- Les services communiquent via des API RESTful ou des files de messages
- Les interfaces utilisateur sont responsives et adaptées à différents appareils
- L'infrastructure peut être déployée sur site ou dans le cloud

## Installation et Déploiement

Chaque module dispose de sa propre documentation d'installation. Pour un déploiement complet du système, suivez ces étapes générales :

1. Installez l'infrastructure de base (serveurs, réseaux, bases de données)
2. Déployez la passerelle IoT et configurez les capteurs
3. Installez le serveur central et les modules d'IA/ML
4. Déployez les interfaces utilisateur sur les tablettes murales
5. Configurez les intégrations API externes
6. Mettez en place les modules marketing et comptabilité
7. Effectuez des tests d'intégration complets

Pour des instructions détaillées, consultez le guide d'installation complet dans [/docs/guides/installation.md](./docs/README.md).

## Multi-Établissements

Le système est conçu dès le départ pour être évolutif et permettre la duplication ou l'extension pour un deuxième établissement prévu cette année. L'architecture modulaire et granulaire facilite cette extension sans nécessiter de refonte majeure.

Les caractéristiques multi-établissements comprennent :
- Isolation des données par établissement
- Partage des modèles d'IA avec paramètres spécifiques par établissement
- Tableaux de bord consolidés ou par établissement
- Comptabilité séparée avec possibilité de consolidation

## Développement et Contribution

### Prérequis de développement
- Node.js 18+
- Python 3.9+
- Docker et Docker Compose
- Clés d'API pour les services tiers

### Mise en place de l'environnement de développement
```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin

# Installer les dépendances (à la racine)
npm install

# Lancer l'environnement de développement
docker-compose up -d
```

### Standards de Code
- ESLint/Prettier pour JavaScript/TypeScript
- PEP 8 pour Python
- Tests unitaires obligatoires
- Revue de code requise pour toutes les Pull Requests

## Statut du Projet

Le projet est actuellement en phase de développement initial. Les spécifications détaillées sont finalisées, et l'architecture est définie. Le développement des différents modules se poursuit selon le calendrier prévu.

## Licence

Ce projet est propriétaire et confidentiel. Tous droits réservés.

---

© 2025 Le Vieux Moulin - Tous droits réservés
