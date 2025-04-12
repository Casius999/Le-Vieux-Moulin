"""
Classe de base pour les adaptateurs de notification

Ce module définit l'interface commune pour tous les adaptateurs
d'envoi de notifications.
"""

import abc
import logging
import datetime
from typing import Dict, Any, Optional, Union


class NotificationAdapter(abc.ABC):
    """
    Classe abstraite définissant l'interface pour les adaptateurs de notification.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'adaptateur avec sa configuration.
        
        Args:
            config: Configuration spécifique au canal
        """
        self.logger = logging.getLogger(f"communication.notification.{self.__class__.__name__}")
        self.config = config
        
        # Vérifier si le canal est activé
        if not config.get('enabled', False):
            self.logger.warning(f"L'adaptateur {self.__class__.__name__} est initialisé mais désactivé")
        
        # Initialiser les informations d'authentification et autres paramètres
        self._setup_auth()
        
        self.logger.info(f"Adaptateur {self.__class__.__name__} initialisé")
    
    @abc.abstractmethod
    def _setup_auth(self) -> None:
        """
        Configure l'authentification pour le canal.
        
        Cette méthode doit être implémentée par chaque adaptateur concret
        pour gérer les spécificités d'authentification de son canal.
        """
        pass
    
    @abc.abstractmethod
    def send(self, recipient: str, content: Dict[str, Any]) -> str:
        """
        Envoie une notification immédiatement.
        
        Args:
            recipient: Destinataire de la notification (email, numéro de téléphone, etc.)
            content: Contenu de la notification (sujet, corps, etc.)
            
        Returns:
            Identifiant du message envoyé
            
        Raises:
            Exception: En cas d'erreur lors de l'envoi
        """
        pass
    
    @abc.abstractmethod
    def schedule(self, recipient: str, content: Dict[str, Any], 
               send_time: Union[str, datetime.datetime]) -> str:
        """
        Programme l'envoi d'une notification.
        
        Args:
            recipient: Destinataire de la notification (email, numéro de téléphone, etc.)
            content: Contenu de la notification (sujet, corps, etc.)
            send_time: Date et heure d'envoi
            
        Returns:
            Identifiant du message programmé
            
        Raises:
            Exception: En cas d'erreur lors de la programmation
        """
        pass
    
    @abc.abstractmethod
    def get_status(self, message_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une notification.
        
        Args:
            message_id: Identifiant du message
            
        Returns:
            Statut de la notification (envoyée, livrée, ouverte, etc.)
            
        Raises:
            Exception: En cas d'erreur lors de la récupération du statut
        """
        pass
    
    @abc.abstractmethod
    def cancel(self, message_id: str) -> bool:
        """
        Annule une notification programmée.
        
        Args:
            message_id: Identifiant du message
            
        Returns:
            True si l'annulation a réussi, False sinon
            
        Raises:
            Exception: En cas d'erreur lors de l'annulation
        """
        pass
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Valide un destinataire pour ce canal.
        
        Args:
            recipient: Destinataire à valider
            
        Returns:
            True si le destinataire est valide, False sinon
        """
        # Par défaut, accepte tous les destinataires
        # Cette méthode peut être surchargée par les adaptateurs concrets
        return True
