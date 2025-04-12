"""
Module de gestion des notifications

Ce module gère l'envoi de notifications personnalisées aux clients via
différents canaux (email, SMS, etc.), ainsi que le suivi des envois et interactions.
"""

from .manager import NotificationManager

__all__ = ['NotificationManager']
