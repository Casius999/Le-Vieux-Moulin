#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contenant les modèles de données liés aux contraintes de planification.

Ces classes définissent la structure des contraintes appliquées lors de
la génération et l'optimisation des plannings.
"""

import uuid
from datetime import datetime, time, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable


class ConstraintType(Enum):
    """Types de contraintes possibles pour la planification."""
    LEGAL = "legal"  # Contraintes légales (temps de repos, heures max)
    AVAILABILITY = "availability"  # Disponibilités des employés
    PREFERENCE = "preference"  # Préférences des employés
    SKILL = "skill"  # Compétences requises
    FAIRNESS = "fairness"  # Équité dans la distribution des horaires
    CONTINUITY = "continuity"  # Continuité de service (même équipe)
    COST = "cost"  # Contraintes de coût
    CUSTOM = "custom"  # Contraintes personnalisées


class ConstraintPriority(Enum):
    """Priorités pour les contraintes."""
    MANDATORY = 100  # Contrainte obligatoire, ne peut pas être violée
    HIGH = 80  # Priorité haute, éviter de violer si possible
    MEDIUM = 50  # Priorité moyenne
    LOW = 30  # Priorité basse
    OPTIONAL = 10  # Contrainte optionnelle, prise en compte si possible


class ConstraintScope(Enum):
    """Périmètres d'application des contraintes."""
    GLOBAL = "global"  # Applicable à tout le planning
    EMPLOYEE = "employee"  # Applicable à un employé spécifique
    ROLE = "role"  # Applicable à un rôle spécifique
    SHIFT = "shift"  # Applicable à un shift spécifique
    DAY = "day"  # Applicable à un jour spécifique
    LOCATION = "location"  # Applicable à une zone spécifique


