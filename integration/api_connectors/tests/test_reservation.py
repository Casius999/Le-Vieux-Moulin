"""
Tests unitaires pour les connecteurs de réservation.

Ce module contient les tests pour les connecteurs TheFork et OpenTable.
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
    pytest.skip("aioresponses not installed, skipping reservation connector tests", allow_module_level=True)

# Import pour les tests asyncio
import asyncio

# Import des connecteurs à tester
from ..reservation.thefork import TheForkConnector
from ..reservation.opentable import OpenTableConnector
from ..common.exceptions import AuthenticationError, APIError, ConnectionError, RateLimitError


@pytest.fixture
def mock_aioresponse():
    """Fixture pour simuler les réponses API."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def thefork_config():
    """Fixture pour la configuration TheFork."""
    return {
        "api": {
            "name": "TheFork API",
            "base_url": "https://api.thefork.com/api/",
            "version": "v2"
        },
        "auth": {
            "method": "oauth2",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scope": "public_api reservations"
        },
        "restaurant": {
            "id": "12345"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
def opentable_config():
    """Fixture pour la configuration OpenTable."""
    return {
        "api": {
            "name": "OpenTable API",
            "base_url": "https://api.opentable.com/api/",
            "version": "v3"
        },
        "auth": {
            "method": "api_key",
            "api_key": "test_api_key"
        },
        "restaurant": {
            "id": "67890"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
async def thefork_connector(thefork_config):
    """Fixture pour un connecteur TheFork avec auth simulée."""
    connector = TheForkConnector(config_dict=thefork_config)
    
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
async def opentable_connector(opentable_config):
    """Fixture pour un connecteur OpenTable avec auth simulée."""
    connector = OpenTableConnector(config_dict=opentable_config)
    
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


@pytest.mark.asyncio
async def test_thefork_get_reservations(mock_aioresponse, thefork_connector):
    """Test de récupération des réservations TheFork."""
    # Configurer le mock
    mock_response = {
        "items": [
            {
                "id": "123456",
                "restaurant_id": "12345",
                "customer": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+33612345678"
                },
                "date": "2025-04-15",
                "time": "20:00:00",
                "people": 4,
                "status": "confirmed",
                "created_at": "2025-04-12T15:30:45Z",
                "notes": "Allergique aux fruits de mer"
            },
            {
                "id": "789012",
                "restaurant_id": "12345",
                "customer": {
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "phone": "+33698765432"
                },
                "date": "2025-04-15",
                "time": "21:30:00",
                "people": 2,
                "status": "confirmed",
                "created_at": "2025-04-12T16:45:10Z",
                "notes": ""
            }
        ],
        "pagination": {
            "total": 2,
            "page": 1,
            "per_page": 20
        }
    }
    
    base_url = thefork_connector.config["api"]["base_url"]
    version = thefork_connector.config["api"]["version"]
    endpoint = f"{version}/reservations"
    url = f"{base_url}{endpoint}"
    
    # Paramètres attendus
    params = {
        "restaurantId": "12345",
        "from": "2025-04-15",
        "to": "2025-04-15",
        "status": "confirmed,seated,complete"
    }
    
    # Configurer la réponse simulée avec vérification des paramètres
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response,
        match_querystring=False
    )
    
    # Exécuter la méthode à tester
    date = datetime.strptime("2025-04-15", "%Y-%m-%d").date()
    reservations = await thefork_connector.get_reservations(date)
    
    # Vérifier les résultats
    assert reservations is not None
    assert "items" in reservations
    assert len(reservations["items"]) == 2
    assert reservations["items"][0]["id"] == "123456"
    assert reservations["items"][0]["people"] == 4
    assert reservations["items"][1]["customer"]["name"] == "Jane Smith"


@pytest.mark.asyncio
async def test_thefork_update_reservation(mock_aioresponse, thefork_connector):
    """Test de mise à jour d'une réservation TheFork."""
    # Configurer le mock
    reservation_id = "123456"
    mock_response = {
        "id": reservation_id,
        "restaurant_id": "12345",
        "customer": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+33612345678"
        },
        "date": "2025-04-15",
        "time": "21:00:00",  # Heure modifiée
        "people": 6,  # Nombre de personnes modifié
        "status": "confirmed",
        "created_at": "2025-04-12T15:30:45Z",
        "updated_at": "2025-04-12T18:15:30Z",
        "notes": "Allergique aux fruits de mer. Table près de la fenêtre."  # Notes modifiées
    }
    
    base_url = thefork_connector.config["api"]["base_url"]
    version = thefork_connector.config["api"]["version"]
    endpoint = f"{version}/reservations/{reservation_id}"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.patch(
        url,
        status=200,
        payload=mock_response
    )
    
    # Données pour la mise à jour
    update_data = {
        "time": "21:00:00",
        "people": 6,
        "notes": "Allergique aux fruits de mer. Table près de la fenêtre."
    }
    
    # Exécuter la méthode à tester
    result = await thefork_connector.update_reservation(reservation_id, update_data)
    
    # Vérifier les résultats
    assert result is not None
    assert result["id"] == reservation_id
    assert result["time"] == "21:00:00"
    assert result["people"] == 6
    assert "Table près de la fenêtre" in result["notes"]


@pytest.mark.asyncio
async def test_opentable_get_reservations(mock_aioresponse, opentable_connector):
    """Test de récupération des réservations OpenTable."""
    # Configurer le mock
    mock_response = {
        "reservations": [
            {
                "id": "OT-123456",
                "restaurant_id": "67890",
                "guest": {
                    "first_name": "Michael",
                    "last_name": "Johnson",
                    "email": "michael.johnson@example.com",
                    "phone": "+1-555-123-4567"
                },
                "reservation_date": "2025-04-16",
                "reservation_time": "19:00",
                "party_size": 3,
                "status": "BOOKED",
                "created_at": "2025-04-12T10:15:22Z",
                "special_request": "Highchair needed"
            },
            {
                "id": "OT-789012",
                "restaurant_id": "67890",
                "guest": {
                    "first_name": "Sarah",
                    "last_name": "Williams",
                    "email": "sarah.williams@example.com",
                    "phone": "+1-555-987-6543"
                },
                "reservation_date": "2025-04-16",
                "reservation_time": "20:30",
                "party_size": 5,
                "status": "BOOKED",
                "created_at": "2025-04-12T11:45:33Z",
                "special_request": ""
            }
        ],
        "pagination": {
            "total": 2,
            "page": 1,
            "per_page": 25
        }
    }
    
    base_url = opentable_connector.config["api"]["base_url"]
    version = opentable_connector.config["api"]["version"]
    restaurant_id = opentable_connector.config["restaurant"]["id"]
    endpoint = f"{version}/restaurant/{restaurant_id}/reservations"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Exécuter la méthode à tester
    start_date = datetime.strptime("2025-04-16", "%Y-%m-%d").date()
    end_date = datetime.strptime("2025-04-16", "%Y-%m-%d").date()
    reservations = await opentable_connector.get_reservations(start_date, end_date)
    
    # Vérifier les résultats
    assert reservations is not None
    assert "reservations" in reservations
    assert len(reservations["reservations"]) == 2
    assert reservations["reservations"][0]["id"] == "OT-123456"
    assert reservations["reservations"][0]["party_size"] == 3
    assert reservations["reservations"][1]["guest"]["first_name"] == "Sarah"


@pytest.mark.asyncio
async def test_opentable_update_availability(mock_aioresponse, opentable_connector):
    """Test de mise à jour des disponibilités OpenTable."""
    # Configurer le mock
    mock_response = {
        "success": True,
        "availability": {
            "date": "2025-04-20",
            "time_slots": [
                {"time": "18:00", "available": 5},
                {"time": "18:30", "available": 4},
                {"time": "19:00", "available": 0},  # Aucune disponibilité
                {"time": "19:30", "available": 0},  # Aucune disponibilité
                {"time": "20:00", "available": 3},
                {"time": "20:30", "available": 6},
                {"time": "21:00", "available": 7}
            ]
        }
    }
    
    base_url = opentable_connector.config["api"]["base_url"]
    version = opentable_connector.config["api"]["version"]
    restaurant_id = opentable_connector.config["restaurant"]["id"]
    endpoint = f"{version}/restaurant/{restaurant_id}/availability"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.put(
        url,
        status=200,
        payload=mock_response
    )
    
    # Données pour la mise à jour
    availability_data = {
        "date": "2025-04-20",
        "time_slots": [
            {"time": "18:00", "available": 5},
            {"time": "18:30", "available": 4},
            {"time": "19:00", "available": 0},
            {"time": "19:30", "available": 0},
            {"time": "20:00", "available": 3},
            {"time": "20:30", "available": 6},
            {"time": "21:00", "available": 7}
        ]
    }
    
    # Exécuter la méthode à tester
    result = await opentable_connector.update_availability(availability_data)
    
    # Vérifier les résultats
    assert result is not None
    assert result["success"] is True
    assert "availability" in result
    assert result["availability"]["date"] == "2025-04-20"
    assert len(result["availability"]["time_slots"]) == 7
    assert result["availability"]["time_slots"][2]["time"] == "19:00"
    assert result["availability"]["time_slots"][2]["available"] == 0


@pytest.mark.asyncio
async def test_thefork_api_error(mock_aioresponse, thefork_connector):
    """Test de gestion des erreurs API avec TheFork."""
    # Configurer le mock pour une erreur
    base_url = thefork_connector.config["api"]["base_url"]
    version = thefork_connector.config["api"]["version"]
    endpoint = f"{version}/reservations"
    url = f"{base_url}{endpoint}"
    
    error_response = {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded. Try again later."
        }
    }
    
    # Configurer la réponse d'erreur simulée
    mock_aioresponse.get(
        url,
        status=429,
        payload=error_response
    )
    
    # Exécuter la méthode et vérifier qu'elle lève une exception
    date = datetime.strptime("2025-04-15", "%Y-%m-%d").date()
    
    with pytest.raises(RateLimitError) as excinfo:
        await thefork_connector.get_reservations(date)
    
    # Vérifier le message d'erreur
    assert "429" in str(excinfo.value)
    assert "Rate limit exceeded" in str(excinfo.value)


# Tests d'intégration (désactivés par défaut)
@pytest.mark.skip(reason="Test d'intégration nécessitant des identifiants valides")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_thefork_integration():
    """Test d'intégration réel avec TheFork."""
    # Ces tests ne sont exécutés que si explicitement demandés et avec des identifiants réels
    if not os.environ.get("THEFORK_CLIENT_ID") or not os.environ.get("THEFORK_CLIENT_SECRET"):
        pytest.skip("Variables d'environnement non définies pour les tests d'intégration TheFork")
    
    config = {
        "api": {
            "name": "TheFork API",
            "base_url": "https://api.thefork.com/api/",
            "version": "v2"
        },
        "auth": {
            "method": "oauth2",
            "client_id": os.environ.get("THEFORK_CLIENT_ID"),
            "client_secret": os.environ.get("THEFORK_CLIENT_SECRET"),
            "scope": "public_api reservations"
        },
        "restaurant": {
            "id": os.environ.get("THEFORK_RESTAURANT_ID")
        }
    }
    
    connector = TheForkConnector(config_dict=config)
    await connector.connect()
    
    # Test simple pour vérifier la connexion
    health_status = await connector.check_health()
    assert health_status is True
    
    # Nettoyage
    await connector.disconnect()
