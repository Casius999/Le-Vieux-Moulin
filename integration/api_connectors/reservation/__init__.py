# Module des connecteurs pour les systèmes de réservation
# Expose les classes de connecteurs spécifiques pour faciliter l'importation

from .base import BaseReservationConnector
from .thefork import TheForkConnector
from .opentable import OpenTableConnector

__all__ = [
    'BaseReservationConnector',
    'TheForkConnector',
    'OpenTableConnector',
]