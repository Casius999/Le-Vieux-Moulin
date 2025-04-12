"""Connecteur pour l'API Transgourmet.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API du fournisseur Transgourmet pour la gestion des commandes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BaseSupplierConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class TransgourmetConnector(BaseSupplierConnector):
    """Connecteur pour l'API Transgourmet.
    
    Cette classe implémente l'interface BaseSupplierConnector pour
    interagir avec le système d'approvisionnement de Transgourmet.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à Transgourmet."""
        super()._validate_config()
        
        # Vérifier la présence des champs spécifiques
        api_config = self.config.get('api', {})
        if 'customer_id' not in api_config:
            raise ConfigurationError("ID client Transgourmet manquant", "api.customer_id")
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API Transgourmet.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/api/health")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé Transgourmet: {str(e)}")
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
            "customerId": self.config['api']['customer_id'],
            "limit": limit,
            "page": page
        }
        
        # Ajouter les filtres si spécifiés
        if category:
            params["category"] = category
        
        if search:
            params["search"] = search
        
        # Appel à l'API Transgourmet
        response = await self.get("/api/catalog", params=params)
        
        # Extraire les produits
        return response.get("products", [])
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un produit spécifique.
        
        Args:
            product_id: Identifiant du produit
            
        Returns:
            Détails du produit
        """
        # Ajouter l'ID client comme paramètre
        params = {"customerId": self.config['api']['customer_id']}
        
        # Appel à l'API Transgourmet
        response = await self.get(f"/api/catalog/products/{product_id}", params=params)
        
        # Vérifier la présence du produit
        if "product" not in response:
            raise APIError(f"Produit {product_id} non trouvé")
        
        return response["product"]
    
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
            "customerId": self.config['api']['customer_id'],
            "productIds": product_ids
        }
        
        # Appel à l'API Transgourmet
        response = await self.post("/api/availability", json=payload)
        
        # Vérifier la présence des données de disponibilité
        if "availability" not in response:
            raise APIError("Données de disponibilité non trouvées dans la réponse")
        
        return response["availability"]
    
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
        
        # Formater les articles pour l'API Transgourmet
        order_items = []
        for item in items:
            order_item = {
                "productId": item["id"],
                "quantity": item["quantity"]
            }
            
            # Ajouter l'unité si spécifiée
            if "unit" in item:
                order_item["unit"] = item["unit"]
            
            order_items.append(order_item)
        
        # Construction du payload pour la commande
        payload = {
            "customerId": self.config['api']['customer_id'],
            "items": order_items
        }
        
        # Ajouter la date de livraison si spécifiée
        if delivery_date:
            if isinstance(delivery_date, str):
                delivery_date = parse_date(delivery_date)
            payload["deliveryDate"] = delivery_date.strftime("%Y-%m-%d")
        
        # Ajouter les notes si spécifiées
        if notes:
            payload["notes"] = notes
        
        # Appel à l'API Transgourmet
        response = await self.post("/api/orders", json=payload)
        
        # Vérifier la présence des données de commande
        if "order" not in response:
            raise APIError("Données de commande non trouvées dans la réponse")
        
        return response["order"]
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une commande spécifique.
        
        Args:
            order_id: Identifiant de la commande
            
        Returns:
            Détails de la commande
        """
        # Ajouter l'ID client comme paramètre
        params = {"customerId": self.config['api']['customer_id']}
        
        # Appel à l'API Transgourmet
        response = await self.get(f"/api/orders/{order_id}", params=params)
        
        # Vérifier la présence de la commande
        if "order" not in response:
            raise APIError(f"Commande {order_id} non trouvée")
        
        return response["order"]
    
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
            "customerId": self.config['api']['customer_id'],
            "limit": limit
        }
        
        # Ajouter les filtres si spécifiés
        if status:
            params["status"] = status
        
        # Gérer les dates de début et de fin
        if start_date:
            if isinstance(start_date, str):
                start_date = parse_date(start_date)
            params["startDate"] = start_date.strftime("%Y-%m-%d")
        
        if end_date:
            if isinstance(end_date, str):
                end_date = parse_date(end_date)
            params["endDate"] = end_date.strftime("%Y-%m-%d")
        
        # Appel à l'API Transgourmet
        response = await self.get("/api/orders", params=params)
        
        # Vérifier la présence des commandes
        if "orders" not in response:
            raise APIError("Données de commandes non trouvées dans la réponse")
        
        return response["orders"]
    
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
        update_data["customerId"] = self.config['api']['customer_id']
        
        # Formater les articles si présents
        if "items" in update_data:
            order_items = []
            for item in update_data["items"]:
                order_item = {
                    "productId": item["id"],
                    "quantity": item["quantity"]
                }
                
                # Ajouter l'unité si spécifiée
                if "unit" in item:
                    order_item["unit"] = item["unit"]
                
                order_items.append(order_item)
            
            update_data["items"] = order_items
        
        # Formater la date de livraison si présente
        if "delivery_date" in update_data:
            delivery_date = update_data.pop("delivery_date")
            if isinstance(delivery_date, str):
                delivery_date = parse_date(delivery_date)
            update_data["deliveryDate"] = delivery_date.strftime("%Y-%m-%d")
        
        # Appel à l'API Transgourmet
        response = await self.put(f"/api/orders/{order_id}", json=update_data)
        
        # Vérifier la présence de la commande mise à jour
        if "order" not in response:
            raise APIError(f"Mise à jour de la commande {order_id} échouée")
        
        return response["order"]
    
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
            "customerId": self.config['api']['customer_id'],
            "status": "CANCELLED"
        }
        
        if reason:
            cancel_data["cancellationReason"] = reason
        
        # Appel à l'API Transgourmet
        response = await self.put(f"/api/orders/{order_id}/status", json=cancel_data)
        
        # Vérifier la présence de la commande annulée
        if "order" not in response:
            raise APIError(f"Annulation de la commande {order_id} échouée")
        
        return response["order"]
    
    async def get_delivery_schedule(self) -> Dict[str, Any]:
        """Récupère le planning de livraison disponible.
        
        Returns:
            Planning de livraison (jours, heures, etc.)
        """
        # Ajouter l'ID client comme paramètre
        params = {"customerId": self.config['api']['customer_id']}
        
        # Appel à l'API Transgourmet
        response = await self.get("/api/delivery/schedule", params=params)
        
        # Vérifier la présence du planning
        if "schedule" not in response:
            raise APIError("Planning de livraison non trouvé dans la réponse")
        
        return response["schedule"]
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Récupère les informations du compte client.
        
        Returns:
            Informations du compte (solde, limite de crédit, etc.)
        """
        # Ajouter l'ID client comme paramètre
        params = {"customerId": self.config['api']['customer_id']}
        
        # Appel à l'API Transgourmet
        response = await self.get("/api/customer/account", params=params)
        
        # Vérifier la présence des informations de compte
        if "account" not in response:
            raise APIError("Informations de compte non trouvées dans la réponse")
        
        return response["account"]