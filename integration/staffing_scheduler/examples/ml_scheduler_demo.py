#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Démo d'utilisation de l'optimiseur ML pour les plannings.

Ce script montre comment utiliser la classe MLScheduleOptimizer pour générer
des plannings optimisés en utilisant l'apprentissage automatique et les données historiques.
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
import random

# Configuration du chemin pour importer le module staffing_scheduler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from integration.staffing_scheduler.scheduler.ml_optimizer import MLScheduleOptimizer
from integration.staffing_scheduler.models.employee import Employee, EmployeeRole
from integration.staffing_scheduler.models.schedule import Schedule
from integration.staffing_scheduler.models.shift import Shift, ShiftType
from integration.staffing_scheduler.models.constraint import Constraint, ConstraintSet, ConstraintPriority

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_test_employees(count: int = 20) -> list:
    """
    Génère des employés de test avec des compétences variées.
    
    Args:
        count: Nombre d'employés à générer
        
    Returns:
        Liste d'employés générés
    """
    employees = []
    roles = [role for role in EmployeeRole]
    
    for i in range(count):
        # Déterminer le rôle principal
        primary_role = random.choice(roles)
        
        # Déterminer les rôles secondaires (0 à 2)
        secondary_roles = []
        for _ in range(random.randint(0, 2)):
            role = random.choice(roles)
            if role != primary_role and role not in secondary_roles:
                secondary_roles.append(role)
        
        # Jours préférés (0-6, 0=Lundi, 6=Dimanche)
        preferred_days = random.sample(range(7), random.randint(1, 3))
        
        # Taux horaire
        hourly_rate = round(random.uniform(12.0, 25.0), 2)
        
        # Niveau de compétence par rôle
        skill_level = {}
        skill_level[primary_role.value] = random.uniform(0.7, 1.0)
        for role in secondary_roles:
            skill_level[role.value] = random.uniform(0.3, 0.7)
        
        # Créer l'employé
        employee = Employee(
            employee_id=f"EMP{i+100}",
            name=f"Employé {i+1}",
            primary_role=primary_role,
            secondary_roles=secondary_roles
        )
        
        # Ajouter des attributs personnalisés
        employee.hourly_rate = hourly_rate
        employee.preferred_days = preferred_days
        employee.skill_level = skill_level
        employee.can_work_role = lambda role: role == primary_role or role in secondary_roles
        
        employees.append(employee)
    
    return employees


def generate_historical_schedules(employees: list, num_schedules: int = 5) -> list:
    """
    Génère des plannings historiques pour l'entraînement du modèle ML.
    
    Args:
        employees: Liste des employés disponibles
        num_schedules: Nombre de plannings à générer
        
    Returns:
        Liste des plannings historiques
    """
    schedules = []
    
    # Générer plusieurs plannings historiques pour différentes semaines passées
    for i in range(num_schedules):
        # Dates pour ce planning (semaines passées)
        end_date = datetime.now() - timedelta(days=7*i)
        start_date = end_date - timedelta(days=6)
        
        # Créer le planning
        schedule = Schedule.create_new(
            start_date=start_date,
            end_date=end_date,
            name=f"Planning Historique {i+1}",
            created_by="system"
        )
        
        # Générer des shifts pour chaque jour
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            
            # Shifts du matin
            for role in EmployeeRole:
                # Nombre de shifts pour ce rôle (dépend du rôle et du jour)
                count = 1
                if role == EmployeeRole.SERVEUR:
                    count = 3 if day >= 4 else 2  # Plus de serveurs en fin de semaine
                elif role == EmployeeRole.CHEF:
                    count = 2 if day >= 4 else 1  # Plus de chefs en fin de semaine
                
                for j in range(count):
                    shift = Shift.create_new(
                        date=current_date,
                        start_time=datetime.strptime("10:00", "%H:%M").time(),
                        end_time=datetime.strptime("15:00", "%H:%M").time(),
                        role=role,
                        shift_type=ShiftType.MIDDAY
                    )
                    
                    # Assigner un employé aléatoire capable de faire ce rôle
                    eligible_employees = [e for e in employees if e.can_work_role(role)]
                    if eligible_employees:
                        employee = random.choice(eligible_employees)
                        shift.assign_employee(employee)
                    
                    schedule.add_shift(shift)
            
            # Shifts du soir
            for role in EmployeeRole:
                # Nombre de shifts pour ce rôle (dépend du rôle et du jour)
                count = 1
                if role == EmployeeRole.SERVEUR:
                    count = 4 if day >= 4 else 3  # Plus de serveurs en fin de semaine
                elif role == EmployeeRole.CHEF:
                    count = 2 if day >= 4 else 1  # Plus de chefs en fin de semaine
                elif role == EmployeeRole.BARMAN:
                    count = 2 if day >= 4 else 1  # Plus de barmans en fin de semaine
                
                for j in range(count):
                    shift = Shift.create_new(
                        date=current_date,
                        start_time=datetime.strptime("18:00", "%H:%M").time(),
                        end_time=datetime.strptime("23:00", "%H:%M").time(),
                        role=role,
                        shift_type=ShiftType.EVENING
                    )
                    
                    # Assigner un employé aléatoire capable de faire ce rôle
                    eligible_employees = [e for e in employees if e.can_work_role(role)]
                    if eligible_employees:
                        employee = random.choice(eligible_employees)
                        shift.assign_employee(employee)
                    
                    schedule.add_shift(shift)
        
        # Ajouter des métriques générées aléatoirement pour simuler les performances
        schedule.metrics = {
            "coverage_rate": random.uniform(0.8, 1.0),
            "preference_satisfaction": random.uniform(0.7, 0.95),
            "cost_efficiency": random.uniform(0.7, 0.9),
            "fairness_index": random.uniform(0.75, 0.95),
            "customer_satisfaction": random.uniform(0.75, 0.98)
        }
        
        schedules.append(schedule)
    
    return schedules


