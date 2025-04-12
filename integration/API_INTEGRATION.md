# Documentation d'Intégration API - Le Vieux Moulin

## Table des Matières

1. [Introduction](#introduction)
2. [Architecture générale](#architecture-générale)
3. [Technologies utilisées](#technologies-utilisées)
4. [Intégrations API implémentées](#intégrations-api-implémentées)
   - [Caisse Enregistreuse (POS)](#caisse-enregistreuse-pos)
   - [Fournisseurs](#fournisseurs)
   - [Réservation](#réservation)
   - [CRM](#crm)
5. [Authentification](#authentification)
6. [Gestion des erreurs](#gestion-des-erreurs)
7. [Performance et mise en cache](#performance-et-mise-en-cache)
8. [Sécurité](#sécurité)
9. [Tests et validation](#tests-et-validation)
10. [Déploiement](#déploiement)
11. [Surveillance et maintenance](#surveillance-et-maintenance)

## Introduction

Ce document décrit l'architecture et l'implémentation des connexions API entre le système de gestion "Le Vieux Moulin" et divers services externes essentiels au fonctionnement du restaurant. Cette intégration est conçue pour optimiser les opérations quotidiennes, automatiser les tâches répétitives et assurer une communication fluide entre les différents systèmes.

Les intégrations couvrent quatre domaines principaux :
- Caisse enregistreuse (transactions, stocks, produits)
- Fournisseurs (commandes, livraisons, catalogues)
- Réservation en ligne (réservations, disponibilités)
- CRM (clients, fidélité, marketing)

## Architecture générale

L'architecture d'intégration API suit les principes suivants :

1. **Conception modulaire** : Chaque intégration est indépendante et peut être déployée, mise à jour ou remplacée sans impact sur les autres composants.

2. **Abstraction des services** : Chaque type de service (POS, fournisseur, etc.) dispose d'une interface abstraite commune, permettant le remplacement facile d'un fournisseur par un autre.

3. **Infrastructure partagée** : Les fonctionnalités communes (authentification, gestion d'erreurs, mise en cache, etc.) sont centralisées pour éviter la duplication de code.

4. **Configuration externe** : Toutes les paramètres spécifiques au déploiement sont externalisés dans des fichiers de configuration plutôt que codés en dur.

5. **Journalisation exhaustive** : Chaque opération est journalisée pour faciliter le débogage et le suivi.

### Diagramme d'architecture

```
+------------------------+      +------------------------+
|                        |      |                        |
|  Système Le Vieux Moulin  |<---->|  Connecteurs API         |
|  (Serveur central)     |      |  (api_connectors)       |
|                        |      |                        |
+------------------------+      +----------+-------------+
                                           |
                                           |
                +-------------------------+----------------+----------------+
                |                         |                |                |
        +-------v------+         +---------v-----+  +------v-------+  +----v---------+
        |              |         |               |  |              |  |              |
        |  Caisse      |         |  Fournisseurs |  |  Réservation |  |  CRM         |
        |  (POS)       |         |  (Suppliers)  |  |  (Booking)   |  |              |
        |              |         |               |  |              |  |              |
        +--------------+         +---------------+  +--------------+  +--------------+
        |              |         |               |  |              |  |              |
        | - Lightspeed |         | - Metro       |  | - TheFork    |  | - HubSpot    |
        | - Square     |         | - Transgourmet|  | - OpenTable  |  | - Zoho CRM   |
        |              |         | - Pomona      |  |              |  |              |
        +--------------+         +---------------+  +--------------+  +--------------+
```

## Technologies utilisées

- **Langage** : Python 3.9+
- **Gestion des requêtes HTTP** : aiohttp (asynchrone)
- **Parsing de données** : pydantic pour la validation et sérialisation
- **Configuration** : PyYAML pour la gestion des fichiers de configuration
- **Authentification** : OAuth2 via authlib, JWT, API Keys
- **Tests** : pytest et aioresponses pour les tests asynchrones
- **Mise en cache** : aiocache pour la mise en cache asynchrone
- **Logging** : logging standard de Python avec structlog pour le formatage
- **Sécurité** : cryptography pour les opérations de chiffrement

## Intégrations API implémentées

### Caisse Enregistreuse (POS)

#### Points d'intégration

| Service | Fonctionnalité | Méthode HTTP | Endpoint | Description |
|---------|----------------|--------------|----------|-------------|
| Lightspeed | Récupération des ventes | GET | `/api/v1/Account/{accountID}/Sale` | Récupère les transactions de vente |
| Lightspeed | Détails d'une vente | GET | `/api/v1/Account/{accountID}/Sale/{saleID}` | Détails d'une transaction spécifique |
| Lightspeed | Mise à jour des produits | PUT | `/api/v1/Account/{accountID}/Item/{itemID}` | Met à jour les informations d'un produit |
| Lightspeed | Récupération des stocks | GET | `/api/v1/Account/{accountID}/ItemCount` | Niveaux de stock actuels |
| Square | Liste des paiements | GET | `/v2/payments` | Récupère l'historique des paiements |
| Square | Catalogue des produits | GET | `/v2/catalog/list` | Liste des produits et services |
| Square | Gestion des stocks | POST | `/v2/inventory/changes/batch-create` | Mise à jour des niveaux de stock |

#### Exemple d'authentification OAuth2 (Lightspeed)

```python
import aiohttp
from authlib.integrations.httpx_client import AsyncOAuth2Client

async def authenticate_lightspeed(client_id, client_secret, redirect_uri):
    oauth = AsyncOAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="employee:inventory employee:sales"
    )
    
    # Générer l'URL d'autorisation pour redirection utilisateur
    uri, state = oauth.create_authorization_url(
        'https://cloud.lightspeedapp.com/oauth/authorize.php'
    )
    
    # Après redirection et récupération du code d'autorisation
    code = "..."  # Code reçu du callback
    
    # Échanger le code contre un token d'accès
    token = await oauth.fetch_token(
        'https://cloud.lightspeedapp.com/oauth/access_token.php',
        code=code
    )
    
    return token
```

#### Exemple de récupération des ventes (Lightspeed)

```python
async def get_recent_sales(access_token, account_id, start_date, end_date):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "timeStamp": f">,[{start_date.isoformat()},{end_date.isoformat()}]",
        "completed": "true",
        "sort": "timeStamp",
        "limit": 100
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.lightspeedapp.com/API/Account/{account_id}/Sale",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("Sale", [])
            else:
                error_text = await response.text()
                raise Exception(f"Erreur API: {response.status} - {error_text}")
```

### Fournisseurs

#### Points d'intégration

| Service | Fonctionnalité | Méthode HTTP | Endpoint | Description |
|---------|----------------|--------------|----------|-------------|
| Metro | Accès au catalogue | GET | `/api/v1/products` | Liste des produits disponibles |
| Metro | Recherche de produits | GET | `/api/v1/products/search` | Recherche dans le catalogue |
| Metro | Création de commande | POST | `/api/v1/orders` | Crée une nouvelle commande |
| Metro | Suivi de commande | GET | `/api/v1/orders/{orderID}` | Vérifie l'état d'une commande |
| Transgourmet | Catalogue | GET | `/api/catalog` | Catalogue des produits |
| Transgourmet | Disponibilité | GET | `/api/availability` | Vérifie la disponibilité des produits |
| Transgourmet | Commander | POST | `/api/orders` | Place une commande |
| Pomona | Catalogue | GET | `/api/catalog/products` | Liste des produits |
| Pomona | Commander | POST | `/api/orders/create` | Crée une commande |

#### Exemple d'authentification par API Key (Metro)

```python
async def get_metro_catalog(api_key, category=None):
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    params = {}
    if category:
        params["category"] = category
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.metro.fr/api/v1/products",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Erreur API Metro: {response.status} - {error_text}")
```

#### Exemple de commande (Metro)

```python
async def place_order(api_key, items, delivery_date=None):
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "items": [{
            "product_id": item["id"],
            "quantity": item["quantity"],
            "unit": item.get("unit", "PC")
        } for item in items],
        "delivery_info": {
            "requested_date": delivery_date.isoformat() if delivery_date else None,
            "delivery_notes": "Livraison avant 10h si possible"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.metro.fr/api/v1/orders",
            headers=headers,
            json=payload
        ) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Erreur commande Metro: {response.status} - {error_text}")
```

### Réservation

#### Points d'intégration

| Service | Fonctionnalité | Méthode HTTP | Endpoint | Description |
|---------|----------------|--------------|----------|-------------|
| TheFork | Récupération des réservations | GET | `/api/v2/reservations` | Liste des réservations |
| TheFork | Détails d'une réservation | GET | `/api/v2/reservations/{id}` | Détails d'une réservation spécifique |
| TheFork | Mise à jour d'une réservation | PUT | `/api/v2/reservations/{id}` | Modifie une réservation |
| TheFork | Disponibilités | PUT | `/api/v2/availability` | Met à jour les disponibilités |
| OpenTable | Récupération des réservations | GET | `/api/v3/restaurant/{id}/reservations` | Liste des réservations |
| OpenTable | Modification d'une réservation | PUT | `/api/v3/restaurant/{id}/reservations/{reservation_id}` | Mise à jour d'une réservation |
| OpenTable | Disponibilités des tables | PUT | `/api/v3/restaurant/{id}/availability` | Met à jour les disponibilités |

#### Exemple d'authentification OAuth2 (TheFork)

```python
async def authenticate_thefork(client_id, client_secret):
    async with aiohttp.ClientSession() as session:
        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "public_api reservations"
        }
        
        async with session.post(
            "https://api.thefork.com/oauth/token",
            data=payload
        ) as response:
            if response.status == 200:
                token_data = await response.json()
                return token_data.get("access_token")
            else:
                error_text = await response.text()
                raise Exception(f"Erreur d'authentification TheFork: {response.status} - {error_text}")
```

#### Exemple de récupération des réservations (TheFork)

```python
async def get_reservations(access_token, start_date, end_date):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "status": "confirmed,seated,complete"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.thefork.com/api/v2/reservations",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("items", [])
            else:
                error_text = await response.text()
                raise Exception(f"Erreur API TheFork: {response.status} - {error_text}")
```

### CRM

#### Points d'intégration

| Service | Fonctionnalité | Méthode HTTP | Endpoint | Description |
|---------|----------------|--------------|----------|-------------|
| HubSpot | Récupération des contacts | GET | `/crm/v3/objects/contacts` | Liste des contacts |
| HubSpot | Création d'un contact | POST | `/crm/v3/objects/contacts` | Crée un nouveau contact |
| HubSpot | Mise à jour d'un contact | PATCH | `/crm/v3/objects/contacts/{id}` | Modifie un contact existant |
| HubSpot | Création d'une transaction | POST | `/crm/v3/objects/deals` | Enregistre une transaction |
| Zoho CRM | Recherche de contacts | GET | `/crm/v2/contacts/search` | Recherche dans les contacts |
| Zoho CRM | Création de contact | POST | `/crm/v2/contacts` | Crée un nouveau contact |
| Zoho CRM | Programme de fidélité | POST | `/crm/v2/Rewards` | Gestion du programme de fidélité |

#### Exemple d'authentification OAuth2 (HubSpot)

```python
from authlib.integrations.httpx_client import AsyncOAuth2Client
import json
import os
from datetime import datetime, timedelta

async def authenticate_hubspot(client_id, client_secret, refresh_token=None, token_path=None):
    # Vérifier si un token existe et est valide
    if token_path and os.path.exists(token_path):
        with open(token_path, 'r') as f:
            token_data = json.load(f)
            expires_at = token_data.get('expires_at', 0)
            if expires_at > datetime.now().timestamp():
                return token_data
            refresh_token = token_data.get('refresh_token')
    
    # Créer le client OAuth2
    client = AsyncOAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        token_endpoint="https://api.hubapi.com/oauth/v1/token"
    )
    
    # Rafraîchir ou obtenir un nouveau token
    if refresh_token:
        token = await client.refresh_token(
            "https://api.hubapi.com/oauth/v1/token",
            refresh_token=refresh_token
        )
    else:
        # Procédure d'autorisation complète (nécessite interaction utilisateur)
        # Pour l'automatisation, utiliser un refresh token généré au préalable
        auth_url = client.create_authorization_url(
            "https://app.hubspot.com/oauth/authorize",
            scopes="crm.objects.contacts.read crm.objects.contacts.write"
        )
        print(f"Visitez cette URL pour autoriser l'accès: {auth_url}")
        # ... (code pour gérer la redirection et obtenir le code d'autorisation)
        # token = await client.fetch_token("https://api.hubapi.com/oauth/v1/token", code=code)
        raise NotImplementedError("L'autorisation interactive n'est pas implémentée dans cet exemple")
    
    # Sauvegarder le token pour une utilisation future
    if token_path:
        with open(token_path, 'w') as f:
            json.dump(token, f)
    
    return token
```

#### Exemple de récupération et mise à jour de contact (HubSpot)

```python
async def get_contacts(access_token, email=None, limit=100):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {"limit": limit}
    if email:
        params["properties"] = "email,firstname,lastname,phone,loyalty_points,last_visit_date"
        params["filterGroups"] = [{"filters":[{"propertyName":"email","operator":"EQ","value":email}]}]
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("results", [])
            else:
                error_text = await response.text()
                raise Exception(f"Erreur API HubSpot: {response.status} - {error_text}")

async def update_contact_loyalty(access_token, contact_id, points, last_visit=None):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    properties = {
        "loyalty_points": str(points)
    }
    
    if last_visit:
        properties["last_visit_date"] = last_visit.isoformat()
    
    payload = {"properties": properties}
    
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Erreur mise à jour HubSpot: {response.status} - {error_text}")
```

## Authentification

L'authentification avec les différentes API est gérée de manière centralisée dans le module `common/auth.py`. Plusieurs méthodes d'authentification sont supportées :

### OAuth 2.0

Utilisé principalement pour Lightspeed, TheFork, HubSpot et d'autres services nécessitant une authentification sécurisée avec autorisations utilisateur. Le processus inclut :

1. Autorisation initiale (généralement interactive, faite une seule fois)
2. Échange du code d'autorisation contre un token d'accès
3. Rafraîchissement automatique des tokens expirés
4. Stockage sécurisé des tokens (par défaut chiffrés sur disque)

### API Keys

Utilisé pour les API plus simples comme certains fournisseurs. Les clés sont stockées de manière sécurisée, jamais en dur dans le code.

### Basic Auth

Utilisé pour certaines API plus anciennes. Les informations d'identification sont stockées de manière sécurisée.

## Gestion des erreurs

Le système implémente une gestion d'erreurs standardisée avec les caractéristiques suivantes :

### Classification des erreurs

Les erreurs sont classées en différentes catégories pour faciliter leur traitement :

- `AuthenticationError` : Problèmes d'authentification (token expiré, identifiants invalides)
- `ConnectionError` : Problèmes réseau (timeout, connexion refusée)
- `RateLimitError` : Limite de requêtes atteinte
- `ResourceNotFoundError` : Ressource inexistante (404)
- `ValidationError` : Données invalides envoyées à l'API
- `APIError` : Autres erreurs API

### Stratégie de réessai (Retry)

Le système implémente une stratégie de réessai automatique pour les erreurs temporaires :

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry_if_exception import retry_if_exception_type
from levieuxmoulin.integration.api_connectors.common.exceptions import ConnectionError, RateLimitError

@retry(
    retry=retry_if_exception_type((ConnectionError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def make_api_request(client, url, params=None):
    try:
        return await client.get(url, params=params)
    except aiohttp.ClientError as e:
        raise ConnectionError(f"Erreur de connexion: {str(e)}")
    except Exception as e:
        # Gestion d'autres types d'erreurs
        raise
```

### Circuit Breaker

Pour éviter de surcharger les services en cas de panne, le système utilise un modèle de Circuit Breaker :

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60, expected_exception=ConnectionError)
async def protected_api_call(client, url):
    # Implémentation de l'appel API
    pass
```

## Performance et mise en cache

### Stratégies de mise en cache

Le système utilise plusieurs niveaux de cache pour optimiser les performances :

1. **Cache en mémoire** : Pour les données fréquemment accédées (ex: référentiels produits)
2. **Cache disque** : Pour les données plus volumineuses (ex: catalogues complets)
3. **Cache distribué** (Redis) : Pour les environnements multi-instances

Exemple d'implémentation avec aiocache :

```python
from aiocache import Cache
from aiocache.serializers import JsonSerializer

# Configuration du cache
cache = Cache.from_url("redis://localhost:6379/0", serializer=JsonSerializer())

async def get_product_catalog(supplier_id, category=None, force_refresh=False):
    # Clé de cache unique basée sur les paramètres
    cache_key = f"catalog:{supplier_id}:{category or 'all'}"
    
    # Tentative de récupération depuis le cache
    if not force_refresh:
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
    
    # Si non caché ou rafraîchissement forcé, appel API
    data = await api_client.get_catalog(supplier_id, category)
    
    # Mise en cache des résultats (TTL de 24h)
    await cache.set(cache_key, data, ttl=86400)
    
    return data
```

### Optimisation des requêtes

Le système utilise plusieurs techniques pour optimiser les requêtes API :

1. **Parallélisation** : Traitement simultané des requêtes indépendantes
2. **Batching** : Regroupement des requêtes quand l'API le permet
3. **Pagination optimisée** : Gestion efficace des résultats paginés

```python
async def fetch_all_pages(client, url, params=None, max_pages=None):
    """Récupère toutes les pages d'une API paginée."""
    if params is None:
        params = {}
    
    all_results = []
    page = 1
    has_more = True
    
    while has_more and (max_pages is None or page <= max_pages):
        params["page"] = page
        data = await client.get(url, params=params)
        
        results = data.get("results", [])
        all_results.extend(results)
        
        has_more = data.get("has_more", False)
        page += 1
    
    return all_results
```

## Sécurité

### Protection des données sensibles

Les données sensibles (clés API, tokens, etc.) sont protégées par plusieurs mécanismes :

1. **Stockage sécurisé** : Jamais en clair dans le code ou les logs
2. **Chiffrement** : Pour les tokens stockés sur disque
3. **Rotation automatique** : Pour les tokens avec durée de validité limitée

```python
from cryptography.fernet import Fernet
import os
import json

class SecureTokenStore:
    """Stockage sécurisé pour les tokens d'authentification."""
    
    def __init__(self, encryption_key=None, token_path=None):
        self.token_path = token_path or "tokens.enc"
        
        # Utiliser une clé fournie ou générer/charger une nouvelle clé
        if encryption_key:
            self.key = encryption_key
        else:
            key_path = os.environ.get("TOKEN_KEY_PATH", ".token.key")
            if os.path.exists(key_path):
                with open(key_path, "rb") as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(key_path, "wb") as f:
                    f.write(self.key)
                os.chmod(key_path, 0o600)  # Permissions restrictives
        
        self.cipher = Fernet(self.key)
    
    async def save_token(self, service_name, token_data):
        """Enregistre un token chiffré."""
        tokens = await self.load_all_tokens()
        tokens[service_name] = token_data
        
        encrypted_data = self.cipher.encrypt(json.dumps(tokens).encode())
        with open(self.token_path, "wb") as f:
            f.write(encrypted_data)
        os.chmod(self.token_path, 0o600)  # Permissions restrictives
    
    async def load_token(self, service_name):
        """Charge un token spécifique."""
        tokens = await self.load_all_tokens()
        return tokens.get(service_name)
    
    async def load_all_tokens(self):
        """Charge tous les tokens."""
        if not os.path.exists(self.token_path):
            return {}
        
        try:
            with open(self.token_path, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            # Gérer les erreurs de déchiffrement ou format invalide
            return {}
```

### Validation des données

Toutes les données en entrée et en sortie sont validées pour éviter les injections et autres vulnérabilités. Pydantic est utilisé pour définir des modèles strict de validation :

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class OrderItem(BaseModel):
    product_id: str
    quantity: float
    unit: str = "PC"  # Unité par défaut
    
    @validator("quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("La quantité doit être positive")
        return v

class OrderRequest(BaseModel):
    items: List[OrderItem]
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)
    priority: str = "normal"
    
    @validator("priority")
    def valid_priority(cls, v):
        if v not in ["low", "normal", "high", "urgent"]:
            raise ValueError("Priorité invalide")
        return v
    
    @validator("delivery_date")
    def date_in_future(cls, v):
        if v and v < datetime.now():
            raise ValueError("La date de livraison doit être future")
        return v
```

## Tests et validation

### Tests unitaires

Chaque connecteur est testé avec pytest et aioresponses pour simuler les réponses API :

```python
import pytest
import aiohttp
from aioresponses import aioresponses
from levieuxmoulin.integration.api_connectors.pos import LightspeedConnector

@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m

@pytest.fixture
async def lightspeed_connector():
    # Créer une configuration de test
    config = {
        "api": {"base_url": "https://api.lightspeedapp.com/API/"},
        "auth": {
            "method": "oauth2",
            "client_id": "test_id",
            "client_secret": "test_secret"
        }
    }
    connector = LightspeedConnector(config_dict=config)
    # Simuler un token valide
    connector.token = {"access_token": "test_token", "expires_at": 9999999999}
    return connector

async def test_get_transactions(mock_aioresponse, lightspeed_connector):
    # Simuler une réponse API
    mock_aioresponse.get(
        "https://api.lightspeedapp.com/API/Account/123/Sale",
        status=200,
        payload={
            "Sale": [
                {"saleID": "1", "timeStamp": "2025-04-01T12:00:00Z", "total": 45.50},
                {"saleID": "2", "timeStamp": "2025-04-01T13:30:00Z", "total": 28.75}
            ]
        }
    )
    
    # Tester la méthode
    transactions = await lightspeed_connector.get_transactions(
        account_id="123",
        start_date="2025-04-01T00:00:00Z",
        end_date="2025-04-01T23:59:59Z"
    )
    
    # Vérifier les résultats
    assert len(transactions) == 2
    assert transactions[0]["saleID"] == "1"
    assert transactions[1]["total"] == 28.75
```

### Tests d'intégration

Des tests d'intégration sont également implémentés pour vérifier l'interaction réelle avec les APIs. Ces tests nécessitent des identifiants valides et sont exécutés dans un environnement contrôlé :

```python
import pytest
import os
from levieuxmoulin.integration.api_connectors.suppliers import MetroConnector

# Ce test est marqué pour n'être exécuté que si explicitement demandé
@pytest.mark.integration
async def test_metro_integration():
    # Utiliser des variables d'environnement pour les identifiants
    api_key = os.environ.get("METRO_API_KEY")
    if not api_key:
        pytest.skip("METRO_API_KEY non défini dans les variables d'environnement")
    
    # Créer le connecteur
    config = {
        "api": {"base_url": "https://api.metro.fr/api/v1/"},
        "auth": {"method": "api_key", "api_key": api_key}
    }
    connector = MetroConnector(config_dict=config)
    
    # Tester une requête réelle
    products = await connector.get_catalog(category="DAIRY")
    
    # Vérifications de base
    assert products is not None
    assert len(products) > 0
    assert "product_id" in products[0]
```

## Déploiement

Le module d'intégration API est conçu pour un déploiement flexible :

### En tant que service autonome

Pour les intégrations nécessitant une haute disponibilité ou des performances optimales, le module peut être déployé comme un service dédié :

```bash
# Exemple avec Docker
docker build -t levieuxmoulin/api-integration .
docker run -d --name api-integration \
  -v /path/to/config:/app/config \
  -v /path/to/tokens:/app/tokens \
  -p 8080:8080 \
  levieuxmoulin/api-integration
```

### Intégré dans l'application principale

Pour une installation plus simple, le module peut être importé directement dans l'application principale :

```python
from levieuxmoulin.integration.api_connectors.pos import LightspeedConnector
from levieuxmoulin.integration.api_connectors.suppliers import MetroConnector

# Initialisation des connecteurs
pos_connector = LightspeedConnector("config/pos.yaml")
metro_connector = MetroConnector("config/suppliers/metro.yaml")

# Utilisation dans l'application
async def sync_data():
    # Récupérer les ventes récentes
    sales = await pos_connector.get_recent_sales()
    
    # Commander des produits en rupture de stock
    low_stock_items = detect_low_stock(sales)
    if low_stock_items:
        order = await metro_connector.create_order(low_stock_items)
        print(f"Commande créée: {order['order_id']}")
```

## Surveillance et maintenance

### Journalisation

Le module utilise un système de journalisation complet pour faciliter le diagnostic :

```python
import logging
import structlog
from datetime import datetime

def configure_logging(log_level="INFO", log_file=None):
    # Configuration de base
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=log_file
    )
    
    # Configuration de structlog pour des logs JSON structurés
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()

# Exemple d'utilisation
logger = configure_logging(log_level="DEBUG", log_file="api_integration.log")

logger.info("Démarrage du connecteur", service="lightspeed", version="1.0.0")
logger.warning("Tentative de rafraîchissement du token", attempts=3, service="thefork")
```

### Métriques et surveillance

Le module implémente des métriques pour surveiller les performances et la santé des intégrations :

- Temps de réponse des API
- Taux de réussite/échec des requêtes
- Utilisation du cache
- Taux de rafraîchissement des tokens

Ces métriques peuvent être exportées vers des outils comme Prometheus pour la visualisation et les alertes.