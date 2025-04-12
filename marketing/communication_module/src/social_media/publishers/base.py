"""
Classe de base pour les adaptateurs de réseaux sociaux

Ce module définit l'interface commune pour tous les adaptateurs
de publication sur les réseaux sociaux.
"""

import abc
import logging
import datetime
from typing import Dict, List, Any, Optional, Union


class SocialMediaPublisher(abc.ABC):
    """
    Classe abstraite définissant l'interface pour les adaptateurs de réseaux sociaux.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'adaptateur avec sa configuration.
        
        Args:
            config: Configuration spécifique à la plateforme
        """
        self.logger = logging.getLogger(f"communication.social_media.{self.__class__.__name__}")
        self.config = config
        
        # Vérifier si la plateforme est activée
        if not config.get('enabled', False):
            self.logger.warning(f"L'adaptateur {self.__class__.__name__} est initialisé mais désactivé")
        
        # Initialiser les tokens d'accès et autres paramètres d'authentification
        self._setup_auth()
        
        self.logger.info(f"Adaptateur {self.__class__.__name__} initialisé")
    
    @abc.abstractmethod
    def _setup_auth(self) -> None:
        """
        Configure l'authentification pour la plateforme.
        
        Cette méthode doit être implémentée par chaque adaptateur concret
        pour gérer les spécificités d'authentification de sa plateforme.
        """
        pass
    
    @abc.abstractmethod
    def publish_post(self, content: Dict[str, Any], 
                   targeting: Optional[Dict[str, Any]] = None) -> str:
        """
        Publie immédiatement du contenu sur la plateforme.
        
        Args:
            content: Contenu à publier (texte, médias, etc.)
            targeting: Paramètres de ciblage (optionnel)
            
        Returns:
            Identifiant de la publication créée
            
        Raises:
            Exception: En cas d'erreur lors de la publication
        """
        pass
    
    @abc.abstractmethod
    def schedule_post(self, content: Dict[str, Any], 
                    publish_time: Union[str, datetime.datetime],
                    targeting: Optional[Dict[str, Any]] = None) -> str:
        """
        Programme la publication de contenu sur la plateforme.
        
        Args:
            content: Contenu à publier (texte, médias, etc.)
            publish_time: Date et heure de publication
            targeting: Paramètres de ciblage (optionnel)
            
        Returns:
            Identifiant de la publication programmée
            
        Raises:
            Exception: En cas d'erreur lors de la programmation
        """
        pass
    
    @abc.abstractmethod
    def delete_post(self, post_id: str) -> bool:
        """
        Supprime une publication.
        
        Args:
            post_id: Identifiant de la publication à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            Exception: En cas d'erreur lors de la suppression
        """
        pass
    
    @abc.abstractmethod
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une publication.
        
        Args:
            post_id: Identifiant de la publication
            
        Returns:
            Détails de la publication
            
        Raises:
            Exception: En cas d'erreur lors de la récupération
        """
        pass
    
    @abc.abstractmethod
    def get_analytics(self, start_date: Optional[Union[str, datetime.datetime]] = None,
                    end_date: Optional[Union[str, datetime.datetime]] = None,
                    post_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Récupère les données d'analyse des publications.
        
        Args:
            start_date: Date de début pour la période d'analyse
            end_date: Date de fin pour la période d'analyse
            post_ids: Liste des IDs de publications spécifiques à analyser
            
        Returns:
            Données d'analyse
            
        Raises:
            Exception: En cas d'erreur lors de la récupération des analytics
        """
        pass
