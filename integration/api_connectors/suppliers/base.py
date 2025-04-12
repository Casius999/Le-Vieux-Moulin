"""Module contenant la classe de base pour les connecteurs de fournisseurs.

Ce module définit BaseSupplierConnector, la classe parente de tous les connecteurs
spécifiques pour les systèmes d'approvisionnement des fournisseurs.
"""

import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from ..base_connector import BaseConnector

logger = logging.getLogger(__name__)

class BaseSupplierConnector(BaseConnector):
    """Classe de base pour les connecteurs de fournisseurs.
    
    Cette classe définit l'interface commune pour interagir avec différents
    systèmes d'approvisionnement des fournisseurs.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un produit spécifique.
        
        Args:
            product_id: Identifiant du produit
            
        Returns:
            Détails du produit
        """
        pass
    
    @abstractmethod
    async def check_product_availability(self, 
                                      product_ids: List[str]) -> Dict[str, Any]:
        """Vérifie la disponibilité de plusieurs produits.
        
        Args:
            product_ids: Liste des identifiants de produits
            
        Returns:
            Disponibilité des produits demandés
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une commande spécifique.
        
        Args:
            order_id: Identifiant de la commande
            
        Returns:
            Détails de la commande
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_delivery_schedule(self) -> Dict[str, Any]:
        """Récupère le planning de livraison disponible.
        
        Returns:
            Planning de livraison (jours, heures, etc.)
        """
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Récupère les informations du compte client.
        
        Returns:
            Informations du compte (solde, limite de crédit, etc.)
        """
        pass