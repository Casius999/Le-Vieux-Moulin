"""Connecteur pour l'API Square Point of Sale.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API de la caisse enregistreuse Square.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BasePOSConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class SquareConnector(BasePOSConnector):
    """Connecteur pour l'API Square Point of Sale.
    
    Cette classe implémente l'interface BasePOSConnector pour
    interagir avec le système de caisse Square.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à Square."""
        super()._validate_config()
        
        # Vérifier la présence de l'ID de l'emplacement (location)
        if 'location_id' not in self.config['api']:
            raise ConfigurationError("ID de l'emplacement Square manquant", "api.location_id")
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API Square.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/v2/catalog/info")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé Square: {str(e)}")
            return False
    
    async def get_transactions(self, 
                             start_date: Union[datetime, str],
                             end_date: Optional[Union[datetime, str]] = None,
                             status: Optional[str] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les transactions sur une période donnée.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période (par défaut: maintenant)
            status: Statut des transactions à récupérer (ex: "completed", "refunded")
            limit: Nombre maximum de transactions à récupérer
            
        Returns:
            Liste des transactions
        """
        # Convertir les dates en objets datetime si nécessaire
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = parse_date(end_date)
        
        # Format de la date pour l'API Square: RFC 3339
        start_rfc = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_rfc = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Récupérer l'ID de l'emplacement depuis la configuration
        location_id = self.config['api']['location_id']
        
        # Construction du payload pour l'API
        payload = {
            "location_id": location_id,
            "begin_time": start_rfc,
            "end_time": end_rfc,
            "limit": limit
        }
        
        # Si un statut est spécifié, l'ajouter au payload
        if status:
            # Mapper le statut au format attendu par Square
            status_map = {
                "completed": "COMPLETED",
                "refunded": "REFUNDED"
            }
            square_status = status_map.get(status.lower())
            if square_status:
                payload["status"] = square_status
        
        # Appel à l'API Square
        response = await self.post("/v2/orders/search", json=payload)
        
        # Extraction des transactions (orders dans Square)
        orders = response.get("orders", [])
        
        return orders
    
    async def get_transaction_details(self, transaction_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une transaction spécifique.
        
        Args:
            transaction_id: Identifiant de la transaction
            
        Returns:
            Détails de la transaction
        """
        # Appel à l'API Square
        response = await self.get(f"/v2/orders/{transaction_id}")
        
        # Vérifier la présence de la transaction
        if "order" not in response:
            raise APIError(f"Transaction {transaction_id} non trouvée")
        
        return response["order"]
    
    async def get_products(self, 
                         category: Optional[str] = None, 
                         updated_since: Optional[Union[datetime, str]] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère la liste des produits.
        
        Args:
            category: Catégorie de produits à filtrer (optionnel)
            updated_since: Récupérer uniquement les produits mis à jour depuis cette date
            limit: Nombre maximum de produits à récupérer
            
        Returns:
            Liste des produits
        """
        # Construction du payload pour l'API
        payload = {
            "object_types": ["ITEM"],
            "limit": limit
        }
        
        # Filtre par catégorie si spécifié
        if category:
            payload["category_ids"] = [category]
        
        # Filtre par date de mise à jour si spécifié
        if updated_since:
            if isinstance(updated_since, str):
                updated_since = parse_date(updated_since)
            
            # Format de la date pour l'API Square: RFC 3339
            updated_rfc = updated_since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            payload["begin_time"] = updated_rfc
        
        # Appel à l'API Square
        response = await self.post("/v2/catalog/search", json=payload)
        
        # Extraction des produits
        items = []
        for obj in response.get("objects", []):
            if obj.get("type") == "ITEM":
                items.append(obj)
        
        return items
    
    async def update_product(self, 
                           product_id: str, 
                           data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour les informations d'un produit.
        
        Args:
            product_id: Identifiant du produit
            data: Données à mettre à jour (prix, nom, etc.)
            
        Returns:
            Produit mis à jour
        """
        # Récupérer d'abord le produit existant
        try:
            existing_product = await self.get(f"/v2/catalog/object/{product_id}")
            if "object" not in existing_product:
                raise APIError(f"Produit {product_id} non trouvé")
            
            existing_item = existing_product["object"]
        except Exception as e:
            raise APIError(f"Erreur lors de la récupération du produit {product_id}: {str(e)}")
        
        # Préparer les données de mise à jour
        update_data = {"idempotency_key": f"update_{product_id}_{int(datetime.now().timestamp())}"}
        
        # Créer l'objet de mise à jour
        object_data = {
            "type": "ITEM",
            "id": product_id,
            "version": existing_item.get("version", 0)
        }
        
        # Mapper les champs à mettre à jour
        item_data = {}
        
        if "name" in data:
            item_data["name"] = data["name"]
        
        if "description" in data:
            item_data["description"] = data["description"]
        
        if "price" in data:
            # La mise à jour du prix est plus complexe car il faut mettre à jour les variations
            variations = existing_item.get("item_data", {}).get("variations", [])
            
            if variations:
                updated_variations = []
                for variation in variations:
                    variation_data = variation.copy()
                    variation_data["item_variation_data"] = variation_data.get("item_variation_data", {}).copy()
                    
                    # Mettre à jour le prix (en centimes pour Square)
                    price_money = {
                        "amount": int(float(data["price"]) * 100),
                        "currency": "EUR"  # Utiliser l'euro comme devise par défaut
                    }
                    
                    variation_data["item_variation_data"]["price_money"] = price_money
                    updated_variations.append(variation_data)
                
                item_data["variations"] = updated_variations
        
        if item_data:
            object_data["item_data"] = item_data
        
        # Si aucune donnée à mettre à jour, retourner une erreur
        if not item_data:
            raise ValidationError(
                "Aucun champ valide pour la mise à jour du produit",
                errors={"valid_fields": ["name", "description", "price"]}
            )
        
        update_data["object"] = object_data
        
        # Appel à l'API Square
        response = await self.put("/v2/catalog/object", json=update_data)
        
        # Vérifier la réponse
        if "object" not in response:
            raise APIError(f"Mise à jour du produit {product_id} échouée")
        
        return response["object"]
    
    async def get_inventory(self,
                          product_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Récupère l'état des stocks.
        
        Args:
            product_ids: Liste des IDs de produits à récupérer (optionnel, tous si None)
            
        Returns:
            Liste des niveaux de stock
        """
        # Construction du payload pour l'API
        location_id = self.config['api']['location_id']
        
        # Si des IDs de produits sont spécifiés, les convertir en IDs de variations Square
        catalog_object_ids = []
        if product_ids:
            # Pour chaque produit, récupérer les variations
            for product_id in product_ids:
                try:
                    product = await self.get(f"/v2/catalog/object/{product_id}")
                    variations = product.get("object", {}).get("item_data", {}).get("variations", [])
                    
                    for variation in variations:
                        variation_id = variation.get("id")
                        if variation_id:
                            catalog_object_ids.append(variation_id)
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération des variations pour {product_id}: {str(e)}")
        
        # Si on a des IDs de variations, les utiliser dans la requête
        payload = {"location_ids": [location_id]}
        if catalog_object_ids:
            payload["catalog_object_ids"] = catalog_object_ids
        
        # Appel à l'API Square
        response = await self.post("/v2/inventory/counts/batch-retrieve", json=payload)
        
        # Extraction des données de stock
        counts = response.get("counts", [])
        
        return counts
    
    async def update_inventory(self,
                             product_id: str,
                             quantity: float,
                             location_id: Optional[str] = None) -> Dict[str, Any]:
        """Met à jour le niveau de stock d'un produit.
        
        Args:
            product_id: Identifiant du produit
            quantity: Nouvelle quantité en stock
            location_id: Identifiant de l'emplacement (optionnel)
            
        Returns:
            Résultat de la mise à jour
        """
        # Utiliser l'ID d'emplacement de la config si non spécifié
        if not location_id:
            location_id = self.config['api']['location_id']
        
        # Générer une clé d'idempotence unique
        idempotency_key = f"inv_update_{product_id}_{int(datetime.now().timestamp())}"
        
        # Récupérer d'abord le produit pour obtenir les IDs de variation
        try:
            product = await self.get(f"/v2/catalog/object/{product_id}")
            variations = product.get("object", {}).get("item_data", {}).get("variations", [])
            
            if not variations:
                raise APIError(f"Aucune variation trouvée pour le produit {product_id}")
            
            # Utiliser le premier ID de variation
            variation_id = variations[0].get("id")
            if not variation_id:
                raise APIError(f"ID de variation introuvable pour le produit {product_id}")
        except Exception as e:
            raise APIError(f"Erreur lors de la récupération des variations pour {product_id}: {str(e)}")
        
        # Préparer les données pour la mise à jour du stock
        changes = [
            {
                "type": "PHYSICAL_COUNT",
                "physical_count": {
                    "catalog_object_id": variation_id,
                    "location_id": location_id,
                    "quantity": str(quantity),
                    "state": "IN_STOCK",
                    "occurred_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                }
            }
        ]
        
        payload = {
            "idempotency_key": idempotency_key,
            "changes": changes
        }
        
        # Appel à l'API Square
        response = await self.post("/v2/inventory/changes/batch-create", json=payload)
        
        # Vérifier la réponse
        if "counts" not in response:
            raise APIError(f"Mise à jour du stock échouée pour le produit {product_id}")
        
        return response
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Récupère la liste des catégories de produits.
        
        Returns:
            Liste des catégories
        """
        # Construction du payload pour l'API
        payload = {
            "object_types": ["CATEGORY"],
            "limit": 200  # Maximum pour récupérer toutes les catégories
        }
        
        # Appel à l'API Square
        response = await self.post("/v2/catalog/search", json=payload)
        
        # Extraction des catégories
        categories = []
        for obj in response.get("objects", []):
            if obj.get("type") == "CATEGORY":
                categories.append(obj)
        
        return categories
    
    async def get_discounts(self) -> List[Dict[str, Any]]:
        """Récupère la liste des remises et promotions actives.
        
        Returns:
            Liste des remises
        """
        # Construction du payload pour l'API
        payload = {
            "object_types": ["DISCOUNT"],
            "limit": 100
        }
        
        # Appel à l'API Square
        response = await self.post("/v2/catalog/search", json=payload)
        
        # Extraction des remises
        discounts = []
        for obj in response.get("objects", []):
            if obj.get("type") == "DISCOUNT":
                discounts.append(obj)
        
        return discounts
    
    async def create_discount(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle remise ou promotion.
        
        Args:
            data: Données de la remise (nom, montant, conditions, etc.)
            
        Returns:
            Remise créée
        """
        # Validation des données minimales
        required_fields = ["name", "amount"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Champ requis manquant: {field}",
                    errors={"required_fields": required_fields}
                )
        
        # Générer une clé d'idempotence unique
        idempotency_key = f"discount_{int(datetime.now().timestamp())}"
        
        # Déterminer le type de remise (pourcentage ou montant fixe)
        discount_type = "FIXED_PERCENTAGE"
        amount_value = data["amount"]
        
        if "type" in data:
            if data["type"].lower() == "fixed" or data["type"].lower() == "amount":
                discount_type = "FIXED_AMOUNT"
        
        # Préparer les données pour l'API
        discount_data = {
            "name": data["name"],
            "discount_type": discount_type
        }
        
        # Configuration selon le type de remise
        if discount_type == "FIXED_PERCENTAGE":
            discount_data["percentage"] = str(amount_value)
        else:
            discount_data["amount_money"] = {
                "amount": int(float(amount_value) * 100),
                "currency": "EUR"  # Utiliser l'euro comme devise par défaut
            }
        
        # Ajouter des champs optionnels
        if "pin_required" in data:
            discount_data["pin_required"] = data["pin_required"]
        
        if "label_color" in data:
            discount_data["label_color"] = data["label_color"]
        
        # Créer l'objet complet
        object_data = {
            "type": "DISCOUNT",
            "discount_data": discount_data
        }
        
        payload = {
            "idempotency_key": idempotency_key,
            "object": object_data
        }
        
        # Appel à l'API Square
        response = await self.post("/v2/catalog/object", json=payload)
        
        # Vérifier la réponse
        if "object" not in response:
            raise APIError("Création de la remise échouée")
        
        return response["object"]
    
    async def get_customers(self, 
                          limit: int = 100,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """Récupère la liste des clients.
        
        Args:
            limit: Nombre maximum de clients à récupérer
            offset: Offset pour la pagination
            
        Returns:
            Liste des clients
        """
        # Paramètres de la requête
        params = {
            "limit": limit,
            "cursor": str(offset) if offset > 0 else None
        }
        
        # Retirer les paramètres None
        params = {k: v for k, v in params.items() if v is not None}
        
        # Appel à l'API Square
        response = await self.get("/v2/customers", params=params)
        
        # Extraction des clients
        customers = response.get("customers", [])
        
        return customers
    
    async def get_sales_summary(self,
                              start_date: Union[datetime, str],
                              end_date: Optional[Union[datetime, str]] = None,
                              group_by: Optional[str] = None) -> Dict[str, Any]:
        """Récupère un résumé des ventes sur une période donnée.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période (par défaut: maintenant)
            group_by: Regroupement des données (ex: "day", "category", "product")
            
        Returns:
            Résumé des ventes
        """
        # Convertir les dates en objets datetime si nécessaire
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = parse_date(end_date)
        
        # Format de la date pour l'API Square: RFC 3339
        start_rfc = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_rfc = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Récupérer l'ID de l'emplacement depuis la configuration
        location_id = self.config['api']['location_id']
        
        # Construction du payload pour l'API
        payload = {
            "location_ids": [location_id],
            "time_range": {
                "start_time": start_rfc,
                "end_time": end_rfc
            }
        }
        
        # Ajouter le regroupement si spécifié
        if group_by:
            if group_by.lower() == "day":
                payload["granularity"] = "DAY"
            elif group_by.lower() == "category":
                payload["query"] = {
                    "group_by_category_id": {
                        "limit": 100  # Nombre max de catégories
                    }
                }
            elif group_by.lower() == "product":
                payload["query"] = {
                    "group_by_item_id": {
                        "limit": 100  # Nombre max de produits
                    }
                }
        
        # Appel à l'API Square
        response = await self.post("/v2/sales/summary", json=payload)
        
        # Récupérer les résultats
        summary_data = response.get("summary", {})
        
        # Formater les résultats
        summary = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        }
        
        # Ajouter les totaux
        if "total_money" in summary_data:
            amount = summary_data["total_money"].get("amount", 0)
            summary["total_sales"] = amount / 100  # Convertir les centimes en euros
        
        if "total_transaction_count" in summary_data:
            summary["total_transactions"] = summary_data["total_transaction_count"]
        
        if "total_sales" in summary and "total_transactions" in summary and summary["total_transactions"] > 0:
            summary["average_sale"] = summary["total_sales"] / summary["total_transactions"]
        
        # Ajouter le regroupement si disponible
        if group_by and "groups" in response:
            groups_data = {}
            
            for group in response["groups"]:
                group_id = group.get("id", "unknown")
                group_total = group.get("total_money", {}).get("amount", 0) / 100
                group_count = group.get("total_transaction_count", 0)
                
                groups_data[group_id] = {
                    "total": group_total,
                    "count": group_count
                }
            
            summary["grouped_by"] = group_by
            summary["groups"] = groups_data
        
        return summary