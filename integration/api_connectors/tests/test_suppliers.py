"""
Tests unitaires pour les connecteurs de fournisseurs.

Ce module contient les tests pour les connecteurs Metro, Transgourmet et Pomona.
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import aioresponses pour simuler les réponses API asynchrones
try:
    from aioresponses import aioresponses
except ImportError:
    pytest.skip("aioresponses not installed, skipping supplier connector tests", allow_module_level=True)

# Import pour les tests asyncio
import asyncio

# Import des connecteurs à tester
from ..suppliers.metro import MetroConnector
from ..suppliers.transgourmet import TransgourmetConnector
from ..suppliers.pomona import PomonaConnector
from ..common.exceptions import AuthenticationError, APIError, ConnectionError, RateLimitError


@pytest.fixture
def mock_aioresponse():
    """Fixture pour simuler les réponses API."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def metro_config():
    """Fixture pour la configuration Metro."""
    return {
        "api": {
            "name": "Metro France API",
            "base_url": "https://api.metro.fr/api/v1/"
        },
        "auth": {
            "method": "api_key",
            "api_key": "test_api_key"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
def transgourmet_config():
    """Fixture pour la configuration Transgourmet."""
    return {
        "api": {
            "name": "Transgourmet API",
            "base_url": "https://api.transgourmet.fr/api/"
        },
        "auth": {
            "method": "basic",
            "username": "test_user",
            "password": "test_password"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
def pomona_config():
    """Fixture pour la configuration Pomona."""
    return {
        "api": {
            "name": "Pomona API",
            "base_url": "https://api.pomona.fr/api/"
        },
        "auth": {
            "method": "jwt",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
async def metro_connector(metro_config):
    """Fixture pour un connecteur Metro avec auth simulée."""
    connector = MetroConnector(config_dict=metro_config)
    
    # Simuler un token d'authentification
    connector.authenticator = MagicMock()
    connector.authenticator.get_auth_headers.return_value = {"X-API-KEY": "test_api_key"}
    connector.authenticator.is_authenticated.return_value = asyncio.Future()
    connector.authenticator.is_authenticated.return_value.set_result(True)
    connector.authenticator.refresh_if_needed.return_value = asyncio.Future()
    connector.authenticator.refresh_if_needed.return_value.set_result(None)
    
    # Initialiser le client HTTP
    connector._init_http_client()
    connector._connected = True
    
    return connector


@pytest.fixture
async def transgourmet_connector(transgourmet_config):
    """Fixture pour un connecteur Transgourmet avec auth simulée."""
    connector = TransgourmetConnector(config_dict=transgourmet_config)
    
    # Simuler un token d'authentification
    connector.authenticator = MagicMock()
    connector.authenticator.get_auth_headers.return_value = {"Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzc3dvcmQ="}
    connector.authenticator.is_authenticated.return_value = asyncio.Future()
    connector.authenticator.is_authenticated.return_value.set_result(True)
    connector.authenticator.refresh_if_needed.return_value = asyncio.Future()
    connector.authenticator.refresh_if_needed.return_value.set_result(None)
    
    # Initialiser le client HTTP
    connector._init_http_client()
    connector._connected = True
    
    return connector


@pytest.fixture
async def pomona_connector(pomona_config):
    """Fixture pour un connecteur Pomona avec auth simulée."""
    connector = PomonaConnector(config_dict=pomona_config)
    
    # Simuler un token d'authentification
    connector.authenticator = MagicMock()
    connector.authenticator.get_auth_headers.return_value = {"Authorization": "Bearer test_jwt_token"}
    connector.authenticator.is_authenticated.return_value = asyncio.Future()
    connector.authenticator.is_authenticated.return_value.set_result(True)
    connector.authenticator.refresh_if_needed.return_value = asyncio.Future()
    connector.authenticator.refresh_if_needed.return_value.set_result(None)
    
    # Initialiser le client HTTP
    connector._init_http_client()
    connector._connected = True
    
    return connector


@pytest.mark.asyncio
async def test_metro_get_catalog(mock_aioresponse, metro_connector):
    """Test de récupération du catalogue Metro."""
    # Configurer le mock
    mock_response = {
        "products": [
            {
                "product_id": "123456",
                "name": "Tomate cerise",
                "unit": "KG",
                "price": 4.95,
                "category": "VEGETABLES",
                "in_stock": True
            },
            {
                "product_id": "789012",
                "name": "Mozzarella",
                "unit": "PC",
                "price": 3.75,
                "category": "DAIRY",
                "in_stock": True
            }
        ],
        "pagination": {
            "total": 2,
            "page": 1,
            "per_page": 20
        }
    }
    
    base_url = metro_connector.config["api"]["base_url"]
    endpoint = "products"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Exécuter la méthode à tester
    catalog = await metro_connector.get_catalog()
    
    # Vérifier les résultats
    assert catalog is not None
    assert "products" in catalog
    assert len(catalog["products"]) == 2
    assert catalog["products"][0]["product_id"] == "123456"
    assert catalog["products"][1]["name"] == "Mozzarella"


@pytest.mark.asyncio
async def test_metro_create_order(mock_aioresponse, metro_connector):
    """Test de création d'une commande Metro."""
    # Configurer le mock
    mock_response = {
        "order_id": "ORD-12345",
        "created_at": "2025-04-12T10:30:45Z",
        "status": "PROCESSING",
        "items": [
            {
                "product_id": "123456",
                "quantity": 5.0,
                "unit": "KG",
                "unit_price": 4.95,
                "total_price": 24.75
            }
        ],
        "total_amount": 24.75,
        "estimated_delivery": "2025-04-14"
    }
    
    base_url = metro_connector.config["api"]["base_url"]
    endpoint = "orders"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.post(
        url,
        status=201,
        payload=mock_response
    )
    
    # Données pour la commande
    order_items = [
        {
            "product_id": "123456",
            "quantity": 5.0,
            "unit": "KG"
        }
    ]
    
    # Exécuter la méthode à tester
    from datetime import date
    delivery_date = date(2025, 4, 14)
    order = await metro_connector.create_order(order_items, delivery_date)
    
    # Vérifier les résultats
    assert order is not None
    assert order["order_id"] == "ORD-12345"
    assert order["status"] == "PROCESSING"
    assert len(order["items"]) == 1
    assert order["items"][0]["product_id"] == "123456"
    assert order["total_amount"] == 24.75


@pytest.mark.asyncio
async def test_transgourmet_get_catalog(mock_aioresponse, transgourmet_connector):
    """Test de récupération du catalogue Transgourmet."""
    # Configurer le mock
    mock_response = {
        "items": [
            {
                "id": "TG-001",
                "name": "Farine de blé T55",
                "unit": "KG",
                "packaging": "Sac 25kg",
                "price": 21.50,
                "category": "INGREDIENTS"
            },
            {
                "id": "TG-002",
                "name": "Huile d'olive extra vierge",
                "unit": "L",
                "packaging": "Bidon 5L",
                "price": 29.95,
                "category": "OILS"
            }
        ],
        "meta": {
            "total": 2,
            "page": 1,
            "per_page": 20
        }
    }
    
    base_url = transgourmet_connector.config["api"]["base_url"]
    endpoint = "catalog"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Exécuter la méthode à tester
    catalog = await transgourmet_connector.get_catalog()
    
    # Vérifier les résultats
    assert catalog is not None
    assert "items" in catalog
    assert len(catalog["items"]) == 2
    assert catalog["items"][0]["id"] == "TG-001"
    assert catalog["items"][1]["name"] == "Huile d'olive extra vierge"


@pytest.mark.asyncio
async def test_pomona_check_availability(mock_aioresponse, pomona_connector):
    """Test de vérification de disponibilité Pomona."""
    # Configurer le mock
    mock_response = {
        "availability": [
            {
                "product_id": "POM-123",
                "available": True,
                "stock_quantity": 150,
                "next_delivery": "2025-04-13"
            },
            {
                "product_id": "POM-456",
                "available": False,
                "stock_quantity": 0,
                "next_delivery": "2025-04-15"
            }
        ]
    }
    
    base_url = pomona_connector.config["api"]["base_url"]
    endpoint = "availability"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.post(
        url,
        status=200,
        payload=mock_response
    )
    
    # Produits à vérifier
    product_ids = ["POM-123", "POM-456"]
    
    # Exécuter la méthode à tester
    availability = await pomona_connector.check_availability(product_ids)
    
    # Vérifier les résultats
    assert availability is not None
    assert "availability" in availability
    assert len(availability["availability"]) == 2
    assert availability["availability"][0]["product_id"] == "POM-123"
    assert availability["availability"][0]["available"] is True
    assert availability["availability"][1]["product_id"] == "POM-456"
    assert availability["availability"][1]["available"] is False


@pytest.mark.asyncio
async def test_metro_api_error(mock_aioresponse, metro_connector):
    """Test de gestion des erreurs API avec Metro."""
    # Configurer le mock pour une erreur
    base_url = metro_connector.config["api"]["base_url"]
    endpoint = "products"
    url = f"{base_url}{endpoint}"
    
    error_response = {
        "error": {
            "code": "ACCESS_DENIED",
            "message": "Invalid API key"
        }
    }
    
    # Configurer la réponse d'erreur simulée
    mock_aioresponse.get(
        url,
        status=401,
        payload=error_response
    )
    
    # Exécuter la méthode et vérifier qu'elle lève une exception
    with pytest.raises(AuthenticationError) as excinfo:
        await metro_connector.get_catalog()
    
    # Vérifier le message d'erreur
    assert "401" in str(excinfo.value)
    assert "Invalid API key" in str(excinfo.value)


# Tests d'intégration (désactivés par défaut)
@pytest.mark.skip(reason="Test d'intégration nécessitant des identifiants valides")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_metro_integration():
    """Test d'intégration réel avec Metro."""
    # Ces tests ne sont exécutés que si explicitement demandés et avec des identifiants réels
    if not os.environ.get("METRO_API_KEY"):
        pytest.skip("Variable d'environnement METRO_API_KEY non définie pour les tests d'intégration")
    
    config = {
        "api": {
            "name": "Metro France API",
            "base_url": "https://api.metro.fr/api/v1/"
        },
        "auth": {
            "method": "api_key",
            "api_key": os.environ.get("METRO_API_KEY")
        }
    }
    
    connector = MetroConnector(config_dict=config)
    await connector.connect()
    
    # Test simple pour vérifier la connexion
    health_status = await connector.check_health()
    assert health_status is True
    
    # Test de récupération du catalogue
    catalog = await connector.get_catalog(category="DAIRY")
    assert catalog is not None
    assert "products" in catalog
    
    # Nettoyage
    await connector.disconnect()
