"""Module contenant la classe de base pour les connecteurs de réservation.

Ce module définit BaseReservationConnector, la classe parente de tous les connecteurs
spécifiques pour les systèmes de réservation en ligne.
"""

import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from ..base_connector import BaseConnector

logger = logging.getLogger(__name__)

class BaseReservationConnector(BaseConnector):
    """Classe de base pour les connecteurs de systèmes de réservation.
    
    Cette classe définit l'interface commune pour interagir avec différents
    systèmes de réservation en ligne (TheFork, OpenTable, etc.).
    """
    
    @abstractmethod
    async def get_reservations(self, 
                             start_date: Union[datetime, str],
                             end_date: Optional[Union[datetime, str]] = None,
                             status: Optional[str] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les réservations sur une période donnée.
        
        Args:
            start_date: Date de début de la période (datetime ou chaîne ISO 8601)
            end_date: Date de fin de la période (datetime ou chaîne ISO 8601, par défaut: J+7)
            status: Statut des réservations à récupérer (ex: "confirmed", "cancelled")
            limit: Nombre maximum de réservations à récupérer
            
        Returns:
            Liste des réservations
        """
        pass
    
    @abstractmethod
    async def get_reservation_details(self, reservation_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une réservation spécifique.
        
        Args:
            reservation_id: Identifiant de la réservation
            
        Returns:
            Détails de la réservation
        """
        pass
    
    @abstractmethod
    async def update_reservation(self, 
                              reservation_id: str,
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une réservation existante.
        
        Args:
            reservation_id: Identifiant de la réservation
            data: Données à mettre à jour (date, heure, nombre de personnes, etc.)
            
        Returns:
            Réservation mise à jour
        """
        pass
    
    @abstractmethod
    async def cancel_reservation(self, 
                              reservation_id: str,
                              reason: Optional[str] = None) -> Dict[str, Any]:
        """Annule une réservation existante.
        
        Args:
            reservation_id: Identifiant de la réservation
            reason: Raison de l'annulation (optionnel)
            
        Returns:
            Confirmation de l'annulation
        """
        pass
    
    @abstractmethod
    async def get_availability(self,
                            date: Union[datetime, str],
                            party_size: int,
                            time_start: Optional[str] = None,
                            time_end: Optional[str] = None) -> List[Dict[str, Any]]:
        """Récupère les disponibilités pour une date et un nombre de personnes.
        
        Args:
            date: Date pour vérifier les disponibilités
            party_size: Nombre de personnes
            time_start: Heure de début (format HH:MM, optionnel)
            time_end: Heure de fin (format HH:MM, optionnel)
            
        Returns:
            Liste des créneaux disponibles
        """
        pass
    
    @abstractmethod
    async def update_availability(self,
                               date: Union[datetime, str],
                               availability: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour les disponibilités pour une date spécifique.
        
        Args:
            date: Date pour mettre à jour les disponibilités
            availability: Informations de disponibilité (créneaux, capacité, etc.)
            
        Returns:
            Confirmation de la mise à jour
        """
        pass
    
    @abstractmethod
    async def create_reservation(self,
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle réservation.
        
        Args:
            data: Données de la réservation (date, heure, nb personnes, client, etc.)
            
        Returns:
            Réservation créée
        """
        pass
    
    @abstractmethod
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Récupère les informations d'un client.
        
        Args:
            customer_id: Identifiant du client
            
        Returns:
            Informations du client
        """
        pass
    
    @abstractmethod
    async def search_customers(self, 
                            search_term: str,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche des clients par terme de recherche.
        
        Args:
            search_term: Terme de recherche (nom, email, téléphone, etc.)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des clients correspondant au terme de recherche
        """
        pass
    
    @abstractmethod
    async def get_restaurant_info(self) -> Dict[str, Any]:
        """Récupère les informations du restaurant sur la plateforme.
        
        Returns:
            Informations du restaurant (horaires, adresse, note, etc.)
        """
        pass