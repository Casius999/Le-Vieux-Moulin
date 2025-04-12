# Module des connecteurs pour les systèmes CRM
# Expose les classes de connecteurs spécifiques pour faciliter l'importation

from .base import BaseCRMConnector
from .hubspot import HubSpotConnector
from .zoho import ZohoCRMConnector

__all__ = [
    'BaseCRMConnector',
    'HubSpotConnector',
    'ZohoCRMConnector',
]