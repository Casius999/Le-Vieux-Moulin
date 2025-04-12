# Tests Unitaires et d'Intégration pour les Connecteurs API

Ce répertoire contient les tests unitaires et d'intégration pour les différents connecteurs API du système "Le Vieux Moulin" :

- `test_pos.py` : Tests pour les connecteurs de caisses enregistreuses (Lightspeed, Square)
- `test_suppliers.py` : Tests pour les connecteurs de fournisseurs (Metro, Transgourmet, Pomona)
- `test_reservation.py` : Tests pour les connecteurs de réservation (TheFork, OpenTable)
- `test_crm.py` : Tests pour les connecteurs CRM (HubSpot, Zoho)

## Prérequis

Avant d'exécuter les tests, assurez-vous d'avoir installé les dépendances :

```bash
pip install pytest pytest-asyncio aioresponses pytest-cov
```

## Exécution des Tests

### Tests Unitaires

Les tests unitaires simulent les réponses API et ne nécessitent pas de connexion aux services externes.

```bash
# Exécuter tous les tests unitaires
pytest integration/api_connectors/tests/

# Exécuter les tests pour un type de connecteur spécifique
pytest integration/api_connectors/tests/test_pos.py
pytest integration/api_connectors/tests/test_suppliers.py
pytest integration/api_connectors/tests/test_reservation.py
pytest integration/api_connectors/tests/test_crm.py

# Exécuter un test spécifique
pytest integration/api_connectors/tests/test_pos.py::test_lightspeed_get_transactions

# Exécuter avec rapport de couverture
pytest integration/api_connectors/tests/ --cov=integration.api_connectors
```

### Tests d'Intégration

Les tests d'intégration se connectent aux services réels et nécessitent des identifiants valides. Ils sont désactivés par défaut.

> **Note** : Les tests d'intégration ne doivent être exécutés que dans un environnement de développement ou de test, jamais en production.

Pour exécuter les tests d'intégration, vous devez :

1. Configurer les variables d'environnement pour les identifiants API (voir ci-dessous)
2. Utiliser le marqueur `integration` pour exécuter les tests d'intégration

```bash
# Exécuter uniquement les tests d'intégration
pytest integration/api_connectors/tests/ -m integration

# Exécuter les tests d'intégration pour un connecteur spécifique
pytest integration/api_connectors/tests/test_pos.py -m integration
```

## Configuration des Variables d'Environnement

Pour les tests d'intégration, vous devez configurer les variables d'environnement correspondant à chaque connecteur :

### Lightspeed POS

```bash
export LIGHTSPEED_CLIENT_ID="your_client_id"
export LIGHTSPEED_CLIENT_SECRET="your_client_secret"
export LIGHTSPEED_REDIRECT_URI="your_redirect_uri"
export LIGHTSPEED_REFRESH_TOKEN="your_refresh_token"
export LIGHTSPEED_ACCOUNT_ID="your_account_id"
```

### Square POS

```bash
export SQUARE_ACCESS_TOKEN="your_access_token"
export SQUARE_APPLICATION_ID="your_application_id"
export SQUARE_LOCATION_ID="your_location_id"
```

### Metro (Fournisseur)

```bash
export METRO_API_KEY="your_api_key"
```

### TheFork (Réservation)

```bash
export THEFORK_CLIENT_ID="your_client_id"
export THEFORK_CLIENT_SECRET="your_client_secret"
export THEFORK_RESTAURANT_ID="your_restaurant_id"
```

### HubSpot (CRM)

```bash
export HUBSPOT_CLIENT_ID="your_client_id"
export HUBSPOT_CLIENT_SECRET="your_client_secret"
export HUBSPOT_REFRESH_TOKEN="your_refresh_token"
```

## Structure des Tests

Chaque fichier de test suit une structure similaire :

1. **Fixtures** : Configurations et objets partagés pour les tests
   - `mock_aioresponse` : Simulateur de réponses HTTP
   - `*_config` : Configurations pour chaque connecteur
   - `*_connector` : Instances de connecteurs préinitialisés

2. **Tests Unitaires** : Tests simulant les réponses API
   - Tests de fonctionnalités standard (récupération, création, mise à jour, etc.)
   - Tests de gestion d'erreurs

3. **Tests d'Intégration** : Tests utilisant les API réelles
   - Désactivés par défaut avec `@pytest.mark.skip`
   - Marqués avec `@pytest.mark.integration`
   - Vérification des identifiants avant exécution

## Bonnes Pratiques

- Exécutez les tests unitaires régulièrement pendant le développement
- Exécutez les tests d'intégration avant de déployer des modifications importantes
- Respectez les limites de débit (rate limits) des API lors des tests d'intégration
- Ne stockez jamais d'identifiants réels dans le code source
- Utilisez des identifiants de test/sandbox pour les tests d'intégration
