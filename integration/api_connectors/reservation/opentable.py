"""Connecteur pour l'API OpenTable.

Ce module fournit une implémentation du connecteur pour interagir
avec l'API de la plateforme de réservation OpenTable.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import BaseReservationConnector
from ..common.exceptions import APIError, ValidationError, ConfigurationError
from ..common.utils import parse_date

logger = logging.getLogger(__name__)

class OpenTableConnector(BaseReservationConnector):
    """Connecteur pour l'API OpenTable.
    
    Cette classe implémente l'interface BaseReservationConnector pour
    interagir avec la plateforme de réservation OpenTable.
    """
    
    def _validate_config(self) -> None:
        """Valide la configuration spécifique à OpenTable."""
        super()._validate_config()
        
        # Vérifier la présence des champs spécifiques
        api_config = self.config.get('api', {})
        if 'restaurant_id' not in api_config:
            raise ConfigurationError("ID du restaurant OpenTable manquant", "api.restaurant_id")
    
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API OpenTable.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        try:
            # Tentative d'appel à un endpoint simple
            await self.get("/api/v3/restaurant/status")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé OpenTable: {str(e)}")
            return False
    
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
        # Convertir les dates au format ISO 8601 si nécessaire
        if isinstance(start_date, datetime):
            start_date = start_date.isoformat()
        
        if end_date is None:
            # Par défaut, récupérer les réservations pour les 7 prochains jours
            end_date = (datetime.now() + timedelta(days=7)).isoformat()
        elif isinstance(end_date, datetime):
            end_date = end_date.isoformat()
        
        # Construction des paramètres de la requête
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": limit
        }
        
        # Ajouter le statut si spécifié
        if status:
            params["status"] = status
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.get(f"/api/v3/restaurant/{restaurant_id}/reservations", params=params)
        
        # Extraire les réservations
        if "reservations" not in response:
            raise APIError("Format de réponse inattendu: champ 'reservations' manquant")
        
        return response["reservations"]
    
    async def get_reservation_details(self, reservation_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une réservation spécifique.
        
        Args:
            reservation_id: Identifiant de la réservation
            
        Returns:
            Détails de la réservation
        """
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.get(f"/api/v3/restaurant/{restaurant_id}/reservations/{reservation_id}")
        
        # Vérifier la présence des détails
        if "reservation" not in response:
            raise APIError(f"Réservation {reservation_id} non trouvée")
        
        return response["reservation"]
    
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
        # Préparer les données pour la mise à jour
        update_data = data.copy()
        
        # Gérer les conversions de dates si nécessaire
        if "date" in update_data and isinstance(update_data["date"], datetime):
            update_data["date"] = update_data["date"].strftime("%Y-%m-%d")
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.put(
            f"/api/v3/restaurant/{restaurant_id}/reservations/{reservation_id}",
            json=update_data
        )
        
        # Vérifier la présence des détails mis à jour
        if "reservation" not in response:
            raise APIError(f"Mise à jour de la réservation {reservation_id} échouée")
        
        return response["reservation"]
    
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
        # Préparer les données pour l'annulation
        cancel_data = {"status": "CANCELLED"}
        
        if reason:
            cancel_data["cancellation_reason"] = reason
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.put(
            f"/api/v3/restaurant/{restaurant_id}/reservations/{reservation_id}/status",
            json=cancel_data
        )
        
        # Vérifier la présence de la confirmation
        if "reservation" not in response:
            raise APIError(f"Annulation de la réservation {reservation_id} échouée")
        
        return response["reservation"]
    
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
        # Convertir la date au format ISO 8601 si nécessaire
        if isinstance(date, datetime):
            date_str = date.strftime("%Y-%m-%d")
        else:
            # Extraire la partie date si une date+heure est fournie
            date_str = date.split("T")[0] if "T" in date else date
        
        # Construction des paramètres de la requête
        params = {
            "date": date_str,
            "party_size": party_size
        }
        
        # Ajouter les heures de début et de fin si spécifiées
        if time_start:
            params["time_start"] = time_start
        
        if time_end:
            params["time_end"] = time_end
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.get(f"/api/v3/restaurant/{restaurant_id}/availability", params=params)
        
        # Extraire les créneaux disponibles
        if "time_slots" not in response:
            raise APIError("Format de réponse inattendu: champ 'time_slots' manquant")
        
        return response["time_slots"]
    
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
        # Convertir la date au format ISO 8601 si nécessaire
        if isinstance(date, datetime):
            date_str = date.strftime("%Y-%m-%d")
        else:
            # Extraire la partie date si une date+heure est fournie
            date_str = date.split("T")[0] if "T" in date else date
        
        # Préparer les données pour la mise à jour
        update_data = availability.copy()
        update_data["date"] = date_str
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.put(
            f"/api/v3/restaurant/{restaurant_id}/availability",
            json=update_data
        )
        
        # Vérifier la présence de la confirmation
        if "availability" not in response:
            raise APIError(f"Mise à jour des disponibilités pour {date_str} échouée")
        
        return response["availability"]
    
    async def create_reservation(self,
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle réservation.
        
        Args:
            data: Données de la réservation (date, heure, nb personnes, client, etc.)
            
        Returns:
            Réservation créée
        """
        # Validation des données minimales
        required_fields = ["date", "time", "party_size", "customer"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Champ requis manquant: {field}",
                    errors={"required_fields": required_fields}
                )
        
        # Validation des données du client
        customer = data["customer"]
        customer_required = ["first_name", "last_name", "email"]
        for field in customer_required:
            if field not in customer:
                raise ValidationError(
                    f"Champ client requis manquant: {field}",
                    errors={"required_customer_fields": customer_required}
                )
        
        # Préparer les données pour la création
        create_data = data.copy()
        
        # Gérer les conversions de dates si nécessaire
        if "date" in create_data and isinstance(create_data["date"], datetime):
            create_data["date"] = create_data["date"].strftime("%Y-%m-%d")
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.post(f"/api/v3/restaurant/{restaurant_id}/reservations", json=create_data)
        
        # Vérifier la présence de la réservation créée
        if "reservation" not in response:
            raise APIError("Création de la réservation échouée")
        
        return response["reservation"]
    
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Récupère les informations d'un client.
        
        Args:
            customer_id: Identifiant du client
            
        Returns:
            Informations du client
        """
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.get(f"/api/v3/restaurant/{restaurant_id}/customers/{customer_id}")
        
        # Vérifier la présence des informations client
        if "customer" not in response:
            raise APIError(f"Client {customer_id} non trouvé")
        
        return response["customer"]
    
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
        # Construction des paramètres de la requête
        params = {
            "query": search_term,
            "per_page": limit
        }
        
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.get(f"/api/v3/restaurant/{restaurant_id}/customers/search", params=params)
        
        # Extraire les résultats de recherche
        if "customers" not in response:
            raise APIError("Format de réponse inattendu: champ 'customers' manquant")
        
        return response["customers"]
    
    async def get_restaurant_info(self) -> Dict[str, Any]:
        """Récupère les informations du restaurant sur la plateforme.
        
        Returns:
            Informations du restaurant (horaires, adresse, note, etc.)
        """
        # Appel à l'API OpenTable
        restaurant_id = self.config['api']['restaurant_id']
        response = await self.get(f"/api/v3/restaurant/{restaurant_id}/profile")
        
        # Vérifier la présence des informations restaurant
        if "restaurant" not in response:
            raise APIError(f"Restaurant {restaurant_id} non trouvé")
        
        return response["restaurant"]