def generate_staffing_needs(start_date: datetime, end_date: datetime) -> dict:
    """
    Génère des besoins en personnel pour la période spécifiée.
    
    Args:
        start_date: Date de début
        end_date: Date de fin
        
    Returns:
        Dictionnaire des besoins en personnel
    """
    staffing_needs = {}
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Détermine si c'est un jour de weekend
        is_weekend = current_date.weekday() >= 5  # 5=Samedi, 6=Dimanche
        
        # Configuration de base
        staffing_needs[date_str] = {
            "shifts": {
                "matin": {
                    "start_time": "10:00",
                    "end_time": "15:00",
                    "roles": {
                        "CHEF": 1 + (1 if is_weekend else 0),
                        "COMMIS": 1,
                        "SERVEUR": 2 + (1 if is_weekend else 0),
                        "BARMAN": 1,
                        "PLONGEUR": 1
                    }
                },
                "soir": {
                    "start_time": "18:00",
                    "end_time": "23:00",
                    "roles": {
                        "CHEF": 1 + (1 if is_weekend else 0),
                        "COMMIS": 1 + (1 if is_weekend else 0),
                        "SERVEUR": 3 + (1 if is_weekend else 0),
                        "BARMAN": 1 + (1 if is_weekend else 0),
                        "PLONGEUR": 1
                    }
                }
            }
        }
        
        current_date += timedelta(days=1)
    
    return staffing_needs


def generate_metrics_for_schedules(schedules: list) -> dict:
    """
    Génère des métriques pour les plannings historiques.
    
    Args:
        schedules: Liste des plannings
        
    Returns:
        Dictionnaire des métriques par planning
    """
    metrics = {}
    
    for schedule in schedules:
        employee_metrics = {}
        
        # Pour chaque shift assigné, générer une métrique de performance
        for shift in schedule.shifts:
            if shift.employee_id:
                if shift.employee_id not in employee_metrics:
                    # Score de base entre 0.7 et 0.95
                    base_score = random.uniform(0.7, 0.95)
                    employee_metrics[shift.employee_id] = base_score
        
        metrics[schedule.schedule_id] = {
            "coverage_rate": getattr(schedule, "metrics", {}).get("coverage_rate", random.uniform(0.8, 1.0)),
            "preference_satisfaction": getattr(schedule, "metrics", {}).get("preference_satisfaction", random.uniform(0.7, 0.95)),
            "cost_efficiency": getattr(schedule, "metrics", {}).get("cost_efficiency", random.uniform(0.7, 0.9)),
            "fairness_index": getattr(schedule, "metrics", {}).get("fairness_index", random.uniform(0.75, 0.95)),
            "customer_satisfaction": getattr(schedule, "metrics", {}).get("customer_satisfaction", random.uniform(0.75, 0.98)),
            "employee_metrics": employee_metrics
        }
    
    return metrics


