"""Connecteur pour l'API Pomona.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API du fournisseur Pomona pour la gestion des commandes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BaseSupplierConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class PomonaConnector(BaseSupplierConnector):
    """Connecteur pour l'API Pomona.
    
    Cette classe implémente l'interface BaseSupplierConnector pour
    interagir avec le système d'approvisionnement de Pomona.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à Pomona."""
        super()._validate_config()
        
        # Vérifier la présence des champs spécifiques
        api_config = self.config.get('api', {})
        if 'establishment_code' not in api_config:
            raise ConfigurationError("Code établissement Pomona manquant", "api.establishment_code")
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API Pomona.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/api/health")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé Pomona: {str(e)}")
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
            "establishment": self.config['api']['establishment_code'],
            "limit": limit,
            "offset": (page - 1) * limit
        }
        
        # Ajouter les filtres si spécifiés
        if category:
            params["category"] = category
        
        if search:
            params["search"] = search
        
        # Appel à l'API Pomona
        response = await self.get("/api/catalog/products", params=params)
        
        # Vérifier et extraire les produits
        return response.get("items", [])
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un produit spécifique.
        
        Args:
            product_id: Identifiant du produit
            
        Returns:
            Détails du produit
        """
        # Ajouter le code établissement comme paramètre
        params = {"establishment": self.config['api']['establishment_code']}
        
        # Appel à l'API Pomona
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
            "establishment": self.config['api']['establishment_code'],
            "product_codes": product_ids
        }
        
        # Appel à l'API Pomona
        response = await self.post("/api/stock/availability", json=payload)
        
        # Restructurer la réponse pour faciliter l'utilisation
        result = {}
        for item in response.get("items", []):
            product_id = item.get("product_code")
            result[product_id] = {
                "available": item.get("available", False),
                "quantity": item.get("available_quantity", 0),
                "next_delivery": item.get("next_delivery_date")
            }
        
        return result
    
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
        
        # Formater les articles pour l'API Pomona
        order_lines = []
        for item in items:
            order_line = {
                "product_code": item["id"],
                "quantity": item["quantity"]
            }
            
            # Ajouter l'unité si spécifiée
            if "unit" in item:
                order_line["unit"] = item["unit"]
            
            order_lines.append(order_line)
        
        # Construction du payload pour la commande
        payload = {
            "establishment": self.config['api']['establishment_code'],
            "items": order_lines
        }
        
        # Ajouter la date de livraison si spécifiée
        if delivery_date:
            if isinstance(delivery_date, str):
                delivery_date = parse_date(delivery_date)
            payload["delivery_date"] = delivery_date.strftime("%Y-%m-%d")
        
        # Ajouter les notes si spécifiées
        if notes:
            payload["notes"] = notes
        
        # Appel à l'API Pomona
        response = await self.post("/api/orders/create", json=payload)
        
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
        # Ajouter le code établissement comme paramètre
        params = {"establishment": self.config['api']['establishment_code']}
        
        # Appel à l'API Pomona
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
            "establishment": self.config['api']['establishment_code'],
            "limit": limit
        }
        
        # Ajouter les filtres si spécifiés
        if status:
            params["status"] = status
        
        # Gérer les dates de début et de fin
        if start_date:
            if isinstance(start_date, str):
                start_date = parse_date(start_date)
            params["from_date"] = start_date.strftime("%Y-%m-%d")
        
        if end_date:
            if isinstance(end_date, str):
                end_date = parse_date(end_date)
            params["to_date"] = end_date.strftime("%Y-%m-%d")
        
        # Appel à l'API Pomona
        response = await self.get("/api/orders", params=params)
        
        # Vérifier la présence des commandes
        return response.get("orders", [])
    
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
        update_data["establishment"] = self.config['api']['establishment_code']
        
        # Formater les articles si présents
        if "items" in update_data:
            order_lines = []
            for item in update_data["items"]:
                order_line = {
                    "product_code": item["id"],
                    "quantity": item["quantity"]
                }
                
                # Ajouter l'unité si spécifiée
                if "unit" in item:
                    order_line["unit"] = item["unit"]
                
                order_lines.append(order_line)
            
            update_data["items"] = order_lines
        
        # Formater la date de livraison si présente
        if "delivery_date" in update_data:
            delivery_date = update_data["delivery_date"]
            if isinstance(delivery_date, str):
                delivery_date = parse_date(delivery_date)
            update_data["delivery_date"] = delivery_date.strftime("%Y-%m-%d")
        
        # Appel à l'API Pomona
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
            "establishment": self.config['api']['establishment_code'],
            "action": "cancel"
        }
        
        if reason:
            cancel_data["reason"] = reason
        
        # Appel à l'API Pomona
        response = await self.post(f"/api/orders/{order_id}/actions", json=cancel_data)
        
        # Vérifier la présence de la commande annulée
        if "order" not in response:
            raise APIError(f"Annulation de la commande {order_id} échouée")
        
        return response["order"]
    
    async def get_delivery_schedule(self) -> Dict[str, Any]:
        """Récupère le planning de livraison disponible.
        
        Returns:
            Planning de livraison (jours, heures, etc.)
        """
        # Ajouter le code établissement comme paramètre
        params = {"establishment": self.config['api']['establishment_code']}
        
        # Appel à l'API Pomona
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
        # Ajouter le code établissement comme paramètre
        params = {"establishment": self.config['api']['establishment_code']}
        
        # Appel à l'API Pomona
        response = await self.get("/api/account", params=params)
        
        # Vérifier la présence des informations de compte
        return response