#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modèles de données pour le module d'optimisation des plannings.

Ce package contient les classes et structures de données utilisées pour
représenter les employés, les plannings, les contraintes et autres entités
nécessaires à la génération et l'optimisation des horaires.
"""

from .employee import Employee, EmployeeAvailability, EmployeeSkill
from .schedule import Schedule, ScheduleMetrics, ScheduleStatus
from .shift import Shift, ShiftType
from .constraint import Constraint, ConstraintType, ConstraintPriority
