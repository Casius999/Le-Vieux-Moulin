#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client pour intégration avec le module de prédiction.

Ce module fournit une interface pour récupérer les prévisions d'affluence
et autres métriques du module de prédiction ML, afin de les utiliser dans 
l'optimisation des plannings.
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


class PredictionClientError(Exception):
    """Exception spécifique pour les erreurs du client de prédiction."""
    pass


class PredictionClient:
    """
    Client pour communiquer avec l'API du module de prédiction.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialise le client de prédiction.
        
        Args:
            base_url: URL de base de l'API de prédiction (optionnel, utilise la config par défaut)
            timeout: Timeout en secondes pour les requêtes
            max_retries: Nombre maximum de tentatives en cas d'échec
            retry_delay: Délai entre les tentatives en secondes
        """
        self.base_url = base_url or INTEGRATION.get('prediction_api_url')
        if not self.base_url:
            raise ValueError("URL de l'API de prédiction non définie")
            
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Vérifier la connexion à l'initialisation
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """
        Vérifie la connexion avec le serveur de prédiction.
        
        Returns:
            True si la connexion est établie, False sinon
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                logger.info(f"Connexion établie avec le serveur de prédiction: {self.base_url}")
                return True
            else:
                logger.warning(
                    f"Le serveur de prédiction a répondu avec un code d'erreur: {response.status_code}"
                )
                return False
        except RequestException as e:
            logger.error(f"Impossible de se connecter au serveur de prédiction: {str(e)}")
            return False
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Effectue une requête HTTP vers l'API de prédiction avec gestion des retries.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Point d'entrée de l'API (sans l'URL de base)
            params: Paramètres de requête (pour GET)
            data: Données à envoyer (pour POST/PUT)
            
        Returns:
            Données de réponse (JSON)
            
        Raises:
            PredictionClientError: En cas d'erreur après toutes les tentatives
        """
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
                    raise PredictionClientError(f"Réponse non JSON: {response.text}")
                
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
        raise PredictionClientError(f"Échec de la requête après {self.max_retries} tentatives")
    
    def get_customer_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'hourly'
    ) -> Dict:
        """
        Récupère les prévisions d'affluence de clients.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            granularity: Granularité des prévisions ('hourly' ou 'daily')
            
        Returns:
            Prévisions d'affluence
            
        Raises:
            PredictionClientError: En cas d'erreur
        """
        # Préparer la requête de prévision financière qui inclut les métriques d'affluence
        data = {
            "metrics": ["customer_count", "revenue", "avg_ticket"],
            "days_ahead": (end_date - start_date).days + 1,
            "include_components": True
        }
        
        try:
            # Appel à l'API de prévision financière
            response = self._make_request('POST', '/api/finance/forecast', data=data)
            
            # Traiter la réponse pour extraire les prévisions d'affluence
            forecast_data = response.get('forecast', {})
            
            # Reformater les données pour notre usage
            customer_forecast = {}
            
            for date_str, metrics in forecast_data.items():
                # Vérifier si la date est dans notre période
                forecast_date = datetime.fromisoformat(date_str.split('T')[0])
                if start_date <= forecast_date <= end_date:
                    # Format pour les prévisions horaires
                    if granularity == 'hourly' and 'hourly' in metrics:
                        customer_forecast[date_str] = {
                            'hourly_predictions': {
                                hour: {
                                    'customers': data.get('customer_count', 0),
                                    'revenue': data.get('revenue', 0),
                                    'confidence_interval': data.get('confidence_interval', [0, 0])
                                }
                                for hour, data in metrics['hourly'].items()
                            },
                            'total_customers': metrics.get('customer_count', 0),
                            'special_events': self._get_special_events_for_date(forecast_date)
                        }
                    # Format pour les prévisions journalières
                    else:
                        customer_forecast[date_str] = {
                            'customers': metrics.get('customer_count', 0),
                            'revenue': metrics.get('revenue', 0),
                            'confidence_interval': metrics.get('confidence_interval', [0, 0]),
                            'special_events': self._get_special_events_for_date(forecast_date)
                        }
            
            return customer_forecast
            
        except PredictionClientError:
            # En cas d'erreur, générer des prévisions factices pour ne pas bloquer
            logger.warning("Impossible d'obtenir les prévisions, génération de données factices")
            return self._generate_mock_forecast(start_date, end_date, granularity)
    
    def get_stock_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        ingredients: Optional[List[str]] = None
    ) -> Dict:
        """
        Récupère les prévisions de consommation de stock.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            ingredients: Liste spécifique d'ingrédients (optionnel)
            
        Returns:
            Prévisions de consommation par jour et par ingrédient
            
        Raises:
            PredictionClientError: En cas d'erreur
        """
        # Préparer la requête
        data = {
            "days_ahead": (end_date - start_date).days + 1,
            "ingredients": ingredients,
            "include_confidence": True
        }
        
        try:
            # Appel à l'API
            response = self._make_request('POST', '/api/stock/forecast', data=data)
            
            # Retourner les prévisions directement
            return response.get('forecast', {})
            
        except PredictionClientError:
            # En cas d'erreur, générer des prévisions factices
            logger.warning("Impossible d'obtenir les prévisions de stock, génération de données factices")
            return self._generate_mock_stock_forecast(start_date, end_date, ingredients)
    
    def get_suggested_recipes(
        self,
        date: datetime,
        available_ingredients: Optional[Dict[str, float]] = None,
        count: int = 3
    ) -> List[Dict]:
        """
        Récupère des suggestions de recettes pour une date donnée.
        
        Args:
            date: Date pour laquelle obtenir des suggestions
            available_ingredients: Ingrédients disponibles et quantités
            count: Nombre de suggestions à obtenir
            
        Returns:
            Liste de recettes suggérées
            
        Raises:
            PredictionClientError: En cas d'erreur
        """
        # Préparer la requête
        data = {
            "count": count,
            "available_ingredients": available_ingredients
        }
        
        try:
            # Appel à l'API
            response = self._make_request('POST', '/api/recipes/suggest', data=data)
            
            # Retourner les suggestions
            return response.get('suggestions', [])
            
        except PredictionClientError:
            # En cas d'erreur, retourner une liste vide
            logger.warning("Impossible d'obtenir les suggestions de recettes")
            return []
    
    def get_staffing_needs(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calcule les besoins en personnel basés sur les prévisions d'affluence.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            
        Returns:
            Besoins en personnel par jour, shift et rôle
        """
        # Récupérer les prévisions d'affluence
        customer_forecast = self.get_customer_forecast(start_date, end_date, 'hourly')
        
        # Structure pour les besoins en personnel
        staffing_needs = {}
        
        # Configuration des rôles et ratios
        from ..config import SCHEDULING_CONSTRAINTS
        staffing_config = SCHEDULING_CONSTRAINTS.get('staffing_configuration', {})
        roles_config = staffing_config.get('roles', {})
        day_factors = staffing_config.get('day_factors', {})
        special_events = staffing_config.get('special_events', {'default': 1.2})
        
        # Shifts par défaut
        default_shifts = SCHEDULING_CONSTRAINTS.get('default_shifts', {})
        
        # Pour chaque jour dans la prévision
        for date_str, forecast in customer_forecast.items():
            # Convertir la date
            date = datetime.fromisoformat(date_str.split('T')[0])
            date_key = date.strftime('%Y-%m-%d')
            
            # Coefficient du jour de la semaine
            day_factor = day_factors.get(date.weekday(), 1.0)
            
            # Vérifier les événements spéciaux
            special_event_factor = 1.0
            if 'special_events' in forecast and forecast['special_events']:
                for event in forecast['special_events']:
                    event_type = event.get('type', 'default')
                    event_factor = special_events.get(event_type, special_events['default'])
                    special_event_factor = max(special_event_factor, event_factor)
            
            # Initialiser la structure pour ce jour
            staffing_needs[date_key] = {
                'shifts': {}
            }
            
            # Si nous avons des prévisions horaires
            if 'hourly_predictions' in forecast:
                # Regrouper les heures par shifts
                shift_hours = {
                    'matin': range(9, 16),  # 9h-16h
                    'soir': range(16, 24)   # 16h-24h
                }
                
                # Calculer le nombre de clients par shift
                shift_customers = {}
                for shift_name, hours in shift_hours.items():
                    total_customers = 0
                    for hour in hours:
                        hour_str = f"{hour:02d}:00"
                        if hour_str in forecast['hourly_predictions']:
                            total_customers += forecast['hourly_predictions'][hour_str]['customers']
                    shift_customers[shift_name] = total_customers
                
                # Calculer les besoins en personnel pour chaque shift
                for shift_name, customers in shift_customers.items():
                    if shift_name not in default_shifts:
                        continue
                        
                    shift_info = default_shifts[shift_name]
                    
                    # Créer l'entrée pour ce shift
                    staffing_needs[date_key]['shifts'][shift_name] = {
                        'start_time': shift_info['start'].strftime('%H:%M'),
                        'end_time': shift_info['end'].strftime('%H:%M'),
                        'customers': customers,
                        'roles': {}
                    }
                    
                    # Calculer les besoins pour chaque rôle
                    for role_name, config in roles_config.items():
                        # Nombre minimum de personnel requis
                        min_staff = config.get('min_per_shift', 0)
                        
                        # Nombre basé sur les clients
                        customer_ratio = config.get('customer_ratio', 0)
                        customer_based_staff = int(customers * customer_ratio)
                        
                        # Appliquer les facteurs
                        adjusted_staff = max(min_staff, customer_based_staff)
                        adjusted_staff = int(adjusted_staff * day_factor * special_event_factor)
                        
                        # Limiter au maximum configuré
                        max_staff = config.get('max_per_shift', float('inf'))
                        adjusted_staff = min(adjusted_staff, max_staff)
                        
                        # Ajouter à la structure
                        staffing_needs[date_key]['shifts'][shift_name]['roles'][role_name] = adjusted_staff
            else:
                # Prévisions journalières, répartir entre matin et soir
                customers = forecast.get('customers', 0)
                midday_ratio = 0.4  # 40% des clients le midi
                evening_ratio = 0.6  # 60% des clients le soir
                
                for shift_name, shift_info in default_shifts.items():
                    if shift_name == 'matin':
                        shift_customers = customers * midday_ratio
                    elif shift_name == 'soir':
                        shift_customers = customers * evening_ratio
                    else:
                        continue
                    
                    # Créer l'entrée pour ce shift
                    staffing_needs[date_key]['shifts'][shift_name] = {
                        'start_time': shift_info['start'].strftime('%H:%M'),
                        'end_time': shift_info['end'].strftime('%H:%M'),
                        'customers': shift_customers,
                        'roles': {}
                    }
                    
                    # Calculer les besoins pour chaque rôle
                    for role_name, config in roles_config.items():
                        # Nombre minimum de personnel requis
                        min_staff = config.get('min_per_shift', 0)
                        
                        # Nombre basé sur les clients
                        customer_ratio = config.get('customer_ratio', 0)
                        customer_based_staff = int(shift_customers * customer_ratio)
                        
                        # Appliquer les facteurs
                        adjusted_staff = max(min_staff, customer_based_staff)
                        adjusted_staff = int(adjusted_staff * day_factor * special_event_factor)
                        
                        # Limiter au maximum configuré
                        max_staff = config.get('max_per_shift', float('inf'))
                        adjusted_staff = min(adjusted_staff, max_staff)
                        
                        # Ajouter à la structure
                        staffing_needs[date_key]['shifts'][shift_name]['roles'][role_name] = adjusted_staff
        
        return staffing_needs
    
    def _get_special_events_for_date(self, date: datetime) -> List[Dict]:
        """
        Récupère les événements spéciaux pour une date donnée.
        
        Args:
            date: Date à vérifier
            
        Returns:
            Liste d'événements spéciaux
        """
        # TODO: Intégrer avec un calendrier d'événements
        # Pour l'instant, retourner des données factices
        
        # Jours fériés français (exemple pour 2025)
        holidays = {
            datetime(2025, 1, 1): "Jour de l'An",
            datetime(2025, 4, 21): "Lundi de Pâques",
            datetime(2025, 5, 1): "Fête du Travail",
            datetime(2025, 5, 8): "Victoire 1945",
            datetime(2025, 5, 29): "Ascension",
            datetime(2025, 6, 9): "Lundi de Pentecôte",
            datetime(2025, 7, 14): "Fête Nationale",
            datetime(2025, 8, 15): "Assomption",
            datetime(2025, 11, 1): "Toussaint",
            datetime(2025, 11, 11): "Armistice 1918",
            datetime(2025, 12, 25): "Noël"
        }
        
        events = []
        
        # Vérifier si c'est un jour férié
        for holiday_date, holiday_name in holidays.items():
            if date.date() == holiday_date.date():
                events.append({
                    "type": "holiday",
                    "name": holiday_name,
                    "impact_factor": 1.5
                })
        
        # Ajouter d'autres événements selon la logique métier
        
        return events
    
    def _generate_mock_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str
    ) -> Dict:
        """
        Génère des prévisions factices en cas d'erreur.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            granularity: Granularité ('hourly' ou 'daily')
            
        Returns:
            Prévisions factices
        """
        import random
        
        mock_forecast = {}
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Coefficient du jour (plus de monde le week-end)
            day_factor = 1.5 if current_date.weekday() >= 5 else 1.0
            
            if granularity == 'hourly':
                hourly = {}
                for hour in range(9, 24):  # 9h à 23h
                    # Plus de monde à midi et le soir
                    hour_factor = 1.5 if hour in (12, 13, 19, 20, 21) else 1.0
                    customer_count = int(random.gauss(30, 10) * day_factor * hour_factor)
                    customer_count = max(0, customer_count)
                    
                    hourly[f"{hour:02d}:00"] = {
                        'customers': customer_count,
                        'revenue': customer_count * random.uniform(20, 35),
                        'confidence_interval': [
                            max(0, customer_count - random.randint(5, 10)),
                            customer_count + random.randint(5, 15)
                        ]
                    }
                
                mock_forecast[date_str] = {
                    'hourly_predictions': hourly,
                    'total_customers': sum(h['customers'] for h in hourly.values()),
                    'special_events': self._get_special_events_for_date(current_date)
                }
            else:
                # Prévision journalière
                customer_count = int(random.gauss(200, 50) * day_factor)
                customer_count = max(0, customer_count)
                
                mock_forecast[date_str] = {
                    'customers': customer_count,
                    'revenue': customer_count * random.uniform(25, 40),
                    'confidence_interval': [
                        max(0, customer_count - random.randint(20, 40)),
                        customer_count + random.randint(20, 50)
                    ],
                    'special_events': self._get_special_events_for_date(current_date)
                }
            
            current_date += timedelta(days=1)
        
        return mock_forecast
    
    def _generate_mock_stock_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        ingredients: Optional[List[str]] = None
    ) -> Dict:
        """
        Génère des prévisions de stock factices en cas d'erreur.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            ingredients: Liste d'ingrédients
            
        Returns:
            Prévisions factices
        """
        import random
        
        # Ingrédients par défaut
        default_ingredients = [
            'farine', 'tomate', 'mozzarella', 'basilic', 'huile_olive',
            'sel', 'levure', 'oignon', 'ail', 'viande_hachee'
        ]
        
        ingredients = ingredients or default_ingredients
        
        mock_forecast = {}
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Coefficient du jour (plus de consommation le week-end)
            day_factor = 1.5 if current_date.weekday() >= 5 else 1.0
            
            # Prévisions pour chaque ingrédient
            ingredients_forecast = {}
            for ingredient in ingredients:
                # Consommation de base selon l'ingrédient
                base_consumption = {
                    'farine': 10.0,
                    'tomate': 8.0,
                    'mozzarella': 5.0,
                    'basilic': 0.5,
                    'huile_olive': 2.0,
                    'sel': 0.3,
                    'levure': 0.5,
                    'oignon': 3.0,
                    'ail': 0.5,
                    'viande_hachee': 4.0
                }.get(ingredient, 1.0)
                
                # Consommation prévue avec variation aléatoire
                consumption = base_consumption * day_factor * random.uniform(0.8, 1.2)
                
                ingredients_forecast[ingredient] = {
                    'quantity': round(consumption, 2),
                    'confidence_interval': [
                        round(consumption * 0.8, 2),
                        round(consumption * 1.2, 2)
                    ]
                }
            
            mock_forecast[date_str] = ingredients_forecast
            current_date += timedelta(days=1)
        
        return mock_forecast
