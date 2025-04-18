#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'optimisation des plannings.

Ce module implémente l'algorithme génétique utilisé pour optimiser les plannings
en fonction des contraintes, des prévisions d'affluence et des préférences.
"""

import copy
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set, Optional, Any, Callable, Union
import concurrent.futures
import threading
from functools import partial

from ..models.employee import Employee, EmployeeRole
from ..models.shift import Shift, ShiftType
from ..models.schedule import Schedule, ScheduleStatus
from ..models.constraint import Constraint, ConstraintSet, ConstraintPriority
from ..config import OPTIMIZATION_CONFIG, SCHEDULING_CONSTRAINTS

# Configurer le logger
logger = logging.getLogger(__name__)


class ScheduleOptimizer:
    """
    Optimiseur de planning utilisant un algorithme génétique.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        constraint_set: Optional[ConstraintSet] = None,
        progress_callback: Optional[Callable[[int, int, Dict], None]] = None
    ):
        """
        Initialise l'optimiseur de planning.
        
        Args:
            config: Configuration personnalisée (surcharge OPTIMIZATION_CONFIG)
            constraint_set: Ensemble de contraintes personnalisé
            progress_callback: Fonction de callback pour le suivi de progression
        """
        # Charger la configuration par défaut ou personnalisée
        self.config = copy.deepcopy(OPTIMIZATION_CONFIG)
        if config:
            self.config.update(config)
            
        # Initialiser l'ensemble de contraintes
        self.constraint_set = constraint_set or ConstraintSet()
        
        # Callback de progression
        self.progress_callback = progress_callback
        
        # État de l'optimisation
        self.stop_requested = False
        self.current_generation = 0
        self.best_schedule = None
        self.best_fitness = -float('inf')
        self.generation_stats = []
        
    def reset(self) -> None:
        """
        Réinitialise l'état de l'optimiseur.
        """
        self.stop_requested = False
        self.current_generation = 0
        self.best_schedule = None
        self.best_fitness = -float('inf')
        self.generation_stats = []
    
    def generate_schedule(
        self,
        start_date: datetime,
        end_date: datetime,
        employees: List[Employee],
        staffing_needs: Optional[Dict] = None,
        constraints: Optional[List[Constraint]] = None,
        previous_schedule: Optional[Schedule] = None,
        **kwargs
    ) -> Schedule:
        """
        Génère un planning optimisé.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            employees: Liste des employés disponibles
            staffing_needs: Besoins en personnel (par jour/heure/poste)
            constraints: Contraintes supplémentaires
            previous_schedule: Planning précédent (optionnel)
            **kwargs: Paramètres supplémentaires
            
        Returns:
            Planning optimisé
        """
        self.reset()
        
        # Ajouter les contraintes supplémentaires
        if constraints:
            for constraint in constraints:
                self.constraint_set.add_constraint(constraint)
        
        # Création de l'objet Schedule vide
        schedule = Schedule.create_new(
            start_date=start_date,
            end_date=end_date,
            name=f"Planning {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            created_by=kwargs.get('created_by')
        )
        
        # Ajuster les paramètres selon les entrées
        if previous_schedule:
            schedule.previous_version_id = previous_schedule.schedule_id
            schedule.version = previous_schedule.version + 1
        
        # Générer les shifts nécessaires selon les besoins
        self._generate_required_shifts(schedule, staffing_needs)
        
        # Si aucun shift n'a été généré, retourner un planning vide
        if not schedule.shifts:
            logger.warning("Aucun shift n'a été généré. Vérifiez les besoins en personnel.")
            return schedule
        
        # Exécuter l'algorithme génétique
        try:
            optimized_schedule = self._run_genetic_algorithm(
                schedule=schedule,
                employees=employees,
                staffing_needs=staffing_needs,
                **kwargs
            )
            
            # Calculer les métriques finales
            optimized_schedule.calculate_metrics(staffing_needs)
            
            return optimized_schedule
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation du planning: {str(e)}")
            # En cas d'erreur, retourner le planning initial avec les shifts non assignés
            schedule.status = ScheduleStatus.DRAFT
            return schedule
    
    def _generate_required_shifts(
        self,
        schedule: Schedule,
        staffing_needs: Optional[Dict]
    ) -> None:
        """
        Génère les shifts nécessaires selon les besoins en personnel.
        
        Args:
            schedule: Planning à compléter
            staffing_needs: Besoins en personnel
        """
        if not staffing_needs:
            # Si pas de besoins définis, générer un planning de base
            self._generate_default_shifts(schedule)
            return
        
        # Format attendu pour staffing_needs:
        # {
        #     '2025-04-21': {  # date au format YYYY-MM-DD
        #         'shifts': {
        #             'matin': {
        #                 'start_time': '09:00',
        #                 'end_time': '16:00',
        #                 'roles': {
        #                     'chef': 1,
        #                     'serveur': 3,
        #                     ...
        #                 }
        #             },
        #             'soir': {
        #                 ...
        #             }
        #         }
        #     },
        #     ...
        # }
        
        current_date = schedule.start_date
        while current_date <= schedule.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Obtenir les besoins pour cette date
            day_needs = staffing_needs.get(date_str, {})
            shifts_info = day_needs.get('shifts', {})
            
            # Si aucun besoin spécifique, utiliser les besoins par défaut
            if not shifts_info:
                self._generate_day_default_shifts(schedule, current_date)
                current_date += timedelta(days=1)
                continue
            
            # Traiter chaque type de shift
            for shift_name, shift_info in shifts_info.items():
                if 'start_time' not in shift_info or 'end_time' not in shift_info or 'roles' not in shift_info:
                    logger.warning(f"Informations manquantes pour le shift {shift_name} du {date_str}")
                    continue
                
                # Convertir les heures en objets time
                try:
                    start_time = datetime.strptime(shift_info['start_time'], '%H:%M').time()
                    end_time = datetime.strptime(shift_info['end_time'], '%H:%M').time()
                except ValueError:
                    logger.error(f"Format d'heure invalide pour {shift_name} du {date_str}")
                    continue
                
                # Créer un shift pour chaque rôle et chaque personne nécessaire
                for role_name, count in shift_info['roles'].items():
                    try:
                        role = EmployeeRole(role_name)
                    except ValueError:
                        logger.error(f"Rôle inconnu: {role_name}")
                        continue
                    
                    # Créer le nombre de shifts nécessaires pour ce rôle
                    for i in range(int(count)):
                        shift = Shift.create_new(
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            role=role,
                            shift_type=ShiftType.CUSTOM
                        )
                        schedule.add_shift(shift)
            
            current_date += timedelta(days=1)
    
    def _generate_default_shifts(self, schedule: Schedule) -> None:
        """
        Génère des shifts par défaut pour toute la période du planning.
        
        Args:
            schedule: Planning à compléter
        """
        current_date = schedule.start_date
        while current_date <= schedule.end_date:
            self._generate_day_default_shifts(schedule, current_date)
            current_date += timedelta(days=1)
    
    def _generate_day_default_shifts(self, schedule: Schedule, date: datetime) -> None:
        """
        Génère des shifts par défaut pour un jour spécifique.
        
        Args:
            schedule: Planning à compléter
            date: Date du jour
        """
        # Récupérer les shifts par défaut de la configuration
        default_shifts = SCHEDULING_CONSTRAINTS.get('default_shifts', {})
        
        # Coefficient d'ajustement selon le jour de la semaine
        day_factors = SCHEDULING_CONSTRAINTS.get('day_factors', {})
        day_factor = day_factors.get(date.weekday(), 1.0)
        
        # Configuration des rôles
        roles_config = SCHEDULING_CONSTRAINTS.get('staffing_configuration', {}).get('roles', {})
        
        # Générer les shifts du matin
        if 'matin' in default_shifts:
            shift_info = default_shifts['matin']
            for role_name, config in roles_config.items():
                try:
                    role = EmployeeRole(role_name)
                    # Calculer le nombre de personnes nécessaires
                    min_count = max(config.get('min_per_shift', 0), int(config.get('min_per_shift', 0) * day_factor))
                    
                    for i in range(min_count):
                        shift = Shift.create_new(
                            date=date,
                            start_time=shift_info.get('start'),
                            end_time=shift_info.get('end'),
                            role=role,
                            shift_type=ShiftType.MIDDAY
                        )
                        schedule.add_shift(shift)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erreur lors de la génération du shift du matin pour {role_name}: {e}")
        
        # Générer les shifts du soir
        if 'soir' in default_shifts:
            shift_info = default_shifts['soir']
            for role_name, config in roles_config.items():
                try:
                    role = EmployeeRole(role_name)
                    # Calculer le nombre de personnes nécessaires
                    min_count = max(config.get('min_per_shift', 0), int(config.get('min_per_shift', 0) * day_factor))
                    
                    for i in range(min_count):
                        shift = Shift.create_new(
                            date=date,
                            start_time=shift_info.get('start'),
                            end_time=shift_info.get('end'),
                            role=role,
                            shift_type=ShiftType.EVENING
                        )
                        schedule.add_shift(shift)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erreur lors de la génération du shift du soir pour {role_name}: {e}")
    
    def _run_genetic_algorithm(
        self,
        schedule: Schedule,
        employees: List[Employee],
        staffing_needs: Optional[Dict] = None,
        **kwargs
    ) -> Schedule:
        """
        Exécute l'algorithme génétique pour optimiser le planning.
        
        Args:
            schedule: Planning initial
            employees: Liste des employés disponibles
            staffing_needs: Besoins en personnel
            **kwargs: Paramètres supplémentaires
            
        Returns:
            Planning optimisé
        """
        # Paramètres de l'algorithme
        population_size = self.config.get('population_size', 100)
        generations = self.config.get('generations', 50)
        mutation_rate = self.config.get('mutation_rate', 0.1)
        crossover_rate = self.config.get('crossover_rate', 0.8)
        elitism_count = self.config.get('elitism_count', 5)
        parallel_processing = self.config.get('parallel_processing', True)
        max_workers = self.config.get('max_workers', 4)
        timeout_seconds = self.config.get('timeout_seconds', 120)
        
        # Vérifier que les employés ont les compétences requises
        if not self._validate_employee_skills(schedule, employees):
            logger.warning("Certains shifts requièrent des compétences non disponibles dans l'équipe")
        
        # Temps de début
        start_time = time.time()
        
        # Initialiser la population
        logger.info("Initialisation de la population...")
        population = self._initialize_population(schedule, employees, population_size)
        
        # Meilleur schedule actuel
        self.best_schedule = population[0]
        self.best_fitness = self._evaluate_fitness(self.best_schedule, staffing_needs)
        
        # Créer un thread pool si traitement parallèle
        pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) if parallel_processing else None
        
        # Boucle principale de l'algorithme génétique
        logger.info(f"Démarrage de l'algorithme génétique avec {generations} générations...")
        
        for generation in range(generations):
            self.current_generation = generation
            
            # Vérifier si arrêt demandé
            if self.stop_requested:
                logger.info("Arrêt demandé de l'algorithme génétique")
                break
                
            # Vérifier timeout
            if (time.time() - start_time) > timeout_seconds:
                logger.info(f"Timeout atteint après {time.time() - start_time:.2f} secondes")
                break
            
            # Évaluer la population
            if parallel_processing and pool:
                # Évaluation parallèle
                partial_eval = partial(self._evaluate_fitness, staffing_needs=staffing_needs)
                fitness_values = list(pool.map(partial_eval, population))
            else:
                # Évaluation séquentielle
                fitness_values = [self._evaluate_fitness(schedule, staffing_needs) for schedule in population]
            
            # Trier la population par fitness
            population_fitness = list(zip(population, fitness_values))
            population_fitness.sort(key=lambda x: x[1], reverse=True)
            
            # Récupérer le meilleur schedule de cette génération
            current_best_schedule, current_best_fitness = population_fitness[0]
            
            # Mettre à jour le meilleur overall si nécessaire
            if current_best_fitness > self.best_fitness:
                self.best_schedule = copy.deepcopy(current_best_schedule)
                self.best_fitness = current_best_fitness
                logger.info(f"Génération {generation}: Nouveau meilleur score: {self.best_fitness:.4f}")
            
            # Enregistrer les statistiques
            gen_stats = {
                "generation": generation,
                "best_fitness": current_best_fitness,
                "avg_fitness": sum(fitness_values) / len(fitness_values),
                "worst_fitness": min(fitness_values),
                "elapsed_time": time.time() - start_time
            }
            self.generation_stats.append(gen_stats)
            
            # Appeler le callback de progression si défini
            if self.progress_callback:
                try:
                    self.progress_callback(generation, generations, gen_stats)
                except Exception as e:
                    logger.error(f"Erreur dans le callback de progression: {str(e)}")
            
            # Créer la nouvelle population
            new_population = []
            
            # Élitisme: conserver les meilleurs individus
            elite_schedules = [schedule for schedule, _ in population_fitness[:elitism_count]]
            new_population.extend(copy.deepcopy(elite_schedules))
            
            # Compléter la population avec sélection, croisement et mutation
            while len(new_population) < population_size:
                # Sélectionner deux parents
                parent1, parent2 = self._selection(population_fitness)
                
                # Croisement (avec probabilité)
                if random.random() < crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
                
                # Mutation (avec probabilité)
                if random.random() < mutation_rate:
                    self._mutate(child1, employees)
                if random.random() < mutation_rate:
                    self._mutate(child2, employees)
                
                # Ajouter les enfants à la nouvelle population
                new_population.append(child1)
                if len(new_population) < population_size:
                    new_population.append(child2)
            
            # Remplacer l'ancienne population
            population = new_population
            
            # Log de progression
            if generation % 5 == 0 or generation == generations - 1:
                logger.info(f"Génération {generation}/{generations} - Meilleur fitness: {self.best_fitness:.4f}")
        
        # Fermer le pool si utilisé
        if pool:
            pool.shutdown()
        
        # Duration de l'optimisation
        duration = time.time() - start_time
        logger.info(f"Optimisation terminée en {duration:.2f} secondes")
        
        # Ajouter des métadonnées au planning optimal
        if self.best_schedule:
            self.best_schedule.metadata.update({
                "optimization_duration": duration,
                "generations_completed": self.current_generation + 1,
                "final_fitness": self.best_fitness,
                "algorithm": "genetic",
                "config": {k: v for k, v in self.config.items() if k not in ["validation_function", "penalty_function"]}
            })
        
        return self.best_schedule
    
    def _validate_employee_skills(self, schedule: Schedule, employees: List[Employee]) -> bool:
        """
        Vérifie que les employés ont les compétences nécessaires pour les shifts.
        
        Args:
            schedule: Planning à valider
            employees: Liste des employés
            
        Returns:
            True si toutes les compétences sont disponibles, False sinon
        """
        # Collecter tous les rôles nécessaires
        required_roles = set()
        for shift in schedule.shifts:
            required_roles.add(shift.role)
        
        # Vérifier les compétences des employés
        available_roles = set()
        for employee in employees:
            available_roles.add(employee.primary_role)
            available_roles.update(employee.secondary_roles)
        
        # Vérifier que tous les rôles requis sont disponibles
        missing_roles = required_roles - available_roles
        if missing_roles:
            logger.warning(f"Rôles manquants dans l'équipe: {missing_roles}")
            return False
        
        return True
    
    def _initialize_population(
        self,
        base_schedule: Schedule,
        employees: List[Employee],
        population_size: int
    ) -> List[Schedule]:
        """
        Initialise la population avec des plannings aléatoires.
        
        Args:
            base_schedule: Planning de base avec shifts non assignés
            employees: Liste des employés disponibles
            population_size: Taille de la population
            
        Returns:
            Liste de plannings générés aléatoirement
        """
        population = []
        
        # Créer une copie profonde du planning de base
        for i in range(population_size):
            # Cloner le planning de base
            schedule_copy = copy.deepcopy(base_schedule)
            
            # Assignation aléatoire des employés aux shifts
            for shift in schedule_copy.shifts:
                # Filtrer les employés qui peuvent travailler ce rôle
                eligible_employees = [e for e in employees if e.can_work_role(shift.role)]
                
                if eligible_employees:
                    if random.random() < 0.8:  # 80% de chance d'assigner un employé
                        # Choisir un employé aléatoire parmi ceux éligibles
                        employee = random.choice(eligible_employees)
                        shift.assign_employee(employee)
            
            population.append(schedule_copy)
        
        return population
    
    def _evaluate_fitness(self, schedule: Schedule, staffing_needs: Optional[Dict] = None) -> float:
        """
        Évalue la qualité d'un planning.
        
        Args:
            schedule: Planning à évaluer
            staffing_needs: Besoins en personnel
            
        Returns:
            Score de fitness (plus élevé = meilleur)
        """
        # Poids pour les différents critères
        weights = self.config.get('weights', {})
        coverage_weight = weights.get('coverage', 0.4)
        preferences_weight = weights.get('preferences', 0.3)
        cost_weight = weights.get('cost', 0.2)
        stability_weight = weights.get('stability', 0.1)
        
        # 1. Score de couverture des besoins
        coverage_score = self._calculate_coverage_score(schedule, staffing_needs)
        
        # 2. Score de respect des préférences
        preferences_score = self._calculate_preferences_score(schedule)
        
        # 3. Score de coût
        cost_score = self._calculate_cost_score(schedule)
        
        # 4. Score de respect des contraintes
        constraints_score = self._calculate_constraints_score(schedule)
        
        # 5. Score de stabilité (minimiser les changements)
        stability_score = 1.0  # Par défaut, pas de pénalité pour stabilité
        
        # Calculer le score final pondéré
        fitness = (
            coverage_weight * coverage_score +
            preferences_weight * preferences_score +
            cost_weight * cost_score +
            stability_weight * stability_score
        )
        
        # Pénalité pour les contraintes non respectées
        if constraints_score < 0.5:  # Si moins de 50% des contraintes sont respectées
            fitness *= constraints_score
        
        return fitness
    
    def _calculate_coverage_score(self, schedule: Schedule, staffing_needs: Optional[Dict] = None) -> float:
        """
        Calcule le score de couverture des besoins en personnel.
        
        Args:
            schedule: Planning à évaluer
            staffing_needs: Besoins en personnel
            
        Returns:
            Score de couverture (0-1)
        """
        # Si pas de besoins définis, compter le taux d'affectation
        if not staffing_needs:
            assigned_shifts = sum(1 for shift in schedule.shifts if shift.employee_id)
            return assigned_shifts / max(1, len(schedule.shifts))
        
        # TODO: Implémentation de l'évaluation basée sur les besoins détaillés
        # Pour cette version de base, nous utilisons le taux d'affectation
        assigned_shifts = sum(1 for shift in schedule.shifts if shift.employee_id)
        return assigned_shifts / max(1, len(schedule.shifts))
    
    def _calculate_preferences_score(self, schedule: Schedule) -> float:
        """
        Calcule le score de respect des préférences des employés.
        
        Args:
            schedule: Planning à évaluer
            
        Returns:
            Score de préférences (0-1)
        """
        # Compter les shifts avec employés assignés
        total_preference_score = 0
        assigned_shifts = 0
        
        for shift in schedule.shifts:
            if shift.employee_id and shift.employee:
                assigned_shifts += 1
                
                # Vérifier la disponibilité et préférence
                preference = 0
                if hasattr(shift.employee, 'get_preference_score'):
                    preference = shift.employee.get_preference_score(
                        shift.date, shift.start_time, shift.end_time
                    )
                    # Normaliser entre 0 et 1 (de -10 à 10 => 0 à 1)
                    preference = (preference + 10) / 20
                
                total_preference_score += preference
        
        if assigned_shifts == 0:
            return 0.0
        
        return total_preference_score / assigned_shifts
    
    def _calculate_cost_score(self, schedule: Schedule) -> float:
        """
        Calcule le score de coût (inverse du coût).
        
        Args:
            schedule: Planning à évaluer
            
        Returns:
            Score de coût (0-1, plus élevé = moins coûteux)
        """
        # Calculer le coût total
        total_cost = 0.0
        max_cost = 0.0
        
        for shift in schedule.shifts:
            duration = shift.duration
            
            # Calculer le coût maximum théorique (taux horaire le plus élevé)
            max_hourly_rate = 25.0  # Valeur arbitraire pour cet exemple
            max_cost += duration * max_hourly_rate
            
            # Calculer le coût réel si un employé est assigné
            if shift.employee_id and shift.employee:
                hourly_rate = getattr(shift.employee, 'hourly_rate', 15.0)
                total_cost += duration * hourly_rate
        
        if max_cost == 0:
            return 1.0
        
        # Score inversé: plus le coût est bas, plus le score est haut
        return 1.0 - (total_cost / max_cost)
    
    def _calculate_constraints_score(self, schedule: Schedule) -> float:
        """
        Calcule le score de respect des contraintes.
        
        Args:
            schedule: Planning à évaluer
            
        Returns:
            Score de contraintes (0-1)
        """
        # Récupérer le contexte d'évaluation
        context = {
            "schedule": schedule,
            "shifts": schedule.shifts,
            "period": {
                "start_date": schedule.start_date,
                "end_date": schedule.end_date
            }
        }
        
        # Vérifier toutes les contraintes
        all_valid, violated = self.constraint_set.validate_all(context)
        
        # Si toutes les contraintes sont respectées, score parfait
        if all_valid:
            return 1.0
        
        # Sinon, calculer un score basé sur le nombre et la priorité des contraintes violées
        total_weight = sum(1 for _ in self.constraint_set.constraints if _.is_active)
        if total_weight == 0:
            return 1.0
        
        violated_weight = 0
        for constraint in violated:
            if constraint.priority == ConstraintPriority.MANDATORY:
                violated_weight += 5
            elif constraint.priority == ConstraintPriority.HIGH:
                violated_weight += 3
            elif constraint.priority == ConstraintPriority.MEDIUM:
                violated_weight += 2
            elif constraint.priority == ConstraintPriority.LOW:
                violated_weight += 1
            else:  # OPTIONAL
                violated_weight += 0.5
        
        # Score: plus de contraintes violées = score plus bas
        return max(0.0, 1.0 - (violated_weight / (total_weight * 3)))
    
    def _selection(self, population_fitness: List[Tuple[Schedule, float]]) -> Tuple[Schedule, Schedule]:
        """
        Sélectionne deux parents pour le croisement en utilisant la sélection par tournoi.
        
        Args:
            population_fitness: Liste de tuples (schedule, fitness)
            
        Returns:
            Deux plannings parents
        """
        # Paramètres du tournoi
        tournament_size = min(5, len(population_fitness) // 2)
        
        # Sélection du premier parent
        tournament1 = random.sample(population_fitness, tournament_size)
        tournament1.sort(key=lambda x: x[1], reverse=True)
        parent1 = tournament1[0][0]
        
        # Sélection du second parent
        tournament2 = random.sample(population_fitness, tournament_size)
        tournament2.sort(key=lambda x: x[1], reverse=True)
        parent2 = tournament2[0][0]
        
        return parent1, parent2
    
    def _crossover(self, parent1: Schedule, parent2: Schedule) -> Tuple[Schedule, Schedule]:
        """
        Réalise un croisement entre deux plannings parents.
        
        Args:
            parent1: Premier planning parent
            parent2: Deuxième planning parent
            
        Returns:
            Deux plannings enfants
        """
        # Créer des copies des parents
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)
        
        # Faire correspondre les shifts par ID entre les deux enfants
        shift_map1 = {shift.shift_id: i for i, shift in enumerate(child1.shifts)}
        shift_map2 = {shift.shift_id: i for i, shift in enumerate(child2.shifts)}
        
        # Trouver les shifts communs aux deux plannings
        common_shifts = set(shift_map1.keys()) & set(shift_map2.keys())
        
        # Choisir un point de croisement aléatoire
        if common_shifts:
            # Convertir en liste pour le slicing
            common_shifts_list = list(common_shifts)
            crossover_point = random.randint(1, len(common_shifts_list) - 1)
            
            # Shifts à échanger
            shifts_to_swap = common_shifts_list[:crossover_point]
            
            # Échanger les assignations d'employés pour ces shifts
            for shift_id in shifts_to_swap:
                idx1 = shift_map1[shift_id]
                idx2 = shift_map2[shift_id]
                
                # Échanger les employés
                child1.shifts[idx1].employee_id, child2.shifts[idx2].employee_id = \
                    child2.shifts[idx2].employee_id, child1.shifts[idx1].employee_id
                
                child1.shifts[idx1].employee, child2.shifts[idx2].employee = \
                    child2.shifts[idx2].employee, child1.shifts[idx1].employee
        
        # Reconstruire les index internes
        child1._rebuild_indexes()
        child2._rebuild_indexes()
        
        return child1, child2
    
    def _mutate(self, schedule: Schedule, employees: List[Employee]) -> None:
        """
        Applique une mutation à un planning.
        
        Args:
            schedule: Planning à muter
            employees: Liste des employés disponibles
        """
        # Sélectionner un nombre aléatoire de shifts à muter
        mutation_count = random.randint(1, max(1, len(schedule.shifts) // 10))
        
        # Sélectionner des shifts aléatoires
        shift_indices = random.sample(range(len(schedule.shifts)), min(mutation_count, len(schedule.shifts)))
        
        for idx in shift_indices:
            shift = schedule.shifts[idx]
            
            # Différents types de mutation
            mutation_type = random.choice([
                'assign',
                'unassign',
                'swap'
            ])
            
            if mutation_type == 'assign':
                # Assigner un employé aléatoire au shift
                eligible_employees = [e for e in employees if e.can_work_role(shift.role)]
                if eligible_employees:
                    employee = random.choice(eligible_employees)
                    shift.assign_employee(employee)
                    
            elif mutation_type == 'unassign':
                # Retirer l'assignation d'employé
                if shift.employee_id:
                    shift.unassign_employee()
                    
            elif mutation_type == 'swap':
                # Échanger avec un autre shift du même rôle
                same_role_shifts = [s for s in schedule.shifts if s.role == shift.role and s.shift_id != shift.shift_id]
                if same_role_shifts:
                    other_shift = random.choice(same_role_shifts)
                    shift.employee_id, other_shift.employee_id = other_shift.employee_id, shift.employee_id
                    shift.employee, other_shift.employee = other_shift.employee, shift.employee
        
        # Reconstruire les index internes
        schedule._rebuild_indexes()
    
    def stop_optimization(self) -> None:
        """
        Demande l'arrêt de l'algorithme d'optimisation.
        """
        self.stop_requested = True
    
    def get_optimization_stats(self) -> Dict:
        """
        Récupère les statistiques de l'optimisation.
        
        Returns:
            Dictionnaire de statistiques
        """
        return {
            "generations_completed": self.current_generation + 1,
            "best_fitness": self.best_fitness,
            "generation_stats": self.generation_stats,
            "algorithm": "genetic",
            "config": {k: v for k, v in self.config.items() if k not in ["validation_function", "penalty_function"]}
        }
