# Module de Paie - Le Vieux Moulin

Ce module est responsable de la préparation des données pour la paie du personnel du restaurant "Le Vieux Moulin". Il automatise la collecte des informations nécessaires, le calcul des heures travaillées, des primes et commissions, et génère les exports compatibles avec les logiciels de paie.

## Fonctionnalités

### 1. Collecte des données de présence

- Intégration avec le système de pointage
- Récupération des plannings validés
- Suivi des congés, absences et jours fériés
- Détection des anomalies (oublis de pointage, heures incohérentes)

### 2. Calcul des heures

- Calcul des heures régulières par employé
- Identification des heures supplémentaires (25%, 50%, etc.)
- Gestion des pauses obligatoires
- Respect des contraintes légales (repos quotidien, hebdomadaire)

### 3. Gestion des primes et variables

- Calcul des primes de service
- Suivi des pourboires centralisés
- Gestion des primes exceptionnelles
- Avantages en nature (repas, logement)

### 4. Préparation des données de paie

- Formatage des données pour export
- Validation des cumuls par catégorie
- Génération des fichiers d'import pour les logiciels de paie
- Archivage des données historiques

## Intégration avec les autres modules

### Planning et gestion du personnel

Le module récupère automatiquement:
- Les plannings prévus et validés
- Les modifications en cours de service
- Les échanges de services entre employés

### Caisse et transactions

Le module exploite:
- Les données de chiffre d'affaires pour les primes sur CA
- Les pourboires collectés par carte bancaire
- Les horaires réels d'activité du restaurant

### Comptabilité générale

Le module contribue aux:
- Provisions de charges sociales
- Écritures comptables liées à la paie
- Analyse du coût de main d'œuvre

## Configuration

### Paramétrage des règles de paie

```javascript
// Exemple de configuration des règles de rémunération
const payrollRules = {
  workingHours: {
    regularHoursPerWeek: 35,
    maxDailyHours: 10,
    overtimeRates: [
      { threshold: 35, rate: 1.25 },
      { threshold: 43, rate: 1.50 }
    ],
    nightHours: {
      start: '22:00',
      end: '07:00',
      rate: 1.15
    }
  },
  breaks: {
    minBreakAfterHours: 6,
    breakDuration: 0.5,
    isPaid: false
  },
  serviceTips: {
    distributionMethod: 'points',
    roles: {
      'server': 10,
      'runner': 7,
      'bartender': 8,
      'kitchen': 5,
      'host': 3
    },
    includedInPayroll: true
  },
  mealAllowance: {
    value: 4.85,
    taxDeductible: true
  }
};
```

### Intégration avec les logiciels de paie

Le module prend en charge l'export vers plusieurs formats:
- Format générique (CSV)
- Formats spécifiques (ADP, Sage Paie, Silae)
- Format DSN pour les déclarations sociales

## Utilisation

### Préparation des données mensuelles

```javascript
// Exemple d'utilisation pour préparer les données mensuelles
const { PayrollProcessor } = require('./payroll_processor');

async function prepareMonthlyPayrollData(year, month) {
  try {
    const processor = new PayrollProcessor({
      year,
      month,
      includeValidatedDataOnly: true
    });
    
    // Collecter les données de présence
    await processor.collectAttendanceData();
    
    // Calculer les heures et variables
    const payrollData = await processor.calculatePayrollData();
    
    // Générer l'export
    const exportPath = await processor.generatePayrollExport({
      format: 'silae',
      outputDir: './exports/payroll'
    });
    
    console.log(`Export de paie généré: ${exportPath}`);
    return payrollData;
  } catch (error) {
    console.error('Erreur lors de la préparation des données de paie:', error);
    throw error;
  }
}
```

### Validation des données

Avant l'export final, un processus de validation permet de:
- Détecter les anomalies (heures manquantes, excès d'heures)
- Alerter sur les écarts importants par rapport aux mois précédents
- Vérifier la cohérence des données (totaux de service vs heures travaillées)
- Générer un rapport de pré-validation pour le manager

## Sécurité et confidentialité

Les données de paie étant sensibles, le module implémente:
- Un chiffrement des données stockées
- Des accès restreints et journalisés
- Un anonymisation des données pour les rapports d'analyse
- Une conformité RGPD complète

## Tableau de bord RH

Un tableau de bord dédié offre aux managers:
- Une vue des heures travaillées par service et par employé
- Une analyse du coût de main d'œuvre (ratio coût/CA)
- Des alertes sur les dépassements de budget
- Des tendances et comparaisons avec les périodes antérieures