def show_schedule_summary(schedule: Schedule, title: str = "Résumé du Planning") -> None:
    """
    Affiche un résumé du planning généré.
    
    Args:
        schedule: Planning à afficher
        title: Titre du résumé
    """
    print("=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)
    
    print(f"ID: {schedule.schedule_id}")
    print(f"Période: {schedule.start_date.strftime('%d/%m/%Y')} - {schedule.end_date.strftime('%d/%m/%Y')}")
    print(f"Statut: {schedule.status.value if hasattr(schedule.status, 'value') else schedule.status}")
    print(f"Shifts totaux: {len(schedule.shifts)}")
    
    # Calculer le nombre de shifts assignés
    assigned_shifts = sum(1 for shift in schedule.shifts if shift.employee_id)
    print(f"Shifts assignés: {assigned_shifts} ({assigned_shifts / max(1, len(schedule.shifts)) * 100:.1f}%)")
    
    # Répartition par rôle
    print("\nRépartition par rôle:")
    role_counts = {}
    for shift in schedule.shifts:
        role = shift.role.value if hasattr(shift.role, "value") else str(shift.role)
        role_counts[role] = role_counts.get(role, 0) + 1
    
    for role, count in sorted(role_counts.items()):
        print(f"  {role}: {count} shifts")
    
    # Répartition par jour
    print("\nRépartition par jour:")
    day_counts = {}
    for shift in schedule.shifts:
        day_name = shift.date.strftime('%A')  # Nom du jour
        day_counts[day_name] = day_counts.get(day_name, 0) + 1
    
    for day, count in sorted(day_counts.items(), key=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(x[0])):
        print(f"  {day}: {count} shifts")
    
    # Métriques
    if hasattr(schedule, "metrics") and schedule.metrics:
        print("\nMétriques:")
        for key, value in schedule.metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:.2f}")
            elif isinstance(value, dict):
                continue  # Ignorer les dictionnaires complexes
            else:
                print(f"  {key}: {value}")
    
    # Métadonnées
    if hasattr(schedule, "metadata") and schedule.metadata:
        print("\nMétadonnées:")
        for key, value in schedule.metadata.items():
            if isinstance(value, dict):
                print(f"  {key}: {json.dumps(value, indent=2)}")
            else:
                print(f"  {key}: {value}")
    
    print("=" * 80)


def save_model(optimizer: MLScheduleOptimizer, path: str) -> None:
    """
    Sauvegarde le modèle d'optimisation pour réutilisation.
    
    Args:
        optimizer: Optimiseur ML
        path: Chemin de sauvegarde
    """
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Exporter le modèle
    result = optimizer.export_optimization_model(path)
    
    if result:
        logger.info(f"Modèle sauvegardé avec succès: {path}")
    else:
        logger.error(f"Échec de la sauvegarde du modèle: {path}")


def load_model(optimizer: MLScheduleOptimizer, path: str) -> bool:
    """
    Charge un modèle d'optimisation préexistant.
    
    Args:
        optimizer: Optimiseur ML
        path: Chemin du modèle
        
    Returns:
        True si chargé avec succès, False sinon
    """
    if not os.path.exists(path):
        logger.error(f"Modèle non trouvé: {path}")
        return False
    
    result = optimizer.import_optimization_model(path)
    
    if result:
        logger.info(f"Modèle chargé avec succès: {path}")
        return True
    else:
        logger.error(f"Échec du chargement du modèle: {path}")
        return False


def progress_callback(current: int, total: int, stats: dict) -> None:
    """
    Callback pour suivre la progression de l'optimisation.
    
    Args:
        current: Génération actuelle
        total: Nombre total de générations
        stats: Statistiques de génération
    """
    if current % 5 == 0 or current == total - 1:
        print(f"Génération {current}/{total}: Score={stats['best_fitness']:.4f}, Temps={stats['elapsed_time']:.2f}s")


