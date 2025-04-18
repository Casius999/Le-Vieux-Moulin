#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interface en ligne de commande pour le module d'optimisation des plannings.

Ce module permet de générer et gérer des plannings directement depuis la ligne de commande.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
import json
import csv
import pandas as pd
from typing import List, Dict, Any, Optional

from .models.employee import Employee, EmployeeRole
from .models.schedule import Schedule, ScheduleStatus
from .models.shift import Shift, ShiftType
from .models.constraint import Constraint, ConstraintSet, ConstraintPriority
from .scheduler.optimizer import ScheduleOptimizer
from .scheduler.ml_optimizer import MLScheduleOptimizer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_date(date_str: str) -> datetime:
    """
    Convertit une chaîne de date en objet datetime.
    
    Args:
        date_str: Date au format YYYY-MM-DD
        
    Returns:
        Objet datetime
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Format de date invalide: {date_str}. Utilisez le format YYYY-MM-DD.")
        sys.exit(1)


def load_employees(file_path: str) -> List[Employee]:
    """
    Charge les employés depuis un fichier CSV ou JSON.
    
    Args:
        file_path: Chemin du fichier contenant les données des employés
        
    Returns:
        Liste d'objets Employee
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier non trouvé: {file_path}")
        sys.exit(1)
    
    employees = []
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.json':
            # Chargement depuis JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                employee_data = json.load(f)
            
            for data in employee_data:
                primary_role = EmployeeRole[data.get('primary_role', 'SERVEUR')]
                secondary_roles = [EmployeeRole[role] for role in data.get('secondary_roles', [])]
                
                employee = Employee(
                    employee_id=data.get('employee_id'),
                    name=data.get('name'),
                    primary_role=primary_role,
                    secondary_roles=secondary_roles
                )
                
                # Ajouter des attributs personnalisés
                if 'hourly_rate' in data:
                    employee.hourly_rate = data['hourly_rate']
                if 'preferred_days' in data:
                    employee.preferred_days = data['preferred_days']
                
                # Ajouter la fonction can_work_role
                roles = [primary_role] + secondary_roles
                employee.can_work_role = lambda role, roles=roles: role in roles
                
                employees.append(employee)
        
        elif ext == '.csv':
            # Chargement depuis CSV
            df = pd.read_csv(file_path)
            
            for _, row in df.iterrows():
                primary_role = EmployeeRole[row.get('primary_role', 'SERVEUR')]
                
                # Les rôles secondaires sont stockés comme une chaîne séparée par des virgules
                secondary_roles_str = row.get('secondary_roles', '')
                secondary_roles = []
                
                if secondary_roles_str:
                    for role_str in secondary_roles_str.split(','):
                        try:
                            role = EmployeeRole[role_str.strip()]
                            secondary_roles.append(role)
                        except KeyError:
                            logger.warning(f"Rôle inconnu ignoré: {role_str}")
                
                employee = Employee(
                    employee_id=row.get('employee_id'),
                    name=row.get('name'),
                    primary_role=primary_role,
                    secondary_roles=secondary_roles
                )
                
                # Ajouter des attributs personnalisés
                if 'hourly_rate' in row:
                    employee.hourly_rate = row['hourly_rate']
                if 'preferred_days' in row:
                    days_str = row['preferred_days']
                    if days_str:
                        employee.preferred_days = [int(d.strip()) for d in days_str.split(',')]
                
                # Ajouter la fonction can_work_role
                roles = [primary_role] + secondary_roles
                employee.can_work_role = lambda role, roles=roles: role in roles
                
                employees.append(employee)
        
        else:
            logger.error(f"Format de fichier non pris en charge: {ext}. Utilisez CSV ou JSON.")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement des employés: {str(e)}")
        sys.exit(1)
    
    logger.info(f"{len(employees)} employés chargés depuis {file_path}")
    return employees


