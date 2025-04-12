"""
Tests unitaires pour les connecteurs de caisses enregistreuses (POS).

Ce module contient les tests pour les connecteurs Lightspeed et Square.
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
    pytest.skip("aioresponses not installed, skipping POS connector tests", allow_module_level=True)

# Import pour les tests asyncio
import asyncio

# Import des connecteurs à tester
from ..pos.lightspeed import LightspeedConnector
from ..pos.square import SquareConnector
from ..common.exceptions import AuthenticationError, APIError, ConnectionError, RateLimitError


@pytest.fixture
def mock_aioresponse():
    """Fixture pour simuler les réponses API."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def lightspeed_config():
    """Fixture pour la configuration Lightspeed."""
    return {
        "api": {
            "name": "Lightspeed POS",
            "base_url": "https://api.lightspeedapp.com/API/",
            "version": "v1"
        },
        "auth": {
            "method": "oauth2",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "redirect_uri": "https://levieuxmoulin.fr/oauth/callback",
            "token_store": "memory"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        },
        "rate_limit": {
            "max_requests_per_minute": 60,
            "throttle_on_limit": True
        }
    }


@pytest.fixture
def square_config():
    """Fixture pour la configuration Square."""
    return {
        "api": {
            "name": "Square POS",
            "base_url": "https://connect.squareup.com/",
            "version": "v2"
        },
        "auth": {
            "method": "access_token",
            "access_token": "test_access_token",
            "application_id": "test_application_id",
            "location_id": "test_location_id"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
async def lightspeed_connector(lightspeed_config):
    """Fixture pour un connecteur Lightspeed avec auth simulée."""
    connector = LightspeedConnector(config_dict=lightspeed_config)
    
    # Simuler un token d'authentification
    connector.authenticator = MagicMock()
    connector.authenticator.get_auth_headers.return_value = {"Authorization": "Bearer test_token"}
    connector.authenticator.is_authenticated.return_value = asyncio.Future()
    connector.authenticator.is_authenticated.return_value.set_result(True)
    connector.authenticator.refresh_if_needed.return_value = asyncio.Future()
    connector.authenticator.refresh_if_needed.return_value.set_result(None)
    
    # Initialiser le client HTTP
    connector._init_http_client()
    connector._connected = True
    
    return connector


@pytest.fixture
async def square_connector(square_config):
    """Fixture pour un connecteur Square avec auth simulée."""
    connector = SquareConnector(config_dict=square_config)
    
    # Simuler un token d'authentification
    connector.authenticator = MagicMock()
    connector.authenticator.get_auth_headers.return_value = {"Authorization": "Bearer test_token"}
    connector.authenticator.is_authenticated.return_value = asyncio.Future()
    connector.authenticator.is_authenticated.return_value.set_result(True)
    connector.authenticator.refresh_if_needed.return_value = asyncio.Future()
    connector.authenticator.refresh_if_needed.return_value.set_result(None)
    
    # Initialiser le client HTTP
    connector._init_http_client()
    connector._connected = True
    
    return connector


@pytest.mark.asyncio
async def test_lightspeed_get_transactions(mock_aioresponse, lightspeed_connector):
    """Test de récupération des transactions avec Lightspeed."""
    # Configurer le mock
    mock_response = {
        "Sale": [
            {"saleID": "1", "timeStamp": "2025-04-01T12:30:00Z", "completed": True, "total": 45.50},
            {"saleID": "2", "timeStamp": "2025-04-01T14:15:00Z", "completed": True, "total": 28.75}
        ]
    }
    
    account_id = "123456"
    base_url = lightspeed_connector.config["api"]["base_url"]
    endpoint = f"Account/{account_id}/Sale"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Exécuter la méthode à tester
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    transactions = await lightspeed_connector.get_transactions(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Vérifier les résultats
    assert transactions is not None
    assert len(transactions) == 2
    assert transactions[0]["saleID"] == "1"
    assert transactions[1]["total"] == 28.75


@pytest.mark.asyncio
async def test_lightspeed_api_error(mock_aioresponse, lightspeed_connector):
    """Test de gestion des erreurs API avec Lightspeed."""
    # Configurer le mock pour une erreur
    account_id = "123456"
    base_url = lightspeed_connector.config["api"]["base_url"]
    endpoint = f"Account/{account_id}/Sale"
    url = f"{base_url}{endpoint}"
    
    error_response = {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "The requested resource was not found"
        }
    }
    
    # Configurer la réponse d'erreur simulée
    mock_aioresponse.get(
        url,
        status=404,
        payload=error_response
    )
    
    # Exécuter la méthode et vérifier qu'elle lève une exception
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    with pytest.raises(APIError) as excinfo:
        await lightspeed_connector.get_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
    
    # Vérifier le message d'erreur
    assert "404" in str(excinfo.value)
    assert "RESOURCE_NOT_FOUND" in str(excinfo.value)


@pytest.mark.asyncio
async def test_square_get_payments(mock_aioresponse, square_connector):
    """Test de récupération des paiements avec Square."""
    # Configurer le mock
    mock_response = {
        "payments": [
            {
                "id": "payment1",
                "created_at": "2025-04-01T12:30:00Z",
                "amount_money": {"amount": 4550, "currency": "EUR"},
                "status": "COMPLETED"
            },
            {
                "id": "payment2",
                "created_at": "2025-04-01T14:15:00Z",
                "amount_money": {"amount": 2875, "currency": "EUR"},
                "status": "COMPLETED"
            }
        ]
    }
    
    base_url = square_connector.config["api"]["base_url"]
    endpoint = "v2/payments"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Exécuter la méthode à tester
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()
    
    payments = await square_connector.get_payments(
        start_time=start_time,
        end_time=end_time
    )
    
    # Vérifier les résultats
    assert payments is not None
    assert len(payments) == 2
    assert payments[0]["id"] == "payment1"
    assert payments[1]["amount_money"]["amount"] == 2875


@pytest.mark.asyncio
async def test_square_update_inventory(mock_aioresponse, square_connector):
    """Test de mise à jour d'inventaire avec Square."""
    # Configurer le mock
    mock_response = {
        "changes": [
            {
                "type": "ADJUSTMENT",
                "adjustment": {
                    "id": "adjustment1",
                    "catalog_object_id": "item1",
                    "quantity": "-2.0"
                }
            }
        ]
    }
    
    base_url = square_connector.config["api"]["base_url"]
    endpoint = "v2/inventory/changes/batch-create"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.post(
        url,
        status=200,
        payload=mock_response
    )
    
    # Données pour la mise à jour
    inventory_changes = [
        {
            "catalog_object_id": "item1",
            "quantity": -2.0,
            "location_id": "location1"
        }
    ]
    
    # Exécuter la méthode à tester
    result = await square_connector.update_inventory(inventory_changes)
    
    # Vérifier les résultats
    assert result is not None
    assert "changes" in result
    assert len(result["changes"]) == 1
    assert result["changes"][0]["adjustment"]["catalog_object_id"] == "item1"


# Tests d'intégration (désactivés par défaut)
@pytest.mark.skip(reason="Test d'intégration nécessitant des identifiants valides")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_lightspeed_integration():
    """Test d'intégration réel avec Lightspeed."""
    # Ces tests ne sont exécutés que si explicitement demandés et avec des identifiants réels
    if not os.environ.get("LIGHTSPEED_CLIENT_ID") or not os.environ.get("LIGHTSPEED_CLIENT_SECRET"):
        pytest.skip("Variables d'environnement non définies pour les tests d'intégration Lightspeed")
    
    config = {
        "api": {
            "name": "Lightspeed POS",
            "base_url": "https://api.lightspeedapp.com/API/",
            "version": "v1"
        },
        "auth": {
            "method": "oauth2",
            "client_id": os.environ.get("LIGHTSPEED_CLIENT_ID"),
            "client_secret": os.environ.get("LIGHTSPEED_CLIENT_SECRET"),
            "redirect_uri": os.environ.get("LIGHTSPEED_REDIRECT_URI"),
            "refresh_token": os.environ.get("LIGHTSPEED_REFRESH_TOKEN")
        }
    }
    
    connector = LightspeedConnector(config_dict=config)
    await connector.connect()
    
    # Test simple pour vérifier la connexion
    account_id = os.environ.get("LIGHTSPEED_ACCOUNT_ID")
    health_status = await connector.check_health()
    assert health_status is True
    
    # Nettoyage
    await connector.disconnect()
