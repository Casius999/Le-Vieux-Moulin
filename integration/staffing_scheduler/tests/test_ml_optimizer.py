#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests unitaires pour le module MLScheduleOptimizer.

Ce module contient les tests pour vérifier le bon fonctionnement
de l'optimiseur ML pour la génération de plannings.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
import random
import tempfile
import json

# Configuration du chemin pour importer le module staffing_scheduler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from integration.staffing_scheduler.scheduler.ml_optimizer import MLScheduleOptimizer
from integration.staffing_scheduler.models.employee import Employee, EmployeeRole
from integration.staffing_scheduler.models.schedule import Schedule, ScheduleStatus
from integration.staffing_scheduler.models.shift import Shift, ShiftType
from integration.staffing_scheduler.models.constraint import Constraint, ConstraintSet, ConstraintPriority

# Création de mocks pour les tests
def create_test_employees(count=10):
    """Crée une liste d'employés pour les tests."""
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
        
        # Créer l'employé
        employee = Employee(
            employee_id=f"TEST_EMP{i+1}",
            name=f"Test Employee {i+1}",
            primary_role=primary_role,
            secondary_roles=secondary_roles
        )
        
        # Ajouter des attributs personnalisés pour les tests
        employee.hourly_rate = round(random.uniform(12.0, 25.0), 2)
        employee.preferred_days = random.sample(range(7), random.randint(1, 3))
        employee.can_work_role = lambda role, primary=primary_role, secondary=secondary_roles: role == primary or role in secondary
        
        employees.append(employee)
    
    return employees

def create_test_schedule(start_date, end_date, employees=None):
    """Crée un planning de test avec des shifts."""
    schedule = Schedule.create_new(
        start_date=start_date,
        end_date=end_date,
        name=f"Test Schedule {start_date.strftime('%Y-%m-%d')}",
        created_by="test_system"
    )
    
    # Ajouter des shifts
    current_date = start_date
    while current_date <= end_date:
        # Shifts du matin pour tous les rôles
        for role in EmployeeRole:
            shift = Shift.create_new(
                date=current_date,
                start_time=datetime.strptime("10:00", "%H:%M").time(),
                end_time=datetime.strptime("15:00", "%H:%M").time(),
                role=role,
                shift_type=ShiftType.MIDDAY
            )
            schedule.add_shift(shift)
        
        # Shifts du soir pour tous les rôles
        for role in EmployeeRole:
            shift = Shift.create_new(
                date=current_date,
                start_time=datetime.strptime("18:00", "%H:%M").time(),
                end_time=datetime.strptime("23:00", "%H:%M").time(),
                role=role,
                shift_type=ShiftType.EVENING
            )
            schedule.add_shift(shift)
        
        current_date += timedelta(days=1)
    
    # Si des employés sont fournis, assigner aléatoirement
    if employees:
        for shift in schedule.shifts:
            if random.random() < 0.8:  # 80% de chance d'être assigné
                eligible_employees = [e for e in employees if e.can_work_role(shift.role)]
                if eligible_employees:
                    employee = random.choice(eligible_employees)
                    shift.assign_employee(employee)
    
    return schedule

def create_test_metrics(schedule):
    """Crée des métriques de test pour un planning."""
    metrics = {
        "coverage_rate": random.uniform(0.8, 1.0),
        "preference_satisfaction": random.uniform(0.7, 0.95),
        "cost_efficiency": random.uniform(0.7, 0.9),
        "fairness_index": random.uniform(0.75, 0.95),
        "customer_satisfaction": random.uniform(0.75, 0.98),
        "employee_metrics": {}
    }
    
    # Ajouter des métriques par employé
    for shift in schedule.shifts:
        if shift.employee_id:
            if shift.employee_id not in metrics["employee_metrics"]:
                metrics["employee_metrics"][shift.employee_id] = random.uniform(0.7, 0.95)
    
    return metrics


