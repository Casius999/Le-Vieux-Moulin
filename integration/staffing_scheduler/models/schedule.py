#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contenant les modèles de données liés aux plannings.

Ces classes définissent la structure des données pour les plannings complets,
incluant les métriques, statuts et méthodes de manipulation.
"""

import uuid
from datetime import datetime, time, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union
import json

from .employee import Employee, EmployeeRole
from .shift import Shift, ShiftStatus


class ScheduleStatus(Enum):
    """Statuts possibles pour un planning."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ScheduleMetrics:
    """
    Métriques de performance d'un planning.
    """
    
    def __init__(
        self,
        total_hours: float = 0.0,
        total_cost: float = 0.0,
        coverage_score: float = 0.0,
        preference_score: float = 0.0,
        employee_count: int = 0,
        shift_count: int = 0,
        unassigned_shifts: int = 0,
        conflicts: int = 0
    ):
        """
        Initialise les métriques d'un planning.
        
        Args:
            total_hours: Total des heures planifiées
            total_cost: Coût total estimé
            coverage_score: Score de couverture des besoins (0-1)
            preference_score: Score de satisfaction des préférences (0-1)
            employee_count: Nombre d'employés impliqués
            shift_count: Nombre total de shifts
            unassigned_shifts: Nombre de shifts non assignés
            conflicts: Nombre de conflits détectés
        """
        self.total_hours = total_hours
        self.total_cost = total_cost
        self.coverage_score = min(1.0, max(0.0, coverage_score))
        self.preference_score = min(1.0, max(0.0, preference_score))
        self.employee_count = employee_count
        self.shift_count = shift_count
        self.unassigned_shifts = unassigned_shifts
        self.conflicts = conflicts
    
    @property
    def overall_score(self) -> float:
        """
        Calcule le score global du planning.
        
        Returns:
            Score global entre 0 et 1
        """
        # 40% couverture, 30% préférences, 20% coût, 10% conflits
        conflict_score = 1.0 if self.conflicts == 0 else max(0.0, 1.0 - (self.conflicts / max(1, self.shift_count)))
        cost_efficiency = 1.0  # À implémenter avec un modèle de coût de référence
        
        return 0.4 * self.coverage_score + 0.3 * self.preference_score + 0.2 * cost_efficiency + 0.1 * conflict_score
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "total_hours": round(self.total_hours, 2),
            "total_cost": round(self.total_cost, 2),
            "coverage_score": round(self.coverage_score, 4),
            "preference_score": round(self.preference_score, 4),
            "overall_score": round(self.overall_score, 4),
            "employee_count": self.employee_count,
            "shift_count": self.shift_count,
            "unassigned_shifts": self.unassigned_shifts,
            "conflicts": self.conflicts,
            "assignment_rate": round(1 - (self.unassigned_shifts / max(1, self.shift_count)), 4) if self.shift_count > 0 else 0
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduleMetrics':
        """
        Crée un objet ScheduleMetrics à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de ScheduleMetrics
        """
        return cls(
            total_hours=data.get("total_hours", 0.0),
            total_cost=data.get("total_cost", 0.0),
            coverage_score=data.get("coverage_score", 0.0),
            preference_score=data.get("preference_score", 0.0),
            employee_count=data.get("employee_count", 0),
            shift_count=data.get("shift_count", 0),
            unassigned_shifts=data.get("unassigned_shifts", 0),
            conflicts=data.get("conflicts", 0)
        )


