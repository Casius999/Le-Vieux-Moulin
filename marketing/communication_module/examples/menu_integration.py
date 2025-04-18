#!/usr/bin/env python3
"""
Exemple d'intégration et de synchronisation des menus pour Le Vieux Moulin.

Ce script montre comment utiliser le module de communication pour automatiser
la mise à jour et la diffusion des menus sur différentes plateformes.
"""

import os
import sys
import asyncio
import datetime
import logging
import json
from typing import Dict, List, Any

# Ajout du répertoire parent au PYTHONPATH pour l'importation des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.common import Config, setup_logger
from src.orchestrator import get_orchestrator
from src.menu_updater import MenuUpdater
from src.integration import get_integrator


async def update_seasonal_menu():
    """
    Met à jour le menu saisonnier sur toutes les plateformes.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("menu_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Définition du nouveau menu saisonnier
    seasonal_menu = {
        "id": "menu_ete_2025",
        "name": "Menu d'Été 2025",
        "start_date": "2025-06-01",
        "end_date": "2025-08-31",
        "type": "seasonal",
        "categories": [
            {
                "name": "Entrées",
                "items": [
                    {
                        "id": "item_001",
                        "name": "Gaspacho de tomates anciennes",
                        "description": "Gaspacho de tomates anciennes, burrata crémeuse et basilic frais",
                        "price": 9.50,
                        "allergens": ["lait"],
                        "vegetarian": True,
                        "image_url": "https://example.com/images/gaspacho.jpg"
                    },
                    {
                        "id": "item_002",
                        "name": "Tartare de dorade",
                        "description": "Tartare de dorade aux agrumes et à l'avocat, croustillant de pain noir",
                        "price": 12.50,
                        "allergens": ["poisson", "gluten"],
                        "vegetarian": False,
                        "image_url": "https://example.com/images/tartare_dorade.jpg"
                    }
                ]
            },
            {
                "name": "Plats",
                "items": [
                    {
                        "id": "item_003",
                        "name": "Pavé de thon mi-cuit",
                        "description": "Pavé de thon mi-cuit, légumes grillés et sauce vierge aux herbes fraîches",
                        "price": 21.90,
                        "allergens": ["poisson"],
                        "vegetarian": False,
                        "image_url": "https://example.com/images/thon.jpg"
                    },
                    {
                        "id": "item_004",
                        "name": "Risotto aux asperges",
                        "description": "Risotto crémeux aux asperges vertes et parmesan, chips de légumes",
                        "price": 18.50,
                        "allergens": ["lait", "céleri"],
                        "vegetarian": True,
                        "image_url": "https://example.com/images/risotto.jpg"
                    }
                ]
            },
            {
                "name": "Desserts",
                "items": [
                    {
                        "id": "item_005",
                        "name": "Fraisier aux agrumes",
                        "description": "Fraisier revisité aux agrumes et basilic, sorbet citron vert",
                        "price": 8.90,
                        "allergens": ["lait", "œufs", "gluten"],
                        "vegetarian": True,
                        "image_url": "https://example.com/images/fraisier.jpg"
                    },
                    {
                        "id": "item_006",
                        "name": "Crème brûlée à la lavande",
                        "description": "Crème brûlée parfumée à la lavande, tuile craquante",
                        "price": 7.50,
                        "allergens": ["lait", "œufs"],
                        "vegetarian": True,
                        "image_url": "https://example.com/images/creme_brulee.jpg"
                    }
                ]
            }
        ],
        "menus_complets": [
            {
                "name": "Menu Découverte",
                "description": "Entrée + Plat + Dessert",
                "price": 32.90,
                "available": ["midi", "soir"],
                "days": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
            },
            {
                "name": "Menu Express",
                "description": "Plat + Dessert",
                "price": 24.90,
                "available": ["midi"],
                "days": ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
            }
        ],
        "wines": [
            {
                "id": "wine_001",
                "name": "Rosé Château Minuty",
                "origin": "Provence",
                "year": 2024,
                "price_bottle": 28.00,
                "price_glass": 6.50,
                "description": "Rosé frais et élégant aux notes d'agrumes et de pêche blanche"
            },
            {
                "id": "wine_002",
                "name": "Sancerre Les Baronnes",
                "origin": "Loire",
                "year": 2023,
                "price_bottle": 35.00,
                "price_glass": 7.50,
                "description": "Blanc sec et minéral aux notes d'agrumes et de fleurs blanches"
            }
        ]
    }
    
    # Mise à jour du menu sur toutes les plateformes
    await orchestrator.update_menu(
        menu_data=seasonal_menu,
        platforms=["website", "social_media", "delivery_platforms", "reservation_platforms"]
    )
    
    logger.info(f"Menu saisonnier mis à jour sur toutes les plateformes: {seasonal_menu['name']}")
    
    # Notification aux clients (optionnel)
    if config.get("menu_updater.notify_on_update", True):
        await notify_menu_update(orchestrator, seasonal_menu)


async def synchronize_with_recipe_module():
    """
    Synchronise les menus avec le module de recettes et ML.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("menu_example", "INFO")
    
    # Obtention de l'intégrateur
    integrator = get_integrator(config)
    
    # Synchronisation avec le module de recettes
    logger.info("Démarrage de la synchronisation avec le module de recettes...")
    
    # Appel à la méthode de synchronisation de l'intégrateur
    await integrator.sync_recipes_and_menu()
    
    logger.info("Synchronisation avec le module de recettes terminée")
    
    # Récupération de l'état de synchronisation
    orchestrator = get_orchestrator(config)
    sync_status = await orchestrator.get_sync_status()
    
    logger.info(f"Dernière mise à jour du menu: {sync_status['last_menu_update']}")


