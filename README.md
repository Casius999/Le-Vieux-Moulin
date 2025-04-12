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

- **[ARCHITECTURE/](./ARCHITECTURE/)** : Schémas et diagrammes du système
  - [system_architecture.svg](./ARCHITECTURE/system_architecture.svg) - Diagramme d'architecture global
  - [architecture_description.md](./ARCHITECTURE/architecture_description.md) - Description de l'architecture

- **[REQUIREMENTS.md](./REQUIREMENTS.md)** : Spécifications détaillées du projet

- **[/docs/](./docs/)** : Documentation générale du projet

- **[/iot/](./iot/)** : Module de gestion des capteurs IoT
  - [/iot/sensor_module/](./iot/sensor_module/) - **Module fonctionnel** pour la gestion des capteurs

- **[/integration/](./integration/)** : Intégrations avec les systèmes externes
  - [/integration/api_connectors/](./integration/api_connectors/) - **Module fonctionnel** pour les connecteurs API
  - [/integration/API_INTEGRATION.md](./integration/API_INTEGRATION.md) - Documentation détaillée des intégrations API

- **Modules en cours de développement** :
  - `/ml/` - Module d'intelligence artificielle et machine learning
  - `/ui/` - Interfaces utilisateur (tablettes, dashboards)
  - `/marketing/` - Module marketing et communication automatisée
  - `/accounting/` - Module de comptabilité avancé

## État du Développement

### ✅ Modules Fonctionnels
- **Module IoT de capteurs** ([/iot/sensor_module/](./iot/sensor_module/)) :
  - Gestion des cellules de charge pour les bacs d'ingrédients
  - Surveillance du niveau et de la qualité d'huile des friteuses
  - Transmission sécurisée des données avec mise en cache
  - Documentation complète d'installation et d'utilisation
  - Prêt pour le déploiement en production

- **Module d'intégration API** ([/integration/api_connectors/](./integration/api_connectors/)) :
  - Connecteurs pour les systèmes de point de vente (Lightspeed, Square)
  - Intégration avec les fournisseurs (Metro, Transgourmet, Pomona)
  - Synchronisation avec les plateformes de réservation (TheFork, OpenTable)
  - Connexion avec les systèmes CRM (HubSpot, Zoho)
  - Gestion sécurisée des authentifications et des tokens
  - Documentation détaillée et exemples d'utilisation
  - Prêt pour le déploiement en production

### 🚧 Modules en Cours de Développement
- **Module ML** : Modèles prédictifs pour la consommation et l'optimisation des stocks
- **Interface Utilisateur** : Application sur tablette et commande vocale

### 📅 Modules Planifiés
- **Module Marketing** : Automatisation des campagnes et réseaux sociaux
- **Module Comptabilité** : Génération de rapports financiers

## Guide pour les Développeurs

Si vous reprenez ce projet pour la première fois, voici comment vous orienter :

1. **Comprendre l'architecture** : Consultez d'abord [ARCHITECTURE/architecture_description.md](./ARCHITECTURE/architecture_description.md) pour une vue d'ensemble.

2. **Consulter les spécifications** : [REQUIREMENTS.md](./REQUIREMENTS.md) détaille toutes les fonctionnalités attendues.

3. **Module Capteurs IoT** : Le [module IoT](./iot/sensor_module/) est fonctionnel et documenté. Consultez son [README](./iot/sensor_module/README.md) pour comprendre l'implémentation.

4. **Module Intégration API** : Le [module d'intégration API](./integration/api_connectors/) permet la connexion avec tous les systèmes externes. Consultez sa [documentation](./integration/API_INTEGRATION.md) et les [exemples](./integration/api_connectors/examples/).

5. **Conventions de code** : Suivez les directives du fichier [CONTRIBUTING.md](./CONTRIBUTING.md) pour maintenir la cohérence du code.

## Scalabilité

Le système est conçu dès le départ pour être évolutif et permettre la duplication ou l'extension pour un deuxième établissement prévu cette année. L'architecture modulaire et granulaire facilite cette extension sans nécessiter de refonte majeure.

## Approche Technique

- **Modularité** : Chaque composant est indépendant et peut être développé, testé et mis à jour séparément
- **Granularité** : Décomposition en micro-tâches pour une maintenance facilitée
- **Évolutivité** : Architecture permettant la duplication pour un nouvel établissement
- **Sécurité** : Authentification forte, chiffrement des communications, protection des données

## Installation et Déploiement

Chaque module dispose de sa propre documentation d'installation. Pour un déploiement complet du système, suivez ces étapes générales :

1. Installez l'infrastructure de base (serveurs, réseaux, bases de données)
2. Déployez la passerelle IoT et configurez les capteurs
3. Installez le serveur central et les modules d'IA/ML
4. Déployez les interfaces utilisateur sur les tablettes murales
5. Configurez les intégrations API externes
6. Mettez en place les modules marketing et comptabilité
7. Effectuez des tests d'intégration complets

Pour plus de détails, consultez les instructions spécifiques dans chaque module.

## Support et Contact

Pour toute question technique ou support :
- Créez une issue sur le dépôt GitHub
- Contactez l'équipe technique à support@levieuxmoulin.fr

---

© 2025 Le Vieux Moulin - Tous droits réservés