def load_staffing_needs(file_path: str) -> Dict:
    """
    Charge les besoins en personnel depuis un fichier JSON.
    
    Args:
        file_path: Chemin du fichier contenant les besoins en personnel
        
    Returns:
        Dictionnaire des besoins en personnel
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier non trouvé: {file_path}")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            staffing_needs = json.load(f)
        
        logger.info(f"Besoins en personnel chargés depuis {file_path}")
        return staffing_needs
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des besoins en personnel: {str(e)}")
        sys.exit(1)


def load_historical_schedules(file_path: str) -> List[Schedule]:
    """
    Charge les plannings historiques depuis un fichier JSON.
    
    Args:
        file_path: Chemin du fichier contenant les plannings historiques
        
    Returns:
        Liste des plannings historiques
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier non trouvé: {file_path}")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            historical_data = json.load(f)
        
        schedules = []
        
        for schedule_data in historical_data.get('schedules', []):
            # Créer le planning
            start_date = datetime.strptime(schedule_data.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(schedule_data.get('end_date'), '%Y-%m-%d')
            
            schedule = Schedule.create_new(
                start_date=start_date,
                end_date=end_date,
                name=schedule_data.get('name', f"Planning {start_date.strftime('%d/%m/%Y')}"),
                created_by=schedule_data.get('created_by', 'system')
            )
            
            # Ajouter l'ID du planning (important pour l'association avec les métriques)
            if 'schedule_id' in schedule_data:
                schedule.schedule_id = schedule_data['schedule_id']
            
            # Ajouter les shifts
            for shift_data in schedule_data.get('shifts', []):
                shift_date = datetime.strptime(shift_data.get('date'), '%Y-%m-%d')
                
                start_time = datetime.strptime(shift_data.get('start_time'), '%H:%M').time()
                end_time = datetime.strptime(shift_data.get('end_time'), '%H:%M').time()
                
                role = EmployeeRole[shift_data.get('role', 'SERVEUR')]
                
                shift_type_str = shift_data.get('shift_type', 'CUSTOM')
                shift_type = ShiftType[shift_type_str]
                
                shift = Shift.create_new(
                    date=shift_date,
                    start_time=start_time,
                    end_time=end_time,
                    role=role,
                    shift_type=shift_type
                )
                
                # Ajouter l'ID de l'employé si assigné
                if 'employee_id' in shift_data:
                    shift.employee_id = shift_data['employee_id']
                
                schedule.add_shift(shift)
            
            # Ajouter les métriques si présentes
            if 'metrics' in schedule_data:
                schedule.metrics = schedule_data['metrics']
            
            schedules.append(schedule)
        
        logger.info(f"{len(schedules)} plannings historiques chargés depuis {file_path}")
        return schedules
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des plannings historiques: {str(e)}")
        sys.exit(1)


def load_historical_metrics(file_path: str) -> Dict:
    """
    Charge les métriques historiques depuis un fichier JSON.
    
    Args:
        file_path: Chemin du fichier contenant les métriques historiques
        
    Returns:
        Dictionnaire des métriques par planning
    """
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"Fichier de métriques non trouvé: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        
        logger.info(f"Métriques historiques chargées depuis {file_path}")
        return metrics_data
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des métriques historiques: {str(e)}")
        return {}


def export_schedule(schedule: Schedule, file_path: str, format_type: str) -> None:
    """
    Exporte un planning dans le format spécifié.
    
    Args:
        schedule: Planning à exporter
        file_path: Chemin du fichier de sortie
        format_type: Type de format (json, csv)
    """
    try:
        if format_type.lower() == 'json':
            # Export en JSON
            schedule_data = {
                'schedule_id': schedule.schedule_id,
                'name': schedule.name,
                'start_date': schedule.start_date.strftime('%Y-%m-%d'),
                'end_date': schedule.end_date.strftime('%Y-%m-%d'),
                'status': schedule.status.value if hasattr(schedule.status, 'value') else str(schedule.status),
                'shifts': []
            }
            
            for shift in schedule.shifts:
                shift_data = {
                    'shift_id': shift.shift_id,
                    'date': shift.date.strftime('%Y-%m-%d'),
                    'start_time': shift.start_time.strftime('%H:%M'),
                    'end_time': shift.end_time.strftime('%H:%M'),
                    'role': shift.role.value if hasattr(shift.role, 'value') else str(shift.role),
                    'shift_type': shift.shift_type.value if hasattr(shift.shift_type, 'value') else str(shift.shift_type)
                }
                
                if shift.employee_id:
                    shift_data['employee_id'] = shift.employee_id
                    if shift.employee:
                        shift_data['employee_name'] = shift.employee.name
                
                schedule_data['shifts'].append(shift_data)
            
            # Ajouter les métadonnées
            if hasattr(schedule, 'metadata') and schedule.metadata:
                schedule_data['metadata'] = {k: v for k, v in schedule.metadata.items() if not isinstance(v, (dict, list))}
            
            # Écrire le fichier JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(schedule_data, f, indent=2)
        
        elif format_type.lower() == 'csv':
            # Export en CSV
            rows = []
            
            # En-têtes
            headers = ['Date', 'Jour', 'Début', 'Fin', 'Rôle', 'ID Employé', 'Nom Employé']
            
            # Ajouter les shifts
            for shift in schedule.shifts:
                day_name = shift.date.strftime('%A')  # Nom du jour
                
                row = [
                    shift.date.strftime('%Y-%m-%d'),
                    day_name,
                    shift.start_time.strftime('%H:%M'),
                    shift.end_time.strftime('%H:%M'),
                    shift.role.value if hasattr(shift.role, 'value') else str(shift.role),
                    shift.employee_id or '',
                    shift.employee.name if shift.employee else ''
                ]
                
                rows.append(row)
            
            # Écrire le fichier CSV
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        
        else:
            logger.error(f"Format d'export non pris en charge: {format_type}")
            return
        
        logger.info(f"Planning exporté avec succès: {file_path}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'export du planning: {str(e)}")


def progress_callback(current: int, total: int, stats: Dict) -> None:
    """
    Callback pour suivre la progression de l'optimisation.
    
    Args:
        current: Génération actuelle
        total: Nombre total de générations
        stats: Statistiques de génération
    """
    if current % 5 == 0 or current == total - 1:
        print(f"\rGénération {current + 1}/{total}: Score={stats['best_fitness']:.4f}", end='')


def command_generate(args: argparse.Namespace) -> None:
    """
    Commande pour générer un planning standard.
    
    Args:
        args: Arguments de la ligne de commande
    """
    logger.info("Génération d'un planning standard...")
    
    # Charger les employés
    employees = load_employees(args.employees)
    
    # Charger les besoins en personnel s'ils sont spécifiés
    staffing_needs = None
    if args.staffing_needs:
        staffing_needs = load_staffing_needs(args.staffing_needs)
    
    # Dates du planning
    start_date = format_date(args.start_date)
    end_date = start_date + timedelta(days=args.days - 1)
    
    # Configuration de l'optimiseur
    optimizer_config = {
        "population_size": args.population_size,
        "generations": args.generations,
        "mutation_rate": args.mutation_rate,
        "crossover_rate": args.crossover_rate,
        "parallel_processing": not args.no_parallel,
        "timeout_seconds": args.timeout
    }
    
    # Créer et configurer l'optimiseur
    optimizer = ScheduleOptimizer(
        config=optimizer_config,
        progress_callback=progress_callback
    )
    
    # Générer le planning
    optimized_schedule = optimizer.generate_schedule(
        start_date=start_date,
        end_date=end_date,
        employees=employees,
        staffing_needs=staffing_needs
    )
    
    # Afficher un résumé
    print("\n")
    print("=" * 80)
    print(f"Planning généré pour la période : {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    print(f"Shifts totaux : {len(optimized_schedule.shifts)}")
    assigned_shifts = sum(1 for shift in optimized_schedule.shifts if shift.employee_id)
    print(f"Shifts assignés : {assigned_shifts} ({assigned_shifts / max(1, len(optimized_schedule.shifts)) * 100:.1f}%)")
    print(f"Score d'optimisation : {optimizer.best_fitness:.4f}")
    print(f"Temps d'optimisation : {optimized_schedule.metadata.get('optimization_duration', 0):.2f} secondes")
    print("=" * 80)
    
    # Exporter le planning si demandé
    if args.output:
        format_type = args.format or 'json'
        export_schedule(optimized_schedule, args.output, format_type)


def command_generate_ml(args: argparse.Namespace) -> None:
    """
    Commande pour générer un planning avec l'optimiseur ML.
    
    Args:
        args: Arguments de la ligne de commande
    """
    logger.info("Génération d'un planning avec l'optimiseur ML...")
    
    # Charger les employés
    employees = load_employees(args.employees)
    
    # Charger les besoins en personnel s'ils sont spécifiés
    staffing_needs = None
    if args.staffing_needs:
        staffing_needs = load_staffing_needs(args.staffing_needs)
    
    # Dates du planning
    start_date = format_date(args.start_date)
    end_date = start_date + timedelta(days=args.days - 1)
    
    # Configuration de l'optimiseur
    optimizer_config = {
        "population_size": args.population_size,
        "generations": args.generations,
        "mutation_rate": args.mutation_rate,
        "crossover_rate": args.crossover_rate,
        "ml_weight": args.ml_weight,
        "parallel_processing": not args.no_parallel,
        "timeout_seconds": args.timeout
    }
    
    # Créer et configurer l'optimiseur ML
    ml_optimizer = MLScheduleOptimizer(
        config=optimizer_config,
        progress_callback=progress_callback,
        model_path=args.model_path
    )
    
    # Si un modèle est spécifié, essayer de le charger
    if args.model_path and os.path.exists(args.model_path):
        logger.info(f"Chargement du modèle ML: {args.model_path}")
        ml_optimizer.import_optimization_model(args.model_path)
    
    # Sinon, charger les données historiques et entraîner un modèle
    elif args.historical_data:
        logger.info("Chargement et analyse des données historiques...")
        
        # Charger les plannings historiques
        historical_schedules = load_historical_schedules(args.historical_data)
        
        # Charger les métriques historiques si spécifiées
        historical_metrics = {}
        if args.historical_metrics:
            historical_metrics = load_historical_metrics(args.historical_metrics)
        
        # Charger les données historiques dans l'optimiseur
        ml_optimizer.load_historical_data(historical_schedules, historical_metrics)
        
        # Entraîner le modèle
        logger.info("Entraînement du modèle ML...")
        ml_optimizer.train_model()
        
        # Sauvegarder le modèle si demandé
        if args.save_model:
            logger.info(f"Sauvegarde du modèle ML: {args.save_model}")
            ml_optimizer.export_optimization_model(args.save_model)
    
    # Générer le planning
    optimized_schedule = ml_optimizer.generate_schedule(
        start_date=start_date,
        end_date=end_date,
        employees=employees,
        staffing_needs=staffing_needs
    )
    
    # Analyser les résultats
    analysis = ml_optimizer.analyze_optimization_results(optimized_schedule)
    
    # Afficher un résumé
    print("\n")
    print("=" * 80)
    print(f"Planning généré pour la période : {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    print(f"Shifts totaux : {len(optimized_schedule.shifts)}")
    assigned_shifts = sum(1 for shift in optimized_schedule.shifts if shift.employee_id)
    print(f"Shifts assignés : {assigned_shifts} ({assigned_shifts / max(1, len(optimized_schedule.shifts)) * 100:.1f}%)")
    print(f"Score d'optimisation : {ml_optimizer.best_fitness:.4f}")
    print(f"Temps d'optimisation : {optimized_schedule.metadata.get('optimization_duration', 0):.2f} secondes")
    
    # Afficher les insights
    print("\nInsights d'optimisation:")
    for insight in analysis["insights"]:
        print(f"  [{insight['type'].upper()}] {insight['message']}")
        if insight["suggested_action"]:
            print(f"    → Action suggérée: {insight['suggested_action']}")
    
    # Afficher les caractéristiques importantes si un modèle a été utilisé
    if ml_optimizer.model and ml_optimizer.feature_importance:
        print("\nCaractéristiques importantes:")
        
        # Afficher les 5 caractéristiques les plus importantes
        features = sorted(ml_optimizer.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        for feature, importance in features:
            print(f"  {feature}: {importance:.4f}")
    
    print("=" * 80)
    
    # Exporter le planning si demandé
    if args.output:
        format_type = args.format or 'json'
        export_schedule(optimized_schedule, args.output, format_type)


def main():
    """
    Fonction principale de l'interface en ligne de commande.
    """
    # Créer le parseur principal
    parser = argparse.ArgumentParser(description="Outil d'optimisation des plannings pour Le Vieux Moulin")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Parseur pour la commande 'generate'
    parser_generate = subparsers.add_parser('generate', help="Générer un planning optimisé standard")
    parser_generate.add_argument('--start-date', required=True, help="Date de début (YYYY-MM-DD)")
    parser_generate.add_argument('--days', type=int, default=7, help="Nombre de jours (défaut: 7)")
    parser_generate.add_argument('--employees', required=True, help="Fichier des employés (CSV ou JSON)")
    parser_generate.add_argument('--staffing-needs', help="Fichier des besoins en personnel (JSON)")
    parser_generate.add_argument('--output', help="Fichier de sortie pour le planning généré")
    parser_generate.add_argument('--format', choices=['json', 'csv'], default='json', help="Format de sortie (défaut: json)")
    parser_generate.add_argument('--population-size', type=int, default=100, help="Taille de la population (défaut: 100)")
    parser_generate.add_argument('--generations', type=int, default=50, help="Nombre de générations (défaut: 50)")
    parser_generate.add_argument('--mutation-rate', type=float, default=0.1, help="Taux de mutation (défaut: 0.1)")
    parser_generate.add_argument('--crossover-rate', type=float, default=0.8, help="Taux de croisement (défaut: 0.8)")
    parser_generate.add_argument('--timeout', type=int, default=120, help="Timeout en secondes (défaut: 120)")
    parser_generate.add_argument('--no-parallel', action='store_true', help="Désactiver le traitement parallèle")
    
    # Parseur pour la commande 'generate-ml'
    parser_generate_ml = subparsers.add_parser('generate-ml', help="Générer un planning optimisé avec ML")
    parser_generate_ml.add_argument('--start-date', required=True, help="Date de début (YYYY-MM-DD)")
    parser_generate_ml.add_argument('--days', type=int, default=7, help="Nombre de jours (défaut: 7)")
    parser_generate_ml.add_argument('--employees', required=True, help="Fichier des employés (CSV ou JSON)")
    parser_generate_ml.add_argument('--staffing-needs', help="Fichier des besoins en personnel (JSON)")
    parser_generate_ml.add_argument('--historical-data', help="Fichier des plannings historiques (JSON)")
    parser_generate_ml.add_argument('--historical-metrics', help="Fichier des métriques historiques (JSON)")
    parser_generate_ml.add_argument('--model-path', help="Chemin du modèle ML pré-entraîné")
    parser_generate_ml.add_argument('--save-model', help="Chemin pour sauvegarder le modèle entraîné")
    parser_generate_ml.add_argument('--output', help="Fichier de sortie pour le planning généré")
    parser_generate_ml.add_argument('--format', choices=['json', 'csv'], default='json', help="Format de sortie (défaut: json)")
    parser_generate_ml.add_argument('--population-size', type=int, default=100, help="Taille de la population (défaut: 100)")
    parser_generate_ml.add_argument('--generations', type=int, default=50, help="Nombre de générations (défaut: 50)")
    parser_generate_ml.add_argument('--mutation-rate', type=float, default=0.1, help="Taux de mutation (défaut: 0.1)")
    parser_generate_ml.add_argument('--crossover-rate', type=float, default=0.8, help="Taux de croisement (défaut: 0.8)")
    parser_generate_ml.add_argument('--ml-weight', type=float, default=0.3, help="Poids du modèle ML (défaut: 0.3)")
    parser_generate_ml.add_argument('--timeout', type=int, default=120, help="Timeout en secondes (défaut: 120)")
    parser_generate_ml.add_argument('--no-parallel', action='store_true', help="Désactiver le traitement parallèle")
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Exécuter la commande appropriée
    if args.command == 'generate':
        command_generate(args)
    elif args.command == 'generate-ml':
        command_generate_ml(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
