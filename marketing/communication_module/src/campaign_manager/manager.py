"""
Gestionnaire de campagnes marketing

Ce module fournit la classe principale pour gérer les campagnes marketing
et leur exécution sur différents canaux.
"""

import os
import logging
import json
import uuid
import datetime
from typing import Dict, List, Any, Optional, Union

from ..common import Config, format_date, safe_json
from ..social_media import SocialMediaManager
from ..notification import NotificationManager


class CampaignManager:
    """Gère les campagnes marketing multicanaux"""
    
    def __init__(self, config: Config):
        """
        Initialise le gestionnaire de campagnes.
        
        Args:
            config: Configuration du module
        """
        self.logger = logging.getLogger("communication.campaign")
        
        # Récupérer la configuration spécifique aux campagnes
        if hasattr(config, 'get'):
            self.config = config
            self.campaigns_config = config.get('campaign_manager', {})
            self.default_tracking_params = config.get('campaign_manager.default_tracking_params', {})
            self.segments = config.get('campaign_manager.segments', [])
        else:
            self.campaigns_config = config.get('campaign_manager', {})
            self.default_tracking_params = config.get('default_tracking_params', {})
            self.segments = config.get('segments', [])
            
        # Initialiser les gestionnaires de canaux
        self.social_media_manager = SocialMediaManager(config)
        self.notification_manager = NotificationManager(config)
        
        # Initialiser la base de données de campagnes (simulée ici)
        self.campaigns_db = {}
        self._load_campaigns()
        
        self.logger.info(f"Gestionnaire de campagnes initialisé avec {len(self.campaigns_db)} campagnes")
    
    def list_campaigns(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste toutes les campagnes, avec filtrage optionnel par statut.
        
        Args:
            status: Statut de filtrage (si None, liste toutes les campagnes)
            
        Returns:
            Liste des campagnes filtrées
        """
        campaigns = list(self.campaigns_db.values())
        
        if status:
            campaigns = [c for c in campaigns if c.get('status') == status]
            
        # Trier par date de début (les plus récentes d'abord)
        campaigns.sort(key=lambda c: c.get('start_date', ''), reverse=True)
        
        return campaigns
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'une campagne spécifique.
        
        Args:
            campaign_id: Identifiant de la campagne
            
        Returns:
            Détails de la campagne ou None si non trouvée
        """
        return self.campaigns_db.get(campaign_id)
    
    def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle campagne.
        
        Args:
            campaign_data: Données de la campagne
            
        Returns:
            Données de la campagne créée
            
        Raises:
            ValueError: Si les données sont invalides
        """
        # Valider les données obligatoires
        if 'name' not in campaign_data:
            raise ValueError("Le nom de la campagne est obligatoire")
        
        # Générer un ID unique
        campaign_id = str(uuid.uuid4())
        
        # Construire la structure de base
        campaign = {
            "id": campaign_id,
            "name": campaign_data['name'],
            "description": campaign_data.get('description', ''),
            "status": "draft",
            "created_at": format_date(datetime.datetime.now()),
            "updated_at": format_date(datetime.datetime.now()),
            "start_date": campaign_data.get('start_date'),
            "end_date": campaign_data.get('end_date'),
            "budget": campaign_data.get('budget', 0.0),
            "currency": campaign_data.get('currency', 'EUR'),
            "tracking_params": {**self.default_tracking_params, **campaign_data.get('tracking_params', {})},
            "segments": campaign_data.get('segments', []),
            "channels": campaign_data.get('channels', []),
            "success_metrics": campaign_data.get('success_metrics', {}),
            "results": {}
        }
        
        # Enregistrer la campagne
        self.campaigns_db[campaign_id] = campaign
        self._save_campaigns()
        
        self.logger.info(f"Campagne créée: {campaign_id} - {campaign['name']}")
        
        return campaign
    
    def update_campaign(self, campaign_id: str, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une campagne existante.
        
        Args:
            campaign_id: Identifiant de la campagne
            campaign_data: Nouvelles données de la campagne
            
        Returns:
            Données de la campagne mise à jour ou None si non trouvée
            
        Raises:
            ValueError: Si les données sont invalides ou si la campagne est déjà active
        """
        # Vérifier que la campagne existe
        if campaign_id not in self.campaigns_db:
            return None
        
        campaign = self.campaigns_db[campaign_id]
        
        # Vérifier que la campagne n'est pas déjà active
        if campaign['status'] in ['active', 'completed']:
            raise ValueError(f"Impossible de modifier une campagne au statut {campaign['status']}")
        
        # Mettre à jour les champs autorisés
        for field in ['name', 'description', 'start_date', 'end_date', 'budget', 'currency', 
                      'segments', 'channels', 'success_metrics', 'tracking_params']:
            if field in campaign_data:
                campaign[field] = campaign_data[field]
        
        # Mettre à jour la date de modification
        campaign['updated_at'] = format_date(datetime.datetime.now())
        
        # Enregistrer les modifications
        self._save_campaigns()
        
        self.logger.info(f"Campagne mise à jour: {campaign_id} - {campaign['name']}")
        
        return campaign
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Supprime une campagne.
        
        Args:
            campaign_id: Identifiant de la campagne
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si la campagne est active et ne peut pas être supprimée
        """
        # Vérifier que la campagne existe
        if campaign_id not in self.campaigns_db:
            return False
        
        campaign = self.campaigns_db[campaign_id]
        
        # Vérifier que la campagne n'est pas active
        if campaign['status'] == 'active':
            raise ValueError("Impossible de supprimer une campagne active")
        
        # Supprimer la campagne
        del self.campaigns_db[campaign_id]
        self._save_campaigns()
        
        self.logger.info(f"Campagne supprimée: {campaign_id} - {campaign['name']}")
        
        return True
    
    def start_campaign(self, campaign_id: str) -> bool:
        """
        Démarre l'exécution d'une campagne.
        
        Args:
            campaign_id: Identifiant de la campagne
            
        Returns:
            True si le démarrage a réussi, False sinon
            
        Raises:
            ValueError: Si la campagne ne peut pas être démarrée
        """
        # Vérifier que la campagne existe
        if campaign_id not in self.campaigns_db:
            return False
        
        campaign = self.campaigns_db[campaign_id]
        
        # Vérifier que la campagne est au statut draft ou scheduled
        if campaign['status'] not in ['draft', 'scheduled']:
            raise ValueError(f"Impossible de démarrer une campagne au statut {campaign['status']}")
        
        # Vérifier que la campagne a des canaux configurés
        if not campaign.get('channels'):
            raise ValueError("La campagne n'a pas de canaux configurés")
        
        # Mettre à jour le statut
        campaign['status'] = 'active'
        campaign['activated_at'] = format_date(datetime.datetime.now())
        
        # Enregistrer les modifications
        self._save_campaigns()
        
        # Exécuter les actions de démarrage pour chaque canal
        self._execute_campaign_channels(campaign)
        
        self.logger.info(f"Campagne démarrée: {campaign_id} - {campaign['name']}")
        
        return True
    
    def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """
        Récupère les performances d'une campagne.
        
        Args:
            campaign_id: Identifiant de la campagne
            
        Returns:
            Données de performance de la campagne
            
        Raises:
            ValueError: Si la campagne n'existe pas
        """
        # Vérifier que la campagne existe
        if campaign_id not in self.campaigns_db:
            raise ValueError(f"Campagne {campaign_id} non trouvée")
        
        campaign = self.campaigns_db[campaign_id]
        
        # Récupérer les performances pour chaque canal
        performance = {
            "campaign_id": campaign_id,
            "name": campaign['name'],
            "status": campaign['status'],
            "channels": {},
            "aggregated": {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "cost": 0
            }
        }
        
        # Pour chaque canal, récupérer les métriques
        for channel in campaign.get('channels', []):
            channel_type = channel.get('type')
            
            if channel_type == 'social_media':
                # Récupérer les performances des réseaux sociaux
                platforms = channel.get('platforms', [])
                posts = channel.get('posts', [])
                
                if posts:
                    post_ids = [post.get('id') for post in posts if 'id' in post]
                    
                    analytics = self.social_media_manager.get_analytics(
                        platform=None,
                        post_ids=post_ids
                    )
                    
                    performance['channels']['social_media'] = analytics
            
            elif channel_type == 'email':
                # Simuler les performances des emails
                performance['channels']['email'] = {
                    "sent": channel.get('sent', 0),
                    "opens": channel.get('opens', 0),
                    "clicks": channel.get('clicks', 0),
                    "conversions": channel.get('conversions', 0)
                }
            
            elif channel_type == 'sms':
                # Simuler les performances des SMS
                performance['channels']['sms'] = {
                    "sent": channel.get('sent', 0),
                    "clicks": channel.get('clicks', 0),
                    "conversions": channel.get('conversions', 0)
                }
        
        # Calculer les métriques agrégées
        if 'social_media' in performance['channels']:
            sm_data = performance['channels']['social_media']
            if 'aggregated' in sm_data:
                performance['aggregated']['impressions'] += sm_data['aggregated'].get('impressions', 0)
                performance['aggregated']['clicks'] += sm_data['aggregated'].get('engagement', 0)
        
        if 'email' in performance['channels']:
            email_data = performance['channels']['email']
            performance['aggregated']['impressions'] += email_data.get('opens', 0)
            performance['aggregated']['clicks'] += email_data.get('clicks', 0)
            performance['aggregated']['conversions'] += email_data.get('conversions', 0)
        
        if 'sms' in performance['channels']:
            sms_data = performance['channels']['sms']
            performance['aggregated']['clicks'] += sms_data.get('clicks', 0)
            performance['aggregated']['conversions'] += sms_data.get('conversions', 0)
        
        return performance
    
    def _execute_campaign_channels(self, campaign: Dict[str, Any]) -> None:
        """
        Exécute les actions pour tous les canaux d'une campagne.
        
        Args:
            campaign: Données de la campagne
        """
        for channel in campaign.get('channels', []):
            channel_type = channel.get('type')
            
            try:
                if channel_type == 'social_media':
                    self._execute_social_media_channel(campaign, channel)
                elif channel_type == 'email':
                    self._execute_email_channel(campaign, channel)
                elif channel_type == 'sms':
                    self._execute_sms_channel(campaign, channel)
                else:
                    self.logger.warning(f"Type de canal non pris en charge: {channel_type}")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution du canal {channel_type}: {e}")
    
    def _execute_social_media_channel(self, campaign: Dict[str, Any], channel: Dict[str, Any]) -> None:
        """
        Exécute les actions pour un canal de réseaux sociaux.
        
        Args:
            campaign: Données de la campagne
            channel: Configuration du canal
        """
        platforms = channel.get('platforms', [])
        frequency = channel.get('frequency', 'once')
        content = channel.get('content', {})
        
        # Ajouter les paramètres de tracking
        tracking_params = campaign.get('tracking_params', {})
        content_with_tracking = content.copy()
        
        # Ajouter des identifiants de campagne dans le contenu
        if 'body' in content_with_tracking:
            urls_with_tracking = self._add_tracking_to_urls(
                content_with_tracking.get('body', ''),
                {**tracking_params, 'utm_campaign': campaign.get('id')}
            )
            content_with_tracking['body'] = urls_with_tracking
        
        # Publication programmée ou immédiate
        schedule_time = None
        if frequency != 'once':
            # Ici, on programmerait plusieurs publications selon la fréquence
            # Pour l'exemple, on fait une seule publication immédiate
            pass
        
        # Publier sur les réseaux sociaux
        result = self.social_media_manager.publish_content(
            content=content_with_tracking,
            platforms=platforms,
            scheduled_time=schedule_time
        )
        
        # Stocker les IDs des publications pour suivi
        if 'publication_ids' in result:
            if 'posts' not in channel:
                channel['posts'] = []
                
            for platform, post_id in result['publication_ids'].items():
                channel['posts'].append({
                    'id': post_id,
                    'platform': platform,
                    'published_at': format_date(datetime.datetime.now())
                })
            
            # Mettre à jour la campagne
            self._save_campaigns()
    
    def _execute_email_channel(self, campaign: Dict[str, Any], channel: Dict[str, Any]) -> None:
        """
        Exécute les actions pour un canal d'email.
        
        Args:
            campaign: Données de la campagne
            channel: Configuration du canal
        """
        template_id = channel.get('template_id')
        schedule = channel.get('schedule')
        segments = campaign.get('segments', [])
        
        # Récupérer les destinataires (simulé ici)
        recipients = self._get_recipients_for_segments(segments)
        
        # Préparer les données du template
        template_data = {
            "campaign": {
                "id": campaign.get('id'),
                "name": campaign.get('name')
            },
            "offer": channel.get('offer', {})
        }
        
        # Ajouter les paramètres de tracking
        tracking_params = campaign.get('tracking_params', {})
        template_data['tracking'] = {**tracking_params, 'utm_campaign': campaign.get('id')}
        
        # Déterminer la date d'envoi
        schedule_time = None
        if schedule == 'immediate':
            # Envoi immédiat
            pass
        elif schedule == 'weekly':
            # Calculer la prochaine date d'envoi selon le jour de la semaine
            day_of_week = channel.get('day_of_week')
            time_of_day = channel.get('time', '10:00')
            schedule_time = self._get_next_weekday(day_of_week, time_of_day)
        
        # Envoyer la notification
        result = self.notification_manager.send_notification(
            template=template_id,
            recipients=recipients,
            data=template_data,
            channels=['email'],
            schedule_time=schedule_time
        )
        
        # Stocker l'ID de la notification pour suivi
        channel['notification_id'] = result.get('notification_id')
        channel['sent'] = len(recipients)
        
        # Mettre à jour la campagne
        self._save_campaigns()
    
    def _execute_sms_channel(self, campaign: Dict[str, Any], channel: Dict[str, Any]) -> None:
        """
        Exécute les actions pour un canal SMS.
        
        Args:
            campaign: Données de la campagne
            channel: Configuration du canal
        """
        template_id = channel.get('template_id')
        trigger = channel.get('trigger')
        segments = campaign.get('segments', [])
        
        # Vérifier si le déclencheur est satisfait
        trigger_condition = True  # À implémenter selon le type de déclencheur
        
        if trigger == 'weather':
            condition = channel.get('condition')
            # Ici, on vérifierait la météo réelle
            # Pour l'exemple, on considère la condition comme satisfaite
            trigger_condition = True
        
        if not trigger_condition:
            self.logger.info(f"Condition de déclenchement SMS non satisfaite pour campagne {campaign.get('id')}")
            return
        
        # Récupérer les destinataires (simulé ici)
        recipients = self._get_recipients_for_segments(segments)
        
        # Préparer les données du template
        template_data = {
            "campaign": {
                "id": campaign.get('id'),
                "name": campaign.get('name')
            },
            "offer": channel.get('offer', {})
        }
        
        # Envoyer la notification
        result = self.notification_manager.send_notification(
            template=template_id,
            recipients=recipients,
            data=template_data,
            channels=['sms']
        )
        
        # Stocker l'ID de la notification pour suivi
        channel['notification_id'] = result.get('notification_id')
        channel['sent'] = len(recipients)
        
        # Mettre à jour la campagne
        self._save_campaigns()
    
    def _get_recipients_for_segments(self, segments: List[str]) -> List[str]:
        """
        Récupère les destinataires correspondant aux segments spécifiés.
        
        Args:
            segments: Liste des identifiants de segments
            
        Returns:
            Liste des destinataires (emails, téléphones, etc.)
        """
        # Dans une implémentation réelle, cette fonction interrogerait une base de données
        # Pour l'exemple, on retourne des destinataires fictifs
        recipients = []
        
        if 'locals' in segments:
            recipients.extend(['local1@example.com', 'local2@example.com'])
        
        if 'tourists' in segments:
            recipients.extend(['tourist1@example.com', 'tourist2@example.com'])
        
        if 'regulars' in segments:
            recipients.extend(['regular1@example.com', 'regular2@example.com'])
        
        return recipients
    
    def _get_next_weekday(self, day_name: str, time_str: str) -> datetime.datetime:
        """
        Calcule la prochaine occurrence d'un jour de la semaine.
        
        Args:
            day_name: Nom du jour en anglais (monday, tuesday, etc.)
            time_str: Heure au format HH:MM
            
        Returns:
            Date et heure de la prochaine occurrence
        """
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        day_num = days.get(day_name.lower(), 0)
        
        # Obtenir la date actuelle
        now = datetime.datetime.now()
        
        # Calculer le nombre de jours à ajouter
        days_ahead = day_num - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        # Calculer la date cible
        target_date = now + datetime.timedelta(days=days_ahead)
        
        # Ajouter l'heure
        hour, minute = map(int, time_str.split(':'))
        target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return target_date
    
    def _add_tracking_to_urls(self, text: str, params: Dict[str, str]) -> str:
        """
        Ajoute des paramètres de tracking aux URLs dans un texte.
        
        Args:
            text: Texte contenant des URLs
            params: Paramètres de tracking à ajouter
            
        Returns:
            Texte avec les URLs modifiées
        """
        import re
        
        # Expression régulière pour trouver les URLs
        url_pattern = r'https?://[^\s]+'
        
        def add_params(match):
            url = match.group(0)
            separator = '&' if '?' in url else '?'
            
            # Construire la chaîne de paramètres
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            
            return f"{url}{separator}{param_str}"
        
        # Remplacer toutes les URLs
        return re.sub(url_pattern, add_params, text)
    
    def _load_campaigns(self) -> None:
        """
        Charge les campagnes depuis le stockage persistent.
        """
        # Dans une implémentation réelle, cela chargerait depuis une base de données
        # Pour l'exemple, on simule avec un fichier JSON
        campaigns_file = os.path.join(os.path.dirname(__file__), 'campaigns_db.json')
        
        try:
            if os.path.exists(campaigns_file):
                with open(campaigns_file, 'r', encoding='utf-8') as f:
                    self.campaigns_db = json.load(f)
                self.logger.info(f"Campagnes chargées: {len(self.campaigns_db)}")
            else:
                self.logger.info("Aucune campagne existante trouvée")
                self.campaigns_db = {}
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des campagnes: {e}")
            self.campaigns_db = {}
    
    def _save_campaigns(self) -> None:
        """
        Sauvegarde les campagnes dans le stockage persistent.
        """
        # Dans une implémentation réelle, cela sauvegarderait dans une base de données
        # Pour l'exemple, on simule avec un fichier JSON
        campaigns_file = os.path.join(os.path.dirname(__file__), 'campaigns_db.json')
        
        try:
            os.makedirs(os.path.dirname(campaigns_file), exist_ok=True)
            
            with open(campaigns_file, 'w', encoding='utf-8') as f:
                json.dump(self.campaigns_db, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(f"Campagnes sauvegardées: {len(self.campaigns_db)}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des campagnes: {e}")