class Schedule:
    """
    Représente un planning complet pour une période donnée.
    """
    
    def __init__(
        self,
        schedule_id: str,
        start_date: datetime,
        end_date: datetime,
        shifts: Optional[List[Shift]] = None,
        status: ScheduleStatus = ScheduleStatus.DRAFT,
        metrics: Optional[ScheduleMetrics] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        approved_by: Optional[str] = None,
        approval_date: Optional[datetime] = None,
        published_date: Optional[datetime] = None,
        version: int = 1,
        previous_version_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Initialise un planning.
        
        Args:
            schedule_id: Identifiant unique du planning
            start_date: Date de début de la période
            end_date: Date de fin de la période
            shifts: Liste des shifts inclus
            status: Statut du planning
            metrics: Métriques de performance
            name: Nom du planning
            description: Description
            created_at: Date de création
            updated_at: Date de dernière mise à jour
            created_by: Identifiant du créateur
            approved_by: Identifiant de l'approbateur
            approval_date: Date d'approbation
            published_date: Date de publication
            version: Numéro de version
            previous_version_id: ID de la version précédente
            metadata: Métadonnées supplémentaires
        """
        self.schedule_id = schedule_id
        self.start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        self.shifts = shifts or []
        self.status = status
        self.metrics = metrics or ScheduleMetrics()
        self.name = name or f"Planning {self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')}"
        self.description = description
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        self.created_by = created_by
        self.approved_by = approved_by
        self.approval_date = approval_date
        self.published_date = published_date
        self.version = version
        self.previous_version_id = previous_version_id
        self.metadata = metadata or {}
        
        # Index pour optimiser les requêtes
        self._employee_index = {}
        self._day_index = {}
        self._rebuild_indexes()
    
    def _rebuild_indexes(self) -> None:
        """
        Reconstruit les index internes pour accélérer les recherches.
        """
        self._employee_index = {}
        self._day_index = {}
        
        for i, shift in enumerate(self.shifts):
            # Index par employé
            if shift.employee_id:
                if shift.employee_id not in self._employee_index:
                    self._employee_index[shift.employee_id] = []
                self._employee_index[shift.employee_id].append(i)
            
            # Index par jour
            day_key = shift.date.strftime("%Y-%m-%d")
            if day_key not in self._day_index:
                self._day_index[day_key] = []
            self._day_index[day_key].append(i)
    
    @property
    def duration_days(self) -> int:
        """
        Calcule la durée du planning en jours.
        
        Returns:
            Nombre de jours couverts par le planning
        """
        return (self.end_date - self.start_date).days + 1
    
    def get_employee_shifts(self, employee_id: str) -> List[Shift]:
        """
        Récupère tous les shifts d'un employé donné.
        
        Args:
            employee_id: ID de l'employé
            
        Returns:
            Liste des shifts de l'employé
        """
        if employee_id not in self._employee_index:
            return []
        
        return [self.shifts[i] for i in self._employee_index[employee_id]]
    
    def get_day_shifts(self, date: datetime) -> List[Shift]:
        """
        Récupère tous les shifts pour un jour donné.
        
        Args:
            date: Jour recherché
            
        Returns:
            Liste des shifts du jour
        """
        day_key = date.strftime("%Y-%m-%d")
        if day_key not in self._day_index:
            return []
        
        return [self.shifts[i] for i in self._day_index[day_key]]
    
    def get_shifts_by_role(self, role: EmployeeRole) -> List[Shift]:
        """
        Récupère tous les shifts pour un rôle donné.
        
        Args:
            role: Rôle recherché
            
        Returns:
            Liste des shifts du rôle
        """
        return [shift for shift in self.shifts if shift.role == role]
    
    def add_shift(self, shift: Shift) -> None:
        """
        Ajoute un shift au planning.
        
        Args:
            shift: Shift à ajouter
        """
        # Vérifier que le shift est dans la période du planning
        if shift.date < self.start_date or shift.date > self.end_date:
            raise ValueError(f"Le shift (date: {shift.date.isoformat()}) est en dehors de la période du planning ({self.start_date.isoformat()} - {self.end_date.isoformat()})")
        
        self.shifts.append(shift)
        self.updated_at = datetime.now()
        
        # Mettre à jour les index
        if shift.employee_id:
            if shift.employee_id not in self._employee_index:
                self._employee_index[shift.employee_id] = []
            self._employee_index[shift.employee_id].append(len(self.shifts) - 1)
        
        day_key = shift.date.strftime("%Y-%m-%d")
        if day_key not in self._day_index:
            self._day_index[day_key] = []
        self._day_index[day_key].append(len(self.shifts) - 1)
    
    def remove_shift(self, shift_id: str) -> bool:
        """
        Supprime un shift du planning.
        
        Args:
            shift_id: ID du shift à supprimer
            
        Returns:
            True si le shift a été trouvé et supprimé, False sinon
        """
        for i, shift in enumerate(self.shifts):
            if shift.shift_id == shift_id:
                removed_shift = self.shifts.pop(i)
                self.updated_at = datetime.now()
                
                # Reconstruire les index (simplification)
                self._rebuild_indexes()
                return True
        
        return False
    
    def update_shift(self, updated_shift: Shift) -> bool:
        """
        Met à jour un shift existant.
        
        Args:
            updated_shift: Shift avec les nouvelles données
            
        Returns:
            True si le shift a été trouvé et mis à jour, False sinon
        """
        for i, shift in enumerate(self.shifts):
            if shift.shift_id == updated_shift.shift_id:
                self.shifts[i] = updated_shift
                self.updated_at = datetime.now()
                
                # Reconstruire les index
                self._rebuild_indexes()
                return True
        
        return False
    
    def get_shift(self, shift_id: str) -> Optional[Shift]:
        """
        Récupère un shift par son ID.
        
        Args:
            shift_id: ID du shift recherché
            
        Returns:
            Le shift s'il est trouvé, None sinon
        """
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                return shift
        return None
    
    def detect_conflicts(self) -> List[Tuple[Shift, Shift]]:
        """
        Détecte les conflits dans le planning (chevauchements de shifts pour un même employé).
        
        Returns:
            Liste de tuples (shift1, shift2) représentant les conflits
        """
        conflicts = []
        
        # Parcourir les employés avec des shifts assignés
        for employee_id, indices in self._employee_index.items():
            employee_shifts = [self.shifts[i] for i in indices]
            
            # Comparer chaque paire de shifts
            for i in range(len(employee_shifts)):
                for j in range(i + 1, len(employee_shifts)):
                    if employee_shifts[i].overlaps(employee_shifts[j]):
                        conflicts.append((employee_shifts[i], employee_shifts[j]))
        
        return conflicts
    
    def calculate_metrics(self, staffing_needs: Optional[Dict] = None) -> ScheduleMetrics:
        """
        Calcule les métriques de performance du planning.
        
        Args:
            staffing_needs: Dictionnaire des besoins en personnel (optionnel)
            
        Returns:
            Métriques calculées
        """
        total_hours = sum(shift.duration for shift in self.shifts)
        total_cost = sum(shift.duration * (shift.employee.hourly_rate if shift.employee else 0) for shift in self.shifts)
        
        employee_ids = set()
        for shift in self.shifts:
            if shift.employee_id:
                employee_ids.add(shift.employee_id)
        
        unassigned_shifts = sum(1 for shift in self.shifts if not shift.employee_id)
        conflicts = len(self.detect_conflicts())
        
        # TODO: Calcul du score de couverture basé sur les besoins en personnel
        coverage_score = 0.0
        if staffing_needs:
            # Implémenter la logique de comparaison entre planning et besoins
            pass
        
        # TODO: Calcul du score de préférence
        preference_score = 0.0
        
        self.metrics = ScheduleMetrics(
            total_hours=total_hours,
            total_cost=total_cost,
            coverage_score=coverage_score,
            preference_score=preference_score,
            employee_count=len(employee_ids),
            shift_count=len(self.shifts),
            unassigned_shifts=unassigned_shifts,
            conflicts=conflicts
        )
        
        return self.metrics
    
    def change_status(self, new_status: ScheduleStatus, actor_id: Optional[str] = None) -> None:
        """
        Change le statut du planning.
        
        Args:
            new_status: Nouveau statut
            actor_id: Identifiant de la personne effectuant la modification
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == ScheduleStatus.APPROVED and old_status != ScheduleStatus.APPROVED:
            self.approved_by = actor_id
            self.approval_date = datetime.now()
        
        elif new_status == ScheduleStatus.PUBLISHED and old_status != ScheduleStatus.PUBLISHED:
            self.published_date = datetime.now()
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "schedule_id": self.schedule_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "duration_days": self.duration_days,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "shifts": [shift.to_dict() for shift in self.shifts],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "version": self.version,
            "previous_version_id": self.previous_version_id,
            "metadata": self.metadata
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Convertit l'objet en chaîne JSON.
        
        Args:
            indent: Nombre d'espaces pour l'indentation (None pour une ligne)
            
        Returns:
            Chaîne JSON représentant l'objet
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict, shifts_data: Optional[List[Dict]] = None) -> 'Schedule':
        """
        Crée un objet Schedule à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données du planning
            shifts_data: Liste de dictionnaires de shifts (optionnel)
            
        Returns:
            Instance de Schedule
        """
        start_date = datetime.fromisoformat(data["start_date"])
        end_date = datetime.fromisoformat(data["end_date"])
        status = ScheduleStatus(data.get("status", "draft"))
        
        # Métriques
        metrics = ScheduleMetrics.from_dict(data.get("metrics", {})) if "metrics" in data else None
        
        # Dates
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else created_at
        approval_date = datetime.fromisoformat(data["approval_date"]) if data.get("approval_date") else None
        published_date = datetime.fromisoformat(data["published_date"]) if data.get("published_date") else None
        
        # Shifts
        shifts = []
        if shifts_data:
            shifts = [Shift.from_dict(shift_data) for shift_data in shifts_data]
        elif "shifts" in data:
            shifts = [Shift.from_dict(shift_data) for shift_data in data["shifts"]]
        
        return cls(
            schedule_id=data["schedule_id"],
            start_date=start_date,
            end_date=end_date,
            shifts=shifts,
            status=status,
            metrics=metrics,
            name=data.get("name"),
            description=data.get("description"),
            created_at=created_at,
            updated_at=updated_at,
            created_by=data.get("created_by"),
            approved_by=data.get("approved_by"),
            approval_date=approval_date,
            published_date=published_date,
            version=data.get("version", 1),
            previous_version_id=data.get("previous_version_id"),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Schedule':
        """
        Crée un objet Schedule à partir d'une chaîne JSON.
        
        Args:
            json_str: Chaîne JSON
            
        Returns:
            Instance de Schedule
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @staticmethod
    def create_new(
        start_date: datetime,
        end_date: datetime,
        name: Optional[str] = None,
        created_by: Optional[str] = None,
        **kwargs
    ) -> 'Schedule':
        """
        Crée un nouveau planning avec un ID généré.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            name: Nom du planning (optionnel)
            created_by: Identifiant du créateur (optionnel)
            **kwargs: Autres arguments pour Schedule
            
        Returns:
            Nouvelle instance de Schedule
        """
        schedule_id = f"SCH-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now()
        
        # Nom par défaut si non spécifié
        if not name:
            name = f"Planning {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        return Schedule(
            schedule_id=schedule_id,
            start_date=start_date,
            end_date=end_date,
            name=name,
            created_at=created_at,
            updated_at=created_at,
            created_by=created_by,
            **kwargs
        )
