# Module de Comptabilité Avancé - Le Vieux Moulin

Ce répertoire contient l'ensemble des composants du module de comptabilité avancé pour le restaurant "Le Vieux Moulin". Ce module génère automatiquement des rapports exhaustifs pour le comptable humain, en s'appuyant sur les données collectées par les autres modules du système. L'objectif est de réduire le travail du comptable au strict minimum grâce à une gestion native optimale et à des données en temps réel.

## Structure du Répertoire

- **/financial_tracking/** - Suivi financier et tableaux de bord en temps réel
- **/reporting/** - Génération automatique de rapports pour le comptable
- **/tax_management/** - Gestion de la TVA et des obligations fiscales
- **/inventory_valuation/** - Valorisation du stock et calcul des coûts
- **/payroll/** - Préparation des données pour la paie
- **/export/** - Formats d'export pour les logiciels comptables

## Fonctionnalités Principales

### 1. Suivi Financier en Temps Réel

Le module de suivi financier offre une vue en temps réel de la situation financière du restaurant.

#### Tableaux de Bord
- Chiffre d'affaires quotidien, hebdomadaire, mensuel et annuel
- Répartition des ventes par catégorie de produits
- Marge brute et nette par plat
- Analyse des coûts et dépenses

#### Alertes et Notifications
- Détection d'écarts significatifs par rapport aux prévisions
- Alertes sur les marges anormalement basses
- Notifications de seuils financiers atteints

#### Exemple de Configuration
```javascript
// Exemple de configuration des tableaux de bord financiers
const financialDashboardConfig = {
  refresh_rate: 15, // minutes
  kpis: [
    {
      id: 'daily_revenue',
      name: 'Chiffre d\'affaires du jour',
      calculation: 'sum',
      source: 'transactions',
      filter: { date: 'today' },
      display: {
        format: 'currency',
        comparison_to_previous: true,
        comparison_to_forecast: true
      },
      alerts: [
        {
          condition: 'value < forecast * 0.7',
          level: 'warning',
          message: 'CA inférieur à 70% des prévisions',
          notify: ['manager', 'owner']
        }
      ]
    },
    {
      id: 'gross_margin',
      name: 'Marge brute',
      calculation: 'custom',
      formula: '(revenue - food_cost) / revenue * 100',
      dependencies: ['revenue', 'food_cost'],
      display: {
        format: 'percentage',
        target: 70, // %
        threshold_low: 65,
        threshold_critical: 60
      }
    },
    // Autres KPIs...
  ],
  views: [
    {
      id: 'manager_dashboard',
      name: 'Tableau de bord Manager',
      kpis: ['daily_revenue', 'weekly_revenue', 'gross_margin', 'labor_cost_percentage'],
      layout: '2x2_grid'
    },
    {
      id: 'owner_dashboard',
      name: 'Tableau de bord Propriétaire',
      kpis: ['monthly_revenue', 'yearly_revenue', 'net_profit', 'roi'],
      layout: 'vertical_list'
    }
  ]
};
```

### 2. Génération Automatique de Rapports

Ce module génère des rapports détaillés et exhaustifs pour le comptable, réduisant considérablement son travail manuel.

#### Types de Rapports
- Journalier : Transactions, encaissements, paiements fournisseurs
- Hebdomadaire : Synthèse des ventes, analyse des coûts
- Mensuel : Compte de résultat, balance âgée, analyse des marges
- Annuel : Bilan, compte de résultat, tableau de flux de trésorerie

#### Formats d'Export
- PDF pour consultation
- Excel/CSV pour analyse
- Formats spécifiques compatibles avec les logiciels comptables (Sage, QuickBooks, etc.)

#### Exemple d'Utilisation
```javascript
// Exemple de génération de rapport comptable
const { ReportGenerator } = require('./reporting/generator');

// Initialiser le générateur
const reportGenerator = new ReportGenerator({
  templates_dir: './templates',
  output_dir: './reports',
  company_info: {
    name: 'SARL Le Vieux Moulin',
    siret: '12345678901234',
    address: 'Camping 3 étoiles, Vensac, Gironde',
    vat_number: 'FR12345678901'
  }
});

// Générer un rapport mensuel
async function generateMonthlyReport(year, month) {
  try {
    // Collecter les données nécessaires
    const transactionData = await dataCollector.getTransactions({ year, month });
    const inventoryData = await dataCollector.getInventoryValuation({ year, month });
    const expensesData = await dataCollector.getExpenses({ year, month });
    
    // Générer le rapport
    const report = await reportGenerator.createMonthlyReport({
      year,
      month,
      data: {
        transactions: transactionData,
        inventory: inventoryData,
        expenses: expensesData
      },
      formats: ['pdf', 'excel', 'sage']
    });
    
    // Notifier le comptable
    await notificationService.sendToAccountant({
      subject: `Rapport comptable ${month}/${year}`,
      message: 'Le rapport comptable mensuel est disponible.',
      attachments: report.files
    });
    
    return report;
  } catch (error) {
    console.error('Erreur lors de la génération du rapport:', error);
    throw error;
  }
}
```

### 3. Gestion de la TVA et Obligations Fiscales

Ce module automatise la gestion de la TVA et prépare les données pour les déclarations fiscales.

#### Fonctionnalités
- Calcul automatique de la TVA collectée et déductible
- Préparation des déclarations périodiques
- Suivi des acomptes et paiements
- Gestion des taux de TVA multiples (standard, réduit, intermédiaire)

#### Schéma de Configuration TVA
```javascript
// Configuration des taux de TVA par catégorie de produit
const vatConfiguration = {
  default_rate: 20.0, // Taux standard en %
  categories: {
    food_onsite: 10.0, // Restauration sur place
    food_takeaway: 5.5, // Vente à emporter
    alcohol: 20.0, // Boissons alcoolisées
    non_alcoholic_drinks: 10.0 // Boissons non alcoolisées sur place
  },
  special_items: {
    // Exceptions produit par produit
    'special_product_id_1': 5.5,
    'special_product_id_2': 20.0
  },
  declaration_period: 'monthly', // ou 'quarterly', 'annual'
  filing_deadline_days: 15, // Jours après la fin de période
  prepayment_required: false
};
```

### 4. Valorisation des Stocks et Calcul des Coûts

Ce module évalue en permanence la valeur du stock et calcule les coûts de revient précis.

#### Méthodes de Valorisation
- Prix moyen pondéré (PAP)
- First In, First Out (FIFO)
- Last In, First Out (LIFO)
- Coût standard

#### Calculs Automatisés
- Coût de revient par plat
- Coût matière des menus
- Impact des variations de prix fournisseurs
- Détection des pertes et gaspillage

#### Exemple de Calcul de Coût
```javascript
// Exemple de calcul de coût de revient d'un plat
const { CostCalculator } = require('./inventory_valuation/calculator');

// Initialiser le calculateur
const costCalculator = new CostCalculator({
  inventory_source: inventoryManager,
  valuation_method: 'weighted_average',
  include_overhead: true,
  overhead_allocation_method: 'percentage' // ou 'fixed'
});

// Calculer le coût d'un plat
async function calculateDishCost(dishId) {
  try {
    // Récupérer la recette et les quantités d'ingrédients
    const recipe = await recipeManager.getRecipe(dishId);
    
    // Calculer le coût
    const costBreakdown = await costCalculator.calculateRecipeCost({
      recipe_id: dishId,
      ingredients: recipe.ingredients,
      portion_size: recipe.portion_size,
      production_time: recipe.preparation_time + recipe.cooking_time,
      energy_usage: recipe.energy_consumption || 'medium'
    });
    
    // Analyser la rentabilité
    const sellingPrice = await menuManager.getDishPrice(dishId);
    const grossMargin = (sellingPrice - costBreakdown.total_cost) / sellingPrice * 100;
    
    return {
      dish_id: dishId,
      dish_name: recipe.name,
      cost_breakdown: costBreakdown,
      selling_price: sellingPrice,
      gross_margin: grossMargin,
      margin_category: categorizeMargin(grossMargin)
    };
  } catch (error) {
    console.error('Erreur lors du calcul du coût du plat:', error);
    throw error;
  }
}

// Catégoriser la marge
function categorizeMargin(marginPercentage) {
  if (marginPercentage < 30) return 'critical';
  if (marginPercentage < 50) return 'low';
  if (marginPercentage < 70) return 'normal';
  return 'excellent';
}
```

### 5. Préparation des Données pour la Paie

Ce module collecte et structure les données nécessaires pour la préparation de la paie.

#### Fonctionnalités
- Suivi des heures travaillées
- Calcul des primes et commissions
- Gestion des congés et absences
- Exportation vers les logiciels de paie

#### Intégration avec les Plannings
- Récupération automatique des heures planifiées
- Comparaison avec les heures réellement travaillées
- Calcul des heures supplémentaires
- Validation par les managers

### 6. Export vers Logiciels Comptables

Ce module assure la compatibilité avec les principaux logiciels de comptabilité.

#### Formats Supportés
- Sage
- QuickBooks
- EBP
- Ciel Compta
- Format standardisé FEC (Fichier des Écritures Comptables)

#### Mappage des Comptes
- Plan comptable français standard
- Personnalisation possible des comptes
- Vérification de cohérence avant export

#### Configuration d'Export
```javascript
// Exemple de configuration d'export comptable
const accountingExportConfig = {
  default_format: 'sage',
  export_schedule: {
    frequency: 'daily',
    time: '23:30',
    auto_send: true
  },
  recipients: [
    {
      name: 'Cabinet Comptable XYZ',
      email: 'comptable@example.com',
      formats: ['sage', 'fec'],
      encryption: true // Chiffrement PGP
    }
  ],
  account_mapping: {
    // Mappage des comptes internes vers plan comptable
    'sales_food': '707100',
    'sales_beverage': '707200',
    'purchase_food': '607100',
    'purchase_beverage': '607200',
    'staff_wages': '641000',
    // Autres comptes...
  },
  data_validation: {
    run_before_export: true,
    checks: [
      'balance_verification',
      'vat_consistency',
      'missing_accounts'
    ]
  },
  retention: {
    keep_exports_for_years: 10,
    archive_after_months: 3
  }
};
```

## Intégration avec les Autres Modules

### Caisse et Transactions
- Récupération en temps réel des ventes
- Catégorisation automatique des transactions
- Suivi des moyens de paiement et réconciliation bancaire

### IoT et Gestion des Stocks
- Valorisation automatique du stock basée sur les données des capteurs
- Calcul précis du coût des matières consommées
- Détection du gaspillage et des pertes

### Planning et Ressources Humaines
- Collecte des heures travaillées pour la paie
- Calcul du coût de main d'œuvre par service
- Optimisation du ratio personnel/chiffre d'affaires

### IA/ML pour Prévisions Financières
- Prévisions de trésorerie
- Détection d'anomalies dans les transactions
- Optimisation financière basée sur les données historiques

## Sécurité et Conformité

### Protection des Données
- Chiffrement des données financières sensibles
- Accès strictement contrôlé aux informations comptables
- Journalisation de toutes les opérations (audit trail)

### Conformité Réglementaire
- Respect des normes comptables françaises
- Conformité RGPD pour les données personnelles
- Format FEC pour contrôles fiscaux
- Archivage légal des documents comptables

## Tableau de Bord Comptable

Un tableau de bord dédié est disponible pour le comptable, offrant :
- Vue d'ensemble de la situation financière
- Accès aux rapports générés automatiquement
- Interface pour valider les écritures importantes
- Système de notes et commentaires

## Configuration pour Multi-Établissements

Le module de comptabilité est conçu pour gérer plusieurs établissements :
- Comptabilité séparée par établissement
- Consolidation possible au niveau groupe
- Analyse comparative entre établissements
- Rapports combinés ou individuels

---

Pour toute question ou assistance concernant le module de comptabilité, consultez la documentation détaillée ou contactez l'équipe financière.
