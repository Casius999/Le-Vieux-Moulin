"""
Adaptateur pour les notifications par email

Ce module implémente l'adaptateur pour l'envoi de notifications
par email, utilisant différents services comme SendGrid ou Mailjet.
"""

import os
import re
import json
import logging
import datetime
import uuid
from typing import Dict, Any, Optional, Union

from .base import NotificationAdapter
from ...common import retry_with_backoff, format_date


class EmailAdapter(NotificationAdapter):
    """
    Adaptateur pour les notifications par email.
    
    Permet d'envoyer des emails via différents fournisseurs
    (SendGrid, Mailjet, etc.).
    """
    
    def _setup_auth(self) -> None:
        """
        Configure l'authentification pour le service d'email.
        """
        self.provider = self.config.get('provider', 'sendgrid')
        self.api_key = self.config.get('api_key', '')
        self.from_email = self.config.get('from_email', 'noreply@levieuxmoulin.fr')
        self.from_name = self.config.get('from_name', 'Le Vieux Moulin')
        self.reply_to = self.config.get('reply_to')
        self.templates_dir = self.config.get('templates_dir')
        self.track_opens = self.config.get('track_opens', True)
        self.track_clicks = self.config.get('track_clicks', True)
        
        # Valider les paramètres obligatoires
        if not self.api_key:
            self.logger.warning("Clé API non configurée pour le service d'email")
        
        # Dans une implémentation réelle, initialiser le client du service
        # Pour l'exemple, on simule simplement l'initialisation
        if self.provider == 'sendgrid':
            # Import simulé de SendGrid
            self.logger.info("Initialisation du client SendGrid")
            # La vraie implémentation utiliserait: import sendgrid; self.client = sendgrid.SendGridAPIClient(api_key=self.api_key)
        elif self.provider == 'mailjet':
            # Import simulé de Mailjet
            self.logger.info("Initialisation du client Mailjet")
            # La vraie implémentation utiliserait: from mailjet_rest import Client; self.client = Client(auth=(self.api_key, self.api_secret))
        else:
            self.logger.warning(f"Fournisseur email non reconnu: {self.provider}")
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def send(self, recipient: str, content: Dict[str, Any]) -> str:
        """
        Envoie un email immédiatement.
        
        Args:
            recipient: Adresse email du destinataire
            content: Contenu de l'email (sujet, corps, etc.)
            
        Returns:
            Identifiant du message envoyé
            
        Raises:
            ValueError: Si le destinataire est invalide ou le contenu incomplet
            Exception: En cas d'erreur lors de l'envoi
        """
        # Valider l'adresse email
        if not self.validate_recipient(recipient):
            raise ValueError(f"Adresse email invalide: {recipient}")
        
        # Valider le contenu minimal
        if 'subject' not in content:
            raise ValueError("Le sujet de l'email est obligatoire")
        
        if 'body' not in content and 'html' not in content:
            raise ValueError("Le corps de l'email est obligatoire (texte ou HTML)")
        
        self.logger.info(f"Envoi d'un email à {recipient}")
        
        # Préparer les données de l'email selon le fournisseur
        if self.provider == 'sendgrid':
            message_data = self._prepare_sendgrid_message(recipient, content)
        elif self.provider == 'mailjet':
            message_data = self._prepare_mailjet_message(recipient, content)
        else:
            # Fournisseur non supporté, format générique
            message_data = {
                "to": recipient,
                "from": f"{self.from_name} <{self.from_email}>",
                "subject": content.get('subject'),
                "body": content.get('body', ''),
                "html": content.get('html', content.get('body', ''))
            }
        
        # Dans une implémentation réelle, envoyer l'email via l'API du fournisseur
        # Pour l'exemple, simuler l'envoi
        try:
            # Simuler un appel API réussi
            self.logger.info(f"POST {self.provider}/v3/mail/send")
            
            # Générer un ID de message fictif
            message_id = f"email_{uuid.uuid4().hex[:10]}"
            
            # Enregistrer localement pour les tests (simulé)
            self._save_message(message_id, recipient, content)
            
            self.logger.info(f"Email envoyé à {recipient} avec ID: {message_id}")
            return message_id
            
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
            Identifiant du message programmé
            
        Raises:
            ValueError: Si le destinataire est invalide, le contenu incomplet ou la date invalide
            Exception: En cas d'erreur lors de la programmation
        """
        # Valider l'adresse email
        if not self.validate_recipient(recipient):
            raise ValueError(f"Adresse email invalide: {recipient}")
        
        # Convertir la date si nécessaire
        if isinstance(send_time, str):
            send_time = datetime.datetime.fromisoformat(send_time.replace('Z', '+00:00'))
        
        # Vérifier que la date est dans le futur
        now = datetime.datetime.now(datetime.timezone.utc)
        if send_time <= now:
            raise ValueError("La date d'envoi doit être dans le futur")
        
        self.logger.info(f"Programmation d'un email à {recipient} pour {send_time}")
        
        # Note: Tous les fournisseurs ne supportent pas la programmation d'emails
        # SendGrid le supporte via l'API v3, Mailjet également
        
        # Ajouter la date de programmation aux données de l'email
        if self.provider == 'sendgrid':
            message_data = self._prepare_sendgrid_message(recipient, content)
            message_data['send_at'] = int(send_time.timestamp())
        elif self.provider == 'mailjet':
            message_data = self._prepare_mailjet_message(recipient, content)
            message_data['ScheduleAt'] = send_time.isoformat()
        else:
            # Fournisseur non supporté, format générique
            message_data = {
                "to": recipient,
                "from": f"{self.from_name} <{self.from_email}>",
                "subject": content.get('subject'),
                "body": content.get('body', ''),
                "html": content.get('html', content.get('body', '')),
                "scheduled_time": send_time.isoformat()
            }
        
        # Dans une implémentation réelle, programmer l'email via l'API du fournisseur
        # Pour l'exemple, simuler la programmation
        try:
            # Simuler un appel API réussi
            self.logger.info(f"POST {self.provider}/v3/mail/send (scheduled)")
            
            # Générer un ID de message fictif
            message_id = f"email_scheduled_{uuid.uuid4().hex[:10]}"
            
            # Enregistrer localement pour les tests (simulé)
            self._save_message(message_id, recipient, content, send_time)
            
            self.logger.info(f"Email programmé à {recipient} pour {send_time} avec ID: {message_id}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la programmation de l'email à {recipient}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def get_status(self, message_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un email.
        
        Args:
            message_id: Identifiant du message
            
        Returns:
            Statut de l'email (envoyé, livré, ouvert, etc.)
            
        Raises:
            ValueError: Si le message n'existe pas
            Exception: En cas d'erreur lors de la récupération du statut
        """
        self.logger.info(f"Récupération du statut de l'email {message_id}")
        
        # Dans une implémentation réelle, interroger l'API du fournisseur
        # Pour l'exemple, simuler la récupération du statut
        try:
            # Charger depuis le stockage local simulé
            message_data = self._load_message(message_id)
            
            if not message_data:
                raise ValueError(f"Message {message_id} non trouvé")
            
            # Simuler un statut
            if 'scheduled_time' in message_data:
                scheduled_time = datetime.datetime.fromisoformat(message_data['scheduled_time'])
                if scheduled_time > datetime.datetime.now(datetime.timezone.utc):
                    status = "scheduled"
                else:
                    status = "sent"
            else:
                status = "delivered"
            
            # Simuler des métriques d'ouverture et de clic
            # Dans une implémentation réelle, ces données viendraient de l'API du fournisseur
            status_data = {
                "message_id": message_id,
                "recipient": message_data.get('recipient'),
                "status": status,
                "sent_at": message_data.get('sent_at', format_date(datetime.datetime.now())),
                "delivered_at": message_data.get('delivered_at'),
                "opened": status == "delivered",
                "opened_at": message_data.get('opened_at'),
                "clicked": False,
                "clicked_at": None
            }
            
            return status_data
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du statut de l'email {message_id}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def cancel(self, message_id: str) -> bool:
        """
        Annule un email programmé.
        
        Args:
            message_id: Identifiant du message
            
        Returns:
            True si l'annulation a réussi, False sinon
            
        Raises:
            ValueError: Si le message n'existe pas ou n'est pas programmé
            Exception: En cas d'erreur lors de l'annulation
        """
        self.logger.info(f"Annulation de l'email programmé {message_id}")
        
        # Dans une implémentation réelle, appeler l'API du fournisseur
        # Pour l'exemple, simuler l'annulation
        try:
            # Charger depuis le stockage local simulé
            message_data = self._load_message(message_id)
            
            if not message_data:
                raise ValueError(f"Message {message_id} non trouvé")
            
            # Vérifier que le message est bien programmé
            if 'scheduled_time' not in message_data:
                raise ValueError(f"Le message {message_id} n'est pas programmé")
            
            # Vérifier que la date de programmation est bien dans le futur
            scheduled_time = datetime.datetime.fromisoformat(message_data['scheduled_time'])
            if scheduled_time <= datetime.datetime.now(datetime.timezone.utc):
                raise ValueError(f"Le message {message_id} a déjà été envoyé")
            
            # Simuler un appel API réussi
            self.logger.info(f"DELETE {self.provider}/v3/mail/send/{message_id}")
            
            # Supprimer localement pour les tests (simulé)
            self._delete_message_file(message_id)
            
            self.logger.info(f"Email programmé {message_id} annulé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation de l'email programmé {message_id}: {e}")
            raise
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Valide une adresse email.
        
        Args:
            recipient: Adresse email à valider
            
        Returns:
            True si l'adresse est valide, False sinon
        """
        # Expression régulière simple pour valider une adresse email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, recipient))
    
    def _prepare_sendgrid_message(self, recipient: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare les données d'un message pour l'API SendGrid.
        
        Args:
            recipient: Adresse email du destinataire
            content: Contenu de l'email
            
        Returns:
            Données du message au format SendGrid
        """
        message = {
            "personalizations": [
                {
                    "to": [{"email": recipient}],
                    "subject": content.get('subject')
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": content.get('body', '')
                }
            ],
            "tracking_settings": {
                "click_tracking": {"enable": self.track_clicks},
                "open_tracking": {"enable": self.track_opens}
            }
        }
        
        # Ajouter le corps HTML s'il est présent
        if 'html' in content:
            message["content"].append({
                "type": "text/html",
                "value": content.get('html')
            })
        
        # Ajouter l'adresse de réponse si elle est configurée
        if self.reply_to:
            message["reply_to"] = {"email": self.reply_to}
        
        return message
    
    def _prepare_mailjet_message(self, recipient: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare les données d'un message pour l'API Mailjet.
        
        Args:
            recipient: Adresse email du destinataire
            content: Contenu de l'email
            
        Returns:
            Données du message au format Mailjet
        """
        message = {
            "Messages": [
                {
                    "From": {
                        "Email": self.from_email,
                        "Name": self.from_name
                    },
                    "To": [
                        {
                            "Email": recipient
                        }
                    ],
                    "Subject": content.get('subject'),
                    "TextPart": content.get('body', ''),
                    "HTMLPart": content.get('html', content.get('body', '')),
                    "TrackOpens": "enabled" if self.track_opens else "disabled",
                    "TrackClicks": "enabled" if self.track_clicks else "disabled"
                }
            ]
        }
        
        # Ajouter l'adresse de réponse si elle est configurée
        if self.reply_to:
            message["Messages"][0]["ReplyTo"] = {"Email": self.reply_to}
        
        return message
    
    def _save_message(self, message_id: str, recipient: str, content: Dict[str, Any], 
                    scheduled_time: Optional[datetime.datetime] = None) -> None:
        """
        Sauvegarde les détails d'un message pour simulation.
        
        Dans une implémentation réelle, cette méthode n'existerait pas.
        Elle est utilisée ici pour simuler la persistance des messages.
        
        Args:
            message_id: Identifiant du message
            recipient: Adresse email du destinataire
            content: Contenu de l'email
            scheduled_time: Date et heure d'envoi programmée (optionnel)
        """
        # Créer un objet représentant le message
        message_data = {
            "id": message_id,
            "recipient": recipient,
            "content": content,
            "created_at": format_date(datetime.datetime.now()),
            "sent_at": format_date(datetime.datetime.now()) if not scheduled_time else None,
            "delivered_at": format_date(datetime.datetime.now()) if not scheduled_time else None,
            "opened_at": None,
            "clicked_at": None,
            "provider": self.provider
        }
        
        # Ajouter la date de programmation si présente
        if scheduled_time:
            message_data["scheduled_time"] = format_date(scheduled_time)
            message_data["status"] = "scheduled"
        else:
            message_data["status"] = "sent"
        
        # Simuler l'enregistrement dans un fichier
        messages_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(messages_dir, exist_ok=True)
        
        message_file = os.path.join(messages_dir, f"{message_id}.json")
        
        with open(message_file, 'w', encoding='utf-8') as f:
            json.dump(message_data, f, indent=2, ensure_ascii=False)
    
    def _load_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Charge les détails d'un message depuis le stockage simulé.
        
        Args:
            message_id: Identifiant du message
            
        Returns:
            Détails du message ou None si non trouvé
        """
        messages_dir = os.path.join(os.path.dirname(__file__), 'data')
        message_file = os.path.join(messages_dir, f"{message_id}.json")
        
        if not os.path.exists(message_file):
            return None
        
        with open(message_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _delete_message_file(self, message_id: str) -> bool:
        """
        Supprime le fichier d'un message dans le stockage simulé.
        
        Args:
            message_id: Identifiant du message
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        messages_dir = os.path.join(os.path.dirname(__file__), 'data')
        message_file = os.path.join(messages_dir, f"{message_id}.json")
        
        if not os.path.exists(message_file):
            return False
        
        os.remove(message_file)
        return True
