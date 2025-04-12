"""
Routes de l'API du module de communication

Ce module définit les routes de l'API REST exposée par
le module de communication et d'automatisation marketing.
"""

import logging
from typing import Dict, Any

from flask import current_app, request, g
from flask_restful import Api, Resource

from ..common import Config
from ..social_media import SocialMediaManager
from ..notification import NotificationManager
from ..campaign_manager import CampaignManager
from ..menu_updater import MenuUpdater


def register_routes(api: Api, config: Config) -> None:
    """
    Enregistre toutes les routes de l'API.
    
    Args:
        api: Instance de Flask-RESTful API
        config: Configuration du module
    """
    # Enregistrer les routes pour les différentes fonctionnalités
    register_social_media_routes(api, config)
    register_notification_routes(api, config)
    register_campaign_routes(api, config)
    register_menu_routes(api, config)


def register_social_media_routes(api: Api, config: Config) -> None:
    """
    Enregistre les routes pour la gestion des réseaux sociaux.
    
    Args:
        api: Instance de Flask-RESTful API
        config: Configuration du module
    """
    class SocialMediaPublish(Resource):
        def post(self):
            """Publie du contenu sur les réseaux sociaux."""
            data = request.get_json()
            
            # Valider les données reçues
            if not data or 'content' not in data:
                return {"status": "error", "message": "Contenu manquant"}, 400
            
            # Obtenir l'instance du gestionnaire
            manager = get_social_media_manager()
            
            # Récupérer les paramètres de la requête
            content = data.get('content', {})
            platforms = data.get('platforms')
            scheduled_time = data.get('scheduled_time')
            targeting = data.get('targeting')
            
            # Effectuer la publication
            try:
                result = manager.publish_content(
                    content=content,
                    platforms=platforms,
                    scheduled_time=scheduled_time,
                    targeting=targeting
                )
                return result, 200 if result.get("status") != "failed" else 400
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    class SocialMediaAnalytics(Resource):
        def get(self):
            """Récupère les analytics des réseaux sociaux."""
            # Obtenir l'instance du gestionnaire
            manager = get_social_media_manager()
            
            # Récupérer les paramètres de la requête
            platform = request.args.get('platform')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            post_ids = request.args.getlist('post_id')
            
            # Obtenir les analytics
            try:
                result = manager.get_analytics(
                    platform=platform,
                    start_date=start_date,
                    end_date=end_date,
                    post_ids=post_ids if post_ids else None
                )
                return result, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    # Enregistrer les ressources
    api.add_resource(SocialMediaPublish, '/communication/social/publish')
    api.add_resource(SocialMediaAnalytics, '/communication/social/analytics')


def register_notification_routes(api: Api, config: Config) -> None:
    """
    Enregistre les routes pour la gestion des notifications.
    
    Args:
        api: Instance de Flask-RESTful API
        config: Configuration du module
    """
    class NotificationSend(Resource):
        def post(self):
            """Envoie une notification."""
            data = request.get_json()
            
            # Valider les données reçues
            if not data or 'template' not in data or 'recipients' not in data:
                return {"status": "error", "message": "Paramètres manquants (template, recipients)"}, 400
            
            # Obtenir l'instance du gestionnaire
            manager = get_notification_manager()
            
            # Récupérer les paramètres de la requête
            template = data.get('template')
            recipients = data.get('recipients', [])
            channels = data.get('channels')
            template_data = data.get('data', {})
            schedule_time = data.get('schedule_time')
            
            # Envoyer la notification
            try:
                result = manager.send_notification(
                    template=template,
                    recipients=recipients,
                    data=template_data,
                    channels=channels,
                    schedule_time=schedule_time
                )
                return result, 200 if result.get("status") != "failed" else 400
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    class NotificationStatus(Resource):
        def get(self, notification_id):
            """Récupère le statut d'une notification."""
            # Obtenir l'instance du gestionnaire
            manager = get_notification_manager()
            
            # Obtenir le statut
            try:
                result = manager.get_notification_status(notification_id)
                return result, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    class NotificationCancel(Resource):
        def post(self, notification_id):
            """Annule une notification programmée."""
            # Obtenir l'instance du gestionnaire
            manager = get_notification_manager()
            
            # Annuler la notification
            try:
                result = manager.cancel_scheduled_notification(notification_id)
                return result, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    # Enregistrer les ressources
    api.add_resource(NotificationSend, '/communication/notification/send')
    api.add_resource(NotificationStatus, '/communication/notification/<string:notification_id>')
    api.add_resource(NotificationCancel, '/communication/notification/<string:notification_id>/cancel')


