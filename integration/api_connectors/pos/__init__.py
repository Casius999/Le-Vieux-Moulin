# Module des connecteurs pour les caisses enregistreuses (POS)
# Expose les classes de connecteurs spécifiques pour faciliter l'importation

from .base import BasePOSConnector
from .lightspeed import LightspeedConnector
from .square import SquareConnector

__all__ = [
    'BasePOSConnector',
    'LightspeedConnector',
    'SquareConnector',
]