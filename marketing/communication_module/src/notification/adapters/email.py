"""
Adaptateur pour les notifications par email

Ce module implémente l'adaptateur pour l'envoi de notifications
par email via différents fournisseurs (SendGrid, Mailjet, etc.).
"""

import os
import json
import re
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

from .base import NotificationAdapter
from ...common import format_date, retry_with_backoff


class EmailAdapter(NotificationAdapter):
    """
    Adaptateur pour l'envoi de notifications par email.
    
    Supporte plusieurs fournisseurs d'email comme SendGrid et Mailjet.
    """
    
    def _setup_auth(self) -> None:
        """
        Configure l'authentification pour le service d'email.
        """
        self.provider = self.config.get('provider', 'sendgrid')
        self.api_key = self.config.get('api_key')
        self.from_email = self.config.get('from_email')
        self.from_name = self.config.get('from_name')
        self.reply_to = self.config.get('reply_to')
        self.templates_dir = self.config.get('templates_dir')
        
        # Valider les paramètres obligatoires
        if not all([self.api_key, self.from_email]):
            self.logger.warning("Configuration email incomplète - service d'envoi peut ne pas fonctionner")
        
        # Initialiser le client API selon le fournisseur
        if self.provider == 'sendgrid':
            self._init_sendgrid()
        elif self.provider == 'mailjet':
            self._init_mailjet()
        else:
            self.logger.warning(f"Fournisseur d'email non reconnu: {self.provider} - utilisation de la simulation")
            
        self.logger.info(f"Client API {self.provider} initialisé pour l'envoi d'emails")
    
    def _init_sendgrid(self) -> None:
        """
        Initialise le client SendGrid.
        
        Dans une implémentation réelle, cela importerait et initialiserait
        le client SendGrid avec l'API key.
        """
        # Simuler l'initialisation
        self.logger.info("Client SendGrid initialisé avec succès")
    
    def _init_mailjet(self) -> None:
        """
        Initialise le client Mailjet.
        
        Dans une implémentation réelle, cela importerait et initialiserait
        le client Mailjet avec l'API key.
        """
        # Simuler l'initialisation
        self.logger.info("Client Mailjet initialisé avec succès")
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def send(self, recipient: str, content: Dict[str, Any]) -> str:
        """
        Envoie un email immédiatement.
        
        Args:
            recipient: Adresse email du destinataire
            content: Contenu de l'email (sujet, corps, etc.)
            
        Returns:
            Identifiant de l'email envoyé
            
        Raises:
            ValueError: Si le destinataire est invalide ou le contenu incomplet
            Exception: En cas d'erreur lors de l'envoi
        """
        self.logger.info(f"Envoi d'un email à {recipient}")
        
        # Valider le destinataire
        if not self.validate_recipient(recipient):
            raise ValueError(f"Adresse email invalide: {recipient}")
            
        # Valider les champs obligatoires
        if 'subject' not in content or 'body' not in content:
            raise ValueError("Le contenu doit contenir au moins un sujet (subject) et un corps (body)")
        
        # Préparer les données pour l'API
        email_data = {
            "to": recipient,
            "from": {
                "email": self.from_email,
                "name": self.from_name or "Le Vieux Moulin"
            },
            "subject": content.get('subject'),
            "content": [
                {
                    "type": "text/html",
                    "value": content.get('body')
                }
            ],
            "tracking_settings": {
                "click_tracking": {
                    "enable": self.config.get('track_clicks', True)
                },
                "open_tracking": {
                    "enable": self.config.get('track_opens', True)
                }
            }
        }
        
        # Ajouter Reply-To si configuré
        if self.reply_to:
            email_data["reply_to"] = {
                "email": self.reply_to,
                "name": self.from_name or "Le Vieux Moulin"
            }
        
        # Dans une implémentation réelle, appeler l'API du fournisseur d'email
        # Pour l'exemple, simuler une réponse réussie
        try:
            # Générer un ID de notification fictif
            notification_id = f"email_{uuid.uuid4().hex[:10]}"
            
            # Simuler l'appel API selon le fournisseur
            if self.provider == 'sendgrid':
                self.logger.info("Appel API SendGrid pour envoi d'email")
                # Simuler un appel API SendGrid
            elif self.provider == 'mailjet':
                self.logger.info("Appel API Mailjet pour envoi d'email")
                # Simuler un appel API Mailjet
            
            # Enregistrer localement pour les tests (simulé)
            self._save_notification(notification_id, recipient, content)
            
            self.logger.info(f"Email envoyé avec succès à {recipient}, ID: {notification_id}")
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de l'email à {recipient}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def schedule(self, recipient: str, content: Dict[str, Any], 
                send_time: Union[str, datetime.datetime]) -> str:
        """
        Programme l'envoi d'un email.
        
        Args:
            recipient: Adresse email du destinataire
            content: Contenu de l'email (sujet, corps, etc.)
            send_time: Date et heure d'envoi
            
        Returns:
            Identifiant de l'email programmé
            
        Raises:
            ValueError: Si le destinataire est invalide, le contenu incomplet ou la date invalide
            Exception: En cas d'erreur lors de la programmation
        """
        self.logger.info(f"Programmation d'un email à {recipient} pour {send_time}")
        
        # Convertir la date si nécessaire
        if isinstance(send_time, str):
            send_time = datetime.datetime.fromisoformat(send_time.replace('Z', '+00:00'))
        
        # Vérifier que la date est dans le futur
        now = datetime.datetime.now(datetime.timezone.utc)
        if send_time <= now:
            raise ValueError("La date d'envoi doit être dans le futur")
        
        # Valider le destinataire
        if not self.validate_recipient(recipient):
            raise ValueError(f"Adresse email invalide: {recipient}")
            
        # Valider les champs obligatoires
        if 'subject' not in content or 'body' not in content:
            raise ValueError("Le contenu doit contenir au moins un sujet (subject) et un corps (body)")
        
        # Préparer les données pour l'API, comme pour send()
        email_data = {
            "to": recipient,
            "from": {
                "email": self.from_email,
                "name": self.from_name or "Le Vieux Moulin"
            },
            "subject": content.get('subject'),
            "content": [
                {
                    "type": "text/html",
                    "value": content.get('body')
                }
            ],
            "send_at": int(send_time.timestamp())
        }
        
        # Dans une implémentation réelle, appeler l'API du fournisseur d'email
        # Pour l'exemple, simuler une réponse réussie
        try:
            # Générer un ID de notification fictif
            notification_id = f"email_scheduled_{uuid.uuid4().hex[:10]}"
            
            # Simuler l'appel API selon le fournisseur
            if self.provider == 'sendgrid':
                self.logger.info("Appel API SendGrid pour programmation d'email")
                # Simuler un appel API SendGrid
            elif self.provider == 'mailjet':
                self.logger.info("Appel API Mailjet pour programmation d'email")
                # Simuler un appel API Mailjet
            
            # Enregistrer localement pour les tests (simulé)
            self._save_notification(notification_id, recipient, content, send_time)
            
            self.logger.info(f"Email programmé avec succès pour {recipient}, ID: {notification_id}")
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la programmation de l'email pour {recipient}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def get_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un email.
        
        Args:
            notification_id: Identifiant de l'email
            
        Returns:
            Détails et statut de l'email
            
        Raises:
            ValueError: Si l'ID de notification est invalide
            Exception: En cas d'erreur lors de la récupération du statut
        """
        self.logger.info(f"Récupération du statut de l'email {notification_id}")
        
        # Dans une implémentation réelle, appeler l'API du fournisseur d'email
        # Pour l'exemple, simuler une réponse en lisant le fichier local
        try:
            # Récupérer depuis le stockage local simulé
            notification_data = self._load_notification(notification_id)
            
            if not notification_data:
                raise ValueError(f"Notification {notification_id} non trouvée")
            
            # Ajouter des statistiques fictives si c'est une notification envoyée
            if notification_data.get('status') == 'sent':
                notification_data['stats'] = {
                    "delivered": True,
                    "opened": True,
                    "clicked": False,
                    "delivered_at": format_date(datetime.datetime.now() - datetime.timedelta(hours=1)),
                    "opened_at": format_date(datetime.datetime.now() - datetime.timedelta(minutes=30))
                }
                
            return notification_data
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du statut de l'email {notification_id}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def cancel(self, notification_id: str) -> bool:
        """
        Annule un email programmé.
        
        Args:
            notification_id: Identifiant de l'email à annuler
            
        Returns:
            True si l'annulation a réussi, False sinon
            
        Raises:
            ValueError: Si l'ID de notification est invalide ou l'email déjà envoyé
            Exception: En cas d'erreur lors de l'annulation
        """
        self.logger.info(f"Annulation de l'email programmé {notification_id}")
        
        # Dans une implémentation réelle, appeler l'API du fournisseur d'email
        # Pour l'exemple, simuler une réponse réussie
        try:
            # Vérifier si la notification existe et est programmée
            notification_data = self._load_notification(notification_id)
            
            if not notification_data:
                raise ValueError(f"Notification {notification_id} non trouvée")
                
            if notification_data.get('status') != 'scheduled':
                raise ValueError(f"Impossible d'annuler un email au statut {notification_data.get('status')}")
            
            # Simuler un appel API selon le fournisseur
            if self.provider == 'sendgrid':
                self.logger.info("Appel API SendGrid pour annulation d'email")
                # Simuler un appel API SendGrid
            elif self.provider == 'mailjet':
                self.logger.info("Appel API Mailjet pour annulation d'email")
                # Simuler un appel API Mailjet
            
            # Mettre à jour le statut localement (simulé)
            notification_data['status'] = 'cancelled'
            notification_data['cancelled_at'] = format_date(datetime.datetime.now())
            self._save_notification(notification_id, notification_data['recipient'], 
                                  notification_data['content'], 
                                  notification_data.get('scheduled_time'),
                                  notification_data)
            
            self.logger.info(f"Email {notification_id} annulé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation de l'email {notification_id}: {e}")
            raise
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Valide le format d'une adresse email.
        
        Args:
            recipient: Adresse email à valider
            
        Returns:
            True si l'adresse email est valide, False sinon
        """
        # Expression régulière pour la validation d'email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, recipient))
    
    def _save_notification(self, notification_id: str, recipient: str, content: Dict[str, Any], 
                         scheduled_time: Optional[datetime.datetime] = None,
                         existing_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Sauvegarde les détails d'une notification pour simulation.
        
        Dans une implémentation réelle, cette méthode n'existerait pas.
        Elle est utilisée ici pour simuler la persistance des notifications.
        
        Args:
            notification_id: Identifiant de la notification
            recipient: Destinataire de la notification
            content: Contenu de la notification
            scheduled_time: Date et heure d'envoi programmée (optionnel)
            existing_data: Données existantes à mettre à jour (optionnel)
        """
        # Utiliser les données existantes ou créer un nouvel objet
        if existing_data:
            notification_data = existing_data
        else:
            # Créer un objet représentant la notification
            notification_data = {
                "id": notification_id,
                "recipient": recipient,
                "content": content,
                "created_at": format_date(datetime.datetime.now()),
                "channel": "email",
                "provider": self.provider
            }
            
            # Ajouter la date d'envoi programmée si présente
            if scheduled_time:
                notification_data["scheduled_time"] = format_date(scheduled_time)
                notification_data["status"] = "scheduled"
            else:
                notification_data["status"] = "sent"
                notification_data["sent_at"] = format_date(datetime.datetime.now())
        
        # Simuler l'enregistrement dans un fichier
        notifications_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(notifications_dir, exist_ok=True)
        
        notification_file = os.path.join(notifications_dir, f"{notification_id}.json")
        
        with open(notification_file, 'w', encoding='utf-8') as f:
            json.dump(notification_data, f, indent=2, ensure_ascii=False)
    
    def _load_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        Charge les détails d'une notification depuis le stockage simulé.
        
        Args:
            notification_id: Identifiant de la notification
            
        Returns:
            Détails de la notification ou None si non trouvée
        """
        notifications_dir = os.path.join(os.path.dirname(__file__), 'data')
        notification_file = os.path.join(notifications_dir, f"{notification_id}.json")
        
        if not os.path.exists(notification_file):
            return None
        
        with open(notification_file, 'r', encoding='utf-8') as f:
            return json.load(f)
