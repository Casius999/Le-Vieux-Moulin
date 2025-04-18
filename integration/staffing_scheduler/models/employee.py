#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contenant les modèles de données liés aux employés.

Ces classes définissent la structure des données liées aux employés,
leurs disponibilités, compétences et autres informations nécessaires
à l'optimisation des plannings.
"""

import uuid
from datetime import datetime, time
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union


class ContractType(Enum):
    """Types de contrats pour les employés."""
    FULL_TIME = auto()
    PART_TIME = auto()
    TEMPORARY = auto()
    SEASONAL = auto()
    INTERN = auto()


class EmployeeRole(Enum):
    """Rôles possibles pour les employés dans le restaurant."""
    CHEF = "chef"
    SOUS_CHEF = "sous_chef"
    CHEF_DE_RANG = "chef_de_rang"
    SERVEUR = "serveur"
    BARMAN = "barman"
    PLONGEUR = "plongeur"
    HOTE = "hôte"
    MANAGER = "manager"


class EmployeeSkillLevel(Enum):
    """Niveaux de compétence possibles."""
    NOVICE = 1
    JUNIOR = 2
    INTERMEDIATE = 3
    SENIOR = 4
    EXPERT = 5


class DayOfWeek(Enum):
    """Jours de la semaine pour les disponibilités."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class EmployeeSkill:
    """
    Représente une compétence d'un employé avec son niveau.
    """
    
    def __init__(
        self,
        skill_id: str,
        skill_name: str,
        level: EmployeeSkillLevel,
        certified: bool = False,
        certification_date: Optional[datetime] = None,
        certification_expiry: Optional[datetime] = None
    ):
        """
        Initialise une compétence.
        
        Args:
            skill_id: Identifiant unique de la compétence
            skill_name: Nom de la compétence
            level: Niveau de maîtrise
            certified: Si la compétence est certifiée
            certification_date: Date de certification
            certification_expiry: Date d'expiration de la certification
        """
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.level = level
        self.certified = certified
        self.certification_date = certification_date
        self.certification_expiry = certification_expiry
    
    @property
    def is_valid(self) -> bool:
        """
        Vérifie si la certification est valide.
        
        Returns:
            True si la certification est valide, False sinon
        """
        if not self.certified:
            return False
        
        if self.certification_expiry and self.certification_expiry < datetime.now():
            return False
        
        return True
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "level": self.level.value,
            "certified": self.certified,
            "certification_date": self.certification_date.isoformat() if self.certification_date else None,
            "certification_expiry": self.certification_expiry.isoformat() if self.certification_expiry else None,
            "is_valid": self.is_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmployeeSkill':
        """
        Crée un objet EmployeeSkill à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de EmployeeSkill
        """
        level = EmployeeSkillLevel(data.get("level", 1))
        certification_date = datetime.fromisoformat(data["certification_date"]) if data.get("certification_date") else None
        certification_expiry = datetime.fromisoformat(data["certification_expiry"]) if data.get("certification_expiry") else None
        
        return cls(
            skill_id=data["skill_id"],
            skill_name=data["skill_name"],
            level=level,
            certified=data.get("certified", False),
            certification_date=certification_date,
            certification_expiry=certification_expiry
        )