def register_campaign_routes(api: Api, config: Config) -> None:
    """
    Enregistre les routes pour la gestion des campagnes.
    
    Args:
        api: Instance de Flask-RESTful API
        config: Configuration du module
    """
    class CampaignList(Resource):
        def get(self):
            """Liste toutes les campagnes."""
            # Obtenir l'instance du gestionnaire
            manager = get_campaign_manager()
            
            # Filtrer selon les paramètres de requête
            status = request.args.get('status')
            
            # Obtenir la liste des campagnes
            try:
                campaigns = manager.list_campaigns(status=status)
                return {"campaigns": campaigns}, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
        
        def post(self):
            """Crée une nouvelle campagne."""
            data = request.get_json()
            
            # Valider les données reçues
            if not data or 'name' not in data:
                return {"status": "error", "message": "Nom de campagne manquant"}, 400
            
            # Obtenir l'instance du gestionnaire
            manager = get_campaign_manager()
            
            # Créer la campagne
            try:
                campaign = manager.create_campaign(data)
                return campaign, 201
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    class CampaignDetail(Resource):
        def get(self, campaign_id):
            """Récupère les détails d'une campagne."""
            # Obtenir l'instance du gestionnaire
            manager = get_campaign_manager()
            
            # Obtenir les détails de la campagne
            try:
                campaign = manager.get_campaign(campaign_id)
                if not campaign:
                    return {"status": "error", "message": "Campagne non trouvée"}, 404
                return campaign, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
        
        def put(self, campaign_id):
            """Met à jour une campagne."""
            data = request.get_json()
            
            # Obtenir l'instance du gestionnaire
            manager = get_campaign_manager()
            
            # Mettre à jour la campagne
            try:
                campaign = manager.update_campaign(campaign_id, data)
                if not campaign:
                    return {"status": "error", "message": "Campagne non trouvée"}, 404
                return campaign, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
        
        def delete(self, campaign_id):
            """Supprime une campagne."""
            # Obtenir l'instance du gestionnaire
            manager = get_campaign_manager()
            
            # Supprimer la campagne
            try:
                result = manager.delete_campaign(campaign_id)
                if not result:
                    return {"status": "error", "message": "Campagne non trouvée"}, 404
                return {"status": "success", "message": "Campagne supprimée"}, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    class CampaignStart(Resource):
        def post(self, campaign_id):
            """Démarre une campagne."""
            # Obtenir l'instance du gestionnaire
            manager = get_campaign_manager()
            
            # Démarrer la campagne
            try:
                result = manager.start_campaign(campaign_id)
                if not result:
                    return {"status": "error", "message": "Campagne non trouvée ou déjà active"}, 400
                return {"status": "success", "message": "Campagne démarrée"}, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    # Enregistrer les ressources
    api.add_resource(CampaignList, '/communication/campaigns')
    api.add_resource(CampaignDetail, '/communication/campaigns/<string:campaign_id>')
    api.add_resource(CampaignStart, '/communication/campaigns/<string:campaign_id>/start')


def register_menu_routes(api: Api, config: Config) -> None:
    """
    Enregistre les routes pour la gestion des menus.
    
    Args:
        api: Instance de Flask-RESTful API
        config: Configuration du module
    """
    class MenuUpdate(Resource):
        def post(self):
            """Met à jour le menu sur les plateformes configurées."""
            data = request.get_json()
            
            # Valider les données reçues
            if not data or 'menu' not in data:
                return {"status": "error", "message": "Données de menu manquantes"}, 400
            
            # Obtenir l'instance du gestionnaire
            manager = get_menu_updater()
            
            # Récupérer les paramètres de la requête
            menu_data = data.get('menu')
            platforms = data.get('platforms')
            schedule_time = data.get('schedule_time')
            
            # Mettre à jour le menu
            try:
                result = manager.update_menu(
                    menu_data=menu_data,
                    platforms=platforms,
                    schedule_time=schedule_time
                )
                return result, 200 if not result.get("errors") else 400
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    class MenuStatus(Resource):
        def get(self):
            """Récupère le statut des menus sur les différentes plateformes."""
            # Obtenir l'instance du gestionnaire
            manager = get_menu_updater()
            
            # Obtenir le statut
            try:
                result = manager.get_menu_status()
                return result, 200
            except Exception as e:
                return {"status": "error", "message": str(e)}, 500
    
    # Enregistrer les ressources
    api.add_resource(MenuUpdate, '/communication/menu/update')
    api.add_resource(MenuStatus, '/communication/menu/status')


# Fonctions utilitaires pour récupérer les instances des gestionnaires

def get_social_media_manager() -> SocialMediaManager:
    """
    Récupère ou crée l'instance du gestionnaire de réseaux sociaux.
    
    Returns:
        Instance du gestionnaire de réseaux sociaux
    """
    if not hasattr(g, 'social_media_manager'):
        config = current_app.config['COMMUNICATION_CONFIG']
        g.social_media_manager = SocialMediaManager(config)
    return g.social_media_manager


def get_notification_manager() -> NotificationManager:
    """
    Récupère ou crée l'instance du gestionnaire de notifications.
    
    Returns:
        Instance du gestionnaire de notifications
    """
    if not hasattr(g, 'notification_manager'):
        config = current_app.config['COMMUNICATION_CONFIG']
        g.notification_manager = NotificationManager(config)
    return g.notification_manager


def get_campaign_manager() -> CampaignManager:
    """
    Récupère ou crée l'instance du gestionnaire de campagnes.
    
    Returns:
        Instance du gestionnaire de campagnes
    """
    if not hasattr(g, 'campaign_manager'):
        config = current_app.config['COMMUNICATION_CONFIG']
        g.campaign_manager = CampaignManager(config)
    return g.campaign_manager


def get_menu_updater() -> MenuUpdater:
    """
    Récupère ou crée l'instance du gestionnaire de menus.
    
    Returns:
        Instance du gestionnaire de menus
    """
    if not hasattr(g, 'menu_updater'):
        config = current_app.config['COMMUNICATION_CONFIG']
        g.menu_updater = MenuUpdater(config)
    return g.menu_updater
