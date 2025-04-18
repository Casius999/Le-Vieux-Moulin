#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client pour intégration avec le système de réservation.

Ce module fournit une interface pour récupérer les informations de réservation
à prendre en compte dans l'optimisation des plannings de personnel.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from ..config import INTEGRATION

# Configurer le logger
logger = logging.getLogger(__name__)


class ReservationClientError(Exception):
    """Exception spécifique pour les erreurs du client de réservation."""
    pass


class ReservationClient:
    """
    Client pour communiquer avec l'API du système de réservation.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialise le client de réservation.
        
        Args:
            base_url: URL de base de l'API de réservation (optionnel, utilise la config par défaut)
            timeout: Timeout en secondes pour les requêtes
            max_retries: Nombre maximum de tentatives en cas d'échec
            retry_delay: Délai entre les tentatives en secondes
        """
        self.base_url = base_url or INTEGRATION.get('reservation_api_url')
        if not self.base_url:
            logger.warning("URL de l'API de réservation non définie, utilisation du mode simulation")
            self.simulation_mode = True
        else:
            self.simulation_mode = False
            
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Vérifier la connexion à l'initialisation
        if not self.simulation_mode:
            self._check_connection()
    
    def _check_connection(self) -> bool:
        """
        Vérifie la connexion avec le serveur de réservation.
        
        Returns:
            True si la connexion est établie, False sinon
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                logger.info(f"Connexion établie avec le système de réservation: {self.base_url}")
                return True
            else:
                logger.warning(
                    f"Le système de réservation a répondu avec un code d'erreur: {response.status_code}"
                )
                self.simulation_mode = True
                return False
        except RequestException as e:
            logger.error(f"Impossible de se connecter au système de réservation: {str(e)}")
            self.simulation_mode = True
            return False
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Effectue une requête HTTP vers l'API de réservation avec gestion des retries.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Point d'entrée de l'API (sans l'URL de base)
            params: Paramètres de requête (pour GET)
            data: Données à envoyer (pour POST/PUT)
            
        Returns:
            Données de réponse (JSON)
            
        Raises:
            ReservationClientError: En cas d'erreur après toutes les tentatives
        """
        if self.simulation_mode:
            logger.info(f"Mode simulation: Simulation de requête {method} {endpoint}")
            return self._simulate_response(method, endpoint, params, data)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, params=params, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = requests.post(url, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Méthode HTTP non supportée: {method}")
                
                # Vérifier le code de statut
                response.raise_for_status()
                
                # Tenter de parser la réponse JSON
                try:
                    return response.json()
                except json.JSONDecodeError:
                    raise ReservationClientError(f"Réponse non JSON: {response.text}")
                
            except Timeout:
                logger.warning(f"Timeout lors de la requête à {url} (tentative {attempt+1}/{self.max_retries})")
            except ConnectionError:
                logger.warning(f"Erreur de connexion à {url} (tentative {attempt+1}/{self.max_retries})")
            except RequestException as e:
                logger.warning(f"Erreur lors de la requête à {url}: {str(e)} (tentative {attempt+1}/{self.max_retries})")
            
            # Attendre avant de réessayer (sauf pour la dernière tentative)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        # Si nous arrivons ici, toutes les tentatives ont échoué
        logger.error(f"Échec de la requête après {self.max_retries} tentatives, passage en mode simulation")
        self.simulation_mode = True
        return self._simulate_response(method, endpoint, params, data)
    
    def _simulate_response(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Simule une réponse pour le mode simulation.
        
        Args:
            method: Méthode HTTP
            endpoint: Point d'entrée
            params: Paramètres
            data: Données
            
        Returns:
            Données simulées
        """
        if endpoint.startswith("reservations/upcoming"):
            # Extraire les dates des paramètres
            start_date = datetime.now()
            end_date = datetime.now() + timedelta(days=7)
            
            if params:
                if 'start_date' in params:
                    try:
                        start_date = datetime.fromisoformat(params['start_date'])
                    except ValueError:
                        pass
                
                if 'end_date' in params:
                    try:
                        end_date = datetime.fromisoformat(params['end_date'])
                    except ValueError:
                        pass
            
            return self._generate_mock_reservations(start_date, end_date)
        
        elif endpoint.startswith("reservations/groups"):
            start_date = datetime.now()
            end_date = datetime.now() + timedelta(days=14)
            
            if params:
                if 'start_date' in params:
                    try:
                        start_date = datetime.fromisoformat(params['start_date'])
                    except ValueError:
                        pass
                
                if 'end_date' in params:
                    try:
                        end_date = datetime.fromisoformat(params['end_date'])
                    except ValueError:
                        pass
            
            return self._generate_mock_group_reservations(start_date, end_date)
        
        # Réponse par défaut pour les autres endpoints
        return {"status": "success", "message": "Réponse simulée", "data": {}}
    
    def get_upcoming_reservations(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """
        Récupère les réservations à venir pour une période donnée.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            
        Returns:
            Réservations par jour
            
        Raises:
            ReservationClientError: En cas d'erreur
        """
        # Préparer les paramètres
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        try:
            # Appel à l'API
            response = self._make_request('GET', 'reservations/upcoming', params=params)
            
            # Traiter et retourner les réservations
            return self._process_reservations(response)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réservations: {str(e)}")
            # En cas d'erreur, générer des réservations factices
            return self._generate_mock_reservations(start_date, end_date)
    
    def get_group_reservations(
        self,
        start_date: datetime,
        end_date: datetime,
        min_guests: int = 8
    ) -> Dict[str, List[Dict]]:
        """
        Récupère les réservations de groupe pour une période donnée.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            min_guests: Nombre minimum d'invités pour considérer comme groupe
            
        Returns:
            Réservations de groupe par jour
            
        Raises:
            ReservationClientError: En cas d'erreur
        """
        # Préparer les paramètres
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "min_guests": min_guests
        }
        
        try:
            # Appel à l'API
            response = self._make_request('GET', 'reservations/groups', params=params)
            
            # Traiter et retourner les réservations
            return self._process_reservations(response)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réservations de groupe: {str(e)}")
            # En cas d'erreur, générer des réservations factices
            return self._generate_mock_group_reservations(start_date, end_date)
    
    def get_special_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """
        Récupère les événements spéciaux pour une période donnée.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            
        Returns:
            Événements spéciaux par jour
            
        Raises:
            ReservationClientError: En cas d'erreur
        """
        # Préparer les paramètres
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        try:
            # Appel à l'API
            response = self._make_request('GET', 'events/special', params=params)
            
            # Traiter et retourner les événements
            return self._process_events(response)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des événements spéciaux: {str(e)}")
            # En cas d'erreur, générer des événements factices
            return self._generate_mock_special_events(start_date, end_date)
    
    def get_estimated_walk_ins(
        self,
        date: datetime
    ) -> Dict:
        """
        Récupère une estimation des clients sans réservation.
        
        Args:
            date: Date pour laquelle obtenir l'estimation
            
        Returns:
            Estimation par tranche horaire
            
        Raises:
            ReservationClientError: En cas d'erreur
        """
        # Préparer les paramètres
        params = {
            "date": date.isoformat()
        }
        
        try:
            # Appel à l'API
            response = self._make_request('GET', 'analytics/walk-ins', params=params)
            
            # Retourner les estimations
            return response.get('data', {})
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des estimations de walk-ins: {str(e)}")
            # En cas d'erreur, générer des estimations factices
            return self._generate_mock_walk_ins(date)
    
    def get_reservation_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Récupère des statistiques sur les réservations pour une période.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            
        Returns:
            Statistiques sur les réservations
            
        Raises:
            ReservationClientError: En cas d'erreur
        """
        # Préparer les paramètres
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        try:
            # Appel à l'API
            response = self._make_request('GET', 'analytics/stats', params=params)
            
            # Retourner les statistiques
            return response.get('data', {})
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques de réservation: {str(e)}")
            # En cas d'erreur, générer des statistiques factices
            return self._generate_mock_reservation_stats(start_date, end_date)
    
    def _process_reservations(self, response: Dict) -> Dict[str, List[Dict]]:
        """
        Traite la réponse de l'API pour standardiser le format des réservations.
        
        Args:
            response: Réponse de l'API
            
        Returns:
            Réservations par jour
        """
        reservations_by_day = {}
        
        # Extraire les réservations de la réponse
        raw_reservations = response.get('data', {}).get('reservations', [])
        
        # Traiter chaque réservation
        for reservation in raw_reservations:
            # Extraire la date
            try:
                reservation_datetime = datetime.fromisoformat(reservation.get('date_time', ''))
                date_key = reservation_datetime.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                logger.warning(f"Format de date invalide dans la réservation: {reservation}")
                continue
            
            # Initialiser la liste pour ce jour si nécessaire
            if date_key not in reservations_by_day:
                reservations_by_day[date_key] = []
            
            # Standardiser le format
            processed_reservation = {
                'time': reservation_datetime.strftime('%H:%M'),
                'guests': reservation.get('guests', 0),
                'table_id': reservation.get('table_id'),
                'reservation_id': reservation.get('id'),
                'customer_name': reservation.get('customer_name'),
                'special_requests': reservation.get('special_requests'),
                'status': reservation.get('status', 'confirmed')
            }
            
            # Ajouter à la liste du jour
            reservations_by_day[date_key].append(processed_reservation)
        
        # Trier les réservations par heure pour chaque jour
        for date_key in reservations_by_day:
            reservations_by_day[date_key].sort(key=lambda r: r['time'])
        
        return reservations_by_day
    
    def _process_events(self, response: Dict) -> Dict[str, List[Dict]]:
        """
        Traite la réponse de l'API pour standardiser le format des événements.
        
        Args:
            response: Réponse de l'API
            
        Returns:
            Événements par jour
        """
        events_by_day = {}
        
        # Extraire les événements de la réponse
        raw_events = response.get('data', {}).get('events', [])
        
        # Traiter chaque événement
        for event in raw_events:
            # Extraire la date
            try:
                event_datetime = datetime.fromisoformat(event.get('date_time', ''))
                date_key = event_datetime.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                logger.warning(f"Format de date invalide dans l'événement: {event}")
                continue
            
            # Initialiser la liste pour ce jour si nécessaire
            if date_key not in events_by_day:
                events_by_day[date_key] = []
            
            # Standardiser le format
            processed_event = {
                'time': event_datetime.strftime('%H:%M'),
                'name': event.get('name'),
                'type': event.get('type'),
                'guests': event.get('expected_guests', 0),
                'duration': event.get('duration_minutes', 120),
                'event_id': event.get('id'),
                'description': event.get('description'),
                'status': event.get('status', 'confirmed'),
                'impact_factor': event.get('impact_factor', 1.5)
            }
            
            # Ajouter à la liste du jour
            events_by_day[date_key].append(processed_event)
        
        return events_by_day
    
    def _generate_mock_reservations(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """
        Génère des réservations factices pour une période donnée.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Réservations factices par jour
        """
        import random
        
        mock_reservations = {}
        current_date = start_date
        
        # Liste de noms pour les clients
        first_names = ['Jean', 'Marie', 'Pierre', 'Sophie', 'Luc', 'Emma', 'Thomas', 'Julie', 'Nicolas', 'Camille']
        last_names = ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau']
        
        # Liste de numéros de table
        table_ids = [f"T{i}" for i in range(1, 21)]
        
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            reservations = []
            
            # Coefficient du jour (plus de réservations le week-end)
            day_factor = 1.5 if current_date.weekday() >= 5 else 1.0
            
            # Nombre de réservations pour ce jour
            num_reservations = int(random.gauss(15, 5) * day_factor)
            num_reservations = max(5, num_reservations)
            
            # Générer les réservations
            for _ in range(num_reservations):
                # Période (midi ou soir)
                is_evening = random.random() > 0.4  # 60% de chance pour le soir
                
                if is_evening:
                    # Réservation du soir (18h-21h30)
                    hour = random.randint(18, 21)
                    minute = random.choice([0, 15, 30, 45])
                    if hour == 21 and minute > 30:
                        minute = 30
                else:
                    # Réservation du midi (11h30-14h)
                    hour = random.randint(11, 13)
                    minute = random.choice([0, 15, 30, 45])
                    if hour == 11 and minute < 30:
                        minute = 30
                    elif hour == 14 and minute > 0:
                        minute = 0
                
                time_str = f"{hour:02d}:{minute:02d}"
                
                # Nombre de personnes
                guests = random.choices(
                    [1, 2, 3, 4, 5, 6, 7, 8],
                    weights=[5, 40, 20, 25, 5, 3, 1, 1],
                    k=1
                )[0]
                
                # Nom du client
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                customer_name = f"{first_name} {last_name}"
                
                # Table assignée
                table_id = random.choice(table_ids)
                
                # Requêtes spéciales (10% de chance)
                special_requests = None
                if random.random() < 0.1:
                    special_requests_options = [
                        "Allergie aux fruits de mer",
                        "Table près de la fenêtre",
                        "Anniversaire",
                        "Chaise haute pour enfant",
                        "Végétarien",
                        "Sans gluten"
                    ]
                    special_requests = random.choice(special_requests_options)
                
                # Créer la réservation
                reservation = {
                    'time': time_str,
                    'guests': guests,
                    'table_id': table_id,
                    'reservation_id': f"RES-{uuid.uuid4().hex[:8].upper()}",
                    'customer_name': customer_name,
                    'special_requests': special_requests,
                    'status': 'confirmed'
                }
                
                reservations.append(reservation)
            
            # Trier par heure
            reservations.sort(key=lambda r: r['time'])
            
            # Ajouter au dictionnaire
            mock_reservations[date_key] = reservations
            
            # Passer au jour suivant
            current_date += timedelta(days=1)
        
        return mock_reservations
    
    def _generate_mock_group_reservations(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """
        Génère des réservations de groupe factices pour une période donnée.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Réservations de groupe factices par jour
        """
        import random
        import uuid
        
        mock_group_reservations = {}
        current_date = start_date
        
        # Liste de noms pour les groupes
        group_names = [
            "Anniversaire de Marie", "Réunion d'entreprise ACME",
            "Dîner de promotion Lycée Victor Hugo", "Association des amis du vin",
            "Équipe de football Les Aigles", "Comité d'entreprise TechCorp",
            "Sortie familiale Dupont", "Célébration de retraite"
        ]
        
        while current_date <= end_date:
            # Pas de groupes tous les jours (30% de chance)
            if random.random() > 0.3:
                current_date += timedelta(days=1)
                continue
                
            date_key = current_date.strftime('%Y-%m-%d')
            reservations = []
            
            # Nombre de réservations de groupe pour ce jour (1-2)
            num_groups = random.randint(1, 2)
            
            for _ in range(num_groups):
                # Période (midi ou soir)
                is_evening = random.random() > 0.3  # 70% de chance pour le soir
                
                if is_evening:
                    # Réservation du soir (19h-20h30)
                    hour = random.randint(19, 20)
                    minute = random.choice([0, 15, 30])
                    if hour == 20 and minute > 30:
                        minute = 30
                else:
                    # Réservation du midi (12h-13h30)
                    hour = random.randint(12, 13)
                    minute = random.choice([0, 15, 30])
                    if hour == 13 and minute > 30:
                        minute = 30
                
                time_str = f"{hour:02d}:{minute:02d}"
                
                # Nombre de personnes (8-20)
                guests = random.randint(8, 20)
                
                # Nom du groupe
                group_name = random.choice(group_names)
                
                # Table assignée (pour les groupes, souvent combinaison de tables)
                tables = ", ".join(random.sample([f"T{i}" for i in range(1, 21)], k=min(guests // 4 + 1, 5)))
                
                # Requêtes spéciales (30% de chance)
                special_requests = None
                if random.random() < 0.3:
                    special_requests_options = [
                        "Menu spécial prévu à l'avance",
                        "Espace privé souhaité",
                        "Présentation du chef demandée",
                        "Gâteau d'anniversaire",
                        "Arrangement de tables spécifique",
                        "Allergies diverses"
                    ]
                    special_requests = random.choice(special_requests_options)
                
                # Créer la réservation
                reservation = {
                    'time': time_str,
                    'guests': guests,
                    'table_id': tables,
                    'reservation_id': f"GRP-{uuid.uuid4().hex[:8].upper()}",
                    'customer_name': group_name,
                    'special_requests': special_requests,
                    'status': 'confirmed',
                    'type': 'group',
                    'contact_email': f"contact@{group_name.lower().replace(' ', '')}.fr",
                    'deposit_paid': random.random() > 0.2  # 80% de chance d'avoir payé un acompte
                }
                
                reservations.append(reservation)
            
            # Trier par heure
            reservations.sort(key=lambda r: r['time'])
            
            # Ajouter au dictionnaire s'il y a des réservations
            if reservations:
                mock_group_reservations[date_key] = reservations
            
            # Passer au jour suivant
            current_date += timedelta(days=1)
        
        return mock_group_reservations
    
    def _generate_mock_special_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """
        Génère des événements spéciaux factices pour une période donnée.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Événements spéciaux factices par jour
        """
        import random
        import uuid
        
        mock_events = {}
        current_date = start_date
        
        # Liste d'événements spéciaux possibles
        event_types = [
            {
                "name": "Soirée dégustation",
                "type": "tasting",
                "description": "Dégustation de vins avec accord mets",
                "impact_factor": 1.8,
                "duration": 180
            },
            {
                "name": "Menu du Chef",
                "type": "special_menu",
                "description": "Menu spécial élaboré par notre chef",
                "impact_factor": 1.5,
                "duration": 240
            },
            {
                "name": "Concert Jazz",
                "type": "entertainment",
                "description": "Trio de jazz en live",
                "impact_factor": 1.7,
                "duration": 150
            },
            {
                "name": "Soirée à thème",
                "type": "themed",
                "description": "Soirée à thème avec décoration spéciale",
                "impact_factor": 1.6,
                "duration": 240
            },
            {
                "name": "Privatisation",
                "type": "private",
                "description": "Restaurant privatisé pour un événement",
                "impact_factor": 2.0,
                "duration": 300
            }
        ]
        
        # Un événement tous les 10 jours environ
        days_period = (end_date - start_date).days
        num_events = max(1, days_period // 10)
        
        # Choisir des jours aléatoires pour les événements
        event_days = []
        for _ in range(num_events):
            day_offset = random.randint(0, days_period)
            event_date = start_date + timedelta(days=day_offset)
            event_days.append(event_date)
        
        # Trier les jours
        event_days.sort()
        
        # Générer les événements
        for event_date in event_days:
            date_key = event_date.strftime('%Y-%m-%d')
            
            # Choisir un type d'événement
            event_template = random.choice(event_types)
            
            # Heure (généralement le soir)
            hour = random.randint(18, 20)
            minute = random.choice([0, 30])
            time_str = f"{hour:02d}:{minute:02d}"
            
            # Nombre de participants estimé
            guests = random.randint(30, 80)
            
            # Créer l'événement
            event = {
                'time': time_str,
                'name': event_template["name"],
                'type': event_template["type"],
                'guests': guests,
                'duration': event_template["duration"],
                'event_id': f"EVT-{uuid.uuid4().hex[:8].upper()}",
                'description': event_template["description"],
                'status': 'confirmed',
                'impact_factor': event_template["impact_factor"]
            }
            
            # Ajouter au dictionnaire
            mock_events[date_key] = [event]
        
        return mock_events
    
    def _generate_mock_walk_ins(self, date: datetime) -> Dict:
        """
        Génère des estimations factices de clients sans réservation.
        
        Args:
            date: Date pour l'estimation
            
        Returns:
            Estimations par tranche horaire
        """
        import random
        
        # Coefficient du jour
        day_factor = 1.5 if date.weekday() >= 5 else 1.0
        
        # Structure de base
        mock_walk_ins = {
            "date": date.strftime('%Y-%m-%d'),
            "total_estimated": 0,
            "by_hour": {}
        }
        
        # Heures d'ouverture
        for hour in range(11, 23):  # 11h à 22h
            # Plus de clients à certaines heures
            hour_factor = 1.0
            if hour in (12, 13):  # Heures de déjeuner
                hour_factor = 2.0
            elif hour in (19, 20, 21):  # Heures de dîner
                hour_factor = 2.5
            elif hour in (14, 15, 16, 17):  # Après-midi calme
                hour_factor = 0.5
            
            # Estimation pour cette heure
            estimate = int(random.gauss(5, 2) * day_factor * hour_factor)
            estimate = max(0, estimate)
            
            # Ajouter à la structure
            hour_str = f"{hour:02d}:00"
            mock_walk_ins["by_hour"][hour_str] = estimate
            mock_walk_ins["total_estimated"] += estimate
        
        return mock_walk_ins
    
    def _generate_mock_reservation_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Génère des statistiques factices sur les réservations.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Statistiques factices
        """
        import random
        
        # Nombre de jours dans la période
        days = (end_date - start_date).days + 1
        
        # Statistiques globales
        total_reservations = int(random.gauss(15, 3) * days)
        total_guests = int(total_reservations * random.uniform(2.5, 3.5))
        avg_party_size = total_guests / max(1, total_reservations)
        cancellation_rate = random.uniform(0.05, 0.15)
        no_show_rate = random.uniform(0.02, 0.08)
        
        # Statistiques par jour de la semaine
        day_stats = {}
        for day in range(7):
            day_name = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][day]
            day_factor = 0.7 if day < 4 else (1.8 if day >= 5 else 1.2)
            
            day_stats[day_name] = {
                "avg_reservations": round(random.gauss(15, 3) * day_factor, 1),
                "avg_guests": round(random.gauss(40, 10) * day_factor, 1),
                "peak_time": "19:30" if day >= 4 else "12:30"
            }
        
        # Statistiques par période
        period_stats = {
            "midi": {
                "percentage": round(random.uniform(0.35, 0.45), 2),
                "avg_party_size": round(random.uniform(2.0, 3.0), 1),
                "peak_time": "12:30"
            },
            "soir": {
                "percentage": round(random.uniform(0.55, 0.65), 2),
                "avg_party_size": round(random.uniform(2.5, 3.5), 1),
                "peak_time": "20:00"
            }
        }
        
        # Structure complète
        mock_stats = {
            "period": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "days": days
            },
            "global": {
                "total_reservations": total_reservations,
                "total_guests": total_guests,
                "avg_reservations_per_day": round(total_reservations / days, 1),
                "avg_party_size": round(avg_party_size, 1),
                "cancellation_rate": round(cancellation_rate, 2),
                "no_show_rate": round(no_show_rate, 2)
            },
            "by_day_of_week": day_stats,
            "by_period": period_stats
        }
        
        return mock_stats
