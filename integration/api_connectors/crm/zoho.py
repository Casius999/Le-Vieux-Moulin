"""Connecteur pour l'API Zoho CRM.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API du système CRM Zoho.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BaseCRMConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class ZohoCRMConnector(BaseCRMConnector):
    """Connecteur pour l'API Zoho CRM.
    
    Cette classe implémente l'interface BaseCRMConnector pour
    interagir avec le système de gestion de la relation client Zoho.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à Zoho CRM."""
        super()._validate_config()
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API Zoho CRM.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/crm/v2/contacts", params={"per_page": 1})
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé Zoho CRM: {str(e)}")
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
        # Construction des paramètres de base
        params = {
            "per_page": limit,
            "page": (offset // limit) + 1 if limit > 0 else 1,
            "fields": "First_Name,Last_Name,Email,Phone,Loyalty_Points,Last_Visit_Date,Lead_Status"
        }
        
        # Si un terme de recherche est spécifié, utiliser l'endpoint de recherche
        if search or filters:
            if search:
                # Utiliser la recherche générale
                params["word"] = search
                
                response = await self.get("/crm/v2/contacts/search", params=params)
            else:
                # Utiliser les critères pour une recherche avancée
                criteria = []
                
                if filters:
                    for field, value in filters.items():
                        if isinstance(value, dict) and "operator" in value and "value" in value:
                            criteria.append({
                                "field": field,
                                "comparator": value["operator"],
                                "value": value["value"]
                            })
                        else:
                            criteria.append({
                                "field": field,
                                "comparator": "equal",
                                "value": value
                            })
                
                search_criteria = {
                    "criteria": criteria
                }
                
                response = await self.post(
                    "/crm/v2/contacts/search", 
                    params={"fields": params["fields"]},
                    json=search_criteria
                )
        else:
            # Utiliser la liste standard
            response = await self.get("/crm/v2/contacts", params=params)
        
        # Extraire les données
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un contact spécifique.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Détails du contact
        """
        # Appel à l'API Zoho CRM
        response = await self.get(f"/crm/v2/contacts/{contact_id}")
        
        # Extraire les données
        if "data" not in response or not response["data"]:
            raise APIError(f"Contact {contact_id} non trouvé")
        
        return response["data"][0]
    
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
        contact_data = {}
        
        # Mapper les champs courants
        field_mapping = {
            "firstName": "First_Name",
            "first_name": "First_Name",
            "lastname": "Last_Name",
            "lastName": "Last_Name",
            "last_name": "Last_Name",
            "email": "Email",
            "phone": "Phone",
            "address": "Mailing_Street",
            "city": "Mailing_City",
            "state": "Mailing_State",
            "zip": "Mailing_Zip",
            "country": "Mailing_Country",
            "company": "Account_Name",
            "notes": "Description",
            "loyalty_points": "Loyalty_Points",
            "last_visit_date": "Last_Visit_Date"
        }
        
        # Extraire les propriétés selon le mapping
        for key, value in data.items():
            zoho_field = field_mapping.get(key, key)  # Utiliser le mapping ou le nom original
            contact_data[zoho_field] = value
        
        # Créer la structure de la requête
        request_data = {"data": [contact_data]}
        
        # Appel à l'API Zoho CRM
        response = await self.post("/crm/v2/contacts", json=request_data)
        
        # Vérifier la réponse
        if "data" not in response or not response["data"]:
            raise APIError("Création du contact échouée")
        
        return response["data"][0]
    
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
        contact_data = {}
        
        # Mapper les champs courants
        field_mapping = {
            "firstName": "First_Name",
            "first_name": "First_Name",
            "lastname": "Last_Name",
            "lastName": "Last_Name",
            "last_name": "Last_Name",
            "email": "Email",
            "phone": "Phone",
            "address": "Mailing_Street",
            "city": "Mailing_City",
            "state": "Mailing_State",
            "zip": "Mailing_Zip",
            "country": "Mailing_Country",
            "company": "Account_Name",
            "notes": "Description",
            "loyalty_points": "Loyalty_Points",
            "last_visit_date": "Last_Visit_Date"
        }
        
        # Extraire les propriétés selon le mapping
        for key, value in data.items():
            zoho_field = field_mapping.get(key, key)  # Utiliser le mapping ou le nom original
            contact_data[zoho_field] = value
        
        # Créer la structure de la requête
        request_data = {"data": [contact_data]}
        
        # Appel à l'API Zoho CRM
        response = await self.put(f"/crm/v2/contacts/{contact_id}", json=request_data)
        
        # Vérifier la réponse
        if "data" not in response or not response["data"]:
            raise APIError(f"Mise à jour du contact {contact_id} échouée")
        
        return response["data"][0]
    
    async def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Supprime un contact.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Confirmation de la suppression
        """
        # Appel à l'API Zoho CRM
        response = await self.delete(f"/crm/v2/contacts/{contact_id}")
        
        # Vérifier la réponse
        if "data" not in response or not response["data"]:
            raise APIError(f"Suppression du contact {contact_id} échouée")
        
        return response["data"][0]
    
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
        # Récupérer les données du contact
        contact = await self.get_contact(contact_id)
        
        # Extraire et formater les informations de fidélité
        loyalty_info = {
            "contact_id": contact_id,
            "points": 0,
            "last_visit": None
        }
        
        # Récupérer les points de fidélité
        if "Loyalty_Points" in contact:
            try:
                loyalty_info["points"] = int(contact["Loyalty_Points"])
            except (ValueError, TypeError):
                loyalty_info["points"] = 0
        
        # Récupérer la date de dernière visite
        if "Last_Visit_Date" in contact and contact["Last_Visit_Date"]:
            loyalty_info["last_visit"] = contact["Last_Visit_Date"]
        
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
            "Loyalty_Points": new_points,
            "Last_Visit_Date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Mettre à jour le contact
        await self.update_contact(contact_id, update_data)
        
        # Si une raison est spécifiée, créer une note
        if reason:
            await self.create_note(
                contact_id=contact_id,
                content=f"Mise à jour des points de fidélité: {'+' if points >= 0 else ''}{points} points. Raison: {reason}",
                type="loyalty_update"
            )
        
        # Formater la réponse
        loyalty_update = {
            "contact_id": contact_id,
            "previous_points": current_points,
            "points_change": points,
            "new_points": new_points,
            "update_time": update_data["Last_Visit_Date"]
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
        note_content = content
        if type:
            note_content = f"[{type.upper()}] {content}"
        
        note_data = {
            "Note_Title": type.title() if type else "Note",
            "Note_Content": note_content,
            "Parent_Id": contact_id,
            "se_module": "Contacts"
        }
        
        # Créer la structure de la requête
        request_data = {"data": [note_data]}
        
        # Appel à l'API Zoho CRM
        response = await self.post("/crm/v2/Notes", json=request_data)
        
        # Vérifier la réponse
        if "data" not in response or not response["data"]:
            raise APIError("Création de la note échouée")
        
        return response["data"][0]
    
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
        # Construction des paramètres de la requête
        params = {
            "per_page": limit,
            "parent_id": contact_id,
            "se_module": "Contacts"
        }
        
        # Appel à l'API Zoho CRM
        response = await self.get("/crm/v2/Notes", params=params)
        
        # Extraire les résultats
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
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
        
        # Préparer les données pour la création de la transaction (deal dans Zoho)
        deal_data = {
            "Deal_Name": data.get("name", f"Transaction du {data['date']}"),
            "Amount": data["amount"],
            "Closing_Date": data["date"] if isinstance(data["date"], str) else data["date"].strftime("%Y-%m-%d"),
            "Stage": "Closed Won",
            "Contact_Name": {"id": contact_id}
        }
        
        # Ajouter d'autres propriétés optionnelles
        if "description" in data:
            deal_data["Description"] = data["description"]
        
        if "items" in data and isinstance(data["items"], list):
            # Convertir la liste des articles en texte
            items_text = ", ".join([f"{item.get('quantity', 1)}x {item.get('name', 'Article')}" for item in data["items"]])
            deal_data["Transaction_Items"] = items_text
        
        # Créer la structure de la requête
        request_data = {"data": [deal_data]}
        
        # Appel à l'API Zoho CRM
        response = await self.post("/crm/v2/Deals", json=request_data)
        
        # Vérifier la réponse
        if "data" not in response or not response["data"]:
            raise APIError("Création de la transaction échouée")
        
        # Mettre à jour les points de fidélité si spécifié
        if "loyalty_points" in data and data["loyalty_points"]:
            try:
                points = int(data["loyalty_points"])
                await self.update_loyalty_points(
                    contact_id=contact_id,
                    points=points,
                    reason=f"Transaction #{response['data'][0]['id']}"
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Erreur lors de la mise à jour des points de fidélité: {str(e)}")
        
        return response["data"][0]
    
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
        # Construire les critères de recherche
        criteria = [
            {
                "field": "Contact_Name",
                "comparator": "equal",
                "value": contact_id
            }
        ]
        
        # Ajouter les filtres de date si spécifiés
        if start_date:
            if isinstance(start_date, datetime):
                start_date = start_date.strftime("%Y-%m-%d")
            
            criteria.append({
                "field": "Closing_Date",
                "comparator": "greater_equal",
                "value": start_date
            })
        
        if end_date:
            if isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y-%m-%d")
            
            criteria.append({
                "field": "Closing_Date",
                "comparator": "less_equal",
                "value": end_date
            })
        
        # Préparer la recherche
        search_criteria = {
            "criteria": criteria
        }
        
        # Appel à l'API Zoho CRM
        response = await self.post(
            "/crm/v2/Deals/search", 
            params={"per_page": limit},
            json=search_criteria
        )
        
        # Extraire les résultats
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
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
        campaign_data = {
            "Campaign_Name": data["name"],
            "Type": data["type"],
            "Description": data.get("description", ""),
            "Status": data.get("status", "Planning"),
            "Start_Date": data.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        }
        
        # Ajouter la date de fin si spécifiée
        if "end_date" in data:
            campaign_data["End_Date"] = data["end_date"] if isinstance(data["end_date"], str) else data["end_date"].strftime("%Y-%m-%d")
        
        # Créer la structure de la requête
        request_data = {"data": [campaign_data]}
        
        # Appel à l'API Zoho CRM
        response = await self.post("/crm/v2/Campaigns", json=request_data)
        
        # Vérifier la réponse
        if "data" not in response or not response["data"]:
            raise APIError("Création de la campagne échouée")
        
        return response["data"][0]
    
    async def get_segments(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les segments de clients disponibles.
        
        Args:
            limit: Nombre maximum de segments à récupérer
            
        Returns:
            Liste des segments
        """
        # Paramètres de la requête
        params = {"per_page": limit}
        
        # Appel à l'API Zoho CRM
        # Zoho utilise les balises pour la segmentation
        response = await self.get("/crm/v2/settings/tags", params=params)
        
        # Extraire les segments (tags)
        if "tags" not in response:
            raise APIError("Format de réponse inattendu: champ 'tags' manquant")
        
        return response["tags"]