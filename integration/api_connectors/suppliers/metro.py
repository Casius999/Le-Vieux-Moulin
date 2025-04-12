"""Connecteur pour l'API Metro France.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API du fournisseur Metro France pour la gestion des commandes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BaseSupplierConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class MetroConnector(BaseSupplierConnector):
    """Connecteur pour l'API Metro France.
    
    Cette classe implémente l'interface BaseSupplierConnector pour
    interagir avec le système d'approvisionnement de Metro France.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à Metro."""
        super()._validate_config()
        
        # Vérifier la présence des champs spécifiques
        api_config = self.config.get('api', {})
        if 'client_number' not in api_config:
            raise ConfigurationError("Numéro client Metro manquant", "api.client_number")
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API Metro.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/status")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé Metro: {str(e)}")
            return False
    
    async def get_catalog(self, 
                        category: Optional[str] = None,
                        search: Optional[str] = None,
                        limit: int = 100,
                        page: int = 1) -> List[Dict[str, Any]]:
        """Récupère le catalogue des produits disponibles.
        
        Args:
            category: Catégorie de produits à filtrer (optionnel)
            search: Terme de recherche (optionnel)
            limit: Nombre maximum de produits à récupérer
            page: Numéro de page pour la pagination
            
        Returns:
            Liste des produits du catalogue
        """
        # Construction des paramètres de la requête
        params = {
            "limit": limit,
            "page": page,
            "sort": "name:asc"
        }
        
        # Ajouter les filtres si spécifiés
        if category:
            params["category"] = category
        
        if search:
            params["search"] = search
        
        # Ajouter le numéro client
        params["client_number"] = self.config['api']['client_number']
        
        # Appel à l'API Metro
        response = await self.get("/api/v1/products", params=params)
        
        # Vérifier et extraire les produits
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un produit spécifique.
        
        Args:
            product_id: Identifiant du produit
            
        Returns:
            Détails du produit
        """
        # Ajouter le numéro client comme paramètre
        params = {"client_number": self.config['api']['client_number']}
        
        # Appel à l'API Metro
        response = await self.get(f"/api/v1/products/{product_id}", params=params)
        
        # Vérifier et extraire les détails du produit
        if "data" not in response:
            raise APIError(f"Produit {product_id} non trouvé ou format de réponse inattendu")
        
        return response["data"]
    
    async def check_product_availability(self, 
                                      product_ids: List[str]) -> Dict[str, Any]:
        """Vérifie la disponibilité de plusieurs produits.
        
        Args:
            product_ids: Liste des identifiants de produits
            
        Returns:
            Disponibilité des produits demandés
        """
        # Construction du payload pour la requête
        payload = {
            "client_number": self.config['api']['client_number'],
            "product_ids": product_ids
        }
        
        # Appel à l'API Metro
        response = await self.post("/api/v1/availability", json=payload)
        
        # Vérifier et extraire les données de disponibilité
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
    async def create_order(self, 
                         items: List[Dict[str, Any]],
                         delivery_date: Optional[Union[datetime, str]] = None,
                         notes: Optional[str] = None) -> Dict[str, Any]:
        """Crée une nouvelle commande.
        
        Args:
            items: Liste des articles à commander (id, quantité, etc.)
            delivery_date: Date de livraison souhaitée (optionnel)
            notes: Notes additionnelles pour la commande (optionnel)
            
        Returns:
            Détails de la commande créée
        """
        # Validation des données des articles
        for i, item in enumerate(items):
            if "id" not in item:
                raise ValidationError(f"Champ 'id' manquant pour l'article à l'indice {i}")
            if "quantity" not in item:
                raise ValidationError(f"Champ 'quantity' manquant pour l'article à l'indice {i}")
        
        # Formater les articles pour l'API Metro
        formatted_items = []
        for item in items:
            formatted_item = {
                "product_id": item["id"],
                "quantity": item["quantity"],
                "unit": item.get("unit", "PC")  # Unité par défaut: Pièce
            }
            formatted_items.append(formatted_item)
        
        # Formater la date de livraison si spécifiée
        delivery_info = {}
        if delivery_date:
            if isinstance(delivery_date, str):
                delivery_date = parse_date(delivery_date)
            delivery_info["requested_date"] = delivery_date.isoformat()
        
        if notes:
            delivery_info["delivery_notes"] = notes
        
        # Construction du payload pour la commande
        payload = {
            "client_number": self.config['api']['client_number'],
            "items": formatted_items
        }
        
        if delivery_info:
            payload["delivery_info"] = delivery_info
        
        # Appel à l'API Metro
        response = await self.post("/api/v1/orders", json=payload)
        
        # Vérifier et extraire les détails de la commande
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une commande spécifique.
        
        Args:
            order_id: Identifiant de la commande
            
        Returns:
            Détails de la commande
        """
        # Ajouter le numéro client comme paramètre
        params = {"client_number": self.config['api']['client_number']}
        
        # Appel à l'API Metro
        response = await self.get(f"/api/v1/orders/{order_id}", params=params)
        
        # Vérifier et extraire les détails de la commande
        if "data" not in response:
            raise APIError(f"Commande {order_id} non trouvée ou format de réponse inattendu")
        
        return response["data"]
    
    async def get_orders(self, 
                       status: Optional[str] = None,
                       start_date: Optional[Union[datetime, str]] = None,
                       end_date: Optional[Union[datetime, str]] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère la liste des commandes.
        
        Args:
            status: Statut des commandes à filtrer (optionnel)
            start_date: Date de début pour filtrer les commandes (optionnel)
            end_date: Date de fin pour filtrer les commandes (optionnel)
            limit: Nombre maximum de commandes à récupérer
            
        Returns:
            Liste des commandes
        """
        # Construction des paramètres de la requête
        params = {
            "client_number": self.config['api']['client_number'],
            "limit": limit
        }
        
        # Ajouter les filtres si spécifiés
        if status:
            params["status"] = status
        
        # Gérer les dates de début et de fin
        if start_date:
            if isinstance(start_date, str):
                start_date = parse_date(start_date)
            params["start_date"] = start_date.isoformat()
        
        if end_date:
            if isinstance(end_date, str):
                end_date = parse_date(end_date)
            params["end_date"] = end_date.isoformat()
        
        # Appel à l'API Metro
        response = await self.get("/api/v1/orders", params=params)
        
        # Vérifier et extraire les commandes
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
    async def update_order(self, 
                         order_id: str,
                         data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une commande existante.
        
        Args:
            order_id: Identifiant de la commande
            data: Données à mettre à jour (articles, date, etc.)
            
        Returns:
            Détails de la commande mise à jour
        """
        # Préparer les données pour la mise à jour
        update_data = data.copy()
        update_data["client_number"] = self.config['api']['client_number']
        
        # Si des items sont présents, les formater correctement
        if "items" in update_data:
            formatted_items = []
            for item in update_data["items"]:
                formatted_item = {
                    "product_id": item["id"],
                    "quantity": item["quantity"],
                    "unit": item.get("unit", "PC")  # Unité par défaut: Pièce
                }
                formatted_items.append(formatted_item)
            update_data["items"] = formatted_items
        
        # Appel à l'API Metro
        response = await self.patch(f"/api/v1/orders/{order_id}", json=update_data)
        
        # Vérifier et extraire les détails de la commande mise à jour
        if "data" not in response:
            raise APIError(f"Mise à jour de la commande {order_id} échouée ou format de réponse inattendu")
        
        return response["data"]
    
    async def cancel_order(self, 
                         order_id: str,
                         reason: Optional[str] = None) -> Dict[str, Any]:
        """Annule une commande existante.
        
        Args:
            order_id: Identifiant de la commande
            reason: Raison de l'annulation (optionnel)
            
        Returns:
            Confirmation de l'annulation
        """
        # Préparer les données pour l'annulation
        cancel_data = {
            "client_number": self.config['api']['client_number'],
            "status": "CANCELLED"
        }
        
        if reason:
            cancel_data["cancellation_reason"] = reason
        
        # Appel à l'API Metro
        response = await self.patch(f"/api/v1/orders/{order_id}", json=cancel_data)
        
        # Vérifier et extraire la confirmation d'annulation
        if "data" not in response:
            raise APIError(f"Annulation de la commande {order_id} échouée ou format de réponse inattendu")
        
        return response["data"]
    
    async def get_delivery_schedule(self) -> Dict[str, Any]:
        """Récupère le planning de livraison disponible.
        
        Returns:
            Planning de livraison (jours, heures, etc.)
        """
        # Ajouter le numéro client comme paramètre
        params = {"client_number": self.config['api']['client_number']}
        
        # Appel à l'API Metro
        response = await self.get("/api/v1/delivery/schedule", params=params)
        
        # Vérifier et extraire le planning de livraison
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Récupère les informations du compte client.
        
        Returns:
            Informations du compte (solde, limite de crédit, etc.)
        """
        # Ajouter le numéro client comme paramètre
        params = {"client_number": self.config['api']['client_number']}
        
        # Appel à l'API Metro
        response = await self.get("/api/v1/account", params=params)
        
        # Vérifier et extraire les informations du compte
        if "data" not in response:
            raise APIError("Format de réponse inattendu: champ 'data' manquant")
        
        return response["data"]