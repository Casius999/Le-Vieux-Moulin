"""
Package de gestion des publications sur les réseaux sociaux

Ce package contient les adaptateurs pour publier du contenu
sur différentes plateformes de réseaux sociaux.
"""

from typing import Dict, Any

from .base import SocialMediaPublisher
from .facebook import FacebookPublisher
from .instagram import InstagramPublisher
from .twitter import TwitterPublisher
from .google_business import GoogleBusinessPublisher


def get_publisher(platform_name: str, config: Dict[str, Any]) -> SocialMediaPublisher:
    """
    Crée et retourne l'adaptateur pour la plateforme spécifiée.
    
    Args:
        platform_name: Nom de la plateforme (facebook, instagram, etc.)
        config: Configuration de la plateforme
        
    Returns:
        Instance de l'adaptateur pour la plateforme
        
    Raises:
        ValueError: Si la plateforme n'est pas prise en charge
    """
    if platform_name == 'facebook':
        return FacebookPublisher(config)
    elif platform_name == 'instagram':
        return InstagramPublisher(config)
    elif platform_name == 'twitter':
        return TwitterPublisher(config)
    elif platform_name == 'google_business':
        return GoogleBusinessPublisher(config)
    else:
        raise ValueError(f"Plateforme non prise en charge: {platform_name}")
