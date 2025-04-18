# Module de Suivi Financier en Temps Réel

Ce module fournit des tableaux de bord financiers en temps réel et un suivi continu des indicateurs clés de performance (KPIs) pour le restaurant "Le Vieux Moulin".

## Fonctionnalités

- Tableaux de bord en temps réel pour différents profils d'utilisateurs (manager, propriétaire, comptable)
- Suivi des KPIs financiers critiques (chiffre d'affaires, marges, coûts, etc.)
- Système d'alertes et de notifications en cas d'écarts significatifs
- Visualisations graphiques des tendances et performances
- Comparaisons avec périodes précédentes, prévisions et objectifs

## Architecture

Le module est structuré autour des composants suivants :

- `financial_dashboard.js` : Moteur principal de génération et mise à jour des tableaux de bord
- `kpi_calculator.js` : Calcul des différents indicateurs de performance
- `alert_manager.js` : Gestion des seuils d'alerte et notifications
- `data_collector.js` : Interface de collecte des données financières des autres modules
- `visualizations/` : Composants de visualisation pour différents types de données

## Configuration

Le comportement des tableaux de bord est entièrement configurable via des fichiers de configuration :

- Définition des KPIs à afficher
- Seuils d'alerte personnalisables
- Fréquence de rafraîchissement des données
- Disposition et organisation des tableaux de bord

## Intégration

Ce module s'intègre avec les autres composants du système :
- Interface avec la caisse et le système de transactions
- Communication avec le module de stocks pour valorisation des inventaires
- Connexion avec le module IA/ML pour comparaison avec les prévisions
- Alimentation du module de reporting pour génération de rapports périodiques