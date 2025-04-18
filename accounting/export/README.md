# Module d'Export Comptable

Ce module assure l'export des données financières du restaurant "Le Vieux Moulin" vers différents formats et logiciels comptables, garantissant une transition fluide entre le système de gestion et la comptabilité externe.

## Fonctionnalités

- Export automatique des données financières vers différents formats compatibles
- Support pour les principaux logiciels comptables du marché français
- Mappage configurable avec les plans comptables normalisés
- Génération du Fichier des Écritures Comptables (FEC) conformément à la législation
- Validation et contrôle de cohérence avant export

## Formats supportés

### Formats génériques
- **CSV** : format tabulaire pour import dans n'importe quel logiciel
- **Excel** : export sous forme de classeurs avec feuilles multiples
- **JSON** : format structuré pour échanges API
- **XML** : format conforme aux standards EDI

### Formats spécifiques
- **Sage** : compatibilité avec la gamme de logiciels Sage Compta
- **QuickBooks** : format d'import IIF et QBX
- **EBP** : format spécifique pour EBP Compta
- **Ciel Compta** : format d'import natif
- **Format FEC** : format normalisé pour l'administration fiscale

## Structure du module

- `export_manager.js` : Gestionnaire central des exports
- `formatters/` : Convertisseurs pour chaque format d'export
  - `csv_formatter.js` : Génération d'exports CSV
  - `excel_formatter.js` : Génération de feuilles de calcul
  - `sage_formatter.js` : Formatage pour Sage
  - `quickbooks_formatter.js` : Formatage pour QuickBooks
  - `fec_formatter.js` : Formatage aux normes FEC
- `mappings/` : Configuration des correspondances entre données
  - `account_mappings.js` : Mappages vers plans comptables standards
  - `transaction_mappings.js` : Mappages des types de transactions
- `validators/` : Vérifications pré-export
  - `data_validator.js` : Validation de la cohérence des données
  - `balance_validator.js` : Vérification des équilibres comptables

## Plan comptable et mappage

Le module implémente un mappage configurable des catégories internes vers les comptes du plan comptable français :

```javascript
// Exemple de mappage vers le plan comptable français
const accountMapping = {
  // Produits
  'sales_food': '707100',         // Ventes de nourriture
  'sales_beverage': '707200',     // Ventes de boissons
  'sales_takeaway': '707300',     // Ventes à emporter
  
  // Charges
  'purchase_food': '607100',      // Achats de nourriture
  'purchase_beverage': '607200',  // Achats de boissons
  'staff_wages': '641000',        // Salaires
  'staff_benefits': '645000',     // Charges sociales
  'rent': '613200',               // Loyers
  'utilities': '606100',          // Électricité, eau, gaz
  'maintenance': '615000',        // Entretien et réparations
  'smallequipment': '606300',     // Petit équipement
  'insurance': '616000',          // Assurances
  'fees': '622600',               // Honoraires
  'advertising': '623100',        // Publicité
  
  // Comptes TVA
  'vat_collected': '445710',      // TVA collectée
  'vat_deductible': '445660',     // TVA déductible
  
  // Comptes financiers
  'bank': '512000',               // Banque
  'cash': '531000',               // Caisse
  'card_payments': '511200',      // Transactions CB à encaisser
};
```

## Configuration

```javascript
// Exemple de configuration du gestionnaire d'exports
const exportConfig = {
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

## Utilisation

```javascript
// Exemple d'utilisation du gestionnaire d'exports
const { ExportManager } = require('./export_manager');

// Initialisation avec configuration
const exportManager = new ExportManager({
  config: exportConfig,
  account_mapping: accountMapping
});

// Génération d'un export comptable
async function generateMonthlyExport(year, month) {
  // Préparation de la période
  const period = { year, month };
  
  // Génération et envoi de l'export
  const exportResult = await exportManager.generateExport({
    period,
    formats: ['sage', 'excel', 'fec'],
    distribute: true // Envoi automatique aux destinataires configurés
  });
  
  return exportResult;
}
```

## Intégration

Ce module s'intègre avec :
- Le module de suivi financier pour récupérer les données financières
- Le module de gestion de TVA pour les déclarations fiscales
- Le module de reporting pour les contrôles de cohérence
- Le système de notification pour la distribution des exports