# Guide d'utilisation - Module de Comptabilité Avancé

## 🌟 Introduction

Bienvenue dans le Guide d'utilisation du Module de Comptabilité Avancé du restaurant "Le Vieux Moulin". Ce document est conçu pour vous aider à exploiter pleinement toutes les fonctionnalités de notre solution comptable automatisée.

Ce module a été développé spécifiquement pour répondre aux besoins du restaurant en automatisant la collecte, le traitement et la présentation des données financières, réduisant ainsi considérablement le travail manuel du comptable.

## 📋 Table des matières

1. [Premiers pas](#1-premiers-pas)
2. [Tableau de bord financier](#2-tableau-de-bord-financier)
3. [Rapports automatisés](#3-rapports-automatisés)
4. [Gestion des exportations](#4-gestion-des-exportations)
5. [Prévisions financières et ML](#5-prévisions-financières-et-ml)
6. [Configuration avancée](#6-configuration-avancée)
7. [Dépannage](#7-dépannage)
8. [FAQ](#8-faq)

## 1. Premiers pas

### 1.1 Accès au système

Pour accéder au module de comptabilité, rendez-vous sur l'interface web:

- **URL**: `http://[adresse-serveur]:[port]/accounting`
- **Utilisateurs standards**: Connectez-vous avec vos identifiants habituels
- **Comptables et administrateurs**: Utilisez vos identifiants privilégiés pour accéder aux fonctionnalités avancées

### 1.2 Interface principale

L'interface principale est divisée en plusieurs sections:

- **Menu latéral**: Navigation entre les différentes fonctionnalités
- **Tableau de bord**: Vue d'ensemble des indicateurs financiers clés
- **Espace de travail**: Affichage détaillé des données et options
- **Barre de notification**: Alertes et rappels importants

### 1.3 Tour rapide

Lors de votre première connexion, un tutoriel interactif vous guidera à travers les principales fonctionnalités. Vous pouvez le relancer à tout moment depuis le menu d'aide (icône "?").

## 2. Tableau de bord financier

Le tableau de bord financier offre une vue d'ensemble de la santé financière du restaurant en temps réel.

### 2.1 KPIs principaux

Les indicateurs clés de performance (KPIs) affichés sur le tableau de bord comprennent:

- **Chiffre d'affaires** (quotidien, hebdomadaire, mensuel, annuel)
- **Marge brute** (globale et par catégorie)
- **Coût des marchandises vendues** (Food Cost, Beverage Cost)
- **Trésorerie disponible**
- **Rentabilité** (EBITDA et résultat net)

### 2.2 Graphiques interactifs

Les données sont présentées sous forme de graphiques interactifs:

- **Évolution du CA**: Courbe temporelle avec comparaison aux périodes précédentes
- **Répartition des ventes**: Diagramme circulaire par catégorie de produits
- **Analyse des coûts**: Histogramme empilé des différentes charges
- **Prévisions**: Projections basées sur l'intelligence artificielle

Pour interagir avec les graphiques:
- Cliquez sur les segments pour obtenir des détails
- Passez la souris pour voir les valeurs précises
- Utilisez les filtres en haut pour ajuster la période d'analyse
- Exportez les données ou les graphiques via le menu contextuel (clic droit)

### 2.3 Alertes et recommandations

Le système génère automatiquement des alertes basées sur des règles métier:

- **Alertes rouges**: Problèmes critiques nécessitant une action immédiate
- **Alertes oranges**: Situations préoccupantes à surveiller
- **Alertes vertes**: Résultats positifs ou opportunités

Les recommandations intelligentes vous aident à interpréter les données et à prendre des décisions éclairées.

## 3. Rapports automatisés

### 3.1 Types de rapports disponibles

Le module génère automatiquement plusieurs types de rapports:

**Rapports quotidiens**:
- Journal des ventes
- État de caisse
- Analyse des ventes par serveur/catégorie

**Rapports hebdomadaires**:
- Analyse des performances
- État des stocks et valorisation
- Planning et coûts du personnel

**Rapports mensuels**:
- Compte de résultat
- Bilan simplifié
- Analyse de trésorerie
- Déclaration de TVA

**Rapports annuels**:
- États financiers complets
- Bilan et compte de résultat
- Tableaux de flux de trésorerie

### 3.2 Planification des rapports

Vous pouvez planifier la génération et l'envoi automatique des rapports:

1. Accédez à **Rapports > Planification**
2. Sélectionnez le type de rapport à planifier
3. Définissez la fréquence (quotidien, hebdomadaire, mensuel)
4. Choisissez le format (PDF, Excel, etc.)
5. Configurez les destinataires (email)
6. Activez ou désactivez selon vos besoins

### 3.3 Personnalisation des rapports

Vous pouvez personnaliser les rapports selon vos besoins:

1. Accédez à **Rapports > Modèles**
2. Sélectionnez le modèle à personnaliser
3. Utilisez l'éditeur visuel pour:
   - Ajouter/supprimer des sections
   - Modifier les graphiques et tableaux
   - Personnaliser les en-têtes et pieds de page
   - Ajuster les formules et calculs
4. Enregistrez vos modifications ou créez un nouveau modèle

## 4. Gestion des exportations

### 4.1 Formats d'exportation disponibles

Le module prend en charge différents formats d'exportation:

- **PDF**: Pour consultation et archivage
- **Excel/CSV**: Pour analyse et traitement ultérieur
- **Formats comptables spécifiques**:
  - Sage
  - QuickBooks
  - Ciel Compta
  - EBP
  - Format FEC (Fichier des Écritures Comptables) pour l'administration fiscale

### 4.2 Configuration des exportations automatiques

Pour configurer des exportations automatiques vers votre logiciel comptable:

1. Accédez à **Configuration > Intégrations comptables**
2. Sélectionnez votre logiciel comptable
3. Configurez le mappage des comptes
4. Définissez la fréquence d'exportation
5. Choisissez la méthode de transfert (email, FTP, API)
6. Testez la connexion et l'exportation

### 4.3 Export FEC pour contrôle fiscal

Le module génère un Fichier des Écritures Comptables (FEC) conforme aux exigences fiscales:

1. Accédez à **Exportations > FEC**
2. Sélectionnez la période fiscale
3. Vérifiez les paramètres (granularité, format, etc.)
4. Lancez la génération
5. Le système effectue une validation automatique
6. Téléchargez le fichier ou envoyez-le directement

## 5. Prévisions financières et ML

### 5.1 Modèles prédictifs disponibles

Le module utilise l'intelligence artificielle pour générer des prévisions financières:

- **Prévisions de ventes**: Par jour, semaine, mois, saison
- **Projections de trésorerie**: Anticipation des flux entrants et sortants
- **Analyse de tendances**: Détection de patterns et saisonnalités
- **Scénarios what-if**: Simulation de différentes hypothèses

### 5.2 Entraînement et amélioration des modèles

Les modèles s'améliorent avec le temps:

1. Le système collecte continuellement des données historiques
2. Les algorithmes apprennent des patterns spécifiques à votre restaurant
3. Les prévisions deviennent de plus en plus précises

Vous pouvez contribuer à l'amélioration:
- Validez ou corrigez les prévisions (feedback)
- Ajoutez des informations contextuelles (événements, météo, etc.)
- Configurez des variables spécifiques (promotions, fermetures, etc.)

### 5.3 Détection d'anomalies

Le système peut détecter automatiquement des anomalies dans vos données financières:

- Transactions inhabituelles
- Écarts significatifs par rapport aux prévisions
- Patterns suspects nécessitant une vérification
- Opportunités d'optimisation

Pour chaque anomalie, vous recevrez:
- Une description du problème détecté
- Une évaluation du niveau de risque
- Des recommandations d'actions
- Des visualisations explicatives

## 6. Configuration avancée

### 6.1 Personnalisation du plan comptable

Vous pouvez adapter le plan comptable à vos besoins:

1. Accédez à **Configuration > Plan comptable**
2. Modifiez les comptes existants ou créez-en de nouveaux
3. Définissez les règles d'affectation automatique
4. Configurez les ventilations analytiques
5. Enregistrez et appliquez vos modifications

### 6.2 Configuration des règles métier

Les règles métier définissent le comportement du système:

1. Accédez à **Configuration > Règles métier**
2. Créez ou modifiez des règles pour:
   - La détection d'anomalies
   - Les alertes automatiques
   - Les contrôles de validation
   - Les calculs d'indicateurs
3. Utilisez l'éditeur visuel ou le mode avancé (JSON)
4. Testez vos règles avant de les mettre en production

### 6.3 Intégration avec d'autres modules

Le module de comptabilité s'intègre avec les autres composants du système:

- **Caisse et ventes**: Importation automatique des transactions
- **Gestion des stocks**: Valorisation et suivi des coûts
- **Planning et RH**: Analyse des coûts de personnel
- **Marketing**: Suivi de l'efficacité des campagnes
- **IoT**: Données des capteurs pour analyse des consommations

Pour configurer ces intégrations:
1. Accédez à **Configuration > Intégrations**
2. Activez ou désactivez les connecteurs
3. Configurez les paramètres de synchronisation
4. Définissez les règles de mappage des données

## 7. Dépannage

### 7.1 Problèmes courants et solutions

**Données manquantes ou incorrectes**:
- Vérifiez la connexion avec le système source (caisse, etc.)
- Consultez les journaux d'importation pour identifier les erreurs
- Utilisez l'outil de réconciliation pour corriger manuellement

**Rapports non générés**:
- Vérifiez les planifications dans "Configuration > Rapports"
- Consultez les journaux d'erreurs dans "Système > Journaux"
- Vérifiez l'espace disque disponible sur le serveur

**Exportations échouées**:
- Vérifiez les paramètres de connexion au logiciel comptable
- Assurez-vous que le mappage des comptes est correct
- Consultez les journaux d'exportation pour plus de détails

### 7.2 Journaux système

Les journaux système contiennent des informations précieuses pour le diagnostic:

1. Accédez à **Système > Journaux**
2. Sélectionnez la période et le niveau de détail
3. Filtrez par type (erreur, avertissement, information)
4. Exportez les journaux pour analyse externe si nécessaire

### 7.3 Support technique

Si vous ne parvenez pas à résoudre un problème:

1. Accédez à **Aide > Support technique**
2. Décrivez le problème rencontré
3. Joignez les captures d'écran ou journaux pertinents
4. Soumettez votre demande

L'équipe de support vous contactera dans les meilleurs délais.

## 8. FAQ

### Général

**Q: À quelle fréquence les données financières sont-elles mises à jour?**

R: Les données sont mises à jour en temps réel pour les transactions et toutes les 15 minutes pour les tableaux de bord et indicateurs agrégés. Vous pouvez forcer une mise à jour immédiate via le bouton "Actualiser".

**Q: Comment puis-je sauvegarder mes données comptables?**

R: Le système effectue automatiquement des sauvegardes quotidiennes. Vous pouvez également déclencher une sauvegarde manuelle via "Système > Sauvegarde > Nouvelle sauvegarde". Les fichiers sont stockés de manière sécurisée et peuvent être restaurés si nécessaire.

### Rapports et exportations

**Q: Puis-je modifier un rapport après sa génération?**

R: Oui, les rapports peuvent être modifiés avant leur finalisation. Accédez à "Rapports > Historique", sélectionnez le rapport concerné, puis cliquez sur "Modifier". Une fois validé ou envoyé, un rapport ne peut plus être modifié, mais vous pouvez en créer une nouvelle version.

**Q: Comment partager des rapports avec des personnes externes?**

R: Vous pouvez partager des rapports de plusieurs façons:
- Envoi par email direct depuis le système
- Génération d'un lien de partage sécurisé (avec ou sans mot de passe)
- Export en PDF ou Excel pour partage manuel
- Configuration d'un accès externe limité pour certains utilisateurs

### Prévisions et ML

**Q: Quelle est la précision des prévisions?**

R: La précision dépend de plusieurs facteurs, notamment la quantité d'historique disponible et la stabilité de votre activité. En général, les prévisions atteignent une précision de 85-95% pour les courts termes (1-7 jours) et 70-85% pour le moyen terme (1-3 mois). Le système affiche toujours des intervalles de confiance pour vous aider à évaluer la fiabilité des prévisions.

**Q: Comment le système détecte-t-il les anomalies?**

R: Le système utilise plusieurs techniques de détection d'anomalies:
- Analyse statistique (écarts par rapport aux moyennes historiques)
- Modèles prédictifs (écarts par rapport aux prévisions)
- Règles métier configurables (seuils et conditions spécifiques)
- Apprentissage non supervisé (détection de patterns inhabituels)

---

*Ce guide est régulièrement mis à jour. Dernière révision: 19 avril 2025.*

*Pour toute question supplémentaire, veuillez contacter le support technique.*