class TestMLScheduleOptimizer(unittest.TestCase):
    """Tests pour la classe MLScheduleOptimizer."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Configuration pour les tests
        self.test_config = {
            "population_size": 20,  # Réduit pour accélérer les tests
            "generations": 10,      # Réduit pour accélérer les tests
            "mutation_rate": 0.2,
            "crossover_rate": 0.8,
            "elitism_count": 2,
            "ml_weight": 0.3,
            "weights": {
                "coverage": 0.4,
                "preferences": 0.3,
                "cost": 0.2,
                "stability": 0.1
            },
            "parallel_processing": False,  # Désactivé pour les tests
            "timeout_seconds": 30
        }
        
        # Créer l'optimiseur
        self.optimizer = MLScheduleOptimizer(config=self.test_config)
        
        # Créer des employés de test
        self.employees = create_test_employees(10)
        
        # Dates pour les tests
        self.today = datetime.now()
        self.start_date = self.today - timedelta(days=7)
        self.end_date = self.start_date + timedelta(days=6)
        
        # Plannings historiques pour l'entraînement
        self.historical_schedules = []
        for i in range(3):
            hist_start = self.start_date - timedelta(days=(i+1)*14)
            hist_end = hist_start + timedelta(days=6)
            schedule = create_test_schedule(hist_start, hist_end, self.employees)
            self.historical_schedules.append(schedule)
        
        # Métriques historiques
        self.historical_metrics = {}
        for schedule in self.historical_schedules:
            self.historical_metrics[schedule.schedule_id] = create_test_metrics(schedule)
    
    def test_initialization(self):
        """Teste l'initialisation correcte de l'optimiseur ML."""
        # Vérifier que l'optimiseur est correctement initialisé
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.config["population_size"], 20)
        self.assertEqual(self.optimizer.config["generations"], 10)
        self.assertEqual(self.optimizer.config["ml_weight"], 0.3)
        
        # Vérifier que les structures internes sont initialisées
        self.assertEqual(self.optimizer.feature_importance, {})
        self.assertEqual(self.optimizer.historical_performance, {})
        self.assertEqual(self.optimizer.employee_performance, {})
        self.assertIsNone(self.optimizer.model)
    
    def test_load_historical_data(self):
        """Teste le chargement des données historiques."""
        # Charger les données historiques
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        
        # Vérifier que les données sont chargées
        self.assertTrue(len(self.optimizer.historical_performance) > 0)
        
        # Vérifier que chaque planning historique est présent
        for schedule in self.historical_schedules:
            self.assertIn(schedule.schedule_id, self.optimizer.historical_performance)
            
            # Vérifier la structure des données
            perf_data = self.optimizer.historical_performance[schedule.schedule_id]
            self.assertIn("features", perf_data)
            self.assertIn("performance", perf_data)
            
            # Vérifier les caractéristiques extraites
            features = perf_data["features"]
            self.assertIn("total_shifts", features)
            self.assertIn("assigned_shifts", features)
            self.assertIn("assignments_by_role", features)
    
    def test_train_model(self):
        """Teste l'entraînement du modèle ML."""
        # Charger les données historiques
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        
        # Entraîner le modèle
        result = self.optimizer.train_model()
        
        # Vérifier que l'entraînement a réussi
        self.assertTrue(result)
        
        # Vérifier que le modèle est créé
        self.assertIsNotNone(self.optimizer.model)
        self.assertIn("weights", self.optimizer.model)
        self.assertIn("feature_count", self.optimizer.model)
        
        # Vérifier l'importance des caractéristiques
        self.assertTrue(len(self.optimizer.feature_importance) > 0)
    
    def test_predict_schedule_performance(self):
        """Teste la prédiction de performance d'un planning."""
        # Charger les données historiques et entraîner le modèle
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        self.optimizer.train_model()
        
        # Créer un planning de test
        schedule = create_test_schedule(self.today, self.today + timedelta(days=6), self.employees)
        
        # Prédire la performance
        performance = self.optimizer.predict_schedule_performance(schedule)
        
        # Vérifier que le score est entre 0 et 1
        self.assertGreaterEqual(performance, 0.0)
        self.assertLessEqual(performance, 1.0)
    
    def test_evaluate_fitness(self):
        """Teste l'évaluation de fitness d'un planning."""
        # Charger les données historiques et entraîner le modèle
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        self.optimizer.train_model()
        
        # Créer un planning de test
        schedule = create_test_schedule(self.today, self.today + timedelta(days=6), self.employees)
        
        # Évaluer le fitness
        fitness = self.optimizer._evaluate_fitness(schedule)
        
        # Vérifier que le score est positif
        self.assertGreater(fitness, 0.0)
    
    def test_generate_schedule(self):
        """Teste la génération complète d'un planning optimisé."""
        # Charger les données historiques et entraîner le modèle
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        self.optimizer.train_model()
        
        # Générer un planning optimisé
        optimized_schedule = self.optimizer.generate_schedule(
            start_date=self.today,
            end_date=self.today + timedelta(days=6),
            employees=self.employees
        )
        
        # Vérifier que le planning est généré
        self.assertIsNotNone(optimized_schedule)
        self.assertEqual(optimized_schedule.start_date, self.today)
        self.assertEqual(optimized_schedule.end_date, self.today + timedelta(days=6))
        
        # Vérifier que des shifts sont créés
        self.assertTrue(len(optimized_schedule.shifts) > 0)
        
        # Vérifier que des employés sont assignés
        assigned_shifts = sum(1 for shift in optimized_schedule.shifts if shift.employee_id)
        self.assertTrue(assigned_shifts > 0)
        
        # Vérifier que les métadonnées sont ajoutées
        self.assertIn("optimization_duration", optimized_schedule.metadata)
        self.assertIn("generations_completed", optimized_schedule.metadata)
        self.assertIn("final_fitness", optimized_schedule.metadata)
    
    def test_export_import_model(self):
        """Teste l'export et l'import du modèle d'optimisation."""
        # Charger les données historiques et entraîner le modèle
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        self.optimizer.train_model()
        
        # Créer un fichier temporaire pour le test
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            model_path = tmp_file.name
        
        try:
            # Exporter le modèle
            export_result = self.optimizer.export_optimization_model(model_path)
            self.assertTrue(export_result)
            self.assertTrue(os.path.exists(model_path))
            
            # Vérifier le contenu du fichier
            with open(model_path, 'r') as f:
                model_data = json.load(f)
            self.assertIn("model", model_data)
            self.assertIn("feature_importance", model_data)
            
            # Créer un nouvel optimiseur
            new_optimizer = MLScheduleOptimizer(config=self.test_config)
            
            # Importer le modèle
            import_result = new_optimizer.import_optimization_model(model_path)
            self.assertTrue(import_result)
            
            # Vérifier que le modèle est chargé
            self.assertIsNotNone(new_optimizer.model)
            self.assertEqual(len(new_optimizer.feature_importance), len(self.optimizer.feature_importance))
            
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(model_path):
                os.unlink(model_path)
    
    def test_employee_insights(self):
        """Teste la génération d'insights sur les employés."""
        # Charger les données historiques et entraîner le modèle
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        
        # Choisir un employé avec des données historiques
        employee_id = None
        for schedule in self.historical_schedules:
            for shift in schedule.shifts:
                if shift.employee_id:
                    employee_id = shift.employee_id
                    break
            if employee_id:
                break
        
        if employee_id:
            # Générer des insights
            insights = self.optimizer.get_employee_insights(employee_id)
            
            # Vérifier la structure des insights
            self.assertIn("employee_id", insights)
            self.assertEqual(insights["employee_id"], employee_id)
            self.assertIn("shifts_worked", insights)
            self.assertIn("recommendations", insights)
            self.assertTrue(isinstance(insights["recommendations"], list))
    
    def test_analyze_optimization_results(self):
        """Teste l'analyse des résultats d'optimisation."""
        # Charger les données historiques et entraîner le modèle
        self.optimizer.load_historical_data(self.historical_schedules, self.historical_metrics)
        self.optimizer.train_model()
        
        # Générer un planning optimisé
        optimized_schedule = self.optimizer.generate_schedule(
            start_date=self.today,
            end_date=self.today + timedelta(days=6),
            employees=self.employees
        )
        
        # Analyser les résultats
        analysis = self.optimizer.analyze_optimization_results(optimized_schedule)
        
        # Vérifier la structure de l'analyse
        self.assertIn("metrics", analysis)
        self.assertIn("insights", analysis)
        self.assertTrue(isinstance(analysis["insights"], list))
        
        # Vérifier les métriques
        metrics = analysis["metrics"]
        self.assertIn("assigned_percentage", metrics)
        self.assertIn("avg_shift_duration", metrics)
        self.assertIn("role_distribution", metrics)
        
        # Vérifier les insights
        self.assertTrue(len(analysis["insights"]) > 0)
        for insight in analysis["insights"]:
            self.assertIn("type", insight)
            self.assertIn("message", insight)
            self.assertIn("suggested_action", insight)


if __name__ == "__main__":
    unittest.main()
