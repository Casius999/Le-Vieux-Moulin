# API Connectors - Le Vieux Moulin

Ce répertoire contient les connecteurs d'API permettant au système "Le Vieux Moulin" d'interagir avec des services externes tels que la caisse enregistreuse, les fournisseurs, les plateformes de réservation et le système CRM.

## Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure du répertoire](#structure-du-répertoire)
3. [Configuration des connecteurs](#configuration-des-connecteurs)
4. [Connecteurs disponibles](#connecteurs-disponibles)
   - [Caisse Enregistreuse (POS)](#caisse-enregistreuse-pos)
   - [Fournisseurs](#fournisseurs)
   - [Réservation](#réservation)
   - [CRM](#crm)
5. [Utilisation](#utilisation)
6. [Gestion des erreurs](#gestion-des-erreurs)
7. [Sécurité](#sécurité)
8. [Maintenance et extension](#maintenance-et-extension)
9. [Tests](#tests)

## Vue d'ensemble

Les connecteurs API sont des interfaces modulaires permettant la communication entre le système central "Le Vieux Moulin" et divers services externes. Chaque connecteur est conçu pour être :

- **Indépendant** : Peut être utilisé, mis à jour ou remplacé sans affecter les autres composants
- **Sécurisé** : Implémente des protocoles d'authentification et de communication sécurisés
- **Résilient** : Gère les erreurs, les délais d'attente et les tentatives de reconnexion
- **Configurable** : Adaptable à différents environnements et besoins
- **Bien documenté** : Avec des exemples clairs et une documentation d'API complète

## Structure du répertoire

```
/api_connectors/
├── __init__.py                 # Rend le dossier importable comme package
├── common/                     # Fonctionnalités partagées entre connecteurs
│   ├── __init__.py
│   ├── auth.py                 # Méthodes d'authentification (OAuth, API keys, etc.)
│   ├── http_client.py          # Client HTTP avec retry, timeouts, etc.
│   ├── rate_limiter.py         # Limitation de débit pour les API
│   ├── exceptions.py           # Exceptions personnalisées
│   └── utils.py                # Utilitaires divers
├── pos/                        # Connecteur pour caisse enregistreuse
│   ├── __init__.py
│   ├── lightspeed.py           # Implémentation spécifique à Lightspeed
│   ├── square.py               # Implémentation spécifique à Square
│   └── base.py                 # Classe de base abstraite pour les POS
├── suppliers/                  # Connecteurs fournisseurs
│   ├── __init__.py
│   ├── metro.py                # API Metro France
│   ├── transgourmet.py         # API Transgourmet
│   ├── pomona.py               # API Pomona
│   └── base.py                 # Classe de base pour les fournisseurs
├── reservation/                # Connecteurs réservation
│   ├── __init__.py
│   ├── thefork.py              # API TheFork (LaFourchette)
│   ├── opentable.py            # API OpenTable
│   └── base.py                 # Classe de base pour les systèmes de réservation
├── crm/                        # Connecteurs CRM
│   ├── __init__.py
│   ├── hubspot.py              # API HubSpot
│   ├── zoho.py                 # API Zoho CRM
│   └── base.py                 # Classe de base pour les systèmes CRM
├── config/                     # Configurations par défaut
│   ├── __init__.py
│   ├── pos_config.example.yaml # Configuration exemple pour POS
│   ├── suppliers_config.example.yaml
│   ├── reservation_config.example.yaml
│   └── crm_config.example.yaml
└── tests/                      # Tests unitaires et d'intégration
    ├── __init__.py
    ├── test_pos.py
    ├── test_suppliers.py
    ├── test_reservation.py
    └── test_crm.py
```

## Configuration des connecteurs

Chaque connecteur API utilise un fichier de configuration au format YAML, permettant une personnalisation sans modification du code. Les fichiers de configuration contiennent :

- URLs des endpoints d'API
- Identifiants et méthodes d'authentification
- Paramètres de timeout et retry
- Options de mise en cache et de logging

Exemple de configuration pour un connecteur POS (caisse enregistreuse) :

```yaml
# Configuration pour Lightspeed POS
api:
  base_url: "https://api.lightspeedapp.com/api/"
  version: "v1"

auth:
  method: "oauth2"
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  redirect_uri: "https://levieuxmoulin.fr/oauth/callback"
  scopes: ["employee:inventory", "employee:sales"]
  token_store: "file"
  token_path: "/path/to/tokens/lightspeed_token.json"

connection:
  timeout: 30  # secondes
  max_retries: 3
  retry_delay: 2  # secondes
  pool_connections: 10
  pool_maxsize: 10

rate_limit:
  max_requests_per_minute: 60
  throttle_on_limit: true

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Connecteurs disponibles

### Caisse Enregistreuse (POS)

Les connecteurs POS permettent la synchronisation bidirectionnelle des données de vente entre le système "Le Vieux Moulin" et la caisse enregistreuse.

#### Fonctionnalités

- Récupération des transactions en temps réel
- Mise à jour des produits et des prix
- Synchronisation des promotions
- Transmission des données vers le module de comptabilité

#### Implémentations disponibles

- **Lightspeed** : API RESTful complète pour les restaurants
- **Square** : Solution pour les paiements et la gestion de point de vente

### Fournisseurs

Les connecteurs fournisseurs permettent la commande automatique d'ingrédients et de fournitures auprès des principaux fournisseurs du restaurant.

#### Fonctionnalités

- Création et suivi des commandes
- Consultation des catalogues et des prix
- Vérification des disponibilités
- Notifications de livraison

#### Implémentations disponibles

- **Metro France** : API DirectOrder pour les commandes B2B
- **Transgourmet** : API REST pour la restauration professionnelle
- **Pomona** : API B2B pour les approvisionnements

### Réservation

Les connecteurs de réservation permettent la gestion centralisée des réservations des clients provenant de différentes plateformes.

#### Fonctionnalités

- Synchronisation des réservations
- Gestion des disponibilités des tables
- Confirmation et modification des réservations
- Création de profils clients

#### Implémentations disponibles

- **TheFork** (LaFourchette) : Principale plateforme de réservation en France
- **OpenTable** : Plateforme de réservation internationale

### CRM

Les connecteurs CRM permettent la gestion des relations clients et l'optimisation des actions marketing.

#### Fonctionnalités

- Synchronisation des profils clients
- Gestion des programmes de fidélité
- Segmentation pour campagnes ciblées
- Analyse du comportement client

#### Implémentations disponibles

- **HubSpot** : Plateforme CRM complète
- **Zoho CRM** : Solution CRM flexible

## Utilisation

Chaque connecteur API suit un modèle d'utilisation similaire :

```python
from levieuxmoulin.integration.api_connectors.pos import LightspeedConnector
from datetime import datetime, timedelta

# Initialiser le connecteur
pos = LightspeedConnector(config_path="/path/to/config.yaml")

# Se connecter et authentifier
await pos.connect()

# Définir la période de recherche
start_date = datetime.now() - timedelta(days=7)  # 7 derniers jours
end_date = datetime.now()

# Récupérer les transactions
transactions = await pos.get_transactions(
    start_date=start_date,
    end_date=end_date,
    status="completed"
)

# Traiter les résultats
for transaction in transactions:
    print(f"Transaction #{transaction.id}: {transaction.total} €")
    
    # Détails des articles vendus
    for item in transaction.items:
        print(f"  - {item.quantity}x {item.name}: {item.price} €")
```

## Gestion des erreurs

Tous les connecteurs implémentent une gestion robuste des erreurs :

1. **Classification des erreurs** : Exceptions spécifiques selon le type d'erreur (authentification, réseau, API, etc.)
2. **Retry automatique** : Tentatives multiples avec backoff exponentiel pour les erreurs temporaires
3. **Circuit Breaker** : Protection contre les pannes prolongées de services externes
4. **Logging détaillé** : Journalisation complète des erreurs pour le diagnostic

Exemple de gestion d'erreur :

```python
from levieuxmoulin.integration.api_connectors.common.exceptions import (
    AuthenticationError, APIError, RateLimitError, ConnectionError
)

try:
    orders = await supplier.create_order(items)
    print(f"Commande créée avec succès: #{orders.order_id}")
    
except AuthenticationError as e:
    # Problème d'authentification (token expiré, identifiants invalides, etc.)
    print(f"Erreur d'authentification: {e}")
    # Tentative de réauthentification
    await supplier.refresh_authentication()
    
except RateLimitError as e:
    # Limite de requêtes API atteinte
    print(f"Limite de requêtes atteinte: {e}")
    print(f"Réessayer après: {e.retry_after} secondes")
    
except ConnectionError as e:
    # Problème de connexion réseau
    print(f"Erreur de connexion: {e}")
    # Mettre en file d'attente pour traitement ultérieur
    queue_for_later(supplier, "create_order", items)
    
except APIError as e:
    # Erreur côté API (validation, ressource inexistante, etc.)
    print(f"Erreur API ({e.status_code}): {e.message}")
    if e.is_retriable:
        print("Erreur temporaire, nouvel essai possible ultérieurement")
```

## Sécurité

Les connecteurs API implémentent plusieurs mesures de sécurité :

1. **Authentification sécurisée** :
   - OAuth 2.0 avec PKCE pour les services le supportant
   - Gestion sécurisée des tokens et des clés API
   - Rotation automatique des tokens expirés

2. **Communication chiffrée** :
   - Utilisation exclusive de HTTPS avec validation des certificats
   - Support de TLS 1.2+ uniquement

3. **Protection des données** :
   - Pas de stockage de données sensibles en clair
   - Options pour le chiffrement des données au repos

4. **Audit et traçabilité** :
   - Journalisation de toutes les opérations pour audit
   - Traçabilité des modifications et des appels API

## Maintenance et extension

### Ajouter un nouveau connecteur

Pour ajouter un nouveau fournisseur de service, créez une nouvelle classe héritant de la classe de base appropriée :

```python
from levieuxmoulin.integration.api_connectors.suppliers.base import BaseSupplierConnector

class NewSupplierConnector(BaseSupplierConnector):
    """Connecteur pour le fournisseur XYZ."""
    
    def __init__(self, config_path=None, config_dict=None):
        super().__init__(config_path, config_dict)
        # Initialisation spécifique au fournisseur
        
    async def connect(self):
        """Établit la connexion avec l'API du fournisseur."""
        # Implémentation de la connexion
        
    async def get_catalog(self, category=None):
        """Récupère le catalogue des produits disponibles."""
        # Implémentation de la récupération du catalogue
        
    async def create_order(self, items, delivery_date=None):
        """Crée une nouvelle commande."""
        # Implémentation de la création de commande
        
    # Autres méthodes spécifiques au fournisseur
```

### Mise à jour des API

En cas de changement dans une API externe, les modifications sont généralement limitées à un seul fichier. La structure modulaire permet de mettre à jour un connecteur sans impacter les autres composants du système.

## Tests

Chaque connecteur est accompagné de tests complets :

- **Tests unitaires** : Validation des fonctionnalités individuelles
- **Tests d'intégration** : Vérification de l'interaction avec les services réels
- **Tests de mock** : Simulation des réponses API pour les tests isolés

Les tests peuvent être exécutés avec pytest :

```bash
# Exécuter tous les tests
pytest

# Exécuter les tests pour un connecteur spécifique
pytest tests/test_pos.py

# Exécuter avec couverture de code
pytest --cov=levieuxmoulin.integration.api_connectors
```

Les tests d'intégration nécessitent des informations d'authentification valides, qui peuvent être fournies via des variables d'environnement ou un fichier de configuration de test.
