#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'optimisation des plannings du personnel pour le restaurant "Le Vieux Moulin".

Ce module fournit un système automatisé pour la génération et l'optimisation des plannings
du personnel basé sur les prévisions d'affluence, l'historique des réservations et les
contraintes des employés.
"""

__version__ = '1.0.0'
__author__ = 'Équipe de Développement Le Vieux Moulin'

# Imports pour faciliter l'utilisation
from staffing_scheduler.models.schedule import Schedule
from staffing_scheduler.models.shift import Shift
from staffing_scheduler.models.employee import Employee
from staffing_scheduler.scheduler.optimizer import ScheduleOptimizer
from staffing_scheduler.scheduler.generator import ScheduleGenerator

# Configuration par défaut
DEFAULT_CONFIG = {
    'min_rest_hours': 11,  # Repos minimum entre deux services (heures)
    'max_daily_hours': 10,  # Heures maximum par jour
    'max_weekly_hours': 48,  # Heures maximum par semaine
    'optimization_parameters': {
        'population_size': 100,  # Taille de la population pour l'algorithme génétique
        'generations': 50,  # Nombre de générations
        'mutation_rate': 0.1,  # Taux de mutation
        'crossover_rate': 0.8,  # Taux de croisement
    },
    'weights': {
        'staff_coverage': 0.4,  # Poids pour la couverture des besoins en personnel
        'employee_preferences': 0.3,  # Poids pour les préférences des employés
        'labor_cost': 0.2,  # Poids pour les coûts de main-d'œuvre
        'schedule_stability': 0.1,  # Poids pour la stabilité du planning
    }
}

# Fonctions d'accès simplifiées
def create_optimized_schedule(start_date, end_date, employees, constraints=None, config=None):
    """
    Crée un planning optimisé pour une période donnée.
    
    Args:
        start_date (datetime): Date de début de la période
        end_date (datetime): Date de fin de la période
        employees (list): Liste des employés disponibles
        constraints (dict, optional): Contraintes spécifiques
        config (dict, optional): Configuration personnalisée
        
    Returns:
        Schedule: Planning optimisé
    """
    from staffing_scheduler.scheduler.optimizer import ScheduleOptimizer
    
    # Fusionner avec la configuration par défaut
    if config:
        from copy import deepcopy
        merged_config = deepcopy(DEFAULT_CONFIG)
        merged_config.update(config)
    else:
        merged_config = DEFAULT_CONFIG
    
    # Créer et exécuter l'optimiseur
    optimizer = ScheduleOptimizer(config=merged_config)
    return optimizer.generate_schedule(
        start_date=start_date,
        end_date=end_date,
        employees=employees,
        constraints=constraints
    )

def load_schedule(schedule_id):
    """
    Charge un planning existant depuis la base de données.
    
    Args:
        schedule_id (str): Identifiant du planning
        
    Returns:
        Schedule: Planning chargé
    """
    from staffing_scheduler.data.repository import ScheduleRepository
    repo = ScheduleRepository()
    return repo.get_by_id(schedule_id)

def get_predicted_staffing_needs(start_date, end_date):
    """
    Récupère les besoins prévus en personnel sur une période.
    
    Args:
        start_date (datetime): Date de début
        end_date (datetime): Date de fin
        
    Returns:
        dict: Besoins en personnel par jour et par poste
    """
    from staffing_scheduler.integration.prediction_client import PredictionClient
    client = PredictionClient()
    return client.get_staffing_needs(start_date, end_date)
