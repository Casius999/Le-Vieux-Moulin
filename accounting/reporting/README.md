# Module de Génération de Rapports

Ce module automatise la génération de rapports financiers détaillés pour le restaurant "Le Vieux Moulin", réduisant considérablement le travail manuel du comptable.

## Fonctionnalités

- Génération automatique de rapports financiers complets (journaliers, hebdomadaires, mensuels, annuels)
- Export vers différents formats (PDF, Excel, CSV, formats comptables spécifiques)
- Distribution automatique des rapports par email et archivage
- Personnalisation des modèles de rapports selon les besoins spécifiques
- Système de validation et vérification pour garantir l'intégrité des données

## Structure des rapports

### Rapports journaliers
- Récapitulatif des ventes par catégorie et par moyen de paiement
- Détail des encaissements et situation de caisse
- Synthèse des transactions avec ventilation TVA
- Indicateurs de performance quotidiens

### Rapports hebdomadaires
- Synthèse des ventes sur la semaine
- Analyse comparative avec semaines précédentes
- Ventilation des coûts de la semaine
- Indicateurs de productivité et d'efficacité

### Rapports mensuels
- Compte de résultat détaillé
- Analyse des marges par catégorie de produits
- Suivi des dépenses par poste
- Rapprochement avec objectifs et budget
- État des stocks et valorisation

### Rapports annuels
- Bilan complet
- Compte de résultat annuel
- Analyse des tendances et évolutions
- Rapports fiscaux préliminaires

## Architecture

Le module est structuré autour des composants suivants :

- `report_generator.js` : Moteur principal de génération de rapports
- `report_templates/` : Modèles pour différents types de rapports
- `formatters/` : Convertisseurs pour différents formats d'export
- `validators/` : Vérification d'intégrité et validation des données
- `distributors/` : Mécanismes d'envoi et distribution des rapports

## Intégration

Ce module s'intègre avec :
- Le module de suivi financier pour récupérer les données en temps réel
- Le module de gestion des stocks pour la valorisation des inventaires
- Le module export pour la compatibilité avec les logiciels comptables
- Le système de notification pour l'envoi des rapports

## Utilisation

```javascript
// Exemple d'utilisation du générateur de rapports
const { ReportGenerator } = require('./report_generator');

// Initialisation avec configuration
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

// Génération d'un rapport mensuel
async function generateMonthlyReport(year, month) {
  // Collecte des données nécessaires
  const period = { year, month };
  
  // Génération et export du rapport
  const report = await reportGenerator.createMonthlyReport({
    period,
    formats: ['pdf', 'excel', 'sage'],
    distribute: true // Envoi automatique aux destinataires configurés
  });
  
  return report;
}
```