"""
Gestionnaire de mise à jour des menus

Ce module fournit la classe principale pour gérer la mise à jour automatique
des menus sur différentes plateformes (site web, réseaux sociaux, etc.).
"""

import os
import logging
import json
import datetime
from typing import Dict, List, Any, Optional, Union

from ..common import Config, format_date, retry_with_backoff


class MenuUpdater:
    """Gère la mise à jour des menus sur différentes plateformes"""
    
    def __init__(self, config: Config):
        """
        Initialise le gestionnaire de mise à jour des menus.
        
        Args:
            config: Configuration du module
        """
        self.logger = logging.getLogger("communication.menu_updater")
        
        # Récupérer la configuration spécifique aux menus
        if hasattr(config, 'get'):
            self.config = config
            self.menu_config = config.get('menu_updater', {})
            self.platforms = config.get('menu_updater.platforms', {})
            self.update_frequency = config.get('menu_updater.update_frequency', 'daily')
            self.default_update_time = config.get('menu_updater.default_update_time', '10:00')
        else:
            self.menu_config = config
            self.platforms = config.get('platforms', {})
            self.update_frequency = config.get('update_frequency', 'daily')
            self.default_update_time = config.get('default_update_time', '10:00')
        
        # Initialiser les connecteurs de plateforme
        self.platform_connectors = {}
        
        # Initialiser le connecteur pour le site web si configuré
        if 'website' in self.platforms and self.platforms['website'].get('enabled', False):
            from .connectors.website import WebsiteConnector
            self.platform_connectors['website'] = WebsiteConnector(self.platforms['website'])
            self.logger.info("Connecteur site web initialisé")
        
        # Initialiser le connecteur pour Google Business si configuré
        if 'google_business' in self.platforms and self.platforms['google_business'].get('enabled', False):
            from .connectors.google_business import GoogleBusinessConnector
            self.platform_connectors['google_business'] = GoogleBusinessConnector(self.platforms['google_business'])
            self.logger.info("Connecteur Google Business initialisé")
        
        # Initialiser le connecteur pour TheFork si configuré
        if 'thefork' in self.platforms and self.platforms['thefork'].get('enabled', False):
            from .connectors.thefork import TheForkConnector
            self.platform_connectors['thefork'] = TheForkConnector(self.platforms['thefork'])
            self.logger.info("Connecteur TheFork initialisé")
        
        # Stockage des données du dernier menu
        self.current_menu = {}
        self._load_current_menu()
        
        self.logger.info(f"Gestionnaire de menus initialisé avec {len(self.platform_connectors)} plateformes")
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def update_menu(self, menu_data: Dict[str, Any], 
                   platforms: Optional[List[str]] = None,
                   schedule_time: Optional[Union[str, datetime.datetime]] = None) -> Dict[str, Any]:
        """
        Met à jour le menu sur les plateformes configurées.
        
        Args:
            menu_data: Données du menu à mettre à jour
            platforms: Liste des plateformes à mettre à jour (si None, utilise toutes les plateformes configurées)
            schedule_time: Date/heure de mise à jour programmée (si None, met à jour immédiatement)
            
        Returns:
            Dictionnaire contenant les résultats de la mise à jour
        """
        if platforms is None:
            platforms = list(self.platform_connectors.keys())
            
        if schedule_time and isinstance(schedule_time, str):
            schedule_time = datetime.datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
            
        results = {
            "status": "scheduled" if schedule_time else "updated",
            "platforms": {},
            "errors": {}
        }
        
        if schedule_time:
            results["scheduled_time"] = format_date(schedule_time)
            
            # Programmer la mise à jour (dans une implémentation réelle, utiliserait une file d'attente)
            self.logger.info(f"Mise à jour du menu programmée pour {schedule_time}")
            # Simuler une programmation pour l'exemple
            return results
        
        # Mettre à jour le menu courant
        self.current_menu = menu_data
        self._save_current_menu()
        
        # Mettre à jour sur chaque plateforme
        for platform in platforms:
            if platform not in self.platform_connectors:
                results["errors"][platform] = f"Plateforme {platform} non configurée"
                continue
                
            try:
                # Adapter le format pour la plateforme
                adapted_menu = self._adapt_menu_for_platform(menu_data, platform)
                
                # Effectuer la mise à jour
                update_result = self.platform_connectors[platform].update_menu(adapted_menu)
                
                results["platforms"][platform] = update_result
                self.logger.info(f"Menu mis à jour sur {platform}")
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la mise à jour sur {platform}: {e}")
                results["errors"][platform] = str(e)
        
        # Si tout a échoué, mettre à jour le statut
        if not results["platforms"] and results["errors"]:
            results["status"] = "failed"
            
        return results
    
    def get_menu_status(self) -> Dict[str, Any]:
        """
        Récupère le statut des menus sur les différentes plateformes.
        
        Returns:
            Dictionnaire contenant le statut des menus
        """
        status = {
            "current_menu": {
                "last_updated": self.current_menu.get('last_updated', None),
                "categories": len(self.current_menu.get('categories', [])),
                "items": sum(len(category.get('items', [])) for category in self.current_menu.get('categories', []))
            },
            "platforms": {}
        }
        
        # Récupérer le statut pour chaque plateforme
        for platform_name, connector in self.platform_connectors.items():
            try:
                platform_status = connector.get_status()
                status["platforms"][platform_name] = platform_status
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération du statut pour {platform_name}: {e}")
                status["platforms"][platform_name] = {"status": "error", "message": str(e)}
        
        return status
    
    def sync_menu_from_source(self, source: str = "recipe_suggestion") -> Dict[str, Any]:
        """
        Synchronise le menu depuis une source externe.
        
        Args:
            source: Source de données pour la synchronisation
            
        Returns:
            Résultat de la synchronisation
        """
        self.logger.info(f"Synchronisation du menu depuis {source}")
        
        # Dans une implémentation réelle, cela interrogerait l'API du module de recettes
        # Pour l'exemple, on utilise un menu fictif
        
        # Données de menu fictives
        menu_data = {
            "last_updated": format_date(datetime.datetime.now()),
            "restaurant_name": "Le Vieux Moulin",
            "categories": [
                {
                    "id": "starters",
                    "name": "Entrées",
                    "description": "Pour commencer votre repas",
                    "items": [
                        {
                            "id": "bruschetta",
                            "name": "Bruschetta",
                            "description": "Pain grillé à l'ail avec tomates, basilic et huile d'olive",
                            "price": 6.50,
                            "allergens": ["gluten"],
                            "vegetarian": True,
                            "image_url": "https://example.com/images/bruschetta.jpg"
                        },
                        {
                            "id": "caesar_salad",
                            "name": "Salade César",
                            "description": "Laitue romaine, parmesan, croûtons et sauce César",
                            "price": 8.90,
                            "allergens": ["gluten", "lactose", "œufs"],
                            "vegetarian": False,
                            "image_url": "https://example.com/images/caesar.jpg"
                        }
                    ]
                },
                {
                    "id": "pizzas",
                    "name": "Pizzas",
                    "description": "Nos délicieuses pizzas cuites au feu de bois",
                    "items": [
                        {
                            "id": "margherita",
                            "name": "Margherita",
                            "description": "Sauce tomate, mozzarella et basilic",
                            "price": 10.50,
                            "allergens": ["gluten", "lactose"],
                            "vegetarian": True,
                            "image_url": "https://example.com/images/margherita.jpg"
                        },
                        {
                            "id": "pepperoni",
                            "name": "Pepperoni",
                            "description": "Sauce tomate, mozzarella et pepperoni",
                            "price": 12.50,
                            "allergens": ["gluten", "lactose"],
                            "vegetarian": False,
                            "image_url": "https://example.com/images/pepperoni.jpg"
                        },
                        {
                            "id": "special",
                            "name": "Pizza du jour",
                            "description": "Pizza spéciale du chef (demandez au serveur)",
                            "price": 14.90,
                            "allergens": ["gluten", "lactose"],
                            "vegetarian": False,
                            "special": True,
                            "image_url": "https://example.com/images/special.jpg"
                        }
                    ]
                },
                {
                    "id": "desserts",
                    "name": "Desserts",
                    "description": "Pour terminer sur une note sucrée",
                    "items": [
                        {
                            "id": "tiramisu",
                            "name": "Tiramisu",
                            "description": "Le classique dessert italien au café",
                            "price": 7.50,
                            "allergens": ["gluten", "lactose", "œufs"],
                            "vegetarian": True,
                            "image_url": "https://example.com/images/tiramisu.jpg"
                        },
                        {
                            "id": "panna_cotta",
                            "name": "Panna Cotta",
                            "description": "Crème cuite servie avec coulis de fruits rouges",
                            "price": 6.90,
                            "allergens": ["lactose"],
                            "vegetarian": True,
                            "image_url": "https://example.com/images/panna_cotta.jpg"
                        }
                    ]
                }
            ]
        }
        
        # Mettre à jour le menu
        return self.update_menu(menu_data)
    
    def _adapt_menu_for_platform(self, menu_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Adapte le format du menu pour une plateforme spécifique.
        
        Args:
            menu_data: Données du menu à adapter
            platform: Nom de la plateforme cible
            
        Returns:
            Menu adapté au format de la plateforme
        """
        adapted_menu = menu_data.copy()
        
        if platform == 'website':
            # Pas d'adaptation nécessaire, le format est déjà compatible
            return adapted_menu
            
        elif platform == 'google_business':
            # Adapter pour Google Business
            gb_menu = {
                "items": []
            }
            
            # Convertir les catégories et items au format Google Business
            for category in menu_data.get('categories', []):
                for item in category.get('items', []):
                    gb_menu["items"].append({
                        "name": item.get('name'),
                        "description": item.get('description', ''),
                        "price": {
                            "amount": item.get('price', 0),
                            "currency": "EUR"
                        },
                        "category": category.get('name'),
                        "attributes": {
                            "vegetarian": item.get('vegetarian', False),
                            "allergens": ", ".join(item.get('allergens', []))
                        }
                    })
            
            return gb_menu
            
        elif platform == 'thefork':
            # Adapter pour TheFork
            tf_menu = {
                "restaurant_id": self.platforms.get('thefork', {}).get('restaurant_id', ''),
                "categories": []
            }
            
            # Convertir les catégories et items au format TheFork
            for category in menu_data.get('categories', []):
                tf_category = {
                    "name": category.get('name'),
                    "description": category.get('description', ''),
                    "dishes": []
                }
                
                for item in category.get('items', []):
                    tf_category["dishes"].append({
                        "name": item.get('name'),
                        "description": item.get('description', ''),
                        "price": item.get('price', 0),
                        "allergens": item.get('allergens', []),
                        "diet_info": {
                            "vegetarian": item.get('vegetarian', False)
                        }
                    })
                
                tf_menu["categories"].append(tf_category)
            
            return tf_menu
        
        # Plateforme non reconnue, retourner le menu original
        return adapted_menu
    
    def _load_current_menu(self) -> None:
        """
        Charge le menu courant depuis le stockage persistent.
        """
        # Dans une implémentation réelle, cela chargerait depuis une base de données
        # Pour l'exemple, on simule avec un fichier JSON
        menu_file = os.path.join(os.path.dirname(__file__), 'current_menu.json')
        
        try:
            if os.path.exists(menu_file):
                with open(menu_file, 'r', encoding='utf-8') as f:
                    self.current_menu = json.load(f)
                self.logger.info("Menu courant chargé")
            else:
                self.logger.info("Aucun menu existant trouvé")
                self.current_menu = {}
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du menu: {e}")
            self.current_menu = {}
    
    def _save_current_menu(self) -> None:
        """
        Sauvegarde le menu courant dans le stockage persistent.
        """
        # Dans une implémentation réelle, cela sauvegarderait dans une base de données
        # Pour l'exemple, on simule avec un fichier JSON
        menu_file = os.path.join(os.path.dirname(__file__), 'current_menu.json')
        
        try:
            os.makedirs(os.path.dirname(menu_file), exist_ok=True)
            
            with open(menu_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_menu, f, indent=2, ensure_ascii=False)
                
            self.logger.debug("Menu courant sauvegardé")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du menu: {e}")
