# Description de l'Architecture Système - Le Vieux Moulin

Ce document explique en détail l'architecture système représentée dans le diagramme `system_architecture.svg` pour le projet de gestion intelligente du restaurant "Le Vieux Moulin".

## Vue d'ensemble

L'architecture a été conçue selon les principes suivants :
- **Modularité** : Chaque composant est indépendant et peut être développé, testé et maintenu séparément
- **Granularité** : Décomposition en micro-tâches dédiées pour une maintenance facilitée
- **Évolutivité** : Conception permettant la duplication ou l'extension pour un deuxième établissement
- **Interconnectivité** : Communication fluide entre tous les modules via des protocoles standardisés

## Description des Modules

### 1. Modules IoT

Ce module gère l'ensemble des capteurs et équipements connectés du restaurant :

- **Cellules de charge pour bacs d'ingrédients** : Mesurent en temps réel les quantités de chaque ingrédient
- **Sonde de niveau d'huile** : Surveille le niveau et la qualité de l'huile dans la friteuse
- **Capteurs de température** : Surveillent les équipements critiques (four à pizza, réfrigérateurs)
- **Passerelle IoT** : Basée sur ESP32/Arduino, agrège les données des capteurs et les transmet au serveur central via MQTT

Les capteurs communiquent par WiFi ou Bluetooth Low Energy avec la passerelle IoT, qui assure également un cache local en cas de perte de connexion avec le serveur central.

### 2. Serveur Central et Base de Données

Cœur du système, le serveur central :

- **API Gateway** : Gère toutes les communications entrantes/sortantes et l'orchestration des services
- **Service Bus / Message Queue** : Assure la communication asynchrone entre les composants
- **Base de Données** : PostgreSQL avec extension TimescaleDB pour gérer efficacement les séries temporelles
  - Stockage des données historiques pour analyses rétrospectives
  - Support des requêtes complexes pour les analyses en temps réel
  - Partitionnement pour la séparation des données entre établissements

Le serveur central utilise une architecture microservices, chaque service étant déployé de manière indépendante.

### 3. Module IA/ML

Ce module apporte l'intelligence au système :

- **Prévision de Consommation** : Utilise des modèles de séries temporelles pour prédire les besoins
- **Détection d'Anomalies** : Identifie les comportements inhabituels dans la consommation ou le fonctionnement
- **Suggestion de Recettes** : Propose des plats du jour ou spécialités basés sur les stocks disponibles et les tendances
- **Optimisation des Stocks** : Utilise des algorithmes génétiques pour optimiser les commandes fournisseurs

Les modèles d'IA sont entraînés régulièrement avec les nouvelles données collectées et s'améliorent continuellement.

### 4. Interface Utilisateur et Commande Vocale

L'interface homme-machine du système comprend :

- **Tablettes Murales** : Interfaces tactiles positionnées stratégiquement dans la cuisine et en salle
- **Reconnaissance Vocale** : Permet au personnel de saisir les commandes sans utiliser les mains
- **Dashboard Temps Réel** : Affiche les informations cruciales sur les stocks, commandes et performance

L'interface est responsive et accessible également sur smartphones pour la mobilité du personnel.

### 5. Intégrations API Externes

Ce module assure la communication avec les systèmes externes :

- **Caisse Enregistreuse** : Synchronisation bidirectionnelle pour le suivi des ventes
- **Fournisseurs** : API pour automatiser les commandes en fonction des prévisions
- **Réservation En Ligne** : Intégration avec les plateformes de réservation (TheFork, OpenTable, etc.)
- **CRM Client** : Gestion des profils clients, préférences et historique

Les connecteurs API utilisent des standards REST ou GraphQL avec OAuth2 pour l'authentification et des webhooks pour les notifications en temps réel.

### 6. Module Marketing et Communication

Ce module automatise les activités marketing :

- **Réseaux Sociaux** : Publication automatique sur Facebook, Instagram, etc.
- **Campagnes Publicitaires** : Création et suivi de campagnes ciblées
- **Notifications** : Envoi d'emails et SMS pour les promotions ou événements
- **Menus en ligne** : Mise à jour automatisée des menus en ligne sur les différentes plateformes

Le module marketing s'appuie sur les suggestions du module IA pour optimiser les campagnes.

### 7. Module de Comptabilité Avancé

Ce module crucial génère automatiquement des rapports exhaustifs pour le comptable :

- **Suivi Financier Temps Réel** : Tableau de bord des indicateurs financiers clés
- **Rapports Automatisés** : Génération quotidienne, hebdomadaire, mensuelle et annuelle
- **Gestion TVA** : Calcul automatique des taxes et préparation des déclarations fiscales
- **Export Comptable** : Interface dédiée pour le comptable avec formats compatibles

Ce module agrège toutes les données financières et opérationnelles pour réduire le travail du comptable au strict minimum.

## Flux de Communication

Les modules communiquent entre eux via différents protocoles adaptés à leurs besoins :

- **REST/GraphQL** : Pour les communications API synchrones
- **MQTT** : Pour les communications IoT légères et efficaces
- **WebSocket** : Pour les mises à jour en temps réel des interfaces utilisateur
- **HTTPS** : Pour sécuriser toutes les communications
- **OAuth2** : Pour l'authentification sécurisée avec les API externes
- **Webhooks** : Pour les notifications asynchrones

## Architecture Évolutive

L'architecture a été spécifiquement conçue pour permettre :

1. **Mise à jour indépendante** : Chaque micro-tâche peut être mise à jour sans impacter les autres
2. **Extension facile** : Nouveaux capteurs, nouvelles fonctionnalités, nouveaux algorithmes
3. **Duplication pour multi-établissements** : L'architecture peut être dupliquée ou étendue pour le deuxième établissement prévu
4. **Compatibilité** : Utilisation de standards ouverts pour assurer une évolutivité à long terme

## Sécurité

Toutes les communications sont sécurisées par chiffrement (HTTPS, MQTT over TLS), et l'authentification est gérée par des mécanismes robustes (OAuth2, JWT). Les données sensibles sont chiffrées au repos et les accès sont contrôlés par un système de rôles et permissions granulaires.

## Prochaines Étapes

1. Définir précisément le nombre et la localisation des capteurs IoT
2. Développer les connecteurs spécifiques pour la caisse enregistreuse et les fournisseurs
3. Affiner les modèles d'IA avec des données initiales
4. Mettre en place l'environnement de développement et de test

---

Ce diagramme d'architecture représente la vision globale du système. Chaque module sera développé séparément avec sa propre documentation technique détaillée, suivant le principe de granularité défini dans les exigences du projet.