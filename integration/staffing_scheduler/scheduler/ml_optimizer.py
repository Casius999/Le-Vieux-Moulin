#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'optimisation des plannings basé sur le machine learning.

Ce module étend l'algorithme génétique standard avec des capacités d'apprentissage
pour optimiser les plannings en fonction des données historiques et des prévisions.
"""

import copy
import logging
import random
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set, Optional, Any, Callable, Union
import concurrent.futures
import threading
from functools import partial
import json

from ..models.employee import Employee, EmployeeRole
from ..models.shift import Shift, ShiftType
from ..models.schedule import Schedule, ScheduleStatus
from ..models.constraint import Constraint, ConstraintSet, ConstraintPriority
from ..config import OPTIMIZATION_CONFIG, SCHEDULING_CONSTRAINTS
from .optimizer import ScheduleOptimizer

# Configuration du logger
logger = logging.getLogger(__name__)


class MLScheduleOptimizer(ScheduleOptimizer):
    """
    Optimiseur de planning avancé utilisant des techniques de ML pour améliorer
    les prédictions et l'optimisation des plannings.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        constraint_set: Optional[ConstraintSet] = None,
        progress_callback: Optional[Callable[[int, int, Dict], None]] = None,
        model_path: Optional[str] = None
    ):
        """
        Initialise l'optimiseur de planning avancé.
        
        Args:
            config: Configuration personnalisée (surcharge OPTIMIZATION_CONFIG)
            constraint_set: Ensemble de contraintes personnalisé
            progress_callback: Fonction de callback pour le suivi de progression
            model_path: Chemin vers le modèle ML pré-entraîné (si disponible)
        """
        # Initialiser la classe parent
        super().__init__(config, constraint_set, progress_callback)
        
        # Paramètres spécifiques à l'optimiseur ML
        self.model_path = model_path
        self.feature_importance = {}  # Stockage de l'importance des caractéristiques
        self.historical_performance = {}  # Performances historiques des plannings
        self.employee_performance = {}  # Performances historiques des employés
        
        # Modèle ML (chargé à la demande)
        self.model = None
        
        # Métriques avancées
        self.advanced_metrics = {}
    
    def load_historical_data(self, schedules: List[Schedule], metrics: Optional[Dict] = None) -> None:
        """
        Charge les données historiques pour alimenter le modèle ML.
        
        Args:
            schedules: Liste des plannings historiques
            metrics: Métriques de performance associées (optionnel)
        """
        if not schedules:
            logger.warning("Aucune donnée historique fournie")
            return
        
        logger.info(f"Chargement de {len(schedules)} plannings historiques")
        
        # Analyser les plannings historiques
        for schedule in schedules:
            schedule_features = self._extract_schedule_features(schedule)
            
            # Si des métriques sont fournies, les associer au planning
            if metrics and schedule.schedule_id in metrics:
                schedule_metrics = metrics[schedule.schedule_id]
                schedule_performance = self._calculate_schedule_performance(schedule_metrics)
                self.historical_performance[schedule.schedule_id] = {
                    "features": schedule_features,
                    "performance": schedule_performance
                }
                
                # Mise à jour des performances des employés
                self._update_employee_performance(schedule, schedule_metrics)
    
    def _extract_schedule_features(self, schedule: Schedule) -> Dict:
        """
        Extrait les caractéristiques d'un planning pour l'analyse ML.
        
        Args:
            schedule: Planning à analyser
            
        Returns:
            Dictionnaire de caractéristiques
        """
        features = {
            "total_shifts": len(schedule.shifts),
            "assigned_shifts": sum(1 for shift in schedule.shifts if shift.employee_id),
            "assignments_by_role": {},
            "assignments_by_day": {},
            "avg_shift_duration": 0,
            "total_hours": 0,
            "weekend_shifts": 0
        }
        
        if not schedule.shifts:
            return features
        
        # Analyser les shifts
        total_duration = 0
        for shift in schedule.shifts:
            # Par rôle
            role = shift.role.value if hasattr(shift.role, "value") else str(shift.role)
            features["assignments_by_role"][role] = features["assignments_by_role"].get(role, 0) + 1
            
            # Par jour
            day_str = shift.date.strftime("%Y-%m-%d")
            features["assignments_by_day"][day_str] = features["assignments_by_day"].get(day_str, 0) + 1
            
            # Durée
            if hasattr(shift, "duration"):
                total_duration += shift.duration
                features["total_hours"] += shift.duration
            
            # Weekend
            if shift.date.weekday() >= 5:  # 5=Samedi, 6=Dimanche
                features["weekend_shifts"] += 1
        
        # Moyenne de durée des shifts
        features["avg_shift_duration"] = total_duration / len(schedule.shifts) if schedule.shifts else 0
        
        return features
    
    def _calculate_schedule_performance(self, metrics: Dict) -> float:
        """
        Calcule un score de performance global pour un planning basé sur ses métriques.
        
        Args:
            metrics: Métriques de performance du planning
            
        Returns:
            Score de performance (0-1)
        """
        performance_score = 0.0
        metrics_count = 0
        
        # Métrique de couverture (% de shifts assignés)
        if "coverage_rate" in metrics:
            performance_score += metrics["coverage_rate"]
            metrics_count += 1
        
        # Satisfaction des préférences
        if "preference_satisfaction" in metrics:
            performance_score += metrics["preference_satisfaction"]
            metrics_count += 1
        
        # Efficacité coût (valeur inverse normalisée)
        if "cost_efficiency" in metrics:
            performance_score += metrics["cost_efficiency"]
            metrics_count += 1
        
        # Répartition équitable
        if "fairness_index" in metrics:
            performance_score += metrics["fairness_index"]
            metrics_count += 1
        
        # Retour des clients/satisfaction
        if "customer_satisfaction" in metrics:
            performance_score += metrics["customer_satisfaction"]
            metrics_count += 1
        
        return performance_score / max(1, metrics_count)
    
    def _update_employee_performance(self, schedule: Schedule, metrics: Dict) -> None:
        """
        Met à jour les statistiques de performance des employés.
        
        Args:
            schedule: Planning analysé
            metrics: Métriques associées
        """
        # Récupérer les données de performance par employé si disponibles
        employee_metrics = metrics.get("employee_metrics", {})
        
        # Pour chaque shift, mettre à jour les statistiques de l'employé
        for shift in schedule.shifts:
            if not shift.employee_id:
                continue
                
            if shift.employee_id not in self.employee_performance:
                self.employee_performance[shift.employee_id] = {
                    "shifts_count": 0,
                    "total_hours": 0,
                    "performance_scores": [],
                    "roles": set(),
                    "last_schedule": schedule.schedule_id
                }
            
            employee_perf = self.employee_performance[shift.employee_id]
            employee_perf["shifts_count"] += 1
            
            if hasattr(shift, "duration"):
                employee_perf["total_hours"] += shift.duration
                
            # Ajouter le rôle
            role = shift.role.value if hasattr(shift.role, "value") else str(shift.role)
            employee_perf["roles"].add(role)
            
            # Ajouter le score de performance spécifique à cet employé pour ce shift
            if shift.employee_id in employee_metrics:
                employee_perf["performance_scores"].append(employee_metrics[shift.employee_id])
    
    def train_model(self) -> bool:
        """
        Entraîne un modèle ML sur les données historiques pour prédire la performance des plannings.
        
        Returns:
            True si l'entraînement a réussi, False sinon
        """
        if not self.historical_performance:
            logger.warning("Pas de données historiques disponibles pour l'entraînement")
            return False
        
        logger.info(f"Entraînement du modèle sur {len(self.historical_performance)} plannings historiques")
        
        try:
            # Préparer les données d'entraînement (exemple simplifié)
            # Dans une implémentation réelle, utiliser scikit-learn, tensorflow, etc.
            X = []
            y = []
            
            for schedule_id, data in self.historical_performance.items():
                features = self._flatten_features(data["features"])
                X.append(features)
                y.append(data["performance"])
            
            # Entraînement simplifié
            # Dans une implémentation réelle, utiliser un modèle propre (random forest, etc.)
            self._train_simplified_model(X, y)
            
            logger.info("Modèle entraîné avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            return False
    
    def _flatten_features(self, features: Dict) -> List[float]:
        """
        Aplatit un dictionnaire de caractéristiques en une liste pour le ML.
        
        Args:
            features: Dictionnaire de caractéristiques
            
        Returns:
            Liste de valeurs numériques
        """
        # Caractéristiques numériques directes
        flattened = [
            features.get("total_shifts", 0),
            features.get("assigned_shifts", 0),
            features.get("avg_shift_duration", 0),
            features.get("total_hours", 0),
            features.get("weekend_shifts", 0)
        ]
        
        # Pourcentage de shifts par rôle
        roles = features.get("assignments_by_role", {})
        total_shifts = features.get("total_shifts", 1)
        
        # Ajouter les pourcentages pour les rôles principaux
        for role in ["chef", "serveur", "barman", "commis", "plongeur"]:
            role_percentage = roles.get(role, 0) / total_shifts
            flattened.append(role_percentage)
        
        # Répartition sur la semaine (pourcentage par jour)
        days = features.get("assignments_by_day", {})
        for i in range(7):  # 0=Lundi à 6=Dimanche
            current_date = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=i)
            day_str = current_date.strftime("%Y-%m-%d")
            day_percentage = days.get(day_str, 0) / total_shifts
            flattened.append(day_percentage)
        
        return flattened
    
    def _train_simplified_model(self, X: List[List[float]], y: List[float]) -> None:
        """
        Entraîne un modèle simplifié pour la prédiction de performance.
        
        Args:
            X: Caractéristiques d'entrée
            y: Valeurs cibles (performances)
        """
        # Modèle très simplifié basé sur des poids moyens
        # Dans une implémentation réelle, utiliser un vrai modèle ML
        
        feature_count = len(X[0])
        weights = [0.0] * feature_count
        
        # Analyse simple de corrélation
        for i in range(feature_count):
            correlation = 0
            for j in range(len(X)):
                correlation += X[j][i] * y[j]
            weights[i] = correlation / len(X)
        
        # Normaliser les poids
        total_weight = sum(abs(w) for w in weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Stocker les poids comme modèle simplifié
        self.model = {
            "weights": weights,
            "feature_count": feature_count
        }
        
        # Calculer l'importance des caractéristiques
        feature_names = [
            "total_shifts", "assigned_shifts", "avg_shift_duration", 
            "total_hours", "weekend_shifts",
            "pct_chef", "pct_serveur", "pct_barman", "pct_commis", "pct_plongeur",
            "pct_lundi", "pct_mardi", "pct_mercredi", "pct_jeudi", 
            "pct_vendredi", "pct_samedi", "pct_dimanche"
        ]
        
        self.feature_importance = {
            feature_names[i]: abs(weights[i]) for i in range(min(len(feature_names), len(weights)))
        }
    
    def predict_schedule_performance(self, schedule: Schedule) -> float:
        """
        Prédit la performance d'un planning en utilisant le modèle ML.
        
        Args:
            schedule: Planning à évaluer
            
        Returns:
            Score de performance prédit (0-1)
        """
        if not self.model:
            logger.warning("Aucun modèle entraîné disponible, utilisation de l'évaluation standard")
            return super()._evaluate_fitness(schedule)
        
        # Extraire les caractéristiques
        features = self._extract_schedule_features(schedule)
        flattened_features = self._flatten_features(features)
        
        # Prédiction simple avec le modèle
        weights = self.model["weights"]
        feature_count = self.model["feature_count"]
        
        # Assurer la compatibilité des dimensions
        if len(flattened_features) != feature_count:
            logger.warning(f"Incompatibilité des dimensions: obtenu {len(flattened_features)}, attendu {feature_count}")
            return super()._evaluate_fitness(schedule)
        
        # Calcul du score prédit
        predicted_score = sum(flattened_features[i] * weights[i] for i in range(feature_count))
        
        # Normaliser entre 0 et 1
        predicted_score = max(0.0, min(1.0, predicted_score))
        
        return predicted_score
    
    def _evaluate_fitness(self, schedule: Schedule, staffing_needs: Optional[Dict] = None) -> float:
        """
        Évalue la qualité d'un planning en combinant le modèle ML et l'algorithme standard.
        
        Args:
            schedule: Planning à évaluer
            staffing_needs: Besoins en personnel
            
        Returns:
            Score de fitness (plus élevé = meilleur)
        """
        # Évaluation standard
        standard_score = super()._evaluate_fitness(schedule, staffing_needs)
        
        # Si le modèle ML n'est pas disponible, utiliser uniquement le score standard
        if not self.model:
            return standard_score
        
        # Prédiction ML
        ml_score = self.predict_schedule_performance(schedule)
        
        # Combiner les scores (pondération configurable)
        ml_weight = self.config.get("ml_weight", 0.3)
        combined_score = (1 - ml_weight) * standard_score + ml_weight * ml_score
        
        return combined_score
    
    def _initialize_population(
        self,
        base_schedule: Schedule,
        employees: List[Employee],
        population_size: int
    ) -> List[Schedule]:
        """
        Initialise la population avec des plannings intelligents basés sur les performances historiques.
        
        Args:
            base_schedule: Planning de base avec shifts non assignés
            employees: Liste des employés disponibles
            population_size: Taille de la population
            
        Returns:
            Liste de plannings générés intelligemment
        """
        # Si pas de données historiques, utiliser l'initialisation standard
        if not self.employee_performance:
            return super()._initialize_population(base_schedule, employees, population_size)
        
        population = []
        
        # Créer des plannings initiaux avec initialisation guidée par les performances
        for i in range(population_size):
            schedule_copy = copy.deepcopy(base_schedule)
            
            # Stratégie d'initialisation hybride
            if i < population_size * 0.7:  # 70% basés sur les performances
                self._smart_initialize_schedule(schedule_copy, employees)
            else:  # 30% aléatoires pour maintenir la diversité
                self._random_initialize_schedule(schedule_copy, employees)
            
            population.append(schedule_copy)
        
        return population
    
    def _smart_initialize_schedule(self, schedule: Schedule, employees: List[Employee]) -> None:
        """
        Initialise un planning en utilisant les données de performance historiques.
        
        Args:
            schedule: Planning à initialiser
            employees: Liste des employés disponibles
        """
        # Classifier les shifts par rôle et par jour
        shifts_by_role_day = {}
        
        for shift in schedule.shifts:
            role = shift.role.value if hasattr(shift.role, "value") else str(shift.role)
            day = shift.date.weekday()  # 0=Lundi, 6=Dimanche
            key = f"{role}_{day}"
            
            if key not in shifts_by_role_day:
                shifts_by_role_day[key] = []
            
            shifts_by_role_day[key].append(shift)
        
        # Pour chaque groupe de shifts, assigner les meilleurs employés selon l'historique
        for key, shifts in shifts_by_role_day.items():
            role, day = key.split("_")
            day = int(day)
            
            # Trouver les employés éligibles pour ce rôle
            eligible_employees = [e for e in employees if 
                                 (hasattr(e, "can_work_role") and e.can_work_role(role)) or 
                                 (hasattr(e, "primary_role") and str(e.primary_role) == role) or
                                 (hasattr(e, "secondary_roles") and role in [str(r) for r in e.secondary_roles])]
            
            if not eligible_employees:
                continue
            
            # Trier les employés par performance pour ce rôle et ce jour
            ranked_employees = self._rank_employees_for_role_day(eligible_employees, role, day)
            
            # Assigner les shifts aux meilleurs employés disponibles
            remaining_shifts = shifts.copy()
            employee_assignments = {e.employee_id: 0 for e in ranked_employees}
            
            while remaining_shifts and ranked_employees:
                # Prendre le prochain employé dans le classement
                for employee in ranked_employees[:]:
                    if not remaining_shifts:
                        break
                        
                    # Vérifier si l'employé n'est pas déjà trop assigné
                    if employee_assignments[employee.employee_id] >= 2:  # Max 2 shifts par jour
                        continue
                    
                    # Assigner le shift
                    shift = remaining_shifts.pop(0)
                    shift.assign_employee(employee)
                    employee_assignments[employee.employee_id] += 1
                    
                    # Si l'employé a atteint sa limite, le retirer du classement
                    if employee_assignments[employee.employee_id] >= 2:
                        ranked_employees.remove(employee)
    
    def _rank_employees_for_role_day(self, employees: List[Employee], role: str, day: int) -> List[Employee]:
        """
        Classe les employés par performance pour un rôle et un jour spécifiques.
        
        Args:
            employees: Liste des employés à classer
            role: Rôle concerné
            day: Jour de la semaine (0=Lundi, 6=Dimanche)
            
        Returns:
            Liste des employés classés par performance
        """
        employee_scores = []
        
        for employee in employees:
            # Score de base
            base_score = 0.5
            
            # Si des données historiques sont disponibles
            if employee.employee_id in self.employee_performance:
                perf_data = self.employee_performance[employee.employee_id]
                
                # Score moyen de performance
                if perf_data["performance_scores"]:
                    base_score = sum(perf_data["performance_scores"]) / len(perf_data["performance_scores"])
                
                # Bonus si c'est un rôle principal
                if role in perf_data["roles"]:
                    base_score += 0.2
            
            # Ajustement pour les préférences de l'employé
            if hasattr(employee, "preferred_days") and day in employee.preferred_days:
                base_score += 0.15
            
            # Bonus de compétence
            if hasattr(employee, "skill_level") and role in employee.skill_level:
                base_score += 0.1 * employee.skill_level[role]
            
            employee_scores.append((employee, base_score))
        
        # Trier par score
        employee_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Introduire un peu d'aléatoire pour éviter de toujours choisir les mêmes employés
        # (Uniquement dans le top 50%)
        top_half = len(employee_scores) // 2
        if top_half > 1:
            for i in range(top_half - 1):
                if random.random() < 0.3:  # 30% de chance d'échanger
                    employee_scores[i], employee_scores[i+1] = employee_scores[i+1], employee_scores[i]
        
        return [employee for employee, _ in employee_scores]
    
    def _random_initialize_schedule(self, schedule: Schedule, employees: List[Employee]) -> None:
        """
        Initialise un planning de manière aléatoire pour maintenir la diversité.
        
        Args:
            schedule: Planning à initialiser
            employees: Liste des employés disponibles
        """
        for shift in schedule.shifts:
            # Filtrer les employés qui peuvent travailler ce rôle
            eligible_employees = [e for e in employees if 
                                 (hasattr(e, "can_work_role") and e.can_work_role(shift.role)) or 
                                 (hasattr(e, "primary_role") and shift.role == e.primary_role) or
                                 (hasattr(e, "secondary_roles") and shift.role in e.secondary_roles)]
            
            if eligible_employees and random.random() < 0.8:  # 80% de chance d'assigner
                employee = random.choice(eligible_employees)
                shift.assign_employee(employee)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Récupère l'importance des caractéristiques pour l'optimisation.
        
        Returns:
            Dictionnaire des importances des caractéristiques
        """
        if not self.feature_importance:
            return {"message": "Aucun modèle entraîné disponible"}
        
        # Trier par importance
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return dict(sorted_features)
    
    def get_employee_insights(self, employee_id: str) -> Dict:
        """
        Fournit des informations détaillées sur les performances d'un employé.
        
        Args:
            employee_id: Identifiant de l'employé
            
        Returns:
            Dictionnaire d'insights sur l'employé
        """
        if employee_id not in self.employee_performance:
            return {"message": "Aucune donnée disponible pour cet employé"}
        
        perf_data = self.employee_performance[employee_id]
        
        # Calculer le score moyen
        avg_score = 0
        if perf_data["performance_scores"]:
            avg_score = sum(perf_data["performance_scores"]) / len(perf_data["performance_scores"])
        
        # Construire les insights
        insights = {
            "employee_id": employee_id,
            "shifts_worked": perf_data["shifts_count"],
            "total_hours": perf_data["total_hours"],
            "average_performance": round(avg_score, 2),
            "roles": list(perf_data["roles"]),
            "last_schedule": perf_data["last_schedule"],
            "recommendations": []
        }
        
        # Ajouter des recommandations selon les performances
        if avg_score > 0.8:
            insights["recommendations"].append("Excellent candidat pour les services importants")
        elif avg_score > 0.6:
            insights["recommendations"].append("Bon candidat pour les services réguliers")
        else:
            insights["recommendations"].append("Peut bénéficier d'une formation supplémentaire")
        
        # Recommandations spécifiques aux rôles
        if "chef" in perf_data["roles"] and avg_score > 0.7:
            insights["recommendations"].append("Bon candidat pour superviser des équipes")
        
        # Recommandation sur les heures
        if perf_data["total_hours"] < 20:
            insights["recommendations"].append("Candidat pour augmentation des heures")
        elif perf_data["total_hours"] > 40:
            insights["recommendations"].append("Attention au respect des heures maximales")
        
        return insights
    
    def analyze_optimization_results(self, final_schedule: Schedule) -> Dict:
        """
        Analyse détaillée des résultats d'optimisation.
        
        Args:
            final_schedule: Planning optimisé final
            
        Returns:
            Dictionnaire d'analyse
        """
        # Extraire les caractéristiques
        features = self._extract_schedule_features(final_schedule)
        
        # Calculer les métriques avancées
        metrics = {
            "assigned_percentage": features["assigned_shifts"] / max(1, features["total_shifts"]),
            "avg_shift_duration": features["avg_shift_duration"],
            "weekend_coverage": features["weekend_shifts"] / max(1, features["total_shifts"]),
            "role_distribution": features["assignments_by_role"],
            "day_distribution": features["assignments_by_day"],
            "optimization_quality": self.best_fitness if hasattr(self, "best_fitness") else 0.0
        }
        
        # Ajouter des insights
        insights = []
        
        # Insight sur la couverture
        if metrics["assigned_percentage"] < 0.9:
            insights.append({
                "type": "warning",
                "message": f"Couverture incomplète: {metrics['assigned_percentage']*100:.1f}% des shifts assignés",
                "suggested_action": "Vérifier la disponibilité du personnel ou recruter temporairement"
            })
        else:
            insights.append({
                "type": "success",
                "message": f"Bonne couverture: {metrics['assigned_percentage']*100:.1f}% des shifts assignés",
                "suggested_action": None
            })
        
        # Insight sur la répartition
        role_percentages = {role: count/features["total_shifts"] for role, count in features["assignments_by_role"].items()}
        if any(pct > 0.5 for pct in role_percentages.values()):
            dominant_role = max(role_percentages.items(), key=lambda x: x[1])
            insights.append({
                "type": "info",
                "message": f"Forte concentration sur le rôle '{dominant_role[0]}': {dominant_role[1]*100:.1f}%",
                "suggested_action": "Vérifier si cette répartition est optimale"
            })
        
        # Insight sur les weekends
        if metrics["weekend_coverage"] > 0.3:
            insights.append({
                "type": "info",
                "message": f"Forte proportion de shifts le weekend: {metrics['weekend_coverage']*100:.1f}%",
                "suggested_action": "Vérifier l'équité de la répartition des weekends"
            })
        
        return {
            "metrics": metrics,
            "insights": insights,
            "feature_importance": self.get_feature_importance() if self.model else {},
            "optimization_stats": self.get_optimization_stats() if hasattr(self, "get_optimization_stats") else {}
        }
    
    def export_optimization_model(self, path: str) -> bool:
        """
        Exporte le modèle d'optimisation pour réutilisation future.
        
        Args:
            path: Chemin où sauvegarder le modèle
            
        Returns:
            True si l'export a réussi, False sinon
        """
        if not self.model:
            logger.warning("Aucun modèle à exporter")
            return False
        
        try:
            # Préparer les données à exporter
            export_data = {
                "model": self.model,
                "feature_importance": self.feature_importance,
                "config": self.config,
                "version": "1.0",
                "created_at": datetime.now().isoformat()
            }
            
            # Sauvegarder au format JSON
            with open(path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Modèle exporté avec succès vers {path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export du modèle: {str(e)}")
            return False
    
    def import_optimization_model(self, path: str) -> bool:
        """
        Importe un modèle d'optimisation précédemment exporté.
        
        Args:
            path: Chemin du modèle à importer
            
        Returns:
            True si l'import a réussi, False sinon
        """
        try:
            # Charger le modèle
            with open(path, 'r') as f:
                import_data = json.load(f)
            
            # Valider le format
            if "model" not in import_data or "feature_importance" not in import_data:
                logger.error("Format de modèle invalide")
                return False
            
            # Charger les données
            self.model = import_data["model"]
            self.feature_importance = import_data["feature_importance"]
            
            # Mettre à jour la configuration si nécessaire
            if "config" in import_data:
                # Fusionner avec la config existante sans écraser
                for key, value in import_data["config"].items():
                    if key not in self.config:
                        self.config[key] = value
            
            logger.info(f"Modèle importé avec succès depuis {path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du modèle: {str(e)}")
            return False
