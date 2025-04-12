# Module des connecteurs pour les fournisseurs
# Expose les classes de connecteurs spécifiques pour faciliter l'importation

from .base import BaseSupplierConnector
from .metro import MetroConnector
from .transgourmet import TransgourmetConnector
from .pomona import PomonaConnector

__all__ = [
    'BaseSupplierConnector',
    'MetroConnector',
    'TransgourmetConnector',
    'PomonaConnector',
]