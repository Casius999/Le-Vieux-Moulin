#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contenant les modèles de données liés aux shifts (plages de travail).

Ces classes définissent la structure des données pour les shifts, y compris
leur type, statut, et métadonnées associées.
"""

import uuid
from datetime import datetime, time, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union

from .employee import Employee, EmployeeRole


class ShiftType(Enum):
    """Types de shifts possibles."""
    OPENING = "opening"
    CLOSING = "closing"
    MIDDAY = "midday"
    EVENING = "evening"
    FULL_DAY = "full_day"
    SPECIAL_EVENT = "special_event"
    CUSTOM = "custom"


class ShiftStatus(Enum):
    """Statuts possibles pour un shift."""
    DRAFT = "draft"
    PUBLISHED = "published"
    CONFIRMED = "confirmed"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"
    NO_SHOW = "no_show"


class LocationArea(Enum):
    """Zones de travail dans le restaurant."""
    MAIN_DINING = "salle_principale"
    TERRACE = "terrasse"
    PRIVATE_ROOM = "salle_privee"
    BAR = "bar"
    KITCHEN = "cuisine"
    RECEPTION = "reception"
    ENTIRE_RESTAURANT = "restaurant_entier"


class Shift:
    """
    Représente un shift (plage horaire de travail) d'un employé.
    """
    
    def __init__(
        self,
        shift_id: str,
        date: datetime,
        start_time: time,
        end_time: time,
        role: EmployeeRole,
        employee: Optional[Employee] = None,
        employee_id: Optional[str] = None,
        shift_type: ShiftType = ShiftType.CUSTOM,
        location: LocationArea = LocationArea.MAIN_DINING,
        status: ShiftStatus = ShiftStatus.DRAFT,
        break_duration: int = 0,  # En minutes
        notes: Optional[str] = None,
        special_event_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        updated_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Initialise un shift.
        
        Args:
            shift_id: Identifiant unique du shift
            date: Date du shift
            start_time: Heure de début
            end_time: Heure de fin
            role: Rôle pendant le shift
            employee: Employé assigné (optionnel)
            employee_id: ID de l'employé si l'objet Employee n'est pas disponible
            shift_type: Type de shift
            location: Zone de travail
            status: Statut du shift
            break_duration: Durée de pause en minutes
            notes: Notes spéciales pour ce shift
            special_event_id: ID d'un événement spécial associé
            created_at: Date de création
            updated_at: Date de dernière mise à jour
            updated_by: Identifiant de la personne ayant fait la mise à jour
            metadata: Métadonnées supplémentaires
        """
        self.shift_id = shift_id
        self.date = date.replace(hour=0, minute=0, second=0, microsecond=0) if date else None
        self.start_time = start_time
        self.end_time = end_time
        self.role = role
        self.employee = employee
        self.employee_id = employee_id or (employee.employee_id if employee else None)
        self.shift_type = shift_type
        self.location = location
        self.status = status
        self.break_duration = break_duration
        self.notes = notes
        self.special_event_id = special_event_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        self.updated_by = updated_by
        self.metadata = metadata or {}
    
    @property
    def duration(self) -> float:
        """
        Calcule la durée du shift en heures.
        
        Returns:
            Durée en heures (décimale)
        """
        if not self.start_time or not self.end_time:
            return 0.0
        
        # Convertir les objets time en datetime pour calculer la différence
        start_dt = datetime.combine(self.date.date(), self.start_time)
        end_dt = datetime.combine(self.date.date(), self.end_time)
        
        # Si le shift se termine le lendemain
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        
        # Calculer la durée et soustraire la pause
        total_seconds = (end_dt - start_dt).total_seconds()
        break_seconds = self.break_duration * 60
        
        return (total_seconds - break_seconds) / 3600  # Convertir en heures
    
    @property
    def effective_duration(self) -> float:
        """
        Calcule la durée effective du shift (sans les pauses) en heures.
        
        Returns:
            Durée effective en heures (décimale)
        """
        return self.duration
    
    @property
    def is_overnight(self) -> bool:
        """
        Vérifie si le shift s'étend sur deux jours.
        
        Returns:
            True si le shift se termine le jour suivant, False sinon
        """
        return self.end_time < self.start_time
    
    @property
    def is_assigned(self) -> bool:
        """
        Vérifie si le shift est assigné à un employé.
        
        Returns:
            True si le shift est assigné, False sinon
        """
        return bool(self.employee_id)
    
    def overlaps(self, other: 'Shift') -> bool:
        """
        Vérifie si ce shift chevauche un autre.
        
        Args:
            other: Autre shift à comparer
            
        Returns:
            True si les shifts se chevauchent, False sinon
        """
        # Si les shifts sont à des dates différentes
        if self.date.date() != other.date.date():
            # Si aucun n'est à cheval sur la nuit, pas de chevauchement
            if not (self.is_overnight or other.is_overnight):
                return False
            
            # Si self est à cheval sur la nuit et other est le jour suivant
            if self.is_overnight and other.date.date() == (self.date.date() + timedelta(days=1)):
                return other.start_time < self.end_time
            
            # Si other est à cheval sur la nuit et self est le jour suivant
            if other.is_overnight and self.date.date() == (other.date.date() + timedelta(days=1)):
                return self.start_time < other.end_time
            
            return False
        
        # Si même jour, vérifier le chevauchement des heures
        if self.is_overnight and other.is_overnight:
            # Les deux shifts sont à cheval sur la nuit => forcément chevauchement
            return True
        elif self.is_overnight:
            # Self est à cheval sur la nuit
            return other.start_time < self.end_time or other.end_time > self.start_time
        elif other.is_overnight:
            # Other est à cheval sur la nuit
            return self.start_time < other.end_time or self.end_time > other.start_time
        else:
            # Aucun shift n'est à cheval sur la nuit
            return self.start_time < other.end_time and self.end_time > other.start_time
    
    def assign_employee(self, employee: Union[Employee, str], updated_by: Optional[str] = None) -> None:
        """
        Assigne un employé à ce shift.
        
        Args:
            employee: Employé ou ID d'employé à assigner
            updated_by: Identifiant de la personne effectuant l'assignation
        """
        if isinstance(employee, Employee):
            self.employee = employee
            self.employee_id = employee.employee_id
        else:
            self.employee_id = employee
            self.employee = None
        
        self.updated_at = datetime.now()
        self.updated_by = updated_by
        self.status = ShiftStatus.PUBLISHED
    
    def unassign_employee(self, updated_by: Optional[str] = None) -> None:
        """
        Retire l'assignation d'employé de ce shift.
        
        Args:
            updated_by: Identifiant de la personne effectuant la modification
        """
        self.employee = None
        self.employee_id = None
        self.updated_at = datetime.now()
        self.updated_by = updated_by
        self.status = ShiftStatus.DRAFT
    
    def change_status(self, new_status: ShiftStatus, updated_by: Optional[str] = None) -> None:
        """
        Change le statut du shift.
        
        Args:
            new_status: Nouveau statut
            updated_by: Identifiant de la personne effectuant la modification
        """
        self.status = new_status
        self.updated_at = datetime.now()
        self.updated_by = updated_by
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        start_datetime = datetime.combine(self.date.date(), self.start_time)
        end_datetime = datetime.combine(self.date.date(), self.end_time)
        
        # Ajuster si le shift se termine le lendemain
        if self.is_overnight:
            end_datetime += timedelta(days=1)
        
        return {
            "shift_id": self.shift_id,
            "date": self.date.isoformat() if self.date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_datetime": start_datetime.isoformat() if self.start_time else None,
            "end_datetime": end_datetime.isoformat() if self.end_time else None,
            "role": self.role.value,
            "employee_id": self.employee_id,
            "employee_name": self.employee.full_name if self.employee else None,
            "shift_type": self.shift_type.value,
            "location": self.location.value,
            "status": self.status.value,
            "break_duration": self.break_duration,
            "duration": self.duration,
            "is_overnight": self.is_overnight,
            "notes": self.notes,
            "special_event_id": self.special_event_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict, employee: Optional[Employee] = None) -> 'Shift':
        """
        Crée un objet Shift à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            employee: Objet Employee optionnel
            
        Returns:
            Instance de Shift
        """
        date = datetime.fromisoformat(data["date"]) if data.get("date") else None
        start_time = datetime.strptime(data["start_time"], "%H:%M:%S").time() if ":" in data.get("start_time", "") else time.fromisoformat(data["start_time"]) if data.get("start_time") else None
        end_time = datetime.strptime(data["end_time"], "%H:%M:%S").time() if ":" in data.get("end_time", "") else time.fromisoformat(data["end_time"]) if data.get("end_time") else None
        role = EmployeeRole(data["role"])
        shift_type = ShiftType(data.get("shift_type", "custom"))
        location = LocationArea(data.get("location", "salle_principale"))
        status = ShiftStatus(data.get("status", "draft"))
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else created_at
        
        return cls(
            shift_id=data["shift_id"],
            date=date,
            start_time=start_time,
            end_time=end_time,
            role=role,
            employee=employee,
            employee_id=data.get("employee_id"),
            shift_type=shift_type,
            location=location,
            status=status,
            break_duration=data.get("break_duration", 0),
            notes=data.get("notes"),
            special_event_id=data.get("special_event_id"),
            created_at=created_at,
            updated_at=updated_at,
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {})
        )
    
    @staticmethod
    def create_new(
        date: datetime,
        start_time: time,
        end_time: time,
        role: EmployeeRole,
        **kwargs
    ) -> 'Shift':
        """
        Crée un nouveau shift avec un ID généré.
        
        Args:
            date: Date du shift
            start_time: Heure de début
            end_time: Heure de fin
            role: Rôle pendant le shift
            **kwargs: Autres arguments pour Shift
            
        Returns:
            Nouvelle instance de Shift
        """
        shift_id = f"SHF-{uuid.uuid4().hex[:8].upper()}"
        return Shift(
            shift_id=shift_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            role=role,
            **kwargs
        )