async def update_daily_specials():
    """
    Met à jour les plats du jour sur les plateformes de communication.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("menu_example", "INFO")
    
    # Utilisation directe du gestionnaire de menus
    menu_updater = MenuUpdater(config)
    
    # Définition des plats du jour
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    daily_specials = {
        "date": today,
        "items": [
            {
                "id": "special_001",
                "type": "entrée",
                "name": "Velouté de petits pois",
                "description": "Velouté de petits pois, chips de lard et menthe fraîche",
                "price": 7.90,
                "allergens": ["lait"],
                "vegetarian": False,
                "image_url": "https://example.com/images/veloute_pois.jpg"
            },
            {
                "id": "special_002",
                "type": "plat",
                "name": "Parmentier de canard",
                "description": "Parmentier de canard confit aux herbes, salade verte aux noisettes",
                "price": 16.50,
                "allergens": ["lait", "fruits à coque"],
                "vegetarian": False,
                "image_url": "https://example.com/images/parmentier.jpg"
            },
            {
                "id": "special_003",
                "type": "dessert",
                "name": "Crumble aux pommes",
                "description": "Crumble aux pommes et aux épices, glace vanille",
                "price": 6.90,
                "allergens": ["gluten", "lait", "œufs"],
                "vegetarian": True,
                "image_url": "https://example.com/images/crumble.jpg"
            }
        ],
        "menu_complet": {
            "name": "Menu du Jour",
            "description": "Entrée + Plat + Dessert du jour",
            "price": 24.90,
            "available": ["midi"],
            "days": ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
        }
    }
    
    # Mise à jour des plats du jour sur les différentes plateformes
    await menu_updater.update_daily_specials_async(daily_specials)
    
    logger.info(f"Plats du jour mis à jour pour le {today}")
    
    # Publication sur les réseaux sociaux
    await menu_updater.publish_daily_specials_to_social_media_async(daily_specials)
    
    logger.info("Plats du jour publiés sur les réseaux sociaux")


async def create_specialized_menus():
    """
    Crée et met à jour des menus spécialisés (végétarien, sans allergènes, etc.).
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("menu_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Création du menu végétarien à partir du menu standard
    # (Dans une implémentation réelle, cela serait fait à partir du menu existant)
    regular_menu = await load_current_menu()
    if not regular_menu:
        logger.error("Impossible de charger le menu standard")
        return
    
    # Filtrer pour ne garder que les plats végétariens
    vegetarian_menu = filter_vegetarian_items(regular_menu)
    
    # Ajouter des métadonnées spécifiques
    vegetarian_menu["id"] = "menu_vegetarien_2025"
    vegetarian_menu["name"] = "Menu Végétarien"
    vegetarian_menu["description"] = "Notre sélection de plats végétariens, élaborés avec des produits frais et locaux"
    vegetarian_menu["type"] = "specialized"
    
    # Mise à jour du menu végétarien
    await orchestrator.update_menu(
        menu_data=vegetarian_menu,
        platforms=["website", "social_media"]
    )
    
    logger.info(f"Menu spécialisé mis à jour: {vegetarian_menu['name']}")
    
    # Création d'autres menus spécialisés
    allergen_free_menu = create_allergen_free_menu(regular_menu)
    kids_menu = create_kids_menu()
    
    # Mise à jour des menus spécialisés
    await orchestrator.update_menu(
        menu_data=allergen_free_menu,
        platforms=["website"]
    )
    
    await orchestrator.update_menu(
        menu_data=kids_menu,
        platforms=["website"]
    )
    
    logger.info("Tous les menus spécialisés ont été mis à jour")


async def notify_menu_update(orchestrator, menu_data):
    """
    Envoie des notifications aux clients concernant la mise à jour du menu.
    
    Args:
        orchestrator: Orchestrateur de communication
        menu_data: Données du menu mis à jour
    """
    logger = logging.getLogger("menu_example")
    
    # Dans une implémentation réelle, récupération des clients abonnés depuis le CRM
    # Ici, nous utilisons des données factices
    subscribed_clients = [
        {"email": "client1@example.com", "first_name": "Jean"},
        {"email": "client2@example.com", "first_name": "Marie"},
        {"email": "client3@example.com", "first_name": "Pierre"}
    ]
    
    # Extraction des emails
    emails = [client["email"] for client in subscribed_clients]
    
    # Préparation des données pour l'email
    notification_data = {
        "restaurant_name": "Le Vieux Moulin",
        "menu_name": menu_data["name"],
        "menu_start_date": menu_data["start_date"],
        "menu_end_date": menu_data.get("end_date", ""),
        "menu_highlights": [
            item["name"] for category in menu_data["categories"] 
            for item in category["items"][:1]  # Prendre le premier élément de chaque catégorie
        ],
        "website_link": "https://levieuxmoulin.fr/menu",
        "reservation_link": "https://levieuxmoulin.fr/reservations"
    }
    
    # Envoi de la notification
    await orchestrator.send_notification(
        template="menu_update",
        recipients=emails,
        data=notification_data,
        channels=["email"]
    )
    
    logger.info(f"Notification de mise à jour du menu envoyée à {len(emails)} clients")


async def load_current_menu():
    """
    Charge le menu actuel.
    
    Returns:
        Données du menu actuel
    """
    # Dans une implémentation réelle, cela viendrait d'une base de données ou d'une API
    # Ici, nous simulons le chargement à partir d'un fichier
    try:
        # Simuler un chargement asynchrone
        await asyncio.sleep(0.2)
        
        # Retourner un menu factice
        return {
            "id": "menu_printemps_2025",
            "name": "Menu de Printemps 2025",
            "start_date": "2025-03-21",
            "end_date": "2025-06-20",
            "type": "seasonal",
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {
                            "id": "item_101",
                            "name": "Asperges blanches",
                            "description": "Asperges blanches, vinaigrette aux agrumes et copeaux de parmesan",
                            "price": 11.50,
                            "allergens": ["lait"],
                            "vegetarian": True,
                            "image_url": "https://example.com/images/asperges.jpg"
                        },
                        {
                            "id": "item_102",
                            "name": "Terrine de canard",
                            "description": "Terrine de canard aux pistaches, chutney de figues",
                            "price": 9.90,
                            "allergens": ["fruits à coque"],
                            "vegetarian": False,
                            "image_url": "https://example.com/images/terrine.jpg"
                        }
                    ]
                },
                {
                    "name": "Plats",
                    "items": [
                        {
                            "id": "item_103",
                            "name": "Navarin d'agneau",
                            "description": "Navarin d'agneau aux petits légumes printaniers",
                            "price": 22.50,
                            "allergens": ["céleri"],
                            "vegetarian": False,
                            "image_url": "https://example.com/images/navarin.jpg"
                        },
                        {
                            "id": "item_104",
                            "name": "Risotto aux petits pois",
                            "description": "Risotto aux petits pois et à la menthe, tuile de parmesan",
                            "price": 17.50,
                            "allergens": ["lait"],
                            "vegetarian": True,
                            "image_url": "https://example.com/images/risotto_pois.jpg"
                        }
                    ]
                }
            ]
        }
    except Exception as e:
        logging.getLogger("menu_example").error(f"Erreur lors du chargement du menu: {e}")
        return None


