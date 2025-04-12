"""Module contenant la classe de base pour les connecteurs de caisses enregistreuses (POS).

Ce module définit BasePOSConnector, la classe parente de tous les connecteurs
spécifiques pour les systèmes de caisse enregistreuse (Point of Sale).
"""

import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from ..base_connector import BaseConnector

logger = logging.getLogger(__name__)

class BasePOSConnector(BaseConnector):
    """Classe de base pour les connecteurs de caisses enregistreuses.
    
    Cette classe définit l'interface commune pour interagir avec différents
    systèmes de caisse enregistreuse (POS).
    """
    
    @abstractmethod
    async def get_transactions(self, 
                             start_date: Union[datetime, str],
                             end_date: Optional[Union[datetime, str]] = None,
                             status: Optional[str] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les transactions sur une période donnée.
        
        Args:
            start_date: Date de début de la période (datetime ou chaîne ISO 8601)
            end_date: Date de fin de la période (datetime ou chaîne ISO 8601, par défaut: maintenant)
            status: Statut des transactions à récupérer (ex: "completed", "refunded")
            limit: Nombre maximum de transactions à récupérer
            
        Returns:
            Liste des transactions
        """
        pass
    
    @abstractmethod
    async def get_transaction_details(self, transaction_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une transaction spécifique.
        
        Args:
            transaction_id: Identifiant de la transaction
            
        Returns:
            Détails de la transaction
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_inventory(self,
                          product_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Récupère l'état des stocks.
        
        Args:
            product_ids: Liste des IDs de produits à récupérer (optionnel, tous si None)
            
        Returns:
            Liste des niveaux de stock
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Récupère la liste des catégories de produits.
        
        Returns:
            Liste des catégories
        """
        pass
    
    @abstractmethod
    async def get_discounts(self) -> List[Dict[str, Any]]:
        """Récupère la liste des remises et promotions actives.
        
        Returns:
            Liste des remises
        """
        pass
    
    @abstractmethod
    async def create_discount(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle remise ou promotion.
        
        Args:
            data: Données de la remise (nom, montant, conditions, etc.)
            
        Returns:
            Remise créée
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass