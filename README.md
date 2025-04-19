# Système de Gestion Intelligente - "Le Vieux Moulin"

> **IMPORTANT - DÉCLARATION D'INTÉGRITÉ SYSTÉMIQUE** : Ce système est 100% RÉEL, PROFESSIONNEL et COMPLET. Tout point factice ou simulé, quelle qu'en soit la raison, est STRICTEMENT INTERDIT. Ce système répond aux standards d'intégrité et d'authenticité les plus élevés, avec une traçabilité complète et une transparence absolue dans toutes ses composantes. La véracité et l'exactitude constituent le fondement inaliénable de cette solution.

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
- **Démonstration** : file:///C:/Users/julie/Desktop/vitrine-vieux-moulin.html

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

- **[/ml/](./ml/)** - Module d'intelligence artificielle et machine learning
  - [/ml/prediction_module/](./ml/prediction_module/) - **Module fonctionnel** de prédiction et d'optimisation

- **[/marketing/](./marketing/)** - Module marketing et communication automatisée
  - [/marketing/recipe_suggestion/](./marketing/recipe_suggestion/) - **Module fonctionnel** de suggestion de recettes et promotions
  - [/marketing/communication_module/](./marketing/communication_module/) - **Module fonctionnel** de communication et d'automatisation marketing

- **Modules en cours de développement** :
  - `/ui/` - Interfaces utilisateur (tablettes, dashboards)
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

- **Module ML de prédiction** ([/ml/prediction_module/](./ml/prediction_module/)) :
  - Prévision des besoins en matières premières et optimisation des stocks
  - Génération automatique de suggestions de recettes (plat du jour, pizza spéciale)
  - Production de prévisions financières pour le module de comptabilité
  - Modèles basés sur TensorFlow et PyTorch (LSTM, XGBoost, systèmes de recommandation)
  - API REST pour l'intégration avec le système central
  - Documentation complète et tests unitaires
  - Prêt pour le déploiement en production

- **Module de suggestion de recettes** ([/marketing/recipe_suggestion/](./marketing/recipe_suggestion/)) :
  - Analyse des promotions des fournisseurs en temps réel
  - Analyse des tendances locales et préférences clients
  - Génération automatique de suggestions de recettes innovantes
  - Création et diffusion de promotions basées sur les suggestions
  - Intégration avec les systèmes de vente et marketing
  - Documentation complète et tests unitaires
  - Prêt pour le déploiement en production

- **Module de communication et d'automatisation marketing** ([/marketing/communication_module/](./marketing/communication_module/)) :
  - Orchestration centralisée de toutes les communications marketing
  - Publication automatisée sur les réseaux sociaux (Facebook, Instagram, etc.)
  - Système de notifications personnalisées par email et SMS
  - Synchronisation automatique des menus sur le site web et plateformes partenaires
  - Gestion intelligente des campagnes marketing multicanal
  - Intégration avec les autres modules du système (CRM, recettes, IoT, comptabilité)
  - Architecture modulaire avec orchestrateur central et intégrateur système
  - Tests unitaires et exemples d'utilisation complets
  - Documentation technique détaillée et guide d'installation
  - Prêt pour le déploiement en production

### 🚧 Modules en Cours de Développement
- **Interface Utilisateur** : Application sur tablette et commande vocale

### 📅 Modules Planifiés
- **Module Comptabilité** : Génération de rapports financiers

## Guide pour les Développeurs

Si vous reprenez ce projet pour la première fois, voici comment vous orienter :

1. **Comprendre l'architecture** : Consultez d'abord [ARCHITECTURE/architecture_description.md](./ARCHITECTURE/architecture_description.md) pour une vue d'ensemble.

2. **Consulter les spécifications** : [REQUIREMENTS.md](./REQUIREMENTS.md) détaille toutes les fonctionnalités attendues.

3. **Module Capteurs IoT** : Le [module IoT](./iot/sensor_module/) est fonctionnel et documenté. Consultez son [README](./iot/sensor_module/README.md) pour comprendre l'implémentation.

4. **Module Intégration API** : Le [module d'intégration API](./integration/api_connectors/) permet la connexion avec tous les systèmes externes. Consultez sa [documentation](./integration/API_INTEGRATION.md) et les [exemples](./integration/api_connectors/examples/).

5. **Module Prédiction ML** : Le [module de prédiction ML](./ml/prediction_module/) offre des fonctionnalités d'intelligence artificielle pour l'optimisation des stocks et la génération de suggestions. Consultez sa [documentation détaillée](./ml/prediction_module/MODEL_DOC.md) pour comprendre les modèles et leur déploiement.

6. **Module de suggestion de recettes** : Le [module de suggestion de recettes](./marketing/recipe_suggestion/) permet d'analyser les promotions fournisseurs et de générer des suggestions culinaires. Consultez sa [documentation](./marketing/recipe_suggestion/RECIPE_STRATEGY.md) pour comprendre l'algorithme.

7. **Module de communication marketing** : Le [module de communication](./marketing/communication_module/) centralise et automatise toutes les actions de communication du restaurant. Consultez sa [documentation technique](./marketing/communication_module/COMMUNICATION.md) et son [guide d'installation](./marketing/communication_module/INSTALL.md) pour comprendre son fonctionnement et son déploiement.

8. **Conventions de code** : Suivez les directives du fichier [CONTRIBUTING.md](./CONTRIBUTING.md) pour maintenir la cohérence du code.

## Scalabilité

Le système est conçu dès le départ pour être évolutif et permettre la duplication ou l'extension pour un deuxième établissement prévu cette année. L'architecture modulaire et granulaire facilite cette extension sans nécessiter de refonte majeure.

## Approche Technique

- **Modularité** : Chaque composant est indépendant et peut être développé, testé et mis à jour séparément
- **Granularité** : Décomposition en micro-tâches pour une maintenance facilitée
- **Évolutivité** : Architecture permettant la duplication pour un nouvel établissement
- **Sécurité** : Authentification forte, chiffrement des communications, protection des données
- **Intégration continue** : Tests automatisés et déploiement continu pour chaque module
- **Orchestration** : Coordination centralisée des différents services et modules

## Installation et Déploiement

Chaque module dispose de sa propre documentation d'installation. Pour un déploiement complet du système, suivez ces étapes générales :

1. Installez l'infrastructure de base (serveurs, réseaux, bases de données)
2. Déployez la passerelle IoT et configurez les capteurs
3. Installez le serveur central et les modules d'IA/ML
4. Déployez les interfaces utilisateur sur les tablettes murales
5. Configurez les intégrations API externes
6. Mettez en place les modules marketing et comptabilité
   - Pour le module de communication : suivez les instructions dans [INSTALL.md](./marketing/communication_module/INSTALL.md)
7. Effectuez des tests d'intégration complets

Pour plus de détails, consultez les instructions spécifiques dans chaque module.

## Support et Contact

Pour toute question technique ou support :
- Créez une issue sur le dépôt GitHub
- Contactez l'équipe technique à support@levieuxmoulin.fr

---

© 2025 Le Vieux Moulin - Tous droits réservés
