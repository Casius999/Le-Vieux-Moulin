# Module de Comptabilité Avancé - Documentation Technique

## Table des matières
1. [Architecture du module](#1-architecture-du-module)
   - [1.1 Vue d'ensemble](#11-vue-densemble)
   - [1.2 Composants clés](#12-composants-clés)
   - [1.3 Sources de données](#13-sources-de-données)
2. [Mécanisme d'agrégation des données](#2-mécanisme-dagrégation-des-données)
   - [2.1 Collecte des données](#21-collecte-des-données)
   - [2.2 Transformation et normalisation](#22-transformation-et-normalisation)
   - [2.3 Validation et contrôle d'intégrité](#23-validation-et-contrôle-dintégrité)
3. [Formules et calculs financiers](#3-formules-et-calculs-financiers)
   - [3.1 Calcul des indicateurs principaux](#31-calcul-des-indicateurs-principaux)
   - [3.2 Analyses de rentabilité](#32-analyses-de-rentabilité)
   - [3.3 Gestion de la TVA](#33-gestion-de-la-tva)
4. [Génération de rapports automatisés](#4-génération-de-rapports-automatisés)
   - [4.1 Types de rapports disponibles](#41-types-de-rapports-disponibles)
   - [4.2 Personnalisation des rapports](#42-personnalisation-des-rapports)
   - [4.3 Automatisation et planification](#43-automatisation-et-planification)
5. [Exemples de rapports](#5-exemples-de-rapports)
   - [5.1 Rapport journalier](#51-rapport-journalier)
   - [5.2 Rapport mensuel](#52-rapport-mensuel)
   - [5.3 Interprétation des résultats](#53-interprétation-des-résultats)

## 1. Architecture du module

### 1.1 Vue d'ensemble

Le module de comptabilité avancé est conçu selon une architecture modulaire et extensible, permettant l'intégration transparente avec l'ensemble du système de gestion du restaurant "Le Vieux Moulin". Ce module est structuré en plusieurs composants spécialisés qui fonctionnent de manière coordonnée pour offrir une solution comptable complète et automatisée.

L'architecture suit un modèle en couches :

```
┌─────────────────────────────────────────────────────────────┐
│                     COUCHE PRÉSENTATION                     │
│  (Tableaux de bord, interfaces de reporting, exports PDF)   │
├─────────────────────────────────────────────────────────────┤
│                      COUCHE MÉTIER                          │
│ (Règles comptables, calculs financiers, validation fiscale) │
├─────────────────────────────────────────────────────────────┤
│                   COUCHE INTÉGRATION                        │
│  (Connecteurs API, adaptateurs de données, synchronisation) │
├─────────────────────────────────────────────────────────────┤
│                    COUCHE DONNÉES                           │
│    (Persistance, historisation, sauvegarde, archivage)      │
└─────────────────────────────────────────────────────────────┘
```

Chaque couche communique exclusivement avec les couches adjacentes via des interfaces bien définies, assurant ainsi une faible interdépendance et une haute cohésion.

### 1.2 Composants clés

Le module de comptabilité est constitué des composants suivants :

#### 1.2.1 Collecteur de données (`DataCollector`)
Composant responsable de la collecte, de l'agrégation et de la normalisation des données financières provenant des différentes sources du système. Il implémente des adaptateurs spécifiques pour chaque type de source (ventes, achats, stocks, etc.).

#### 1.2.2 Moteur de calcul financier (`FinancialEngine`)
Cœur analytique du module qui implémente l'ensemble des formules et règles comptables nécessaires aux calculs financiers, incluant :
- Calcul des indicateurs clés (CA, marges, rentabilité)
- Gestion de la TVA et autres taxes
- Amortissements et provisions
- Consolidation financière

#### 1.2.3 Générateur de rapports (`ReportGenerator`)
Composant de génération de rapports financiers qui :
- Transforme les données brutes en documents structurés
- Applique les templates de présentation
- Gère l'export vers différents formats (PDF, CSV, Excel)
- S'occupe de la diffusion automatique des rapports

#### 1.2.4 Vérificateur d'intégrité (`IntegrityChecker`)
Vérifie la cohérence, l'exactitude et l'intégrité des données financières via :
- Des contrôles de validation configurables
- Des réconciliations automatiques
- La détection d'anomalies et d'incohérences
- Des logs d'audit complets

#### 1.2.5 Gestionnaire d'export (`ExportManager`)
Gère l'export de données vers les systèmes comptables externes :
- Mappage avec les plans comptables standards
- Génération de fichiers aux formats compatibles (Sage, QuickBooks, etc.)
- Format FEC (Fichier des Écritures Comptables) pour l'administration fiscale

### 1.3 Sources de données

Le module de comptabilité s'appuie sur diverses sources de données réparties dans l'écosystème du restaurant :

#### 1.3.1 Système de caisse (POS)
- Transactions de vente (tickets, factures)
- Modes de paiement et encaissements
- Annulations et remboursements
- TVA collectée par taux

#### 1.3.2 Module de gestion des stocks
- Valeur du stock en temps réel
- Mouvements de stock (entrées, sorties, pertes)
- Inventaires physiques
- Coût des matières consommées

#### 1.3.3 Module de gestion des achats
- Commandes fournisseurs
- Réceptions et factures
- Conditions de paiement
- TVA déductible

#### 1.3.4 Module de gestion du personnel
- Heures travaillées
- Calcul des salaires bruts
- Primes et commissions
- Congés et absences

#### 1.3.5 Module IoT
- Consommation énergétique
- Suivi des équipements
- Détection automatique des pertes

## 2. Mécanisme d'agrégation des données

### 2.1 Collecte des données

Le processus de collecte des données financières s'effectue selon plusieurs méthodes adaptées à la nature et à la source des données :

#### 2.1.1 Collecte en temps réel
Pour les données critiques comme les transactions de vente, le système utilise :
- Des webhooks pour capture immédiate des événements
- Des connexions WebSocket pour mise à jour en continu
- Des files d'attente de messages pour garantir la fiabilité

#### 2.1.2 Collecte programmée
Pour les données moins urgentes ou les sources externes :
- Jobs programmés à intervalles réguliers (horaire, quotidien)
- Synchronisation complète nocturne
- Mécanismes de reprise en cas d'échec

#### 2.1.3 Connecteurs API dédiés
Pour chaque source externe, un connecteur spécifique est implémenté :

```javascript
// Exemple de connecteur pour système de caisse
class POSConnector extends BaseConnector {
  constructor(config) {
    super(config);
    this.apiUrl = config.apiUrl;
    this.apiToken = config.apiToken;
    this.posType = config.posType; // "Square", "Lightspeed", etc.
  }

  async fetchDailyTransactions(date) {
    try {
      const formattedDate = this.formatDate(date);
      const response = await this.request('GET', `/transactions?date=${formattedDate}`);
      
      return this.normalizeTransactions(response.data);
    } catch (error) {
      this.logger.error(`Failed to fetch transactions for ${date}:`, error);
      throw new DataCollectionError('transactions', date, error);
    }
  }

  normalizeTransactions(rawData) {
    // Transformation spécifique selon le type de caisse
    switch(this.posType) {
      case 'Square':
        return this.normalizeSquareTransactions(rawData);
      case 'Lightspeed':
        return this.normalizeLightspeedTransactions(rawData);
      default:
        return this.normalizeGenericTransactions(rawData);
    }
  }
  
  // Autres méthodes spécifiques...
}
```

### 2.2 Transformation et normalisation

Une fois collectées, les données subissent plusieurs étapes de transformation pour les rendre exploitables par le moteur financier :

#### 2.2.1 Normalisation des formats
- Conversion vers des formats standardisés
- Harmonisation des unités de mesure
- Normalisation des identifiants
- Structuration en modèles de données cohérents

#### 2.2.2 Enrichissement
- Ajout de métadonnées contextuelles
- Catégorisation comptable
- Association avec les comptes comptables
- Enrichissement avec données historiques ou prévisionnelles

#### 2.2.3 Agrégation
- Regroupement par périodes (jour, semaine, mois)
- Consolidation par catégories (produits, services)
- Synthèse par entités (départements, établissements)
- Calcul des totaux et sous-totaux

```javascript
// Exemple de processeur d'agrégation
class SalesAggregator {
  constructor(options = {}) {
    this.groupingFields = options.groupingFields || ['category', 'taxRate'];
    this.timeGranularity = options.timeGranularity || 'day';
  }

  aggregate(transactions, period) {
    const { startDate, endDate } = this.calculatePeriodDates(period);
    
    // Filtrage par période
    const filteredTransactions = transactions.filter(tx => 
      tx.timestamp >= startDate && tx.timestamp <= endDate
    );
    
    // Préparation de la structure d'agrégation
    const aggregationMap = new Map();
    
    // Agrégation des transactions
    for (const transaction of filteredTransactions) {
      const key = this.buildAggregationKey(transaction);
      
      if (!aggregationMap.has(key)) {
        aggregationMap.set(key, this.initializeAggregation(transaction));
      }
      
      const aggregation = aggregationMap.get(key);
      this.updateAggregation(aggregation, transaction);
    }
    
    // Conversion en tableau de résultats
    return Array.from(aggregationMap.values());
  }
  
  // Autres méthodes d'aide à l'agrégation...
}
```

### 2.3 Validation et contrôle d'intégrité

Avant d'être consolidées dans le système comptable, les données subissent des contrôles d'intégrité rigoureux :

#### 2.3.1 Contrôles automatiques
- Vérification de l'exhaustivité des données
- Contrôle des totaux de contrôle
- Validation des formats et types de données
- Détection des données aberrantes ou incohérentes

#### 2.3.2 Réconciliation
- Rapprochement entre différentes sources (ex: ventes vs encaissements)
- Vérification de la cohérence entre flux physiques et financiers
- Réconciliation bancaire automatisée
- Balance de vérification

#### 2.3.3 Journalisation des anomalies
Toute anomalie détectée est :
- Enregistrée dans un journal d'audit
- Classifiée par niveau de gravité
- Notifiée aux responsables concernés
- Traitée selon un workflow prédéfini

## 3. Formules et calculs financiers

### 3.1 Calcul des indicateurs principaux

Le moteur de calcul financier implémente un ensemble complet de formules pour les indicateurs clés de performance financière :

#### 3.1.1 Indicateurs de vente
```
Chiffre d'affaires HT = Somme des ventes - TVA collectée
Ticket moyen = Chiffre d'affaires / Nombre de clients
Chiffre d'affaires par m² = Chiffre d'affaires / Surface du restaurant
Chiffre d'affaires par heure d'ouverture = Chiffre d'affaires / Heures d'ouverture
```

#### 3.1.2 Indicateurs de coût et marge
```
Coût des matières premières (Food Cost) = Somme des coûts des ingrédients consommés
Ratio Food Cost = (Coût des matières premières / Chiffre d'affaires nourriture) × 100
Coût des boissons (Beverage Cost) = Somme des coûts des boissons consommées
Ratio Beverage Cost = (Coût des boissons / Chiffre d'affaires boissons) × 100
Marge brute = Chiffre d'affaires - (Food Cost + Beverage Cost)
Taux de marge brute = (Marge brute / Chiffre d'affaires) × 100
```

#### 3.1.3 Indicateurs de rentabilité
```
Frais de personnel = Salaires + Charges sociales + Primes + Extras
Ratio frais de personnel = (Frais de personnel / Chiffre d'affaires) × 100
Frais généraux = Loyer + Énergie + Assurances + Frais divers
Ratio frais généraux = (Frais généraux / Chiffre d'affaires) × 100
EBITDA = Marge brute - Frais de personnel - Frais généraux
Taux d'EBITDA = (EBITDA / Chiffre d'affaires) × 100
```

#### 3.1.4 Indicateurs de trésorerie
```
Délai moyen de paiement fournisseurs = (Dettes fournisseurs / Achats) × 365
Délai moyen d'encaissement clients = (Créances clients / Ventes) × 365
Besoin en fonds de roulement = Stocks + Créances clients - Dettes fournisseurs
Trésorerie nette = Disponibilités - Découverts bancaires
```

### 3.2 Analyses de rentabilité

Le module effectue des analyses de rentabilité détaillées à plusieurs niveaux :

#### 3.2.1 Rentabilité par produit
Chaque élément vendu fait l'objet d'une analyse de rentabilité :
```javascript
// Exemple de calcul de rentabilité pour un plat
function calculateDishProfitability(dishId, period) {
  // Récupérer les ventes de la période
  const sales = salesRepository.getDishSales(dishId, period);
  const totalSalesQuantity = sales.reduce((sum, s) => sum + s.quantity, 0);
  const totalSalesRevenue = sales.reduce((sum, s) => sum + s.total, 0);
  
  // Récupérer la recette et calculer le coût
  const recipe = recipeRepository.getRecipe(dishId);
  const ingredientsCost = recipe.ingredients.reduce((sum, ingredient) => {
    const unitCost = inventoryRepository.getIngredientCost(ingredient.id, period);
    return sum + (unitCost * ingredient.quantity);
  }, 0);
  
  const totalCost = ingredientsCost * totalSalesQuantity;
  
  // Calcul des indicateurs de rentabilité
  const grossProfit = totalSalesRevenue - totalCost;
  const grossMarginPercentage = (grossProfit / totalSalesRevenue) * 100;
  const contributionToRevenue = (totalSalesRevenue / totalRevenueInPeriod) * 100;
  
  return {
    dishId,
    name: recipe.name,
    salesQuantity: totalSalesQuantity,
    salesRevenue: totalSalesRevenue,
    totalCost,
    grossProfit,
    grossMarginPercentage,
    contributionToRevenue,
    revenuePerUnit: totalSalesRevenue / totalSalesQuantity,
    costPerUnit: totalCost / totalSalesQuantity,
    profitPerUnit: grossProfit / totalSalesQuantity
  };
}
```

#### 3.2.2 Rentabilité par service
Analyse comparative entre différents services (midi, soir) :
```
Marge par service = CA service - Coûts variables du service
Contribution par service = Marge service - (Frais de personnel dédiés au service)
Taux d'occupation = Nombre de couverts / Capacité totale
Revenu par siège disponible = CA service / Nombre total de places
```

#### 3.2.3 Seuil de rentabilité
Calcul du point mort financier :
```
Coûts fixes = Loyer + Salaires fixes + Assurances + Abonnements + etc.
Taux de marge sur coûts variables = (CA - Coûts variables) / CA
Seuil de rentabilité = Coûts fixes / Taux de marge sur coûts variables
```

### 3.3 Gestion de la TVA

Le module intègre une gestion complète de la TVA adaptée à la restauration en France :

#### 3.3.1 Différenciation des taux
- 10% pour la restauration sur place
- 5,5% pour la vente à emporter (nourriture)
- 20% pour les boissons alcoolisées
- Gestion des cas particuliers (produits spécifiques)

#### 3.3.2 Calcul et déclaration
```javascript
// Exemple de calcul de TVA pour déclaration
function calculateVATReport(period) {
  // Récupération des transactions de la période
  const transactions = transactionRepository.getByPeriod(period);
  
  // Initialisation des compteurs par taux
  const vatCollected = {
    '5.5': 0,
    '10': 0,
    '20': 0
  };
  
  // Calcul de la TVA collectée
  transactions.forEach(transaction => {
    transaction.items.forEach(item => {
      const vatRate = item.vatRate.toString();
      const vatAmount = item.total - (item.total / (1 + item.vatRate / 100));
      vatCollected[vatRate] += vatAmount;
    });
  });
  
  // Récupération des achats de la période
  const purchases = purchaseRepository.getByPeriod(period);
  
  // Initialisation des compteurs de TVA déductible
  const vatDeductible = {
    '5.5': 0,
    '10': 0,
    '20': 0
  };
  
  // Calcul de la TVA déductible
  purchases.forEach(purchase => {
    purchase.items.forEach(item => {
      const vatRate = item.vatRate.toString();
      vatDeductible[vatRate] += item.vatAmount;
    });
  });
  
  // Calcul des totaux et du solde
  const totalCollected = Object.values(vatCollected).reduce((a, b) => a + b, 0);
  const totalDeductible = Object.values(vatDeductible).reduce((a, b) => a + b, 0);
  const balance = totalCollected - totalDeductible;
  
  return {
    period,
    collected: vatCollected,
    totalCollected,
    deductible: vatDeductible,
    totalDeductible,
    balance,
    payable: balance > 0 ? balance : 0,
    refundable: balance < 0 ? Math.abs(balance) : 0
  };
}
```

#### 3.3.3 Contrôles de cohérence
- Vérification de l'application correcte des taux
- Réconciliation entre CA déclaré et TVA collectée
- Validation des montants de TVA déductible

## 4. Génération de rapports automatisés

### 4.1 Types de rapports disponibles

Le module génère automatiquement une variété de rapports financiers adaptés aux différents besoins du restaurant et du comptable :

#### 4.1.1 Rapports d'activité
- **Rapport de ventes journalier** : détail des ventes par catégorie, mode de paiement, TVA
- **Rapport de caisse** : récapitulatif des encaissements, fond de caisse, écarts
- **Rapport d'activité hebdomadaire** : analyse des ventes, fréquentation, ticket moyen, comparaison avec semaines précédentes
- **Dashboard opérationnel** : visuels et KPIs pour les managers (temps réel ou quotidien)

#### 4.1.2 Rapports comptables
- **Journal des ventes** : détail chronologique de toutes les transactions
- **Journal des achats** : suivi des factures fournisseurs
- **Grand livre** : mouvement de chaque compte sur la période
- **Balance âgée** : suivi des créances et dettes par ancienneté
- **Compte de résultat mensuel** : synthèse des revenus et charges
- **Bilan périodique** : état des actifs et passifs

#### 4.1.3 Rapports fiscaux
- **Déclaration de TVA** : préparation des données pour déclaration
- **État des taxes spécifiques** : taxe sur les boissons alcoolisées, etc.
- **Préparation liasse fiscale** : données formatées pour déclarations annuelles

#### 4.1.4 Rapports analytiques
- **Analyse de rentabilité** : par produit, catégorie, période
- **Évolution des marges** : suivi des tendances et écarts
- **Analyse des coûts** : décomposition et évolution dans le temps
- **Prévisions financières** : projections basées sur données historiques et IA

### 4.2 Personnalisation des rapports

Le système offre des options de personnalisation pour adapter les rapports aux besoins spécifiques :

#### 4.2.1 Templates configurables
- Charte graphique adaptable
- En-têtes et pieds de page personnalisés
- Sections optionnelles activables/désactivables
- Niveau de détail ajustable

#### 4.2.2 Filtres et paramètres
- Filtrage par période (jour, semaine, mois, trimestre, année)
- Comparaison avec périodes précédentes ou budgets
- Sélection des catégories à inclure
- Choix des indicateurs et KPIs à présenter

#### 4.2.3 Formats d'export
- PDF pour impression et archivage
- Excel pour analyse approfondie
- CSV pour import dans d'autres systèmes
- Formats spécifiques pour logiciels comptables (Sage, etc.)
- Format FEC normalisé pour l'administration fiscale

### 4.3 Automatisation et planification

Le module permet une automatisation complète de la génération et de la distribution des rapports :

#### 4.3.1 Planification flexible
```javascript
// Exemple de configuration de planification de rapports
const reportSchedules = [
  {
    reportType: 'daily_sales',
    schedule: '0 23 * * *', // Tous les jours à 23h (format cron)
    formats: ['pdf', 'excel'],
    recipients: [
      { email: 'manager@levieuxmoulin.fr', format: 'pdf' },
      { email: 'comptable@cabinet.fr', formats: ['pdf', 'excel'] }
    ],
    parameters: {
      includeComparison: true,
      comparisonPeriod: 'previous_day',
      detailLevel: 'medium'
    }
  },
  {
    reportType: 'monthly_financial',
    schedule: '0 9 1 * *', // Le 1er jour de chaque mois à 9h
    formats: ['pdf', 'excel', 'sage'],
    recipients: [
      { email: 'direction@levieuxmoulin.fr', format: 'pdf' },
      { email: 'comptable@cabinet.fr', formats: ['pdf', 'excel', 'sage'] }
    ],
    parameters: {
      includeComparison: true,
      comparisonPeriod: 'previous_month,same_month_previous_year',
      detailLevel: 'high',
      includeForecast: true
    }
  }
];
```

#### 4.3.2 Distribution multicanale
- Envoi automatique par email
- Stockage dans un espace documentaire sécurisé
- API pour récupération par systèmes externes
- Impression automatique pour certains rapports

#### 4.3.3 Gestion des erreurs et reprises
- Mécanisme de détection des échecs
- Notifications en cas de problème
- Tentatives automatiques de relance
- Log des actions et résultats

## 5. Exemples de rapports

### 5.1 Rapport journalier

#### 5.1.1 Exemple de rapport de ventes journalier

```
RESTAURANT LE VIEUX MOULIN - RAPPORT DE VENTES JOURNALIER
Date: 17/04/2025
Période d'activité: 11:30 - 23:00

RÉSUMÉ DES VENTES
---------------------------------------------------------------
Chiffre d'affaires total TTC:                     4,586.50 €
Nombre de tickets:                                     127
Ticket moyen:                                       36.12 €
Nombre de couverts:                                    168
CA par couvert:                                     27.30 €

RÉPARTITION PAR CATÉGORIE
---------------------------------------------------------------
Pizzas:                         2,156.00 € (47.0%)  68 unités
Plats:                            986.50 € (21.5%)  32 unités
Entrées:                          468.00 € (10.2%)  51 unités
Desserts:                         319.00 € (7.0%)   43 unités
Boissons non-alcoolisées:         245.00 € (5.3%)   87 unités
Boissons alcoolisées:             412.00 € (9.0%)   56 unités

RÉPARTITION PAR SERVICE
---------------------------------------------------------------
Service midi (11:30-15:00):     1,856.50 € (40.5%)  72 tickets
Service soir (18:30-23:00):     2,730.00 € (59.5%)  55 tickets

MOYENS DE PAIEMENT
---------------------------------------------------------------
Carte bancaire:                 3,456.50 € (75.4%)  96 tickets
Espèces:                          658.00 € (14.3%)  24 tickets
Tickets restaurant:               472.00 € (10.3%)   7 tickets

DÉTAIL TVA
---------------------------------------------------------------
TVA 10% (restauration):           356.32 €
TVA 20% (alcool):                  68.67 €
TVA 5.5% (vente à emporter):       23.54 €
Total TVA:                        448.53 €

ANALYSE DE PERFORMANCE
---------------------------------------------------------------
Comparaison J-1:                 +12.5% (+510.50 €)
Comparaison même jour S-1:        +5.3% (+230.00 €)
Objectif journalier:              103.5% (Objectif: 4,430.00 €)
```

### 5.2 Rapport mensuel

#### 5.2.1 Exemple de rapport mensuel pour le comptable

```
RESTAURANT LE VIEUX MOULIN - RAPPORT FINANCIER MENSUEL
Période: Avril 2025

COMPTE DE RÉSULTAT SIMPLIFIÉ
---------------------------------------------------------------
REVENUS
Ventes nourriture:              98,564.00 €
Ventes boissons:                24,352.00 €
Autres revenus:                  1,245.00 €
                            -------------- 
TOTAL REVENUS:                124,161.00 €

COÛTS DIRECTS
Coût des ingrédients:          -31,456.20 €
Coût des boissons:              -8,523.40 €
                            --------------
TOTAL COÛTS DIRECTS:          -39,979.60 €

MARGE BRUTE:                    84,181.40 € (67.8%)

CHARGES D'EXPLOITATION
Salaires et charges:           -35,425.00 €
Loyer et charges:               -4,500.00 €
Énergie et fluides:             -3,245.60 €
Marketing et communication:     -1,850.00 €
Maintenance et réparations:     -1,235.00 €
Assurances:                       -850.00 €
Fournitures et consommables:    -1,450.00 €
Frais bancaires:                  -625.00 €
Autres charges:                 -1,350.00 €
                            --------------
TOTAL CHARGES:                -50,530.60 €

RÉSULTAT D'EXPLOITATION:        33,650.80 € (27.1%)

ANALYSE DU CASH-FLOW
---------------------------------------------------------------
Solde de trésorerie initial:    56,325.00 €
Encaissements du mois:         122,450.00 €
Décaissements du mois:         -95,675.00 €
                            --------------
Solde de trésorerie final:      83,100.00 €

ÉTAT DES STOCKS
---------------------------------------------------------------
Valeur du stock initial:        12,345.00 €
Achats du mois:                 41,250.00 €
Consommation du mois:          -39,979.60 €
                            --------------
Valeur du stock final:          13,615.40 €
Taux de rotation:                     2.93

INDICATEURS DE PERFORMANCE
---------------------------------------------------------------
Food Cost Ratio:                    31.9%
Beverage Cost Ratio:                35.0%
Labor Cost Ratio:                   28.5%
Prime Cost:                         60.4%
Marge EBITDA:                       27.1%
Ticket moyen:                      37.60 €
Rotation des tables (moyenne):       2.15
```

### 5.3 Interprétation des résultats

Pour aider à l'analyse des rapports, le module inclut des commentaires d'interprétation automatisés basés sur des règles métier et l'intelligence artificielle :

#### 5.3.1 Analyse comparative

```
ANALYSE DES PERFORMANCES - AVRIL 2025

TENDANCES PRINCIPALES
---------------------------------------------------------------
✅ Chiffre d'affaires en hausse de 8.5% par rapport au mois précédent
✅ Marge brute améliorée de 1.2 points (67.8% vs 66.6%)
⚠️ Hausse des coûts énergétiques de 12.3% à surveiller
✅ Ticket moyen en progression à 37.60€ (+1.50€)

RECOMMANDATIONS
---------------------------------------------------------------
1. Le ratio food cost est légèrement au-dessus de l'objectif (31.9% vs 30.0%)
   → Vérifier la tarification des nouveaux plats
   → Analyser les pertes potentielles sur les ingrédients coûteux

2. Les ventes de boissons représentent 19.6% du CA (objectif: 22%)
   → Évaluer la stratégie de vente suggérée pour les boissons
   → Revoir la formation du personnel sur les recommandations

3. Prévision trésorerie: attention au pic de paiements fournisseurs prévu 
   mi-mai (environ 28,000€)
```

#### 5.3.2 Indicateurs et alertes

Le système génère automatiquement des alertes visuelles dans les tableaux de bord :

- 🟢 Vert : Indicateur au-dessus des objectifs
- 🟠 Orange : Indicateur proche des seuils de vigilance
- 🔴 Rouge : Indicateur en-dessous des objectifs ou problème détecté

Exemple d'alerte : 
```
🔴 ALERTE - La marge sur la catégorie "Pizzas Spéciales" est passée sous le seuil
    de rentabilité cible (43.5% vs objectif 50%)
    
    Causes possibles identifiées :
    - Augmentation du coût des ingrédients fromagers (+18% sur le mois)
    - Proportion élevée de promotions sur cette catégorie (24% des ventes)
    
    Actions suggérées :
    - Réévaluer la tarification de cette catégorie
    - Ajuster les portions des ingrédients les plus coûteux
    - Réviser la stratégie promotionnelle
```

Cette documentation détaillée du module de comptabilité offre une vision complète de son architecture, ses mécanismes de fonctionnement, et ses capacités de reporting. Elle servira de référence pour l'équipe technique, le personnel comptable et la direction du restaurant "Le Vieux Moulin".