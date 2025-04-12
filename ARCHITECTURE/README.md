# Architecture du Système - Le Vieux Moulin

Ce dossier contient tous les schémas et diagrammes relatifs à l'architecture du système de gestion intelligente pour le restaurant "Le Vieux Moulin".

## Contenu

- [Diagramme d'Architecture Système](./system_architecture.svg) - Représentation visuelle complète de l'architecture modulaire et granulaire du système
- [Description Détaillée de l'Architecture](./architecture_description.md) - Explication exhaustive des modules, flux et interactions

## Diagramme d'Architecture

Le diagramme d'architecture système présente une vue globale de tous les composants du système, leurs interactions et les protocoles de communication utilisés. Il met en évidence :

- Les 7 modules principaux (IoT, Serveur Central, IA/ML, Interface Utilisateur, Intégrations API, Marketing, Comptabilité)
- La décomposition en micro-tâches pour assurer la granularité
- Les flux de données entre les modules
- Les protocoles de communication adaptés à chaque besoin
- L'architecture évolutive permettant la duplication pour le second établissement

## Prochains documents d'architecture à venir

Les documents suivants viendront compléter ce dossier au fur et à mesure du développement du projet :

- Schéma détaillé de la base de données
- Diagrammes de séquence pour les processus critiques
- Topologie précise du réseau IoT
- Architecture de déploiement
- Modèle de sécurité

## Principes d'architecture

Tous les diagrammes et schémas adhèrent aux principes suivants :

1. **Modularité** - Chaque composant est indépendant
2. **Granularité** - Décomposition en micro-tâches
3. **Évolutivité** - Support multi-établissements natif
4. **Sécurité** - Communications chiffrées et authentification robuste
5. **Maintenabilité** - Documentation exhaustive de chaque composant

## Format des diagrammes

Les diagrammes sont réalisés dans des formats standards (SVG, PDF) pour assurer une compatibilité maximale et permettre les modifications futures. Ils suivent les conventions UML ou C4 selon les besoins.