# Module de Comptabilité Avancé - Le Vieux Moulin

Ce module automatise la génération de rapports financiers détaillés pour le restaurant "Le Vieux Moulin", consolidant les données de tous les autres modules (ventes, stocks, commandes, marketing, prévisions IA/ML) et réduisant au strict minimum l'intervention du comptable humain.

## Fonctionnalités principales

- Collecte et consolidation automatique des données financières
- Génération de rapports détaillés (chiffre d'affaires, dépenses, profits, marges, etc.)
- Tableaux de bord financiers en temps réel
- Vérification d'intégrité et contrôles automatiques
- Export automatisé vers différents formats (PDF, CSV)
- Calcul automatique de la TVA et autres taxes applicables

## Structure du module

- `src/` - Code source principal
  - `collectors/` - Collecteurs de données depuis les différentes sources
  - `processors/` - Traitement et analyse des données financières
  - `reports/` - Générateurs de rapports et tableaux de bord
  - `exporters/` - Exportation de rapports vers différents formats
  - `utils/` - Utilitaires communs

- `config/` - Fichiers de configuration
  - `accounts.json` - Configuration du plan comptable
  - `taxes.json` - Configuration des taux de TVA et autres taxes
  - `sources.json` - Configuration des sources de données

- `tests/` - Tests unitaires et d'intégration
  - `unit/` - Tests unitaires
  - `integration/` - Tests d'intégration
  - `scenarios/` - Scénarios de test pour la validation

## Installation et configuration

Consultez le fichier [INSTALL.md](./INSTALL.md) pour les instructions détaillées d'installation et de configuration du module.

## Documentation

La documentation complète du module est disponible dans le fichier [ACCOUNTING.md](./ACCOUNTING.md).

## Intégration avec les autres modules

Ce module s'intègre avec les autres composants du système "Le Vieux Moulin" via des API REST et/ou webhooks. Pour les détails d'intégration, consultez la section appropriée dans la documentation [ACCOUNTING.md](./ACCOUNTING.md).

## Tests

Pour exécuter les tests unitaires et d'intégration:

```bash
cd accounting
python -m pytest
```

Pour exécuter les tests de scénarios spécifiques:

```bash
cd accounting
python -m pytest tests/scenarios/test_monthly_report.py -v
```

## Licence

© 2025 Le Vieux Moulin - Tous droits réservés
