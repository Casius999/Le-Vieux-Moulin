"""
Classe de base pour les adaptateurs de notification

Ce module définit l'interface commune pour tous les adaptateurs
d'envoi de notifications.
"""

import abc
import logging
import datetime
from typing import Dict, List, Any, Optional, Union


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
        
        # Initialiser les paramètres d'authentification et autres configurations
        self._setup_auth()
        
        self.logger.info(f"Adaptateur {self.__class__.__name__} initialisé")
    
    @abc.abstractmethod
    def _setup_auth(self) -> None:
        """
        Configure l'authentification pour le canal de notification.
        
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
            Identifiant de la notification envoyée
            
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
            Identifiant de la notification programmée
            
        Raises:
            Exception: En cas d'erreur lors de la programmation
        """
        pass
    
    @abc.abstractmethod
    def get_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une notification.
        
        Args:
            notification_id: Identifiant de la notification
            
        Returns:
            Détails et statut de la notification
            
        Raises:
            Exception: En cas d'erreur lors de la récupération du statut
        """
        pass
    
    @abc.abstractmethod
    def cancel(self, notification_id: str) -> bool:
        """
        Annule une notification programmée.
        
        Args:
            notification_id: Identifiant de la notification à annuler
            
        Returns:
            True si l'annulation a réussi, False sinon
            
        Raises:
            Exception: En cas d'erreur lors de l'annulation
        """
        pass
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Valide le format du destinataire pour ce canal.
        
        Args:
            recipient: Destinataire à valider
            
        Returns:
            True si le destinataire est valide, False sinon
        """
        # À implémenter par les classes concrètes
        return True
    
    def format_content(self, template_content: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formate le contenu d'une notification en injectant les données.
        
        Args:
            template_content: Template de contenu avec variables
            data: Données à injecter dans le template
            
        Returns:
            Contenu formaté pour l'envoi
        """
        # Implémentation basique, à personnaliser par les classes concrètes
        formatted = {}
        
        for key, value in template_content.items():
            if isinstance(value, str):
                # Substitution basique des variables {{var}}
                formatted_value = value
                for data_key, data_value in data.items():
                    placeholder = "{{" + data_key + "}}"
                    formatted_value = formatted_value.replace(placeholder, str(data_value))
                formatted[key] = formatted_value
            else:
                formatted[key] = value
        
        return formatted
