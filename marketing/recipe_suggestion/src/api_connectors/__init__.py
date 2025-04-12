"""
Module de connexion aux API des fournisseurs pour Le Vieux Moulin.

Ce package gère la communication avec les différentes API
des fournisseurs pour récupérer les promotions actuelles.
"""

from .provider_api import ProviderAPI

__all__ = ['ProviderAPI']
