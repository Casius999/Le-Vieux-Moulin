#!/usr/bin/env python3
"""
Intégrateur système pour le module de communication.

Ce module assure la synchronisation des données entre le module de communication
et les autres modules du système Le Vieux Moulin (CRM, recettes, comptabilité, IoT).
"""

import logging
import asyncio
import datetime
import json
from typing import Dict, List, Any, Optional, Union

from src.common import Config
from src.orchestrator import get_orchestrator


class SystemIntegrator:
    """
    Intégrateur système qui gère les échanges de données entre modules.
    
    Cette classe assure la communication bidirectionnelle entre le module de
    communication et les autres composants du système Le Vieux Moulin.
    """
    
    def __init__(self, config: Config):
        """
        Initialise l'intégrateur système.
        
        Args:
            config: Configuration du module
        """
        self.logger = logging.getLogger("communication.integration")
        self.config = config
        
        # Référence à l'orchestrateur de communication
        self.orchestrator = get_orchestrator(config)
        
        # Paramètres de connexion aux autres modules
        self._api_endpoints = {
            "central": config.get("integration.central_api_url", "http://localhost:8000/api"),
            "crm": config.get("integration.crm_api_url", "http://localhost:8001/api"),
            "recipes": config.get("integration.recipes_api_url", "http://localhost:8002/api"),
            "accounting": config.get("integration.accounting_api_url", "http://localhost:8003/api"),
            "iot": config.get("integration.iot_api_url", "http://localhost:8004/api"),
        }
        
        # Dictionnaire de mappage pour la transformation des données
        self._data_mappings = self._load_data_mappings()
        
        # Cache des données (évite des appels API répétés)
        self._data_cache = {
            "recipes": {"data": None, "timestamp": None, "ttl": 3600},  # 1 heure
            "customers": {"data": None, "timestamp": None, "ttl": 1800},  # 30 minutes
            "promotions": {"data": None, "timestamp": None, "ttl": 1800},  # 30 minutes
        }
        
        self.logger.info("Intégrateur système initialisé")
    
    def _load_data_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Charge les mappages de données depuis la configuration.
        
        Returns:
            Dictionnaire des mappages
        """
        mappings_path = self.config.get("integration.mappings_file", "../config/data_mappings.json")
        
        try:
            with open(mappings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Impossible de charger les mappages depuis {mappings_path}: {e}")
            
            # Mappages par défaut
            return {
                "recipe_to_post": {
                    "name": "title",
                    "description": "content",
                    "image": "media_url",
                    "price": "price_info",
                    "ingredients": "ingredients_list",
                    "preparation_time": "preparation_info"
                },
                "customer_to_recipient": {
                    "email": "email",
                    "phone": "phone",
                    "first_name": "first_name",
                    "last_name": "last_name",
                    "preferences": "preferences"
                }
            }
    
    async def start(self):
        """
        Démarre l'intégrateur et initialise les écouteurs d'événements.
        """
        self.logger.info("Démarrage de l'intégrateur système")
        
        # Enregistrer les webhooks pour écouter les événements des autres modules
        await self._register_webhooks()
        
        # Initialiser les tâches périodiques de synchronisation
        self._start_periodic_tasks()
        
        self.logger.info("Intégrateur système démarré")
    
    async def _register_webhooks(self):
        """
        Enregistre les webhooks auprès des autres modules du système.
        """
        callback_url = self.config.get("integration.webhook_callback_url", "http://localhost:5000/api/communication/webhook")
        
        # Enregistrer les webhooks auprès des modules source
        endpoints = {
            "central": "/webhooks/register",
            "crm": "/webhooks/register",
            "recipes": "/webhooks/register",
            "accounting": "/webhooks/register",
            "iot": "/webhooks/register"
        }
        
        events = {
            "recipes": ["new_recipe", "recipe_updated", "menu_changed"],
            "crm": ["customer_preferences_changed", "new_reservation", "feedback_received"],
            "accounting": ["promotion_approved", "budget_updated"],
            "iot": ["inventory_low", "customer_presence_changed"]
        }
        
        # Dans une implémentation réelle, cela serait fait par appels API asynchrones
        for module, module_events in events.items():
            for event in module_events:
                self.logger.info(f"Enregistrement du webhook pour {module}.{event} vers {callback_url}")
    
    def _start_periodic_tasks(self):
        """
        Démarre les tâches périodiques de synchronisation.
        """
        # Synchronisation du menu et des recettes (toutes les 4 heures)
        asyncio.create_task(self._periodic_task(
            task_func=self.sync_recipes_and_menu,
            interval=4 * 60 * 60,  # 4 heures
            initial_delay=60  # 1 minute après le démarrage
        ))
        
        # Synchronisation des données clients (toutes les 3 heures)
        asyncio.create_task(self._periodic_task(
            task_func=self.sync_customer_data,
            interval=3 * 60 * 60,  # 3 heures
            initial_delay=5 * 60  # 5 minutes après le démarrage
        ))
        
        # Synchronisation des promotions (toutes les 2 heures)
        asyncio.create_task(self._periodic_task(
            task_func=self.sync_promotions,
            interval=2 * 60 * 60,  # 2 heures
            initial_delay=10 * 60  # 10 minutes après le démarrage
        ))
    
    async def _periodic_task(self, task_func, interval, initial_delay=0):
        """
        Exécute une tâche périodiquement.
        
        Args:
            task_func: Fonction à exécuter
            interval: Intervalle en secondes
            initial_delay: Délai initial en secondes
        """
        await asyncio.sleep(initial_delay)
        while True:
            try:
                await task_func()
            except Exception as e:
                self.logger.error(f"Erreur dans la tâche périodique {task_func.__name__}: {e}")
            await asyncio.sleep(interval)
    
    # === Méthodes de synchronisation des données ===
    
    async def sync_recipes_and_menu(self):
        """
        Synchronise les recettes et le menu avec le module de recettes.
        """
        self.logger.info("Synchronisation des recettes et du menu")
        
        try:
            # Récupérer les recettes du module de recettes
            recipes = await self._fetch_data("recipes", "recipes/current")
            
            # Récupérer le menu actuel
            menu = await self._fetch_data("recipes", "menu/current")
            
            # Mettre à jour le menu sur les plateformes
            if menu:
                await self.orchestrator.update_menu(menu)
                self.logger.info("Menu mis à jour")
            
            # Créer des publications pour les nouvelles recettes
            if recipes:
                recent_recipes = [r for r in recipes if self._is_recent_recipe(r)]
                
                for recipe in recent_recipes:
                    post_content = self._transform_data(recipe, "recipe_to_post")
                    
                    # Publier sur les réseaux sociaux si la recette est nouvelle ou mise en avant
                    if recipe.get("featured", False) or self._is_very_recent_recipe(recipe):
                        await self.orchestrator.publish_to_social_media(
                            content=post_content,
                            platforms=["facebook", "instagram"],
                            scheduled_time=self._get_optimal_posting_time()
                        )
                        self.logger.info(f"Publication programmée pour la recette: {recipe['name']}")
            
            self.logger.info("Synchronisation des recettes et du menu terminée")
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des recettes et du menu: {e}")
    
    async def sync_customer_data(self):
        """
        Synchronise les données client avec le CRM.
        """
        self.logger.info("Synchronisation des données client")
        
        try:
            # Récupérer les données client du CRM
            customers = await self._fetch_data("crm", "customers")
            
            if not customers:
                self.logger.warning("Aucune donnée client reçue du CRM")
                return
            
            # Mettre à jour le cache
            self._update_cache("customers", customers)
            
            # Vérifier les préférences de communication et récupérer les segments
            communication_segments = await self._fetch_data("crm", "customers/segments/communication")
            
            if communication_segments:
                # Pour chaque segment, préparer les listes de diffusion appropriées
                for segment in communication_segments:
                    segment_id = segment.get("id")
                    segment_name = segment.get("name")
                    segment_customers = segment.get("customers", [])
                    
                    # Enregistrer le segment dans le gestionnaire de notifications
                    self._register_customer_segment(segment_id, segment_name, segment_customers)
                    
                    self.logger.info(f"Segment client enregistré: {segment_name} ({len(segment_customers)} clients)")
            
            self.logger.info("Synchronisation des données client terminée")
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des données client: {e}")
    
    async def sync_promotions(self):
        """
        Synchronise les promotions avec le module de comptabilité.
        """
        self.logger.info("Synchronisation des promotions")
        
        try:
            # Récupérer les promotions actives et à venir
            promotions = await self._fetch_data("accounting", "promotions/active")
            
            if not promotions:
                self.logger.warning("Aucune promotion active trouvée")
                return
            
            # Mettre à jour le cache
            self._update_cache("promotions", promotions)
            
            # Pour chaque promotion, créer ou mettre à jour une campagne
            for promo in promotions:
                campaign_data = self._create_campaign_from_promotion(promo)
                
                # Vérifier si la campagne existe déjà
                existing_campaign = await self._check_campaign_exists(promo.get("id"))
                
                if existing_campaign:
                    # Mettre à jour la campagne existante
                    await self.orchestrator.manage_campaign(
                        action="update",
                        campaign_id=existing_campaign.get("id"),
                        campaign_data=campaign_data
                    )
                    self.logger.info(f"Campagne mise à jour pour la promotion: {promo.get('name')}")
                else:
                    # Créer une nouvelle campagne
                    campaign_id = await self._create_campaign(campaign_data)
                    
                    # Démarrer la campagne si la date de début est atteinte
                    if self._should_start_campaign(promo):
                        await self.orchestrator.manage_campaign(
                            action="start",
                            campaign_id=campaign_id
                        )
                        self.logger.info(f"Nouvelle campagne démarrée: {promo.get('name')}")
                    else:
                        self.logger.info(f"Nouvelle campagne créée (démarrage planifié): {promo.get('name')}")
            
            self.logger.info("Synchronisation des promotions terminée")
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des promotions: {e}")
    
    # === Gestionnaire d'événements (webhooks) ===
    
    async def handle_webhook(self, event: str, source: str, data: Dict[str, Any]):
        """
        Gère les événements reçus via webhook.
        
        Args:
            event: Nom de l'événement
            source: Module source
            data: Données de l'événement
        """
        self.logger.info(f"Événement webhook reçu: {source}.{event}")
        
        # Router l'événement au gestionnaire approprié
        handler_method = f"_handle_{source}_{event}"
        
        if hasattr(self, handler_method) and callable(getattr(self, handler_method)):
            try:
                await getattr(self, handler_method)(data)
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de l'événement {source}.{event}: {e}")
        else:
            self.logger.warning(f"Pas de gestionnaire pour l'événement {source}.{event}")
    
    async def _handle_recipes_new_recipe(self, data: Dict[str, Any]):
        """
        Gère l'événement de création d'une nouvelle recette.
        
        Args:
            data: Données de la recette
        """
        self.logger.info(f"Nouvelle recette reçue: {data.get('name')}")
        
        # Transformer les données de la recette en publication
        post_content = self._transform_data(data, "recipe_to_post")
        
        # Publier sur les réseaux sociaux
        await self.orchestrator.publish_to_social_media(
            content=post_content,
            platforms=["facebook", "instagram"],
            scheduled_time=self._get_optimal_posting_time()
        )
        
        # Notifier les clients intéressés par les nouvelles recettes
        if self.config.get("integration.notify_on_new_recipe", True):
            recipients = await self._get_customers_by_preference("new_recipes")
            
            if recipients:
                await self.orchestrator.send_notification(
                    template="new_recipe",
                    recipients=recipients,
                    data={
                        "recipe": data,
                        "restaurant_name": "Le Vieux Moulin"
                    }
                )
                self.logger.info(f"Notification envoyée à {len(recipients)} clients pour la nouvelle recette")
    
    async def _handle_recipes_menu_changed(self, data: Dict[str, Any]):
        """
        Gère l'événement de changement de menu.
        
        Args:
            data: Données du nouveau menu
        """
        self.logger.info("Changement de menu détecté")
        
        # Mettre à jour le menu sur toutes les plateformes
        await self.orchestrator.update_menu(data)
        
        # Notifier les clients intéressés par les mises à jour de menu
        if self.config.get("integration.notify_on_menu_change", True):
            recipients = await self._get_customers_by_preference("menu_updates")
            
            if recipients:
                await self.orchestrator.send_notification(
                    template="menu_update",
                    recipients=recipients,
                    data={
                        "menu": data,
                        "restaurant_name": "Le Vieux Moulin"
                    }
                )
                self.logger.info(f"Notification de mise à jour du menu envoyée à {len(recipients)} clients")
    
    async def _handle_crm_customer_preferences_changed(self, data: Dict[str, Any]):
        """
        Gère l'événement de changement des préférences client.
        
        Args:
            data: Données de préférences client
        """
        self.logger.info(f"Préférences client modifiées: {data.get('customer_id')}")
        
        # Forcer une synchronisation des données client
        await self.sync_customer_data()
    
    async def _handle_accounting_promotion_approved(self, data: Dict[str, Any]):
        """
        Gère l'événement d'approbation d'une promotion.
        
        Args:
            data: Données de la promotion
        """
        self.logger.info(f"Promotion approuvée: {data.get('name')}")
        
        # Créer une campagne pour la promotion
        campaign_data = self._create_campaign_from_promotion(data)
        campaign_id = await self._create_campaign(campaign_data)
        
        # Démarrer la campagne si elle doit commencer immédiatement
        if self._should_start_campaign(data):
            await self.orchestrator.manage_campaign(
                action="start",
                campaign_id=campaign_id
            )
            self.logger.info(f"Campagne démarrée pour la promotion: {data.get('name')}")
    
    async def _handle_iot_inventory_low(self, data: Dict[str, Any]):
        """
        Gère l'événement de niveau bas d'inventaire.
        
        Args:
            data: Données d'inventaire
        """
        self.logger.info(f"Alerte de niveau bas d'inventaire: {data.get('item_name')}")
        
        # Vérifier si cette alerte devrait affecter les communications
        if data.get("impact_level", "low") in ["medium", "high"]:
            # Récupérer les recettes affectées
            affected_recipes = await self._get_recipes_using_ingredient(data.get("item_id"))
            
            if affected_recipes:
                # Adapter les communications et campagnes en cours
                await self._adjust_campaigns_for_inventory(affected_recipes, data)
                self.logger.info(f"Campagnes ajustées pour {len(affected_recipes)} recettes affectées")
    
    # === Méthodes utilitaires privées ===
    
    async def _fetch_data(self, module: str, endpoint: str) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Récupère des données depuis un autre module.
        
        Args:
            module: Nom du module source
            endpoint: Point de terminaison API
            
        Returns:
            Données récupérées ou None en cas d'erreur
        """
        # Dans une implémentation réelle, utiliserait aiohttp ou httpx
        # pour faire un appel API asynchrone
        
        # Ici, nous simulons un temps de latence
        await asyncio.sleep(0.2)
        
        # Simuler les données de retour
        if module == "recipes" and endpoint == "recipes/current":
            return [
                {
                    "id": "recipe_001",
                    "name": "Salade de Chèvre Chaud",
                    "description": "Salade fraîche avec toasts de chèvre chaud et miel",
                    "image": "https://example.com/images/chevre_salad.jpg",
                    "price": 8.50,
                    "ingredients": ["salade", "chèvre", "miel", "noix", "toasts"],
                    "preparation_time": 15,
                    "created_at": (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
                    "featured": True
                },
                {
                    "id": "recipe_002",
                    "name": "Entrecôte Grillée",
                    "description": "Entrecôte grillée avec frites maison et sauce béarnaise",
                    "image": "https://example.com/images/entrecote.jpg",
                    "price": 19.90,
                    "ingredients": ["boeuf", "pommes de terre", "œufs", "échalotes", "estragon"],
                    "preparation_time": 25,
                    "created_at": (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
                    "featured": False
                }
            ]
        elif module == "recipes" and endpoint == "menu/current":
            return {
                "id": "menu_2025_04",
                "name": "Menu Printemps 2025",
                "start_date": "2025-04-01",
                "end_date": "2025-06-30",
                "categories": [
                    {
                        "name": "Entrées",
                        "items": [
                            {"id": "recipe_001", "name": "Salade de Chèvre Chaud", "price": 8.50},
                            {"id": "recipe_003", "name": "Terrine Maison", "price": 7.90}
                        ]
                    },
                    {
                        "name": "Plats",
                        "items": [
                            {"id": "recipe_002", "name": "Entrecôte Grillée", "price": 19.90},
                            {"id": "recipe_004", "name": "Poisson du Jour", "price": 18.50}
                        ]
                    }
                ]
            }
        elif module == "accounting" and endpoint == "promotions/active":
            return [
                {
                    "id": "promo_001",
                    "name": "Happy Hour",
                    "description": "Apéritifs à -50% entre 18h et 19h",
                    "discount_percentage": 50,
                    "start_date": "2025-04-15T00:00:00Z",
                    "end_date": "2025-05-15T00:00:00Z",
                    "conditions": "Valable uniquement sur les apéritifs, du lundi au vendredi",
                    "budget": 500.00,
                    "target_audience": ["locals", "after_work"]
                },
                {
                    "id": "promo_002",
                    "name": "Menu Découverte",
                    "description": "Menu complet à prix réduit pour découvrir nos spécialités",
                    "fixed_price": 25.90,
                    "start_date": "2025-04-20T00:00:00Z",
                    "end_date": "2025-05-10T00:00:00Z",
                    "conditions": "Entrée + Plat + Dessert, hors boissons",
                    "budget": 1000.00,
                    "target_audience": ["new_customers", "food_lovers"]
                }
            ]
        
        # Si le endpoint n'est pas géré, retourner None
        self.logger.warning(f"Endpoint non simulé: {module}/{endpoint}")
        return None
    
    def _update_cache(self, cache_key: str, data: Any):
        """
        Met à jour le cache de données.
        
        Args:
            cache_key: Clé du cache
            data: Données à stocker
        """
        if cache_key in self._data_cache:
            self._data_cache[cache_key]["data"] = data
            self._data_cache[cache_key]["timestamp"] = datetime.datetime.now()
            self.logger.debug(f"Cache mis à jour: {cache_key}")
    
    def _transform_data(self, source_data: Dict[str, Any], mapping_key: str) -> Dict[str, Any]:
        """
        Transforme les données d'un format à un autre selon le mapping défini.
        
        Args:
            source_data: Données source
            mapping_key: Clé du mapping à utiliser
            
        Returns:
            Données transformées
        """
        if mapping_key not in self._data_mappings:
            self.logger.warning(f"Mapping non trouvé: {mapping_key}")
            return source_data
        
        mapping = self._data_mappings[mapping_key]
        result = {}
        
        # Appliquer le mapping
        for source_key, target_key in mapping.items():
            if source_key in source_data:
                result[target_key] = source_data[source_key]
        
        return result
    
    def _is_recent_recipe(self, recipe: Dict[str, Any]) -> bool:
        """
        Vérifie si une recette est récente (moins de 30 jours).
        
        Args:
            recipe: Données de la recette
            
        Returns:
            True si la recette est récente
        """
        try:
            created_at = datetime.datetime.fromisoformat(recipe.get("created_at", ""))
            now = datetime.datetime.now()
            return (now - created_at).days < 30
        except (ValueError, TypeError):
            return False
    
    def _is_very_recent_recipe(self, recipe: Dict[str, Any]) -> bool:
        """
        Vérifie si une recette est très récente (moins de 7 jours).
        
        Args:
            recipe: Données de la recette
            
        Returns:
            True si la recette est très récente
        """
        try:
            created_at = datetime.datetime.fromisoformat(recipe.get("created_at", ""))
            now = datetime.datetime.now()
            return (now - created_at).days < 7
        except (ValueError, TypeError):
            return False
    
    def _get_optimal_posting_time(self) -> str:
        """
        Détermine l'heure optimale pour une publication.
        
        Returns:
            Horodatage ISO 8601 pour la publication
        """
        now = datetime.datetime.now()
        
        # Déterminer l'heure cible (par exemple, 18h00 le même jour)
        target_hour = 18
        
        # Si l'heure actuelle est après l'heure cible, planifier pour le lendemain
        if now.hour >= target_hour:
            target_date = now.date() + datetime.timedelta(days=1)
        else:
            target_date = now.date()
        
        target_time = datetime.datetime.combine(
            target_date,
            datetime.time(hour=target_hour, minute=0)
        )
        
        return target_time.isoformat()
    
    def _register_customer_segment(self, segment_id: str, segment_name: str, customer_ids: List[str]):
        """
        Enregistre un segment client dans le gestionnaire de notifications.
        
        Args:
            segment_id: Identifiant du segment
            segment_name: Nom du segment
            customer_ids: Liste des identifiants clients
        """
        # Dans une implémentation réelle, cela appellerait une méthode
        # du NotificationManager pour enregistrer le segment
        self.logger.info(f"Segment client enregistré: {segment_name} ({len(customer_ids)} clients)")
    
    def _create_campaign_from_promotion(self, promotion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une structure de campagne à partir d'une promotion.
        
        Args:
            promotion: Données de la promotion
            
        Returns:
            Données de la campagne
        """
        # Convertir la promotion en structure de campagne
        return {
            "name": f"Campagne - {promotion.get('name')}",
            "description": promotion.get('description', ''),
            "start_date": promotion.get('start_date'),
            "end_date": promotion.get('end_date'),
            "target_audience": promotion.get('target_audience', []),
            "budget": promotion.get('budget', 0),
            "promotion_id": promotion.get('id'),
            "channels": [
                {
                    "type": "social_media",
                    "config": {
                        "platforms": ["facebook", "instagram"],
                        "frequency": "daily"
                    }
                },
                {
                    "type": "email",
                    "config": {
                        "template": "promotion_announcement",
                        "frequency": "once"
                    }
                }
            ],
            "content": {
                "title": promotion.get('name'),
                "body": promotion.get('description', ''),
                "call_to_action": "Réservez maintenant pour en profiter !",
                "conditions": promotion.get('conditions', '')
            }
        }
    
    async def _check_campaign_exists(self, promotion_id: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie si une campagne existe déjà pour une promotion.
        
        Args:
            promotion_id: Identifiant de la promotion
            
        Returns:
            Données de la campagne si elle existe, sinon None
        """
        # Dans une implémentation réelle, cette méthode interrogerait
        # le CampaignManager pour trouver une campagne existante
        
        # Ici, nous simulons simplement qu'aucune campagne n'existe
        return None
    
    async def _create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """
        Crée une nouvelle campagne.
        
        Args:
            campaign_data: Données de la campagne
            
        Returns:
            Identifiant de la campagne créée
        """
        # Dans une implémentation réelle, cette méthode appellerait
        # le CampaignManager pour créer une nouvelle campagne
        
        # Simuler un identifiant de campagne
        campaign_id = f"campaign_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.logger.info(f"Nouvelle campagne créée: {campaign_id}")
        return campaign_id
    
    def _should_start_campaign(self, promotion: Dict[str, Any]) -> bool:
        """
        Détermine si une campagne doit être démarrée immédiatement.
        
        Args:
            promotion: Données de la promotion
            
        Returns:
            True si la campagne doit être démarrée
        """
        try:
            start_date = datetime.datetime.fromisoformat(promotion.get("start_date", "").replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # Si la date de début est dans le passé ou dans moins de 24 heures
            return (start_date - now).total_seconds() < 24 * 60 * 60
        except (ValueError, TypeError):
            # Par défaut, ne pas démarrer
            return False
    
    async def _get_customers_by_preference(self, preference: str) -> List[str]:
        """
        Récupère les clients ayant une préférence spécifique.
        
        Args:
            preference: Type de préférence
            
        Returns:
            Liste des adresses email des clients
        """
        # Dans une implémentation réelle, cette méthode interrogerait le CRM
        # pour obtenir les clients ayant une préférence spécifique
        
        # Simuler une liste d'emails
        return ["client1@example.com", "client2@example.com"]
    
    async def _get_recipes_using_ingredient(self, ingredient_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les recettes utilisant un ingrédient spécifique.
        
        Args:
            ingredient_id: Identifiant de l'ingrédient
            
        Returns:
            Liste des recettes utilisant l'ingrédient
        """
        # Dans une implémentation réelle, cette méthode interrogerait
        # le module de recettes pour trouver les recettes utilisant un ingrédient
        
        # Simuler une liste de recettes
        return []
    
    async def _adjust_campaigns_for_inventory(self, affected_recipes: List[Dict[str, Any]], inventory_data: Dict[str, Any]):
        """
        Ajuste les campagnes en fonction des problèmes d'inventaire.
        
        Args:
            affected_recipes: Recettes affectées
            inventory_data: Données d'inventaire
        """
        # Dans une implémentation réelle, cette méthode ajusterait
        # les campagnes pour éviter de promouvoir des recettes indisponibles
        
        self.logger.info(f"Ajustement des campagnes pour {len(affected_recipes)} recettes affectées")


# Singleton pour un accès facile depuis d'autres modules
_instance = None

def get_integrator(config: Config = None):
    """
    Récupère l'instance singleton de l'intégrateur.
    
    Args:
        config: Configuration (uniquement utilisée lors de la première initialisation)
        
    Returns:
        Instance de l'intégrateur
    """
    global _instance
    if _instance is None:
        if config is None:
            raise ValueError("La configuration est requise pour l'initialisation de l'intégrateur")
        _instance = SystemIntegrator(config)
    return _instance
