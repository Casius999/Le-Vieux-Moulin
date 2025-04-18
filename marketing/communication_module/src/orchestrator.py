#!/usr/bin/env python3
"""
Orchestrateur central de communication pour Le Vieux Moulin.

Ce module centralise et synchronise toutes les actions de communication
du système en coordonnant les différents gestionnaires de communication
(réseaux sociaux, notifications, menus, campagnes).
"""

import logging
import threading
import asyncio
import datetime
from typing import Dict, List, Any, Optional, Union, Callable

from src.common import Config
from src.social_media import SocialMediaManager
from src.notification import NotificationManager
from src.campaign_manager import CampaignManager
from src.menu_updater import MenuUpdater


class CommunicationOrchestrator:
    """
    Orchestrateur central qui coordonne toutes les actions de communication.
    
    Cette classe assure la cohérence des messages marketing sur tous les canaux,
    gère les dépendances entre les actions et optimise le timing des communications.
    """
    
    def __init__(self, config: Config):
        """
        Initialise l'orchestrateur avec les gestionnaires de communication.
        
        Args:
            config: Configuration du module de communication
        """
        self.logger = logging.getLogger("communication.orchestrator")
        self.config = config
        
        # Initialisation des gestionnaires
        self.social_media = SocialMediaManager(config)
        self.notification = NotificationManager(config)
        self.campaign = CampaignManager(config)
        self.menu_updater = MenuUpdater(config)
        
        # File d'attente des tâches de communication
        self.task_queue = asyncio.Queue()
        
        # Registre des webhooks et callbacks
        self.webhooks = {}
        
        # État de synchronisation
        self.sync_state = {
            "last_menu_update": None,
            "pending_social_posts": [],
            "pending_notifications": [],
            "active_campaigns": []
        }
        
        # Verrou de synchronisation pour les opérations concurrentes
        self.sync_lock = threading.RLock()
        
        self.logger.info("Orchestrateur de communication initialisé")
    
    async def start(self):
        """
        Démarre l'orchestrateur et initialise les tâches planifiées.
        """
        self.logger.info("Démarrage de l'orchestrateur de communication")
        
        # Démarrer les gestionnaires
        await self._start_managers()
        
        # Démarrer le worker de traitement des tâches
        asyncio.create_task(self._process_task_queue())
        
        # Initialiser les tâches planifiées
        self._initialize_scheduled_tasks()
        
        self.logger.info("Orchestrateur de communication démarré")
    
    async def _start_managers(self):
        """
        Démarre tous les gestionnaires de communication.
        """
        # Ces appels seraient asynchrones dans une implémentation réelle
        # Start managers concurrently
        await asyncio.gather(
            self._start_manager("social_media", self.social_media),
            self._start_manager("notification", self.notification),
            self._start_manager("campaign", self.campaign),
            self._start_manager("menu_updater", self.menu_updater)
        )
    
    async def _start_manager(self, name, manager):
        """
        Démarre un gestionnaire spécifique de manière sécurisée.
        
        Args:
            name: Nom du gestionnaire
            manager: Instance du gestionnaire
        """
        try:
            self.logger.info(f"Démarrage du gestionnaire {name}")
            # Appel hypothétique à une méthode de démarrage async
            if hasattr(manager, 'start') and callable(getattr(manager, 'start')):
                await manager.start()
            self.logger.info(f"Gestionnaire {name} démarré avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du gestionnaire {name}: {e}")
            # Ne pas propager l'erreur pour éviter un arrêt complet
    
    def _initialize_scheduled_tasks(self):
        """
        Initialise les tâches planifiées pour la synchronisation automatique.
        """
        # Planifier la synchronisation des menus (quotidienne)
        self._schedule_task(
            task_func=self.sync_menus,
            initial_delay=self._get_time_until_next_hour(10),  # 10h du matin
            interval=24 * 60 * 60  # 24 heures
        )
        
        # Planifier la vérification des campagnes (toutes les heures)
        self._schedule_task(
            task_func=self.check_campaign_triggers,
            initial_delay=60,  # 1 minute après le démarrage
            interval=60 * 60  # Toutes les heures
        )
        
        # Planifier la synchronisation des statistiques (toutes les 3 heures)
        self._schedule_task(
            task_func=self.sync_analytics,
            initial_delay=5 * 60,  # 5 minutes après le démarrage
            interval=3 * 60 * 60  # Toutes les 3 heures
        )
    
    def _schedule_task(self, task_func: Callable, initial_delay: int, interval: int):
        """
        Planifie une tâche récurrente.
        
        Args:
            task_func: Fonction à exécuter
            initial_delay: Délai initial en secondes
            interval: Intervalle de répétition en secondes
        """
        async def scheduled_runner():
            await asyncio.sleep(initial_delay)
            while True:
                try:
                    if asyncio.iscoroutinefunction(task_func):
                        await task_func()
                    else:
                        task_func()
                except Exception as e:
                    self.logger.error(f"Erreur dans la tâche planifiée {task_func.__name__}: {e}")
                await asyncio.sleep(interval)
        
        # Démarrer la tâche planifiée
        asyncio.create_task(scheduled_runner())
        self.logger.info(f"Tâche '{task_func.__name__}' planifiée (délai: {initial_delay}s, intervalle: {interval}s)")
    
    def _get_time_until_next_hour(self, hour: int) -> int:
        """
        Calcule le temps en secondes jusqu'à la prochaine occurrence d'une heure spécifique.
        
        Args:
            hour: Heure cible (0-23)
            
        Returns:
            Nombre de secondes jusqu'à l'heure cible
        """
        now = datetime.datetime.now()
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if target <= now:
            # Si l'heure cible est déjà passée aujourd'hui, prendre celle de demain
            target += datetime.timedelta(days=1)
        
        return (target - now).total_seconds()
    
    async def _process_task_queue(self):
        """
        Traite en continu les tâches de la file d'attente.
        """
        self.logger.info("Démarrage du traitement de la file des tâches")
        while True:
            try:
                # Récupérer une tâche de la file d'attente
                task = await self.task_queue.get()
                
                # Exécuter la tâche
                task_type = task.get("type")
                handler_method = f"_handle_{task_type}_task"
                
                if hasattr(self, handler_method) and callable(getattr(self, handler_method)):
                    handler = getattr(self, handler_method)
                    await handler(task)
                else:
                    self.logger.warning(f"Pas de gestionnaire pour le type de tâche '{task_type}'")
                
                # Marquer la tâche comme terminée
                self.task_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement d'une tâche: {e}")
                # Continue à traiter les tâches suivantes
    
    async def enqueue_task(self, task_type: str, **kwargs):
        """
        Ajoute une tâche à la file d'attente pour traitement asynchrone.
        
        Args:
            task_type: Type de tâche (publish, notify, update_menu, campaign)
            **kwargs: Paramètres spécifiques à la tâche
        """
        task = {
            "type": task_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "params": kwargs
        }
        
        await self.task_queue.put(task)
        self.logger.debug(f"Tâche '{task_type}' ajoutée à la file d'attente")
    
    # === Gestionnaires de tâches spécifiques ===
    
    async def _handle_publish_task(self, task):
        """
        Gère une tâche de publication sur les réseaux sociaux.
        
        Args:
            task: Définition de la tâche
        """
        params = task.get("params", {})
        content = params.get("content")
        platforms = params.get("platforms", [])
        
        if not content or not platforms:
            self.logger.error("Impossible de publier: contenu ou plateformes manquants")
            return
        
        try:
            result = await self.social_media.publish_content_async(
                content=content,
                platforms=platforms,
                scheduled_time=params.get("scheduled_time"),
                targeting=params.get("targeting")
            )
            
            self.logger.info(f"Publication réussie sur {len(platforms)} plateformes")
            
            # Mise à jour de l'état de synchronisation
            with self.sync_lock:
                self.sync_state["pending_social_posts"] = [
                    post for post in self.sync_state["pending_social_posts"] 
                    if post.get("id") != params.get("id")
                ]
            
            # Déclencher les webhooks de succès
            await self._trigger_webhooks("publication_success", {
                "publication_id": params.get("id"),
                "platforms": platforms,
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la publication: {e}")
            
            # Déclencher les webhooks d'échec
            await self._trigger_webhooks("publication_failure", {
                "publication_id": params.get("id"),
                "error": str(e)
            })
    
    async def _handle_notify_task(self, task):
        """
        Gère une tâche d'envoi de notification.
        
        Args:
            task: Définition de la tâche
        """
        params = task.get("params", {})
        template = params.get("template")
        recipients = params.get("recipients", [])
        data = params.get("data", {})
        channels = params.get("channels", ["email"])
        
        if not template or not recipients:
            self.logger.error("Impossible d'envoyer la notification: template ou destinataires manquants")
            return
        
        try:
            result = await self.notification.send_notification_async(
                template=template,
                recipients=recipients,
                data=data,
                channels=channels
            )
            
            self.logger.info(f"Notification envoyée à {len(recipients)} destinataires")
            
            # Mise à jour de l'état de synchronisation
            with self.sync_lock:
                self.sync_state["pending_notifications"] = [
                    notif for notif in self.sync_state["pending_notifications"] 
                    if notif.get("id") != params.get("id")
                ]
            
            # Déclencher les webhooks de succès
            await self._trigger_webhooks("notification_success", {
                "notification_id": params.get("id"),
                "recipients_count": len(recipients),
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de notification: {e}")
            
            # Déclencher les webhooks d'échec
            await self._trigger_webhooks("notification_failure", {
                "notification_id": params.get("id"),
                "error": str(e)
            })
    
    async def _handle_update_menu_task(self, task):
        """
        Gère une tâche de mise à jour de menu.
        
        Args:
            task: Définition de la tâche
        """
        params = task.get("params", {})
        menu_data = params.get("menu_data", {})
        platforms = params.get("platforms", ["website", "social_media"])
        
        if not menu_data:
            self.logger.error("Impossible de mettre à jour le menu: données manquantes")
            return
        
        try:
            result = await self.menu_updater.update_menu_async(
                menu_data=menu_data,
                platforms=platforms
            )
            
            self.logger.info(f"Menu mis à jour sur {len(platforms)} plateformes")
            
            # Mise à jour de l'état de synchronisation
            with self.sync_lock:
                self.sync_state["last_menu_update"] = datetime.datetime.now().isoformat()
            
            # Déclencher les webhooks de succès
            await self._trigger_webhooks("menu_update_success", {
                "update_id": params.get("id"),
                "platforms": platforms,
                "result": result
            })
            
            # Si la configuration indique de notifier les clients lors des mises à jour de menu
            if self.config.get("menu_updater.notify_customers", False):
                await self.enqueue_task("notify", 
                    template="menu_update", 
                    recipients=await self._get_subscribed_customers("menu_updates"),
                    data={
                        "menu": menu_data,
                        "restaurant_name": "Le Vieux Moulin"
                    },
                    channels=["email"]
                )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour du menu: {e}")
            
            # Déclencher les webhooks d'échec
            await self._trigger_webhooks("menu_update_failure", {
                "update_id": params.get("id"),
                "error": str(e)
            })
    
    async def _handle_campaign_task(self, task):
        """
        Gère une tâche de campagne marketing.
        
        Args:
            task: Définition de la tâche
        """
        params = task.get("params", {})
        action = params.get("action")
        campaign_id = params.get("campaign_id")
        
        if not action or not campaign_id:
            self.logger.error("Impossible de gérer la campagne: action ou ID manquant")
            return
        
        try:
            if action == "start":
                result = await self.campaign.start_campaign_async(campaign_id)
                log_message = f"Campagne {campaign_id} démarrée avec succès"
                webhook_event = "campaign_started"
            elif action == "stop":
                result = await self.campaign.stop_campaign_async(campaign_id)
                log_message = f"Campagne {campaign_id} arrêtée avec succès"
                webhook_event = "campaign_stopped"
            elif action == "pause":
                result = await self.campaign.pause_campaign_async(campaign_id)
                log_message = f"Campagne {campaign_id} mise en pause avec succès"
                webhook_event = "campaign_paused"
            else:
                self.logger.error(f"Action de campagne non reconnue: {action}")
                return
            
            self.logger.info(log_message)
            
            # Mise à jour de l'état de synchronisation
            with self.sync_lock:
                campaign_info = await self.campaign.get_campaign_info_async(campaign_id)
                
                # Mettre à jour la liste des campagnes actives
                active_campaigns = [c for c in self.sync_state["active_campaigns"] if c["id"] != campaign_id]
                if campaign_info["status"] == "active":
                    active_campaigns.append(campaign_info)
                
                self.sync_state["active_campaigns"] = active_campaigns
            
            # Déclencher les webhooks
            await self._trigger_webhooks(webhook_event, {
                "campaign_id": campaign_id,
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la gestion de la campagne {campaign_id}: {e}")
            
            # Déclencher les webhooks d'échec
            await self._trigger_webhooks("campaign_action_failure", {
                "campaign_id": campaign_id,
                "action": action,
                "error": str(e)
            })
    
    # === Méthodes de synchronisation ===
    
    async def sync_menus(self):
        """
        Synchronise les menus sur toutes les plateformes.
        """
        self.logger.info("Démarrage de la synchronisation des menus")
        
        try:
            # Récupération des données du menu depuis le système central
            menu_data = await self._fetch_current_menu()
            
            # Mise à jour du menu sur toutes les plateformes
            await self.enqueue_task("update_menu", 
                menu_data=menu_data,
                platforms=["website", "social_media", "delivery_platforms", "reservation_platforms"]
            )
            
            self.logger.info("Synchronisation des menus planifiée")
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des menus: {e}")
    
    async def check_campaign_triggers(self):
        """
        Vérifie les déclencheurs de campagnes et active les campagnes appropriées.
        """
        self.logger.info("Vérification des déclencheurs de campagnes")
        
        try:
            # Récupération des campagnes avec des déclencheurs actifs
            triggered_campaigns = await self.campaign.check_campaign_triggers_async()
            
            for campaign in triggered_campaigns:
                self.logger.info(f"Campagne déclenchée: {campaign['id']} - {campaign['name']}")
                
                # Démarrer la campagne
                await self.enqueue_task("campaign", 
                    action="start",
                    campaign_id=campaign["id"]
                )
            
            self.logger.info(f"Vérification terminée: {len(triggered_campaigns)} campagne(s) déclenchée(s)")
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des déclencheurs de campagnes: {e}")
    
    async def sync_analytics(self):
        """
        Synchronise et consolide les analyses de toutes les plateformes.
        """
        self.logger.info("Démarrage de la synchronisation des analyses")
        
        try:
            # Récupération des analyses de chaque gestionnaire
            social_analytics = await self.social_media.get_analytics_async()
            notification_analytics = await self.notification.get_analytics_async()
            campaign_analytics = await self.campaign.get_analytics_async()
            
            # Consolidation des données
            consolidated_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "social_media": social_analytics,
                "notifications": notification_analytics,
                "campaigns": campaign_analytics
            }
            
            # Stocker les analytics consolidées
            await self._store_analytics(consolidated_data)
            
            self.logger.info("Synchronisation des analyses terminée")
            
            # Déclencher les webhooks
            await self._trigger_webhooks("analytics_updated", {
                "analytics": consolidated_data
            })
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des analyses: {e}")
    
    # === Méthodes d'utilitaires privées ===
    
    async def _trigger_webhooks(self, event: str, data: Dict[str, Any]):
        """
        Déclenche tous les webhooks enregistrés pour un événement spécifique.
        
        Args:
            event: Nom de l'événement
            data: Données de l'événement à envoyer
        """
        if event not in self.webhooks:
            return
        
        event_payload = {
            "event": event,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data
        }
        
        for webhook_url in self.webhooks.get(event, []):
            try:
                # Envoi asynchrone du webhook (implémentation simplifiée)
                self.logger.debug(f"Déclenchement du webhook {event} vers {webhook_url}")
                # Dans une implémentation réelle, utiliserait aiohttp ou httpx
            except Exception as e:
                self.logger.error(f"Erreur lors du déclenchement du webhook {event}: {e}")
    
    async def _fetch_current_menu(self) -> Dict[str, Any]:
        """
        Récupère les données actuelles du menu depuis le système central.
        
        Returns:
            Données du menu
        """
        # Dans une implémentation réelle, cette méthode ferait un appel API
        # au système central pour récupérer les données du menu actuelles
        
        # Simuler un appel asynchrone
        await asyncio.sleep(0.1)
        
        # Retourner des données factices de menu
        return {
            "menu_id": "current_menu_2025",
            "last_updated": datetime.datetime.now().isoformat(),
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {"name": "Salade de chèvre chaud", "price": 8.50, "description": "Salade, toasts de chèvre, miel, noix"},
                        {"name": "Terrine maison", "price": 7.90, "description": "Terrine de campagne aux herbes"}
                    ]
                },
                {
                    "name": "Plats",
                    "items": [
                        {"name": "Entrecôte grillée", "price": 19.90, "description": "Avec frites maison et sauce béarnaise"},
                        {"name": "Poisson du jour", "price": 18.50, "description": "Selon arrivage, avec légumes de saison"}
                    ]
                }
            ]
        }
    
    async def _get_subscribed_customers(self, subscription_type: str) -> List[str]:
        """
        Récupère la liste des clients abonnés à un type de communication spécifique.
        
        Args:
            subscription_type: Type d'abonnement (ex: "menu_updates", "promotions")
            
        Returns:
            Liste des emails des clients abonnés
        """
        # Dans une implémentation réelle, cette méthode interrogerait le CRM
        # pour obtenir la liste des clients abonnés

        # Simuler un appel asynchrone
        await asyncio.sleep(0.1)
        
        # Retourner des données factices
        return ["client1@example.com", "client2@example.com"]
    
    async def _store_analytics(self, data: Dict[str, Any]):
        """
        Stocke les données d'analyse consolidées.
        
        Args:
            data: Données d'analyse à stocker
        """
        # Dans une implémentation réelle, cette méthode stockerait les données
        # dans une base de données ou un service d'analyse
        
        # Simuler un appel asynchrone
        await asyncio.sleep(0.1)
        
        # Dans cet exemple, simplement journaliser l'action
        self.logger.info(f"Données d'analyse stockées pour {data['timestamp']}")
    
    # === API publique pour les autres modules ===
    
    async def publish_to_social_media(self, content: Dict[str, Any], platforms: List[str], **kwargs):
        """
        Publie du contenu sur les réseaux sociaux.
        
        Args:
            content: Contenu à publier
            platforms: Liste des plateformes cibles
            **kwargs: Options supplémentaires
        """
        await self.enqueue_task("publish", content=content, platforms=platforms, **kwargs)
    
    async def send_notification(self, template: str, recipients: List[str], data: Dict[str, Any], channels: List[str] = None):
        """
        Envoie une notification aux clients.
        
        Args:
            template: Identifiant du template de notification
            recipients: Liste des destinataires
            data: Données à insérer dans le template
            channels: Canaux de notification (par défaut: email)
        """
        await self.enqueue_task("notify", template=template, recipients=recipients, data=data, channels=channels or ["email"])
    
    async def update_menu(self, menu_data: Dict[str, Any], platforms: List[str] = None):
        """
        Met à jour le menu sur les plateformes spécifiées.
        
        Args:
            menu_data: Données du menu
            platforms: Plateformes à mettre à jour
        """
        await self.enqueue_task("update_menu", menu_data=menu_data, platforms=platforms or ["website", "social_media"])
    
    async def manage_campaign(self, action: str, campaign_id: str):
        """
        Gère une campagne marketing.
        
        Args:
            action: Action à effectuer (start, stop, pause)
            campaign_id: Identifiant de la campagne
        """
        await self.enqueue_task("campaign", action=action, campaign_id=campaign_id)
    
    def register_webhook(self, event: str, url: str):
        """
        Enregistre un webhook pour un événement spécifique.
        
        Args:
            event: Nom de l'événement
            url: URL du webhook
        """
        if event not in self.webhooks:
            self.webhooks[event] = []
        
        if url not in self.webhooks[event]:
            self.webhooks[event].append(url)
            self.logger.info(f"Webhook enregistré pour l'événement '{event}': {url}")
    
    def unregister_webhook(self, event: str, url: str):
        """
        Désenregistre un webhook.
        
        Args:
            event: Nom de l'événement
            url: URL du webhook
        """
        if event in self.webhooks and url in self.webhooks[event]:
            self.webhooks[event].remove(url)
            self.logger.info(f"Webhook désenregistré pour l'événement '{event}': {url}")
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Récupère l'état actuel de synchronisation.
        
        Returns:
            État de synchronisation actuel
        """
        with self.sync_lock:
            return self.sync_state.copy()


# Singleton pour un accès facile depuis d'autres modules
_instance = None

def get_orchestrator(config: Config = None):
    """
    Récupère l'instance singleton de l'orchestrateur.
    
    Args:
        config: Configuration (uniquement utilisée lors de la première initialisation)
        
    Returns:
        Instance de l'orchestrateur
    """
    global _instance
    if _instance is None:
        if config is None:
            raise ValueError("La configuration est requise pour l'initialisation de l'orchestrateur")
        _instance = CommunicationOrchestrator(config)
    return _instance
