"""Connecteur pour l'API Lightspeed Retail POS.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API de la caisse enregistreuse Lightspeed Retail.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BasePOSConnector
from ..common.exceptions import APIError, ValidationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class LightspeedConnector(BasePOSConnector):
    """Connecteur pour l'API Lightspeed Retail POS.
    
    Cette classe implémente l'interface BasePOSConnector pour
    interagir avec le système de caisse Lightspeed.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à Lightspeed."""
        super()._validate_config()
        
        # Vérifier la présence de l'ID de compte
        if 'account_id' not in self.config['api']:
            raise ConfigurationError("ID de compte Lightspeed manquant", "api.account_id")
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API Lightspeed.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/Info")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé Lightspeed: {str(e)}")
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
        
        # Format de la date pour l'API Lightspeed: ISO 8601
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()
        
        # Construction des paramètres de la requête
        params = {
            "timeStamp": f">,[{start_iso},{end_iso}]",
            "limit": limit,
            "sort": "timeStamp"
        }
        
        if status:
            if status.lower() == "completed":
                params["completed"] = "true"
            elif status.lower() == "refunded":
                params["refundedSaleID"] = ">"
        
        # Récupérer l'ID du compte depuis la configuration
        account_id = self.config['api']['account_id']
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/Sale", params=params)
        
        # Extraction des transactions
        sales = response.get("Sale", [])
        if not isinstance(sales, list):
            # Si une seule transaction est retournée, la convertir en liste
            sales = [sales]
        
        return sales
    
    async def get_transaction_details(self, transaction_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une transaction spécifique.
        
        Args:
            transaction_id: Identifiant de la transaction
            
        Returns:
            Détails de la transaction
        """
        account_id = self.config['api']['account_id']
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/Sale/{transaction_id}")
        
        # Vérifier la présence de la transaction
        if "Sale" not in response:
            raise APIError(f"Transaction {transaction_id} non trouvée")
        
        return response["Sale"]
    
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
        account_id = self.config['api']['account_id']
        
        # Construction des paramètres de la requête
        params = {
            "limit": limit,
            "sort": "description"
        }
        
        # Filtre par catégorie si spécifié
        if category:
            params["categoryID"] = category
        
        # Filtre par date de mise à jour si spécifié
        if updated_since:
            if isinstance(updated_since, str):
                updated_since = parse_date(updated_since)
            params["timeStamp"] = f">={updated_since.isoformat()}"
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/Item", params=params)
        
        # Extraction des produits
        items = response.get("Item", [])
        if not isinstance(items, list):
            # Si un seul produit est retourné, le convertir en liste
            items = [items]
        
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
        account_id = self.config['api']['account_id']
        
        # Validation des données
        valid_fields = {
            "description", "tax", "defaultCost", "departmentID", "categoryID",
            "defaultPrice", "itemType", "taxClassID", "seasonID", "manufacturerID",
            "Prices", "ItemShops"
        }
        
        update_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Si le dictionnaire est vide, lever une erreur
        if not update_data:
            raise ValidationError(
                "Aucun champ valide pour la mise à jour du produit",
                errors={"valid_fields": list(valid_fields)}
            )
        
        # Préparer les données pour l'API
        payload = {"Item": update_data}
        
        # Appel à l'API Lightspeed
        response = await self.put(f"/Account/{account_id}/Item/{product_id}", json=payload)
        
        # Vérifier la présence du produit dans la réponse
        if "Item" not in response:
            raise APIError(f"Produit {product_id} non trouvé ou mise à jour échouée")
        
        return response["Item"]
    
    async def get_inventory(self,
                          product_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Récupère l'état des stocks.
        
        Args:
            product_ids: Liste des IDs de produits à récupérer (optionnel, tous si None)
            
        Returns:
            Liste des niveaux de stock
        """
        account_id = self.config['api']['account_id']
        
        # Construction des paramètres de la requête
        params = {}
        
        # Filtre par produits si spécifié
        if product_ids:
            if len(product_ids) == 1:
                params["itemID"] = product_ids[0]
            else:
                # Format spécifique pour les filtres multi-valeurs
                ids_filter = ",".join(product_ids)
                params["itemID"] = f"IN,[{ids_filter}]"
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/ItemQuantity", params=params)
        
        # Extraction des données de stock
        inventory = response.get("ItemQuantity", [])
        if not isinstance(inventory, list):
            # Si un seul élément est retourné, le convertir en liste
            inventory = [inventory]
        
        return inventory
    
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
        account_id = self.config['api']['account_id']
        
        # Récupérer l'ID de l'entrée de stock pour ce produit
        inventory_query = {"itemID": product_id}
        if location_id:
            inventory_query["shopID"] = location_id
        
        inventory_response = await self.get(f"/Account/{account_id}/ItemQuantity", params=inventory_query)
        
        # Extraction des données de stock
        inventory_items = inventory_response.get("ItemQuantity", [])
        if not isinstance(inventory_items, list):
            inventory_items = [inventory_items]
        
        if not inventory_items:
            raise APIError(f"Aucune entrée de stock trouvée pour le produit {product_id}")
        
        # Utiliser la première entrée (ou la seule) correspondant au filtre
        inventory_item = inventory_items[0]
        inventory_id = inventory_item.get("itemQuantityID")
        
        if not inventory_id:
            raise APIError(f"ID d'entrée de stock introuvable pour le produit {product_id}")
        
        # Préparer les données pour la mise à jour
        update_data = {
            "ItemQuantity": {
                "quantity": str(quantity)  # Lightspeed attend une chaîne
            }
        }
        
        # Appel à l'API Lightspeed pour mettre à jour le stock
        response = await self.put(f"/Account/{account_id}/ItemQuantity/{inventory_id}", json=update_data)
        
        # Vérifier la réponse
        if "ItemQuantity" not in response:
            raise APIError(f"Mise à jour du stock échouée pour le produit {product_id}")
        
        return response["ItemQuantity"]
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Récupère la liste des catégories de produits.
        
        Returns:
            Liste des catégories
        """
        account_id = self.config['api']['account_id']
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/Category")
        
        # Extraction des catégories
        categories = response.get("Category", [])
        if not isinstance(categories, list):
            # Si une seule catégorie est retournée, la convertir en liste
            categories = [categories]
        
        return categories
    
    async def get_discounts(self) -> List[Dict[str, Any]]:
        """Récupère la liste des remises et promotions actives.
        
        Returns:
            Liste des remises
        """
        account_id = self.config['api']['account_id']
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/Sale/Discount")
        
        # Extraction des remises
        discounts = response.get("Discount", [])
        if not isinstance(discounts, list):
            # Si une seule remise est retournée, la convertir en liste
            discounts = [discounts]
        
        return discounts
    
    async def create_discount(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle remise ou promotion.
        
        Args:
            data: Données de la remise (nom, montant, conditions, etc.)
            
        Returns:
            Remise créée
        """
        account_id = self.config['api']['account_id']
        
        # Validation des données minimales
        required_fields = ["name", "amount", "type"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Champ requis manquant: {field}",
                    errors={"required_fields": required_fields}
                )
        
        # Préparer les données pour l'API
        payload = {"Discount": data}
        
        # Appel à l'API Lightspeed
        response = await self.post(f"/Account/{account_id}/Sale/Discount", json=payload)
        
        # Vérifier la réponse
        if "Discount" not in response:
            raise APIError("Création de la remise échouée")
        
        return response["Discount"]
    
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
        account_id = self.config['api']['account_id']
        
        # Construction des paramètres de la requête
        params = {
            "limit": limit,
            "offset": offset,
            "sort": "lastName"
        }
        
        # Appel à l'API Lightspeed
        response = await self.get(f"/Account/{account_id}/Customer", params=params)
        
        # Extraction des clients
        customers = response.get("Customer", [])
        if not isinstance(customers, list):
            # Si un seul client est retourné, le convertir en liste
            customers = [customers]
        
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
        # Obtenir d'abord les transactions pour la période
        transactions = await self.get_transactions(
            start_date=start_date,
            end_date=end_date,
            status="completed",
            limit=1000  # Augmenter la limite pour obtenir plus de données
        )
        
        # Résumé de base
        summary = {
            "period": {
                "start": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                "end": end_date.isoformat() if isinstance(end_date, datetime) else end_date or datetime.now().isoformat(),
            },
            "total_sales": 0,
            "total_transactions": len(transactions),
            "average_sale": 0,
        }
        
        # Calculer les totaux
        if transactions:
            total_amount = sum(float(t.get("total", 0)) for t in transactions)
            summary["total_sales"] = total_amount
            summary["average_sale"] = total_amount / len(transactions) if transactions else 0
        
        # Regroupement par groupe si demandé
        if group_by:
            grouped_data = {}
            
            if group_by == "day":
                # Regrouper par jour
                for transaction in transactions:
                    if "timeStamp" in transaction:
                        # Extraire la date (partie avant l'heure)
                        date_str = transaction["timeStamp"].split("T")[0]
                        grouped_data.setdefault(date_str, {"total": 0, "count": 0})
                        grouped_data[date_str]["total"] += float(transaction.get("total", 0))
                        grouped_data[date_str]["count"] += 1
            
            elif group_by == "category" or group_by == "product":
                # Pour ces regroupements, il faut obtenir les détails de chaque transaction
                detailed_transactions = []
                for transaction in transactions:
                    details = await self.get_transaction_details(transaction["saleID"])
                    detailed_transactions.append(details)
                
                # Traiter selon le type de regroupement
                if group_by == "category":
                    # Regrouper par catégorie
                    for detail in detailed_transactions:
                        for line in detail.get("SaleLines", {}).get("SaleLine", []):
                            category_id = line.get("categoryID")
                            if category_id:
                                grouped_data.setdefault(category_id, {"total": 0, "count": 0})
                                grouped_data[category_id]["total"] += float(line.get("total", 0))
                                grouped_data[category_id]["count"] += 1
                
                elif group_by == "product":
                    # Regrouper par produit
                    for detail in detailed_transactions:
                        for line in detail.get("SaleLines", {}).get("SaleLine", []):
                            item_id = line.get("itemID")
                            if item_id:
                                grouped_data.setdefault(item_id, {"total": 0, "count": 0})
                                grouped_data[item_id]["total"] += float(line.get("total", 0))
                                grouped_data[item_id]["count"] += 1
            
            # Ajouter le regroupement au résumé
            summary["grouped_by"] = group_by
            summary["groups"] = grouped_data
        
        return summary