class EmployeeAvailability:
    """
    Représente les disponibilités d'un employé.
    """
    
    def __init__(
        self,
        availability_id: str,
        day_of_week: DayOfWeek,
        start_time: time,
        end_time: time,
        preference_score: int = 0,
        is_recurring: bool = True,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Initialise une disponibilité.
        
        Args:
            availability_id: Identifiant unique de la disponibilité
            day_of_week: Jour de la semaine
            start_time: Heure de début
            end_time: Heure de fin
            preference_score: Score de préférence (-10 à 10, 0 étant neutre)
            is_recurring: Si la disponibilité est récurrente
            start_date: Date de début (pour non récurrent)
            end_date: Date de fin (pour non récurrent)
        """
        self.availability_id = availability_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
        self.preference_score = max(-10, min(10, preference_score))  # Limiter entre -10 et 10
        self.is_recurring = is_recurring
        self.start_date = start_date
        self.end_date = end_date
    
    def overlaps(self, other: 'EmployeeAvailability') -> bool:
        """
        Vérifie si cette disponibilité chevauche une autre.
        
        Args:
            other: Autre disponibilité à comparer
            
        Returns:
            True si les disponibilités se chevauchent, False sinon
        """
        if self.day_of_week != other.day_of_week:
            return False
        
        return (self.start_time < other.end_time and self.end_time > other.start_time)
    
    def contains(self, day: datetime, shift_start: time, shift_end: time) -> bool:
        """
        Vérifie si cette disponibilité couvre un créneau spécifique.
        
        Args:
            day: Jour à vérifier
            shift_start: Heure de début du shift
            shift_end: Heure de fin du shift
            
        Returns:
            True si la disponibilité couvre le créneau, False sinon
        """
        # Vérifier le jour de la semaine
        if self.day_of_week.value != day.weekday():
            return False
        
        # Vérifier si non récurrent et hors période
        if not self.is_recurring:
            if self.start_date and day.date() < self.start_date.date():
                return False
            if self.end_date and day.date() > self.end_date.date():
                return False
        
        # Vérifier le créneau horaire
        return (self.start_time <= shift_start and self.end_time >= shift_end)
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "availability_id": self.availability_id,
            "day_of_week": self.day_of_week.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "preference_score": self.preference_score,
            "is_recurring": self.is_recurring,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmployeeAvailability':
        """
        Crée un objet EmployeeAvailability à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de EmployeeAvailability
        """
        day_of_week = DayOfWeek(data["day_of_week"])
        start_time = datetime.strptime(data["start_time"], "%H:%M:%S").time() if ":" in data["start_time"] else time.fromisoformat(data["start_time"])
        end_time = datetime.strptime(data["end_time"], "%H:%M:%S").time() if ":" in data["end_time"] else time.fromisoformat(data["end_time"])
        start_date = datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None
        end_date = datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None
        
        return cls(
            availability_id=data["availability_id"],
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            preference_score=data.get("preference_score", 0),
            is_recurring=data.get("is_recurring", True),
            start_date=start_date,
            end_date=end_date
        )


class Employee:
    """
    Représente un employé du restaurant.
    """
    
    def __init__(
        self,
        employee_id: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        primary_role: EmployeeRole,
        secondary_roles: Optional[List[EmployeeRole]] = None,
        contract_type: ContractType = ContractType.FULL_TIME,
        hourly_rate: float = 0.0,
        weekly_hours: int = 40,
        hire_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skills: Optional[List[EmployeeSkill]] = None,
        availabilities: Optional[List[EmployeeAvailability]] = None,
        max_consecutive_days: int = 6,
        min_rest_hours: int = 11,
        special_requirements: Optional[Dict] = None
    ):
        """
        Initialise un employé.
        
        Args:
            employee_id: Identifiant unique de l'employé
            first_name: Prénom
            last_name: Nom de famille
            email: Adresse email
            phone: Numéro de téléphone
            primary_role: Rôle principal
            secondary_roles: Rôles secondaires (optionnel)
            contract_type: Type de contrat
            hourly_rate: Taux horaire
            weekly_hours: Heures hebdomadaires prévues
            hire_date: Date d'embauche
            end_date: Date de fin de contrat (si applicable)
            skills: Liste des compétences
            availabilities: Liste des disponibilités
            max_consecutive_days: Nombre maximum de jours consécutifs de travail
            min_rest_hours: Nombre minimal d'heures de repos entre deux services
            special_requirements: Exigences spéciales (dictionnaire)
        """
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.primary_role = primary_role
        self.secondary_roles = secondary_roles or []
        self.contract_type = contract_type
        self.hourly_rate = hourly_rate
        self.weekly_hours = weekly_hours
        self.hire_date = hire_date or datetime.now()
        self.end_date = end_date
        self.skills = skills or []
        self.availabilities = availabilities or []
        self.max_consecutive_days = max_consecutive_days
        self.min_rest_hours = min_rest_hours
        self.special_requirements = special_requirements or {}
    
    @property
    def full_name(self) -> str:
        """
        Retourne le nom complet de l'employé.
        
        Returns:
            Nom complet (prénom + nom)
        """
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self) -> bool:
        """
        Vérifie si l'employé est actuellement actif.
        
        Returns:
            True si l'employé est actif, False sinon
        """
        now = datetime.now()
        return (now >= self.hire_date) and (self.end_date is None or now <= self.end_date)
    
    def has_skill(self, skill_name: str, min_level: EmployeeSkillLevel = EmployeeSkillLevel.NOVICE) -> bool:
        """
        Vérifie si l'employé possède une compétence spécifique à un niveau minimum.
        
        Args:
            skill_name: Nom de la compétence
            min_level: Niveau minimum requis
            
        Returns:
            True si l'employé possède la compétence au niveau requis, False sinon
        """
        for skill in self.skills:
            if skill.skill_name == skill_name and skill.level.value >= min_level.value:
                return True
        return False
    
    def can_work_role(self, role: EmployeeRole) -> bool:
        """
        Vérifie si l'employé peut travailler dans un rôle spécifique.
        
        Args:
            role: Rôle à vérifier
            
        Returns:
            True si l'employé peut travailler dans ce rôle, False sinon
        """
        return role == self.primary_role or role in self.secondary_roles
    
    def is_available(self, day: datetime, start_time: time, end_time: time) -> bool:
        """
        Vérifie si l'employé est disponible pour un créneau spécifique.
        
        Args:
            day: Jour du créneau
            start_time: Heure de début
            end_time: Heure de fin
            
        Returns:
            True si l'employé est disponible, False sinon
        """
        # Vérifier si l'employé est actif à cette date
        if not self.is_active:
            return False
        
        # Parcourir toutes les disponibilités pour trouver une correspondance
        for availability in self.availabilities:
            if availability.contains(day, start_time, end_time):
                return True
        
        return False
    
    def get_preference_score(self, day: datetime, start_time: time, end_time: time) -> int:
        """
        Obtient le score de préférence de l'employé pour un créneau spécifique.
        
        Args:
            day: Jour du créneau
            start_time: Heure de début
            end_time: Heure de fin
            
        Returns:
            Score de préférence (-10 à 10, 0 par défaut)
        """
        # Si l'employé n'est pas disponible du tout, retourner -10
        if not self.is_available(day, start_time, end_time):
            return -10
        
        # Parcourir toutes les disponibilités pour trouver une correspondance
        for availability in self.availabilities:
            if availability.contains(day, start_time, end_time):
                return availability.preference_score
        
        # Par défaut, retourner 0 (neutre)
        return 0
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "employee_id": self.employee_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "primary_role": self.primary_role.value,
            "secondary_roles": [role.value for role in self.secondary_roles],
            "contract_type": self.contract_type.name,
            "hourly_rate": self.hourly_rate,
            "weekly_hours": self.weekly_hours,
            "hire_date": self.hire_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "skills": [skill.to_dict() for skill in self.skills],
            "availabilities": [availability.to_dict() for availability in self.availabilities],
            "max_consecutive_days": self.max_consecutive_days,
            "min_rest_hours": self.min_rest_hours,
            "special_requirements": self.special_requirements,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Employee':
        """
        Crée un objet Employee à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Employee
        """
        primary_role = EmployeeRole(data["primary_role"])
        secondary_roles = [EmployeeRole(role) for role in data.get("secondary_roles", [])]
        contract_type = ContractType[data.get("contract_type", "FULL_TIME")]
        hire_date = datetime.fromisoformat(data["hire_date"])
        end_date = datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None
        
        skills = [EmployeeSkill.from_dict(skill_data) for skill_data in data.get("skills", [])]
        availabilities = [EmployeeAvailability.from_dict(avail_data) for avail_data in data.get("availabilities", [])]
        
        return cls(
            employee_id=data["employee_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data["phone"],
            primary_role=primary_role,
            secondary_roles=secondary_roles,
            contract_type=contract_type,
            hourly_rate=data.get("hourly_rate", 0.0),
            weekly_hours=data.get("weekly_hours", 40),
            hire_date=hire_date,
            end_date=end_date,
            skills=skills,
            availabilities=availabilities,
            max_consecutive_days=data.get("max_consecutive_days", 6),
            min_rest_hours=data.get("min_rest_hours", 11),
            special_requirements=data.get("special_requirements", {})
        )
    
    @staticmethod
    def create_new(
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        primary_role: EmployeeRole,
        **kwargs
    ) -> 'Employee':
        """
        Crée un nouvel employé avec un ID généré.
        
        Args:
            first_name: Prénom
            last_name: Nom de famille
            email: Adresse email
            phone: Numéro de téléphone
            primary_role: Rôle principal
            **kwargs: Autres arguments pour Employee
            
        Returns:
            Nouvelle instance de Employee
        """
        employee_id = f"EMP-{uuid.uuid4().hex[:8].upper()}"
        return Employee(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            primary_role=primary_role,
            **kwargs
        )