class Constraint:
    """
    Représente une contrainte à respecter lors de la génération de planning.
    """
    
    def __init__(
        self,
        constraint_id: str,
        name: str,
        constraint_type: ConstraintType,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
        scope: ConstraintScope = ConstraintScope.GLOBAL,
        scope_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        parameters: Optional[Dict[str, Any]] = None,
        validation_function: Optional[Callable] = None,
        penalty_function: Optional[Callable] = None,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        is_active: bool = True
    ):
        """
        Initialise une contrainte.
        
        Args:
            constraint_id: Identifiant unique de la contrainte
            name: Nom de la contrainte
            constraint_type: Type de contrainte
            priority: Priorité de la contrainte
            scope: Périmètre d'application de la contrainte
            scope_id: Identifiant associé au périmètre (ex: ID employé)
            start_date: Date de début de validité
            end_date: Date de fin de validité
            parameters: Paramètres spécifiques à la contrainte
            validation_function: Fonction de validation
            penalty_function: Fonction de pénalité
            description: Description détaillée
            created_at: Date de création
            created_by: Identifiant du créateur
            is_active: Si la contrainte est active
        """
        self.constraint_id = constraint_id
        self.name = name
        self.constraint_type = constraint_type
        self.priority = priority
        self.scope = scope
        self.scope_id = scope_id
        self.start_date = start_date
        self.end_date = end_date
        self.parameters = parameters or {}
        self.validation_function = validation_function
        self.penalty_function = penalty_function
        self.description = description
        self.created_at = created_at or datetime.now()
        self.created_by = created_by
        self.is_active = is_active
    
    def is_valid_for_date(self, date: datetime) -> bool:
        """
        Vérifie si la contrainte est applicable à une date donnée.
        
        Args:
            date: Date à vérifier
            
        Returns:
            True si la contrainte est applicable, False sinon
        """
        if not self.is_active:
            return False
        
        if self.start_date and date < self.start_date:
            return False
        
        if self.end_date and date > self.end_date:
            return False
        
        return True
    
    def is_applicable(self, entity_id: str, entity_type: ConstraintScope) -> bool:
        """
        Vérifie si la contrainte est applicable à une entité donnée.
        
        Args:
            entity_id: Identifiant de l'entité
            entity_type: Type de l'entité
            
        Returns:
            True si la contrainte est applicable, False sinon
        """
        if not self.is_active:
            return False
        
        # Si la contrainte est globale, elle s'applique partout
        if self.scope == ConstraintScope.GLOBAL:
            return True
        
        # Si la contrainte s'applique au même type d'entité
        if self.scope == entity_type:
            # Si un ID de périmètre est spécifié, vérifier la correspondance
            if self.scope_id:
                return self.scope_id == entity_id
            # Sinon, la contrainte s'applique à toutes les entités de ce type
            return True
        
        return False
    
    def validate(self, context: Dict[str, Any]) -> bool:
        """
        Valide la contrainte dans un contexte donné.
        
        Args:
            context: Contexte d'évaluation (planning, shifts, etc.)
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        if not self.is_active:
            return True
        
        if self.validation_function:
            try:
                return self.validation_function(context, self.parameters)
            except Exception as e:
                print(f"Erreur lors de la validation de la contrainte {self.name}: {str(e)}")
                return False
        
        # Implémentations de base pour certains types de contraintes
        if self.constraint_type == ConstraintType.LEGAL:
            return self._validate_legal_constraint(context)
        elif self.constraint_type == ConstraintType.AVAILABILITY:
            return self._validate_availability_constraint(context)
        elif self.constraint_type == ConstraintType.SKILL:
            return self._validate_skill_constraint(context)
        
        # Par défaut, considérer que la contrainte est respectée
        return True
    
    def calculate_penalty(self, context: Dict[str, Any]) -> float:
        """
        Calcule la pénalité associée à la violation de cette contrainte.
        
        Args:
            context: Contexte d'évaluation (planning, shifts, etc.)
            
        Returns:
            Valeur de pénalité (0 si la contrainte est respectée)
        """
        if not self.is_active:
            return 0.0
        
        # Si la contrainte est respectée, pas de pénalité
        if self.validate(context):
            return 0.0
        
        if self.penalty_function:
            try:
                return self.penalty_function(context, self.parameters)
            except Exception as e:
                print(f"Erreur lors du calcul de pénalité pour la contrainte {self.name}: {str(e)}")
                # En cas d'erreur, appliquer une pénalité par défaut selon la priorité
                return self._default_penalty()
        
        # Pénalité par défaut
        return self._default_penalty()
    
    def _default_penalty(self) -> float:
        """
        Calcule la pénalité par défaut selon la priorité.
        
        Returns:
            Valeur de pénalité par défaut
        """
        if self.priority == ConstraintPriority.MANDATORY:
            return 1000.0
        elif self.priority == ConstraintPriority.HIGH:
            return 100.0
        elif self.priority == ConstraintPriority.MEDIUM:
            return 10.0
        elif self.priority == ConstraintPriority.LOW:
            return 1.0
        else:  # OPTIONAL
            return 0.1
    
    def _validate_legal_constraint(self, context: Dict[str, Any]) -> bool:
        """
        Validation par défaut pour les contraintes légales.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        constraint_name = self.parameters.get('constraint_name', '')
        
        if constraint_name == 'min_rest_hours':
            return self._validate_min_rest_hours(context)
        elif constraint_name == 'max_daily_hours':
            return self._validate_max_daily_hours(context)
        elif constraint_name == 'max_weekly_hours':
            return self._validate_max_weekly_hours(context)
        elif constraint_name == 'max_consecutive_days':
            return self._validate_max_consecutive_days(context)
        
        return True  # Par défaut
    
    def _validate_min_rest_hours(self, context: Dict[str, Any]) -> bool:
        """
        Valide le temps minimum de repos entre deux services.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        # À implémenter
        return True
    
    def _validate_max_daily_hours(self, context: Dict[str, Any]) -> bool:
        """
        Valide les heures maximum par jour.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        # À implémenter
        return True
    
    def _validate_max_weekly_hours(self, context: Dict[str, Any]) -> bool:
        """
        Valide les heures maximum par semaine.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        # À implémenter
        return True
    
    def _validate_max_consecutive_days(self, context: Dict[str, Any]) -> bool:
        """
        Valide le nombre maximum de jours consécutifs de travail.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        # À implémenter
        return True
    
    def _validate_availability_constraint(self, context: Dict[str, Any]) -> bool:
        """
        Validation par défaut pour les contraintes de disponibilité.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        # À implémenter
        return True
    
    def _validate_skill_constraint(self, context: Dict[str, Any]) -> bool:
        """
        Validation par défaut pour les contraintes de compétences.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            True si la contrainte est respectée, False sinon
        """
        # À implémenter
        return True
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "constraint_type": self.constraint_type.value,
            "priority": self.priority.value,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "parameters": self.parameters,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "is_active": self.is_active,
            # Les fonctions ne peuvent pas être sérialisées
            "has_validation_function": self.validation_function is not None,
            "has_penalty_function": self.penalty_function is not None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Constraint':
        """
        Crée un objet Constraint à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Constraint
        """
        constraint_type = ConstraintType(data["constraint_type"])
        priority = ConstraintPriority(data["priority"]) if "priority" in data else ConstraintPriority.MEDIUM
        scope = ConstraintScope(data["scope"]) if "scope" in data else ConstraintScope.GLOBAL
        start_date = datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None
        end_date = datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        
        return cls(
            constraint_id=data["constraint_id"],
            name=data["name"],
            constraint_type=constraint_type,
            priority=priority,
            scope=scope,
            scope_id=data.get("scope_id"),
            start_date=start_date,
            end_date=end_date,
            parameters=data.get("parameters", {}),
            validation_function=None,  # Les fonctions ne peuvent pas être désérialisées
            penalty_function=None,  # Les fonctions ne peuvent pas être désérialisées
            description=data.get("description"),
            created_at=created_at,
            created_by=data.get("created_by"),
            is_active=data.get("is_active", True)
        )
    
    @staticmethod
    def create_new(
        name: str,
        constraint_type: ConstraintType,
        **kwargs
    ) -> 'Constraint':
        """
        Crée une nouvelle contrainte avec un ID généré.
        
        Args:
            name: Nom de la contrainte
            constraint_type: Type de contrainte
            **kwargs: Autres arguments pour Constraint
            
        Returns:
            Nouvelle instance de Constraint
        """
        constraint_id = f"CNS-{uuid.uuid4().hex[:8].upper()}"
        return Constraint(
            constraint_id=constraint_id,
            name=name,
            constraint_type=constraint_type,
            **kwargs
        )


class ConstraintSet:
    """
    Ensemble de contraintes pour l'optimisation de planning.
    """
    
    def __init__(
        self,
        constraints: Optional[List[Constraint]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialise un ensemble de contraintes.
        
        Args:
            constraints: Liste de contraintes
            name: Nom de l'ensemble
            description: Description de l'ensemble
        """
        self.constraints = constraints or []
        self.name = name or "Ensemble de contraintes"
        self.description = description
    
    def add_constraint(self, constraint: Constraint) -> None:
        """
        Ajoute une contrainte à l'ensemble.
        
        Args:
            constraint: Contrainte à ajouter
        """
        self.constraints.append(constraint)
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """
        Supprime une contrainte de l'ensemble.
        
        Args:
            constraint_id: ID de la contrainte à supprimer
            
        Returns:
            True si la contrainte a été trouvée et supprimée, False sinon
        """
        for i, constraint in enumerate(self.constraints):
            if constraint.constraint_id == constraint_id:
                self.constraints.pop(i)
                return True
        return False
    
    def get_constraint(self, constraint_id: str) -> Optional[Constraint]:
        """
        Récupère une contrainte par son ID.
        
        Args:
            constraint_id: ID de la contrainte
            
        Returns:
            La contrainte si trouvée, None sinon
        """
        for constraint in self.constraints:
            if constraint.constraint_id == constraint_id:
                return constraint
        return None
    
    def get_applicable_constraints(
        self,
        date: datetime,
        scope: ConstraintScope,
        entity_id: Optional[str] = None
    ) -> List[Constraint]:
        """
        Récupère les contraintes applicables à une entité et une date.
        
        Args:
            date: Date à considérer
            scope: Type d'entité
            entity_id: ID de l'entité (optionnel)
            
        Returns:
            Liste des contraintes applicables
        """
        applicable = []
        for constraint in self.constraints:
            if not constraint.is_valid_for_date(date):
                continue
                
            if entity_id:
                if constraint.is_applicable(entity_id, scope):
                    applicable.append(constraint)
            elif constraint.scope == scope or constraint.scope == ConstraintScope.GLOBAL:
                applicable.append(constraint)
        
        return applicable
    
    def validate_all(self, context: Dict[str, Any]) -> Tuple[bool, List[Constraint]]:
        """
        Valide toutes les contraintes avec un contexte donné.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            Tuple (toutes_valides, contraintes_violées)
        """
        violated = []
        
        for constraint in self.constraints:
            if not constraint.is_active:
                continue
                
            if not constraint.validate(context):
                violated.append(constraint)
        
        return len(violated) == 0, violated
    
    def calculate_penalty_sum(self, context: Dict[str, Any]) -> float:
        """
        Calcule la somme des pénalités pour toutes les contraintes.
        
        Args:
            context: Contexte d'évaluation
            
        Returns:
            Somme des pénalités
        """
        return sum(constraint.calculate_penalty(context) for constraint in self.constraints if constraint.is_active)
    
    def to_dict(self) -> Dict:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'objet
        """
        return {
            "name": self.name,
            "description": self.description,
            "constraints": [constraint.to_dict() for constraint in self.constraints]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConstraintSet':
        """
        Crée un objet ConstraintSet à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de ConstraintSet
        """
        constraints = [Constraint.from_dict(c) for c in data.get("constraints", [])]
        return cls(
            constraints=constraints,
            name=data.get("name"),
            description=data.get("description")
        )


# Fonctions utilitaires pour créer des contraintes courantes

def create_min_rest_hours_constraint(
    hours: float = 11.0,
    priority: ConstraintPriority = ConstraintPriority.MANDATORY,
    scope: ConstraintScope = ConstraintScope.GLOBAL,
    scope_id: Optional[str] = None
) -> Constraint:
    """
    Crée une contrainte de temps minimum de repos entre deux services.
    
    Args:
        hours: Nombre d'heures minimum de repos
        priority: Priorité de la contrainte
        scope: Périmètre d'application
        scope_id: ID du périmètre si applicable
        
    Returns:
        Contrainte de temps minimum de repos
    """
    return Constraint.create_new(
        name=f"Repos minimum de {hours} heures",
        constraint_type=ConstraintType.LEGAL,
        priority=priority,
        scope=scope,
        scope_id=scope_id,
        parameters={
            'constraint_name': 'min_rest_hours',
            'hours': hours
        },
        description=f"Impose un repos minimum de {hours} heures entre deux services pour respecter la réglementation."
    )


def create_max_daily_hours_constraint(
    hours: float = 10.0,
    priority: ConstraintPriority = ConstraintPriority.MANDATORY,
    scope: ConstraintScope = ConstraintScope.GLOBAL,
    scope_id: Optional[str] = None
) -> Constraint:
    """
    Crée une contrainte d'heures maximum par jour.
    
    Args:
        hours: Nombre d'heures maximum par jour
        priority: Priorité de la contrainte
        scope: Périmètre d'application
        scope_id: ID du périmètre si applicable
        
    Returns:
        Contrainte d'heures maximum par jour
    """
    return Constraint.create_new(
        name=f"Maximum {hours} heures par jour",
        constraint_type=ConstraintType.LEGAL,
        priority=priority,
        scope=scope,
        scope_id=scope_id,
        parameters={
            'constraint_name': 'max_daily_hours',
            'hours': hours
        },
        description=f"Limite le temps de travail à {hours} heures par jour pour respecter la réglementation."
    )


def create_max_weekly_hours_constraint(
    hours: float = 48.0,
    priority: ConstraintPriority = ConstraintPriority.MANDATORY,
    scope: ConstraintScope = ConstraintScope.GLOBAL,
    scope_id: Optional[str] = None
) -> Constraint:
    """
    Crée une contrainte d'heures maximum par semaine.
    
    Args:
        hours: Nombre d'heures maximum par semaine
        priority: Priorité de la contrainte
        scope: Périmètre d'application
        scope_id: ID du périmètre si applicable
        
    Returns:
        Contrainte d'heures maximum par semaine
    """
    return Constraint.create_new(
        name=f"Maximum {hours} heures par semaine",
        constraint_type=ConstraintType.LEGAL,
        priority=priority,
        scope=scope,
        scope_id=scope_id,
        parameters={
            'constraint_name': 'max_weekly_hours',
            'hours': hours
        },
        description=f"Limite le temps de travail à {hours} heures par semaine pour respecter la réglementation."
    )


def create_skill_requirement_constraint(
    role: str,
    skill: str,
    min_level: int = 1,
    priority: ConstraintPriority = ConstraintPriority.HIGH,
    scope: ConstraintScope = ConstraintScope.ROLE,
) -> Constraint:
    """
    Crée une contrainte de compétence requise pour un rôle.
    
    Args:
        role: Rôle concerné
        skill: Compétence requise
        min_level: Niveau minimum requis
        priority: Priorité de la contrainte
        scope: Périmètre d'application (généralement ROLE)
        
    Returns:
        Contrainte de compétence
    """
    return Constraint.create_new(
        name=f"{skill} niveau {min_level} requis pour {role}",
        constraint_type=ConstraintType.SKILL,
        priority=priority,
        scope=scope,
        scope_id=role,
        parameters={
            'skill': skill,
            'min_level': min_level
        },
        description=f"Exige que les employés assignés au rôle {role} aient la compétence {skill} au niveau {min_level} minimum."
    )


def create_fair_weekend_distribution_constraint(
    max_weekends_per_month: int = 2,
    priority: ConstraintPriority = ConstraintPriority.MEDIUM
) -> Constraint:
    """
    Crée une contrainte d'équité pour la distribution des weekends.
    
    Args:
        max_weekends_per_month: Nombre maximum de weekends par mois
        priority: Priorité de la contrainte
        
    Returns:
        Contrainte d'équité
    """
    return Constraint.create_new(
        name=f"Maximum {max_weekends_per_month} weekends par mois",
        constraint_type=ConstraintType.FAIRNESS,
        priority=priority,
        scope=ConstraintScope.GLOBAL,
        parameters={
            'max_weekends_per_month': max_weekends_per_month
        },
        description=f"Assure une répartition équitable des weekends travaillés avec un maximum de {max_weekends_per_month} par mois."
    )
