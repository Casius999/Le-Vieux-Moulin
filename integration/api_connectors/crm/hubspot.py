"""Connecteur pour l'API HubSpot CRM.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API du système CRM HubSpot.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BaseCRMConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class HubSpotConnector(BaseCRMConnector):
    """Connecteur pour l'API HubSpot CRM.
    
    Cette classe implémente l'interface BaseCRMConnector pour
    interagir avec le système de gestion de la relation client HubSpot.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à HubSpot."""
        super()._validate_config()
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API HubSpot.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/crm/v3/objects/contacts", params={"limit": 1})
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé HubSpot: {str(e)}")
            return False
    
    async def get_contacts(self, 
                         limit: int = 100,
                         offset: int = 0,
                         search: Optional[str] = None,
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Récupère la liste des contacts.
        
        Args:
            limit: Nombre maximum de contacts à récupérer
            offset: Offset pour la pagination
            search: Terme de recherche (optionnel)
            filters: Filtres supplémentaires (optionnel)
            
        Returns:
            Liste des contacts
        """
        # Construction des paramètres de la requête
        params = {
            "limit": limit,
            "after": offset if offset > 0 else None,
            "properties": "firstname,lastname,email,phone,loyalty_points,last_visit_date,hs_lead_status"
        }
        
        # Retirer les paramètres None
        params = {k: v for k, v in params.items() if v is not None}
        
        # Gérer la recherche et les filtres si présents
        if search or filters:
            # Créer un corps de requête pour la recherche avancée
            filter_groups = []
            
            if search:
                # Recherche dans les champs courants (nom, email, téléphone)
                search_filters = [
                    {"propertyName": "firstname", "operator": "CONTAINS", "value": search},
                    {"propertyName": "lastname", "operator": "CONTAINS", "value": search},
                    {"propertyName": "email", "operator": "CONTAINS", "value": search},
                    {"propertyName": "phone", "operator": "CONTAINS", "value": search}
                ]
                filter_groups.append({"filters": search_filters})
            
            if filters:
                # Convertir les filtres en format HubSpot
                custom_filters = []
                for property_name, value in filters.items():
                    if isinstance(value, dict) and "operator" in value and "value" in value:
                        custom_filters.append({
                            "propertyName": property_name,
                            "operator": value["operator"],
                            "value": value["value"]
                        })
                    else:
                        custom_filters.append({
                            "propertyName": property_name,
                            "operator": "EQ",
                            "value": str(value)
                        })
                
                filter_groups.append({"filters": custom_filters})
            
            # Appel à l'API HubSpot avec recherche
            search_request = {
                "filterGroups": filter_groups,
                "sorts": [{"propertyName": "createdate", "direction": "DESCENDING"}],
                "properties": params.pop("properties", "").split(","),
                "limit": params.pop("limit", 100),
                "after": params.pop("after", 0) if "after" in params else None
            }
            
            # Retirer les champs None
            if search_request["after"] is None:
                search_request.pop("after")
            
            response = await self.post("/crm/v3/objects/contacts/search", json=search_request)
        else:
            # Appel simple à l'API HubSpot
            response = await self.get("/crm/v3/objects/contacts", params=params)
        
        # Extraire les résultats
        if "results" not in response:
            raise APIError("Format de réponse inattendu: champ 'results' manquant")
        
        return response["results"]
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un contact spécifique.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Détails du contact
        """
        # Définir les propriétés à récupérer
        params = {
            "properties": "firstname,lastname,email,phone,loyalty_points,last_visit_date,hs_lead_status,notes_last_updated,address,company"
        }
        
        # Appel à l'API HubSpot
        response = await self.get(f"/crm/v3/objects/contacts/{contact_id}", params=params)
        
        return response
    
    async def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau contact.
        
        Args:
            data: Données du contact (nom, email, téléphone, etc.)
            
        Returns:
            Contact créé
        """
        # Validation des données minimales
        if "email" not in data and "phone" not in data:
            raise ValidationError(
                "Au moins un email ou un numéro de téléphone est requis",
                errors={"required_fields": ["email ou phone"]}
            )
        
        # Préparer les données pour la création
        properties = {}
        
        # Mapper les champs courants
        field_mapping = {
            "firstName": "firstname",
            "first_name": "firstname",
            "lastname": "lastname",
            "last_name": "lastname",
            "lastName": "lastname",
            "email": "email",
            "phone": "phone",
            "address": "address",
            "company": "company",
            "notes": "notes",
            "loyalty_points": "loyalty_points",
            "last_visit_date": "last_visit_date"
        }
        
        # Extraire les propriétés selon le mapping
        for key, value in data.items():
            hubspot_field = field_mapping.get(key, key)  # Utiliser le mapping ou le nom original
            properties[hubspot_field] = str(value)  # Convertir en chaîne comme attendu par HubSpot
        
        # Créer la structure de la requête
        request_data = {"properties": properties}
        
        # Appel à l'API HubSpot
        response = await self.post("/crm/v3/objects/contacts", json=request_data)
        
        return response
    
    async def update_contact(self, 
                          contact_id: str,
                          data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un contact existant.
        
        Args:
            contact_id: Identifiant du contact
            data: Données à mettre à jour
            
        Returns:
            Contact mis à jour
        """
        # Préparer les données pour la mise à jour
        properties = {}
        
        # Mapper les champs courants
        field_mapping = {
            "firstName": "firstname",
            "first_name": "firstname",
            "lastname": "lastname",
            "last_name": "lastname",
            "lastName": "lastname",
            "email": "email",
            "phone": "phone",
            "address": "address",
            "company": "company",
            "notes": "notes",
            "loyalty_points": "loyalty_points",
            "last_visit_date": "last_visit_date"
        }
        
        # Extraire les propriétés selon le mapping
        for key, value in data.items():
            hubspot_field = field_mapping.get(key, key)  # Utiliser le mapping ou le nom original
            properties[hubspot_field] = str(value)  # Convertir en chaîne comme attendu par HubSpot
        
        # Créer la structure de la requête
        request_data = {"properties": properties}
        
        # Appel à l'API HubSpot
        response = await self.patch(f"/crm/v3/objects/contacts/{contact_id}", json=request_data)
        
        return response
    
    async def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Supprime un contact.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Confirmation de la suppression
        """
        # Appel à l'API HubSpot
        response = await self.delete(f"/crm/v3/objects/contacts/{contact_id}")
        
        # HubSpot renvoie un code 204 et aucun contenu pour les suppressions réussies
        # On crée donc une réponse standardisée
        return {"id": contact_id, "deleted": True, "status": "success"}
    
    async def search_contacts(self, 
                           query: str,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Recherche des contacts par requête de recherche.
        
        Args:
            query: Requête de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des contacts correspondant à la recherche
        """
        # Déléguer à la méthode get_contacts avec paramètre de recherche
        return await self.get_contacts(limit=limit, search=query)
    
    async def get_loyalty_points(self, contact_id: str) -> Dict[str, Any]:
        """Récupère les points de fidélité d'un contact.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Informations sur les points de fidélité
        """
        # Récupérer uniquement les propriétés liées à la fidélité
        params = {
            "properties": "loyalty_points,last_visit_date"
        }
        
        # Appel à l'API HubSpot
        response = await self.get(f"/crm/v3/objects/contacts/{contact_id}", params=params)
        
        # Extraire et formater les informations de fidélité
        loyalty_info = {
            "contact_id": contact_id,
            "points": 0,
            "last_visit": None
        }
        
        if "properties" in response:
            properties = response["properties"]
            
            # Récupérer les points de fidélité
            if "loyalty_points" in properties:
                try:
                    loyalty_info["points"] = int(properties["loyalty_points"])
                except ValueError:
                    loyalty_info["points"] = 0
            
            # Récupérer la date de dernière visite
            if "last_visit_date" in properties and properties["last_visit_date"]:
                loyalty_info["last_visit"] = properties["last_visit_date"]
        
        return loyalty_info
    
    async def update_loyalty_points(self,
                                 contact_id: str,
                                 points: int,
                                 reason: Optional[str] = None) -> Dict[str, Any]:
        """Met à jour les points de fidélité d'un contact.
        
        Args:
            contact_id: Identifiant du contact
            points: Nombre de points à ajouter (positif) ou soustraire (négatif)
            reason: Raison de la modification (optionnel)
            
        Returns:
            Confirmation de la mise à jour
        """
        # Récupérer d'abord les points actuels
        loyalty_info = await self.get_loyalty_points(contact_id)
        current_points = loyalty_info["points"]
        
        # Calculer le nouveau total
        new_points = max(0, current_points + points)  # Empêcher les points négatifs
        
        # Préparer les données pour la mise à jour
        update_data = {
            "loyalty_points": str(new_points),
            "last_visit_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        
        # Ajouter la raison si spécifiée
        if reason:
            # Créer une note pour enregistrer la raison
            await self.create_note(
                contact_id=contact_id,
                content=f"Mise à jour des points de fidélité: {'+' if points >= 0 else ''}{points} points. Raison: {reason}",
                type="loyalty_update"
            )
        
        # Mettre à jour le contact
        response = await self.update_contact(contact_id, update_data)
        
        # Formater la réponse
        loyalty_update = {
            "contact_id": contact_id,
            "previous_points": current_points,
            "points_change": points,
            "new_points": new_points,
            "update_time": update_data["last_visit_date"]
        }
        
        if reason:
            loyalty_update["reason"] = reason
        
        return loyalty_update
    
    async def create_note(self,
                       contact_id: str,
                       content: str,
                       type: Optional[str] = None) -> Dict[str, Any]:
        """Ajoute une note à un contact.
        
        Args:
            contact_id: Identifiant du contact
            content: Contenu de la note
            type: Type de note (optionnel)
            
        Returns:
            Note créée
        """
        # Préparer les données pour la création de la note
        note_data = {
            "properties": {
                "hs_note_body": content,
                "hs_timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            },
            "associations": [
                {
                    "to": {
                        "id": contact_id
                    },
                    "types": [
                        {
                            "category": "HUBSPOT_DEFINED",
                            "typeId": 202
                        }
                    ]
                }
            ]
        }
        
        # Ajouter le type de note si spécifié
        if type:
            note_data["properties"]["hs_note_body"] = f"[{type.upper()}] {content}"
        
        # Appel à l'API HubSpot
        response = await self.post("/crm/v3/objects/notes", json=note_data)
        
        return response
    
    async def get_notes(self, 
                      contact_id: str,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les notes d'un contact.
        
        Args:
            contact_id: Identifiant du contact
            limit: Nombre maximum de notes à récupérer
            
        Returns:
            Liste des notes
        """
        # Construire la requête pour les associations
        filter_groups = [
            {
                "filters": [
                    {
                        "propertyName": "associations.contact",
                        "operator": "EQ",
                        "value": contact_id
                    }
                ]
            }
        ]
        
        search_request = {
            "filterGroups": filter_groups,
            "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
            "properties": ["hs_note_body", "hs_timestamp"],
            "limit": limit
        }
        
        # Appel à l'API HubSpot
        response = await self.post("/crm/v3/objects/notes/search", json=search_request)
        
        # Extraire les résultats
        if "results" not in response:
            raise APIError("Format de réponse inattendu: champ 'results' manquant")
        
        return response["results"]
    
    async def create_transaction(self,
                             contact_id: str,
                             data: Dict[str, Any]) -> Dict[str, Any]:
        """Enregistre une transaction pour un contact.
        
        Args:
            contact_id: Identifiant du contact
            data: Données de la transaction (montant, date, produits, etc.)
            
        Returns:
            Transaction créée
        """
        # Validation des données minimales
        required_fields = ["amount", "date"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Champ requis manquant: {field}",
                    errors={"required_fields": required_fields}
                )
        
        # Préparer les données pour la création de la transaction (deal dans HubSpot)
        deal_properties = {
            "amount": str(data["amount"]),
            "dealname": data.get("name", f"Transaction du {data['date']}"),
            "dealstage": "closedwon",
            "pipeline": "default",
            "closedate": data["date"] if isinstance(data["date"], str) else data["date"].strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        
        # Ajouter d'autres propriétés optionnelles
        if "description" in data:
            deal_properties["description"] = data["description"]
        
        if "items" in data and isinstance(data["items"], list):
            # Convertir la liste des articles en texte
            items_text = ", ".join([f"{item.get('quantity', 1)}x {item.get('name', 'Article')}" for item in data["items"]])
            deal_properties["transaction_items"] = items_text
        
        deal_data = {
            "properties": deal_properties,
            "associations": [
                {
                    "to": {
                        "id": contact_id
                    },
                    "types": [
                        {
                            "category": "HUBSPOT_DEFINED",
                            "typeId": 3
                        }
                    ]
                }
            ]
        }
        
        # Appel à l'API HubSpot pour créer le deal
        response = await self.post("/crm/v3/objects/deals", json=deal_data)
        
        # Mettre à jour les points de fidélité si spécifié
        if "loyalty_points" in data and data["loyalty_points"]:
            try:
                points = int(data["loyalty_points"])
                await self.update_loyalty_points(
                    contact_id=contact_id,
                    points=points,
                    reason=f"Transaction #{response.get('id', 'inconnue')}"
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Erreur lors de la mise à jour des points de fidélité: {str(e)}")
        
        return response
    
    async def get_transactions(self,
                            contact_id: str,
                            start_date: Optional[Union[datetime, str]] = None,
                            end_date: Optional[Union[datetime, str]] = None,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les transactions d'un contact.
        
        Args:
            contact_id: Identifiant du contact
            start_date: Date de début pour filtrer les transactions (optionnel)
            end_date: Date de fin pour filtrer les transactions (optionnel)
            limit: Nombre maximum de transactions à récupérer
            
        Returns:
            Liste des transactions
        """
        # Convertir les dates si nécessaire
        if start_date and isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        if end_date and isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Construire les filtres pour la recherche
        filters = [
            {
                "propertyName": "associations.contact",
                "operator": "EQ",
                "value": contact_id
            }
        ]
        
        # Ajouter les filtres de date si spécifiés
        if start_date:
            filters.append({
                "propertyName": "closedate",
                "operator": "GTE",
                "value": start_date
            })
        
        if end_date:
            filters.append({
                "propertyName": "closedate",
                "operator": "LTE",
                "value": end_date
            })
        
        search_request = {
            "filterGroups": [{"filters": filters}],
            "sorts": [{"propertyName": "closedate", "direction": "DESCENDING"}],
            "properties": ["amount", "dealname", "closedate", "description", "transaction_items"],
            "limit": limit
        }
        
        # Appel à l'API HubSpot
        response = await self.post("/crm/v3/objects/deals/search", json=search_request)
        
        # Extraire les résultats
        if "results" not in response:
            raise APIError("Format de réponse inattendu: champ 'results' manquant")
        
        return response["results"]
    
    async def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une campagne marketing.
        
        Args:
            data: Données de la campagne (nom, type, contenu, audience, etc.)
            
        Returns:
            Campagne créée
        """
        # Validation des données minimales
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Champ requis manquant: {field}",
                    errors={"required_fields": required_fields}
                )
        
        # Préparer les données pour la création de la campagne
        campaign_properties = {
            "name": data["name"],
            "hs_campaign_type": data["type"],
            "description": data.get("description", ""),
            "startDate": data.get("start_date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        }
        
        # Ajouter la date de fin si spécifiée
        if "end_date" in data:
            campaign_properties["endDate"] = data["end_date"] if isinstance(data["end_date"], str) else data["end_date"].strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Créer la structure de la requête
        campaign_data = {"properties": campaign_properties}
        
        # Appel à l'API HubSpot
        response = await self.post("/crm/v3/objects/campaigns", json=campaign_data)
        
        return response
    
    async def get_segments(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les segments de clients disponibles.
        
        Args:
            limit: Nombre maximum de segments à récupérer
            
        Returns:
            Liste des segments
        """
        # Paramètres de la requête
        params = {"limit": limit}
        
        # Appel à l'API HubSpot
        response = await self.get("/contacts/v1/lists/static", params=params)
        
        # Extraire les segments
        if "lists" not in response:
            raise APIError("Format de réponse inattendu: champ 'lists' manquant")
        
        return response["lists"]