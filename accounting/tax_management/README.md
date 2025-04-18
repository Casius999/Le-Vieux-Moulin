# Module de Gestion de la TVA et Obligations Fiscales

Ce module gère automatiquement la TVA et prépare les documents pour les différentes obligations fiscales du restaurant "Le Vieux Moulin".

## Fonctionnalités

- Calcul automatique de la TVA collectée et déductible par taux
- Préparation des déclarations périodiques de TVA
- Suivi des acomptes et paiements fiscaux
- Préparation des données pour les obligations fiscales annuelles
- Archives sécurisées pour les contrôles fiscaux

## Structure du module

### Gestion de la TVA
- Différenciation des taux (10% restauration sur place, 5.5% vente à emporter, 20% boissons alcoolisées)
- Calcul automatique de la TVA à partir des données de vente et d'achat
- Génération des rapports de TVA (mensuels ou trimestriels)
- Préparation des fichiers compatibles pour déclaration en ligne

### Obligations fiscales
- Calendrier fiscal avec rappels automatiques
- Suivi des échéances et délais légaux
- Préparation des données pour les déclarations fiscales annuelles
- Calcul des charges fiscales provisionnées

### Conformité légale
- Archivage conforme des documents fiscaux (durée légale)
- Format FEC (Fichier des Écritures Comptables) pour contrôles fiscaux
- Piste d'audit fiable pour toutes les transactions
- Justificatifs numériques sécurisés

## Architecture technique

Le module est structuré autour des composants suivants :
- `vat_calculator.js` : Calcul de la TVA selon les différentes règles et taux
- `tax_declaration_generator.js` : Génération des déclarations et formulaires fiscaux
- `fiscal_calendar.js` : Gestion des échéances et rappels fiscaux
- `fec_exporter.js` : Générateur de fichiers aux normes FEC
- `vat_report.js` : Rapports d'analyse et suivi de TVA

## Configuration

Le système gère différentes configurations selon les besoins spécifiques :

```javascript
// Exemple de configuration des taux de TVA
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

## Intégration

Ce module s'intègre avec :
- Le module de caisse pour récupérer les données de TVA collectée
- Le module de gestion des achats pour la TVA déductible
- Le module de reporting pour la génération des rapports fiscaux
- Le système de notification pour les rappels d'échéances fiscales