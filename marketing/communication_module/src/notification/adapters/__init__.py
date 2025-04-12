"""
Package de gestion des adaptateurs de notification

Ce package contient les adaptateurs pour envoyer des notifications
via différents canaux (email, SMS, push, etc.).
"""

from typing import Dict, Any

from .base import NotificationAdapter
from .email import EmailAdapter
from .sms import SMSAdapter
from .push import PushAdapter


def get_adapter(channel_name: str, config: Dict[str, Any]) -> NotificationAdapter:
    """
    Crée et retourne l'adaptateur pour le canal spécifié.
    
    Args:
        channel_name: Nom du canal (email, sms, push, etc.)
        config: Configuration du canal
        
    Returns:
        Instance de l'adaptateur pour le canal
        
    Raises:
        ValueError: Si le canal n'est pas pris en charge
    """
    if channel_name == 'email':
        return EmailAdapter(config)
    elif channel_name == 'sms':
        return SMSAdapter(config)
    elif channel_name == 'push':
        return PushAdapter(config)
    else:
        raise ValueError(f"Canal non pris en charge: {channel_name}")
