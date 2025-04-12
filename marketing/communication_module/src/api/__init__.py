"""
Module API pour le module de communication

Ce module expose les fonctionnalités du système de communication via une API REST,
permettant l'intégration avec d'autres systèmes.
"""

from .server import create_app
from .routes import register_routes

__all__ = ['create_app', 'register_routes']