def main():
    """
    Fonction principale de démonstration.
    """
    # Créer les employés de test
    logger.info("Génération des employés de test...")
    employees = generate_test_employees(20)
    logger.info(f"{len(employees)} employés générés")
    
    # Créer les plannings historiques
    logger.info("Génération des plannings historiques...")
    historical_schedules = generate_historical_schedules(employees, 5)
    logger.info(f"{len(historical_schedules)} plannings historiques générés")
    
    # Générer des métriques pour les plannings historiques
    logger.info("Génération des métriques historiques...")
    historical_metrics = generate_metrics_for_schedules(historical_schedules)
    
    # Période pour le nouveau planning
    start_date = datetime.now()
    end_date = start_date + timedelta(days=6)  # Planning sur 7 jours
    
    # Générer les besoins en personnel
    logger.info("Génération des besoins en personnel...")
    staffing_needs = generate_staffing_needs(start_date, end_date)
    
    # Configuration de l'optimiseur
    logger.info("Configuration de l'optimiseur ML...")
    optimizer_config = {
        "population_size": 100,
        "generations": 50,
        "mutation_rate": 0.15,
        "crossover_rate": 0.8,
        "elitism_count": 5,
        "ml_weight": 0.3,  # Poids du modèle ML dans le score final
        "weights": {
            "coverage": 0.4,
            "preferences": 0.3,
            "cost": 0.2,
            "stability": 0.1
        },
        "parallel_processing": True,
        "max_workers": 4,
        "timeout_seconds": 120
    }
    
    # Créer l'optimiseur ML
    ml_optimizer = MLScheduleOptimizer(
        config=optimizer_config,
        progress_callback=progress_callback
    )
    
    # Charger les données historiques
    logger.info("Chargement des données historiques dans l'optimiseur...")
    ml_optimizer.load_historical_data(historical_schedules, historical_metrics)
    
    # Entraîner le modèle
    logger.info("Entraînement du modèle ML...")
    training_success = ml_optimizer.train_model()
    
    if training_success:
        logger.info("Modèle entraîné avec succès")
        
        # Afficher l'importance des caractéristiques
        feature_importance = ml_optimizer.get_feature_importance()
        print("\nImportance des caractéristiques:")
        for feature, importance in feature_importance.items():
            print(f"  {feature}: {importance:.4f}")
    else:
        logger.warning("L'entraînement du modèle a échoué, utilisation de l'algorithme standard")
    
    # Générer le planning optimisé
    logger.info("Génération du planning optimisé...")
    optimized_schedule = ml_optimizer.generate_schedule(
        start_date=start_date,
        end_date=end_date,
        employees=employees,
        staffing_needs=staffing_needs
    )
    
    # Afficher un résumé du planning généré
    show_schedule_summary(optimized_schedule, "Planning Optimisé avec ML")
    
    # Analyser les résultats d'optimisation
    logger.info("Analyse des résultats d'optimisation...")
    optimization_analysis = ml_optimizer.analyze_optimization_results(optimized_schedule)
    
    # Afficher les insights
    print("\nInsights d'optimisation:")
    for insight in optimization_analysis["insights"]:
        print(f"  [{insight['type'].upper()}] {insight['message']}")
        if insight["suggested_action"]:
            print(f"      → Action suggérée: {insight['suggested_action']}")
    
    # Sauvegarder le modèle pour réutilisation
    model_path = "models/staffing_optimizer_model.json"
    logger.info(f"Sauvegarde du modèle: {model_path}")
    save_model(ml_optimizer, model_path)
    
    # Exemple d'insights sur un employé
    if employees:
        employee_id = employees[0].employee_id
        employee_insights = ml_optimizer.get_employee_insights(employee_id)
        
        print(f"\nInsights pour l'employé {employee_id}:")
        if "message" in employee_insights:
            print(f"  {employee_insights['message']}")
        else:
            for key, value in employee_insights.items():
                if key == "recommendations":
                    print("  Recommandations:")
                    for rec in value:
                        print(f"    - {rec}")
                elif isinstance(value, list):
                    print(f"  {key}: {', '.join(map(str, value))}")
                else:
                    print(f"  {key}: {value}")
    
    logger.info("Démo terminée avec succès")


if __name__ == "__main__":
    main()
