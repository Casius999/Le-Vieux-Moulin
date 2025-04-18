#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package contenant les modules d'intégration avec les autres services.

Ces modules permettent de communiquer avec les services externes comme
le module de prédiction, le système de réservation, etc.
"""

from .prediction_client import PredictionClient
from .reservation_client import ReservationClient
from .notification_service import NotificationService
