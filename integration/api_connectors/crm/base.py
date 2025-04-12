"""Module contenant la classe de base pour les connecteurs CRM.

Ce module définit BaseCRMConnector, la classe parente de tous les connecteurs
spécifiques pour les systèmes de gestion de la relation client (CRM).
"""

import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from ..base_connector import BaseConnector

logger = logging.getLogger(__name__)

class BaseCRMConnector(BaseConnector):
    """Classe de base pour les connecteurs CRM.
    
    Cette classe définit l'interface commune pour interagir avec différents
    systèmes de gestion de la relation client (CRM).
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Récupère les détails d'un contact spécifique.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Détails du contact
        """
        pass
    
    @abstractmethod
    async def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau contact.
        
        Args:
            data: Données du contact (nom, email, téléphone, etc.)
            
        Returns:
            Contact créé
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Supprime un contact.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Confirmation de la suppression
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_loyalty_points(self, contact_id: str) -> Dict[str, Any]:
        """Récupère les points de fidélité d'un contact.
        
        Args:
            contact_id: Identifiant du contact
            
        Returns:
            Informations sur les points de fidélité
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une campagne marketing.
        
        Args:
            data: Données de la campagne (nom, type, contenu, audience, etc.)
            
        Returns:
            Campagne créée
        """
        pass
    
    @abstractmethod
    async def get_segments(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les segments de clients disponibles.
        
        Args:
            limit: Nombre maximum de segments à récupérer
            
        Returns:
            Liste des segments
        """
        pass