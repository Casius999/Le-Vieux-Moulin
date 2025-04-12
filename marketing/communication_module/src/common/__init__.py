"""
Module common - Composants partagés

Ce module contient les utilitaires, classes et fonctions partagés entre 
tous les composants du module de communication.
"""

from .config import Config
from .logger import setup_logger
from .utils import format_date, safe_json, retry_with_backoff

__all__ = ['Config', 'setup_logger', 'format_date', 'safe_json', 'retry_with_backoff']