def filter_vegetarian_items(menu):
    """
    Filtre un menu pour ne garder que les plats végétariens.
    
    Args:
        menu: Menu complet
        
    Returns:
        Menu filtré avec uniquement les plats végétariens
    """
    vegetarian_menu = menu.copy()
    
    # Créer de nouvelles catégories avec uniquement les plats végétariens
    vegetarian_menu["categories"] = []
    
    for category in menu["categories"]:
        veg_items = [item for item in category["items"] if item.get("vegetarian", False)]
        
        if veg_items:
            vegetarian_menu["categories"].append({
                "name": category["name"],
                "items": veg_items
            })
    
    return vegetarian_menu


def create_allergen_free_menu(menu):
    """
    Crée un menu sans allergènes majeurs.
    
    Args:
        menu: Menu standard
        
    Returns:
        Menu sans allergènes
    """
    # Définir les allergènes majeurs à exclure
    major_allergens = ["gluten", "lait", "œufs", "fruits à coque", "arachides", "soja", "poisson", "crustacés"]
    
    allergen_free_menu = menu.copy()
    allergen_free_menu["id"] = "menu_sans_allergenes_2025"
    allergen_free_menu["name"] = "Menu Sans Allergènes Majeurs"
    allergen_free_menu["description"] = "Notre sélection de plats sans allergènes majeurs"
    allergen_free_menu["type"] = "specialized"
    
    # Filtrer les catégories
    allergen_free_menu["categories"] = []
    
    for category in menu["categories"]:
        safe_items = []
        
        for item in category["items"]:
            item_allergens = item.get("allergens", [])
            if not any(allergen in major_allergens for allergen in item_allergens):
                safe_items.append(item)
        
        if safe_items:
            allergen_free_menu["categories"].append({
                "name": category["name"],
                "items": safe_items
            })
    
    return allergen_free_menu


