#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package contenant les algorithmes d'optimisation et de génération des plannings.

Ces modules implémentent les algorithmes utilisés pour générer et optimiser
les plannings du personnel en fonction des contraintes et prévisions.
"""

from .generator import ScheduleGenerator
from .optimizer import ScheduleOptimizer
from .evaluator import ScheduleEvaluator
from .predictor import StaffingPredictor
