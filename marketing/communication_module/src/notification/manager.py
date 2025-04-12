"""
Gestionnaire de notifications

Ce module fournit la classe principale pour gérer l'envoi de notifications
aux clients via différents canaux (email, SMS, etc.).
"""

import os
import logging
import json
import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

from ..common import retry_with_backoff, format_date


class NotificationManager:
    """
    Gère l'envoi de notifications via différents canaux.
    """
    
    def __init__(self, config):
        """
        Initialise le gestionnaire de notifications.
        
        Args:
            config: L'objet de configuration global ou spécifique aux notifications
        """
        self.logger = logging.getLogger("communication.notification")
        
        # Récupérer la configuration spécifique aux notifications
        if hasattr(config, 'get'):
            self.channels_config = config.get('notification.channels', {})
            self.templates_config = config.get('notification.templates', {})
            self.default_channels = config.get('notification.default_channels', ['email'])
        else:
            self.channels_config = config.get('channels', {})
            self.templates_config = config.get('templates', {})
            self.default_channels = config.get('default_channels', ['email'])
        
        # Initialiser les adaptateurs pour chaque canal
        self.channel_adapters = {}
        
        # Initialiser l'adaptateur email si configuré
        if 'email' in self.channels_config and self.channels_config['email'].get('enabled', False):
            from .adapters.email import EmailAdapter
            self.channel_adapters['email'] = EmailAdapter(self.channels_config['email'])
            self.logger.info("Adaptateur email initialisé")
            
        # Initialiser l'adaptateur SMS si configuré
        if 'sms' in self.channels_config and self.channels_config['sms'].get('enabled', False):
            from .adapters.sms import SMSAdapter
            self.channel_adapters['sms'] = SMSAdapter(self.channels_config['sms'])
            self.logger.info("Adaptateur SMS initialisé")
            
        # Initialiser l'adaptateur push si configuré
        if 'push' in self.channels_config and self.channels_config['push'].get('enabled', False):
            from .adapters.push import PushAdapter
            self.channel_adapters['push'] = PushAdapter(self.channels_config['push'])
            self.logger.info("Adaptateur push initialisé")
        
        self.logger.info(f"Gestionnaire de notifications initialisé avec {len(self.channel_adapters)} canaux")
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def send_notification(self, template: str, recipients: Union[str, List[str]], 
                        data: Dict[str, Any] = None,
                        channels: Optional[List[str]] = None,
                        schedule_time: Optional[Union[str, datetime.datetime]] = None) -> Dict[str, Any]:
        """
        Envoie une notification à un ou plusieurs destinataires.
        
        Args:
            template: Identifiant du template à utiliser
            recipients: Liste des destinataires (emails, numéros de téléphone, etc.)
            data: Données à injecter dans le template
            channels: Canaux à utiliser pour l'envoi (si None, utilise les canaux par défaut)
            schedule_time: Date/heure d'envoi programmée (si None, envoie immédiatement)
            
        Returns:
            Dictionnaire contenant les IDs des notifications et leur statut
        """
        if channels is None:
            channels = self.default_channels
            
        if data is None:
            data = {}
            
        if isinstance(recipients, str):
            recipients = [recipients]
            
        if schedule_time and isinstance(schedule_time, str):
            schedule_time = datetime.datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
            
        results = {
            "notification_id": str(uuid.uuid4()),
            "status": "scheduled" if schedule_time else "sent",
            "channels": {},
            "errors": {}
        }
        
        if schedule_time:
            results["scheduled_time"] = format_date(schedule_time)
        
        # Vérifier que le template existe
        if template not in self.templates_config:
            error_msg = f"Template '{template}' non trouvé"
            self.logger.error(error_msg)
            results["status"] = "failed"
            results["error"] = error_msg
            return results
        
        template_config = self.templates_config[template]
        
        for channel in channels:
            if channel not in self.channel_adapters:
                results["errors"][channel] = f"Canal {channel} non configuré"
                continue
                
            try:
                # Préparer le contenu spécifique au canal
                content = self._prepare_content(template_config, channel, data)
                
                channel_results = {
                    "success": [],
                    "failed": []
                }
                
                # Envoyer à chaque destinataire
                for recipient in recipients:
                    try:
                        # Selon le type de notification (immédiate ou programmée)
                        if schedule_time:
                            message_id = self.channel_adapters[channel].schedule(
                                recipient, content, schedule_time
                            )
                            self.logger.debug(f"Notification programmée pour {recipient} via {channel}")
                        else:
                            message_id = self.channel_adapters[channel].send(
                                recipient, content
                            )
                            self.logger.debug(f"Notification envoyée à {recipient} via {channel}")
                            
                        channel_results["success"].append({
                            "recipient": recipient,
                            "message_id": message_id
                        })
                    except Exception as e:
                        self.logger.error(f"Erreur lors de l'envoi à {recipient} via {channel}: {e}")
                        channel_results["failed"].append({
                            "recipient": recipient,
                            "error": str(e)
                        })
                
                results["channels"][channel] = channel_results
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'utilisation du canal {channel}: {e}")
                results["errors"][channel] = str(e)
        
        # Mettre à jour le statut si nécessaire
        if all(not channel_result.get("success") for channel_result in results["channels"].values()):
            results["status"] = "failed"
        
        return results
    
    def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une notification.
        
        Args:
            notification_id: Identifiant de la notification
            
        Returns:
            Dictionnaire contenant le statut de la notification
        """
        # Note: Dans une implémentation réelle, cela interrogerait une base de données
        # Pour l'exemple, nous simulons une réponse
        self.logger.info(f"Récupération du statut de la notification {notification_id}")
        
        return {
            "notification_id": notification_id,
            "status": "delivered",
            "channels": {
                "email": {
                    "status": "delivered",
                    "delivery_time": format_date(datetime.datetime.now())
                }
            }
        }
    
    def cancel_scheduled_notification(self, notification_id: str) -> Dict[str, Any]:
        """
        Annule une notification programmée.
        
        Args:
            notification_id: Identifiant de la notification
            
        Returns:
            Dictionnaire indiquant le résultat de l'annulation
        """
        # Note: Dans une implémentation réelle, cela interrogerait une base de données et
        # annulerait les tâches programmées
        self.logger.info(f"Annulation de la notification programmée {notification_id}")
        
        return {
            "notification_id": notification_id,
            "status": "cancelled",
            "message": "Notification annulée avec succès"
        }
    
    def _prepare_content(self, template_config: Dict[str, Any], channel: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare le contenu d'une notification pour un canal spécifique.
        
        Args:
            template_config: Configuration du template
            channel: Canal cible
            data: Données à injecter dans le template
            
        Returns:
            Contenu formaté pour le canal spécifié
        """
        # Par défaut, utiliser la version générique du template
        if channel == 'email':
            subject = self._render_template(template_config.get('subject', 'Notification du Vieux Moulin'), data)
            body = self._render_template(template_config.get('body_html', ''), data)
            
            return {
                "subject": subject,
                "body": body,
                "format": "html",
                "from_name": self.channels_config.get('email', {}).get('from_name', 'Le Vieux Moulin'),
                "reply_to": self.channels_config.get('email', {}).get('reply_to')
            }
            
        elif channel == 'sms':
            # Pour les SMS, utiliser une version concise ou une version spécifique si disponible
            sms_template = template_config.get('sms_version', template_config.get('subject', ''))
            body = self._render_template(sms_template, data)
            
            return {
                "body": body,
                "sender_id": self.channels_config.get('sms', {}).get('sender_id', 'VieuxMoulin')
            }
            
        elif channel == 'push':
            # Pour les notifications push
            title = self._render_template(template_config.get('push_title', template_config.get('subject', '')), data)
            body = self._render_template(template_config.get('push_body', ''), data)
            
            return {
                "title": title,
                "body": body,
                "data": data,
                "icon": self.channels_config.get('push', {}).get('icon_url'),
                "click_action": template_config.get('push_action')
            }
        
        # Canal non reconnu, retourner un contenu minimal
        return {
            "body": self._render_template(template_config.get('body', ''), data)
        }
    
    def _render_template(self, template_str: str, data: Dict[str, Any]) -> str:
        """
        Rend un template en remplaçant les variables par leurs valeurs.
        
        Args:
            template_str: Chaîne de template avec des placeholders
            data: Données à injecter dans le template
            
        Returns:
            Chaîne rendue
        """
        # Implémentation simple de substitution de variables
        # Dans une version réelle, utiliser un moteur de template comme Jinja2
        result = template_str
        
        # Substitution basique des variables {{var}}
        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
        
        return result