def create_kids_menu():
    """
    Crée un menu enfant.
    
    Returns:
        Menu enfant
    """
    return {
        "id": "menu_enfant_2025",
        "name": "Menu Enfant",
        "description": "Menu spécial pour les enfants jusqu'à 12 ans",
        "type": "specialized",
        "price": 12.90,
        "categories": [
            {
                "name": "Plats",
                "items": [
                    {
                        "id": "kid_001",
                        "name": "Filet de poulet pané",
                        "description": "Filet de poulet pané, purée maison ou frites",
                        "allergens": ["gluten"],
                        "image_url": "https://example.com/images/poulet_enfant.jpg"
                    },
                    {
                        "id": "kid_002",
                        "name": "Mini burger",
                        "description": "Mini burger de bœuf, fromage et tomate, servi avec des frites",
                        "allergens": ["gluten", "lait"],
                        "image_url": "https://example.com/images/burger_enfant.jpg"
                    }
                ]
            },
            {
                "name": "Desserts",
                "items": [
                    {
                        "id": "kid_003",
                        "name": "Moelleux au chocolat",
                        "description": "Moelleux au chocolat et sa boule de glace vanille",
                        "allergens": ["gluten", "lait", "œufs"],
                        "image_url": "https://example.com/images/moelleux_enfant.jpg"
                    },
                    {
                        "id": "kid_004",
                        "name": "Coupe de glace",
                        "description": "Deux boules de glace au choix (vanille, chocolat, fraise) et sirop",
                        "allergens": ["lait"],
                        "image_url": "https://example.com/images/glace_enfant.jpg"
                    }
                ]
            }
        ],
        "includes": ["Sirop à l'eau", "Surprise"]
    }


async def main():
    """
    Fonction principale exécutant les exemples.
    """
    # Configuration du logger
    logger = setup_logger("menu_example", "INFO")
    logger.info("Démarrage des exemples d'intégration des menus...")
    
    # Exécution des exemples
    await update_seasonal_menu()
    await synchronize_with_recipe_module()
    await update_daily_specials()
    await create_specialized_menus()
    
    logger.info("Exemples terminés avec succès")


if __name__ == "__main__":
    # Exécution du code asynchrone
    asyncio.run(main())
