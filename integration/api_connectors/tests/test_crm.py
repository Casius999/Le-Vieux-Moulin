"""
Tests unitaires pour les connecteurs CRM.

Ce module contient les tests pour les connecteurs HubSpot et Zoho CRM.
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
    pytest.skip("aioresponses not installed, skipping CRM connector tests", allow_module_level=True)

# Import pour les tests asyncio
import asyncio

# Import des connecteurs à tester
from ..crm.hubspot import HubspotConnector
from ..crm.zoho import ZohoConnector
from ..common.exceptions import AuthenticationError, APIError, ConnectionError, RateLimitError


@pytest.fixture
def mock_aioresponse():
    """Fixture pour simuler les réponses API."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def hubspot_config():
    """Fixture pour la configuration HubSpot."""
    return {
        "api": {
            "name": "HubSpot CRM",
            "base_url": "https://api.hubapi.com/",
            "version": "v3"
        },
        "auth": {
            "method": "oauth2",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": "crm.objects.contacts.read crm.objects.contacts.write"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
def zoho_config():
    """Fixture pour la configuration Zoho CRM."""
    return {
        "api": {
            "name": "Zoho CRM",
            "base_url": "https://www.zohoapis.eu/crm/",
            "version": "v2"
        },
        "auth": {
            "method": "oauth2",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "refresh_token": "test_refresh_token"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        }
    }


@pytest.fixture
async def hubspot_connector(hubspot_config):
    """Fixture pour un connecteur HubSpot avec auth simulée."""
    connector = HubspotConnector(config_dict=hubspot_config)
    
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
async def zoho_connector(zoho_config):
    """Fixture pour un connecteur Zoho avec auth simulée."""
    connector = ZohoConnector(config_dict=zoho_config)
    
    # Simuler un token d'authentification
    connector.authenticator = MagicMock()
    connector.authenticator.get_auth_headers.return_value = {"Authorization": "Zoho-oauthtoken test_token"}
    connector.authenticator.is_authenticated.return_value = asyncio.Future()
    connector.authenticator.is_authenticated.return_value.set_result(True)
    connector.authenticator.refresh_if_needed.return_value = asyncio.Future()
    connector.authenticator.refresh_if_needed.return_value.set_result(None)
    
    # Initialiser le client HTTP
    connector._init_http_client()
    connector._connected = True
    
    return connector


@pytest.mark.asyncio
async def test_hubspot_get_contacts(mock_aioresponse, hubspot_connector):
    """Test de récupération des contacts HubSpot."""
    # Configurer le mock
    mock_response = {
        "results": [
            {
                "id": "1",
                "properties": {
                    "email": "john.doe@example.com",
                    "firstname": "John",
                    "lastname": "Doe",
                    "phone": "+33612345678",
                    "loyalty_points": "120",
                    "last_visit_date": "2025-04-01"
                },
                "createdAt": "2024-12-15T10:30:45Z",
                "updatedAt": "2025-04-01T18:15:22Z"
            },
            {
                "id": "2",
                "properties": {
                    "email": "jane.smith@example.com",
                    "firstname": "Jane",
                    "lastname": "Smith",
                    "phone": "+33698765432",
                    "loyalty_points": "75",
                    "last_visit_date": "2025-03-28"
                },
                "createdAt": "2025-01-05T14:22:33Z",
                "updatedAt": "2025-03-28T20:45:10Z"
            }
        ],
        "paging": {
            "next": {
                "after": "2",
                "link": "https://api.hubapi.com/crm/v3/objects/contacts?after=2"
            }
        }
    }
    
    base_url = hubspot_connector.config["api"]["base_url"]
    endpoint = "crm/v3/objects/contacts"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Exécuter la méthode à tester
    contacts = await hubspot_connector.get_contacts(limit=10)
    
    # Vérifier les résultats
    assert contacts is not None
    assert "results" in contacts
    assert len(contacts["results"]) == 2
    assert contacts["results"][0]["properties"]["email"] == "john.doe@example.com"
    assert int(contacts["results"][0]["properties"]["loyalty_points"]) == 120
    assert contacts["results"][1]["properties"]["firstname"] == "Jane"


@pytest.mark.asyncio
async def test_hubspot_create_contact(mock_aioresponse, hubspot_connector):
    """Test de création de contact HubSpot."""
    # Configurer le mock
    mock_response = {
        "id": "3",
        "properties": {
            "email": "robert.brown@example.com",
            "firstname": "Robert",
            "lastname": "Brown",
            "phone": "+33645678901",
            "loyalty_points": "0",
            "last_visit_date": "2025-04-12"
        },
        "createdAt": "2025-04-12T18:30:00Z",
        "updatedAt": "2025-04-12T18:30:00Z"
    }
    
    base_url = hubspot_connector.config["api"]["base_url"]
    endpoint = "crm/v3/objects/contacts"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.post(
        url,
        status=201,
        payload=mock_response
    )
    
    # Données pour la création
    contact_data = {
        "properties": {
            "email": "robert.brown@example.com",
            "firstname": "Robert",
            "lastname": "Brown",
            "phone": "+33645678901",
            "loyalty_points": "0",
            "last_visit_date": "2025-04-12"
        }
    }
    
    # Exécuter la méthode à tester
    result = await hubspot_connector.create_contact(contact_data)
    
    # Vérifier les résultats
    assert result is not None
    assert result["id"] == "3"
    assert result["properties"]["email"] == "robert.brown@example.com"
    assert result["properties"]["firstname"] == "Robert"
    assert result["properties"]["lastname"] == "Brown"


@pytest.mark.asyncio
async def test_hubspot_update_contact(mock_aioresponse, hubspot_connector):
    """Test de mise à jour de contact HubSpot."""
    # Configurer le mock
    contact_id = "1"
    mock_response = {
        "id": contact_id,
        "properties": {
            "email": "john.doe@example.com",
            "firstname": "John",
            "lastname": "Doe",
            "phone": "+33612345678",
            "loyalty_points": "150",  # Mise à jour
            "last_visit_date": "2025-04-12"  # Mise à jour
        },
        "createdAt": "2024-12-15T10:30:45Z",
        "updatedAt": "2025-04-12T18:45:33Z"
    }
    
    base_url = hubspot_connector.config["api"]["base_url"]
    endpoint = f"crm/v3/objects/contacts/{contact_id}"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.patch(
        url,
        status=200,
        payload=mock_response
    )
    
    # Données pour la mise à jour
    update_data = {
        "properties": {
            "loyalty_points": "150",
            "last_visit_date": "2025-04-12"
        }
    }
    
    # Exécuter la méthode à tester
    result = await hubspot_connector.update_contact(contact_id, update_data)
    
    # Vérifier les résultats
    assert result is not None
    assert result["id"] == contact_id
    assert result["properties"]["loyalty_points"] == "150"
    assert result["properties"]["last_visit_date"] == "2025-04-12"


@pytest.mark.asyncio
async def test_zoho_search_contacts(mock_aioresponse, zoho_connector):
    """Test de recherche de contacts Zoho CRM."""
    # Configurer le mock
    mock_response = {
        "data": [
            {
                "id": "4567890123456789",
                "Email": "alice.johnson@example.com",
                "First_Name": "Alice",
                "Last_Name": "Johnson",
                "Phone": "+33678901234",
                "Loyalty_Points": 85,
                "Last_Visit": "2025-04-05",
                "Created_Time": "2025-01-10T09:22:45+0000",
                "Modified_Time": "2025-04-05T19:30:15+0000"
            },
            {
                "id": "7890123456789012",
                "Email": "david.miller@example.com",
                "First_Name": "David",
                "Last_Name": "Miller",
                "Phone": "+33654321098",
                "Loyalty_Points": 210,
                "Last_Visit": "2025-04-10",
                "Created_Time": "2024-11-22T14:15:30+0000",
                "Modified_Time": "2025-04-10T20:10:45+0000"
            }
        ],
        "info": {
            "per_page": 10,
            "count": 2,
            "page": 1,
            "more_records": false
        }
    }
    
    base_url = zoho_connector.config["api"]["base_url"]
    version = zoho_connector.config["api"]["version"]
    endpoint = f"{version}/Contacts/search"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.get(
        url,
        status=200,
        payload=mock_response
    )
    
    # Critères de recherche
    criteria = "Last_Visit:greater_than:2025-04-01"
    
    # Exécuter la méthode à tester
    contacts = await zoho_connector.search_contacts(criteria)
    
    # Vérifier les résultats
    assert contacts is not None
    assert "data" in contacts
    assert len(contacts["data"]) == 2
    assert contacts["data"][0]["Email"] == "alice.johnson@example.com"
    assert contacts["data"][0]["Loyalty_Points"] == 85
    assert contacts["data"][1]["First_Name"] == "David"


@pytest.mark.asyncio
async def test_zoho_create_contact(mock_aioresponse, zoho_connector):
    """Test de création de contact Zoho CRM."""
    # Configurer le mock
    mock_response = {
        "data": [
            {
                "id": "8901234567890123",
                "Email": "michel.durand@example.com",
                "First_Name": "Michel",
                "Last_Name": "Durand",
                "Phone": "+33612345678",
                "Loyalty_Points": 0,
                "Last_Visit": "2025-04-12",
                "Created_Time": "2025-04-12T18:50:22+0000",
                "Modified_Time": "2025-04-12T18:50:22+0000"
            }
        ],
        "code": "SUCCESS"
    }
    
    base_url = zoho_connector.config["api"]["base_url"]
    version = zoho_connector.config["api"]["version"]
    endpoint = f"{version}/Contacts"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.post(
        url,
        status=201,
        payload=mock_response
    )
    
    # Données pour la création
    contact_data = {
        "Email": "michel.durand@example.com",
        "First_Name": "Michel",
        "Last_Name": "Durand",
        "Phone": "+33612345678",
        "Loyalty_Points": 0,
        "Last_Visit": "2025-04-12"
    }
    
    # Exécuter la méthode à tester
    result = await zoho_connector.create_contact(contact_data)
    
    # Vérifier les résultats
    assert result is not None
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["Email"] == "michel.durand@example.com"
    assert result["data"][0]["First_Name"] == "Michel"
    assert result["data"][0]["Last_Name"] == "Durand"


@pytest.mark.asyncio
async def test_zoho_update_loyalty(mock_aioresponse, zoho_connector):
    """Test de mise à jour du programme de fidélité Zoho CRM."""
    # Configurer le mock
    mock_response = {
        "data": [
            {
                "code": "SUCCESS",
                "status": "success",
                "details": {
                    "id": "4567890123456789",
                    "Modified_Time": "2025-04-12T19:05:33+0000"
                },
                "message": "Loyalty record updated successfully"
            }
        ]
    }
    
    base_url = zoho_connector.config["api"]["base_url"]
    version = zoho_connector.config["api"]["version"]
    endpoint = f"{version}/Rewards"
    url = f"{base_url}{endpoint}"
    
    # Configurer la réponse simulée
    mock_aioresponse.post(
        url,
        status=200,
        payload=mock_response
    )
    
    # Données pour la mise à jour
    loyalty_data = {
        "Contact_ID": "4567890123456789",
        "Points": 25,
        "Transaction_Date": "2025-04-12",
        "Transaction_Type": "EARN",
        "Transaction_Description": "Visite restaurant"
    }
    
    # Exécuter la méthode à tester
    result = await zoho_connector.update_loyalty(loyalty_data)
    
    # Vérifier les résultats
    assert result is not None
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["code"] == "SUCCESS"
    assert result["data"][0]["details"]["id"] == "4567890123456789"


@pytest.mark.asyncio
async def test_hubspot_api_error(mock_aioresponse, hubspot_connector):
    """Test de gestion des erreurs API avec HubSpot."""
    # Configurer le mock pour une erreur
    base_url = hubspot_connector.config["api"]["base_url"]
    endpoint = "crm/v3/objects/contacts"
    url = f"{base_url}{endpoint}"
    
    error_response = {
        "status": "error",
        "message": "Invalid request",
        "correlationId": "abc123xyz456",
        "category": "VALIDATION_ERROR",
        "errors": [
            {
                "message": "Email address is required",
                "errorType": "PROPERTY_VALIDATION",
                "subCategory": "MISSING_REQUIRED_PROPERTY"
            }
        ]
    }
    
    # Configurer la réponse d'erreur simulée
    mock_aioresponse.post(
        url,
        status=400,
        payload=error_response
    )
    
    # Données pour la création (avec email manquant)
    contact_data = {
        "properties": {
            "firstname": "Robert",
            "lastname": "Brown",
            "phone": "+33645678901"
        }
    }
    
    # Exécuter la méthode et vérifier qu'elle lève une exception
    with pytest.raises(APIError) as excinfo:
        await hubspot_connector.create_contact(contact_data)
    
    # Vérifier le message d'erreur
    assert "400" in str(excinfo.value)
    assert "Email address is required" in str(excinfo.value)


# Tests d'intégration (désactivés par défaut)
@pytest.mark.skip(reason="Test d'intégration nécessitant des identifiants valides")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_hubspot_integration():
    """Test d'intégration réel avec HubSpot."""
    # Ces tests ne sont exécutés que si explicitement demandés et avec des identifiants réels
    if not os.environ.get("HUBSPOT_CLIENT_ID") or not os.environ.get("HUBSPOT_CLIENT_SECRET"):
        pytest.skip("Variables d'environnement non définies pour les tests d'intégration HubSpot")
    
    config = {
        "api": {
            "name": "HubSpot CRM",
            "base_url": "https://api.hubapi.com/",
            "version": "v3"
        },
        "auth": {
            "method": "oauth2",
            "client_id": os.environ.get("HUBSPOT_CLIENT_ID"),
            "client_secret": os.environ.get("HUBSPOT_CLIENT_SECRET"),
            "refresh_token": os.environ.get("HUBSPOT_REFRESH_TOKEN"),
            "scopes": "crm.objects.contacts.read crm.objects.contacts.write"
        }
    }
    
    connector = HubspotConnector(config_dict=config)
    await connector.connect()
    
    # Test simple pour vérifier la connexion
    health_status = await connector.check_health()
    assert health_status is True
    
    # Nettoyage
    await connector.disconnect()
