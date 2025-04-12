#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestionnaires de commandes pour la catégorie 'recipe'.

Ce module contient les fonctions qui exécutent les commandes identifiées
liées aux recettes dans le système Le Vieux Moulin.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import logging
from typing import Dict, Any

from config import Config
from api_client import APIClient, APIError


logger = logging.getLogger("voice_command.command_handlers.recipe")


def handle_show_recipe(params: Dict[str, Any], config: Config) -> Dict:
    """Affiche une recette complète.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'dish'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec les détails de la recette.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande recipe.show avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'dish' not in params:
        raise ValueError("Paramètre 'dish' manquant")
    
    dish = params['dish']
    detail_level = params.get('detail_level', 'full')
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Récupérer la recette via l'API
        recipe_info = api_client.get_recipe(dish)
        
        # Formater le résultat
        result = {
            "name": recipe_info.get("name", dish),
            "ingredients": recipe_info.get("ingredients", []),
            "instructions": recipe_info.get("instructions", []),
            "prep_time": recipe_info.get("prep_time"),
            "cook_time": recipe_info.get("cook_time"),
            "difficulty": recipe_info.get("difficulty"),
            "detail_level": detail_level
        }
        
        logger.debug(f"Résultat de l'affichage de recette: {result}")
        return result
        
    except APIError as e:
        logger.error(f"Erreur API lors de la récupération de recette: {str(e)}")
        raise Exception(f"Erreur lors de la récupération de la recette: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de recette: {str(e)}")
        raise


def handle_recipe_ingredients(params: Dict[str, Any], config: Config) -> Dict:
    """Affiche uniquement les ingrédients d'une recette.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'dish'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec la liste des ingrédients.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande recipe.ingredients avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'dish' not in params:
        raise ValueError("Paramètre 'dish' manquant")
    
    dish = params['dish']
    with_quantities = params.get('with_quantities', True)
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Récupérer la recette via l'API
        recipe_info = api_client.get_recipe(dish)
        
        # Extraire uniquement les ingrédients
        ingredients = recipe_info.get("ingredients", [])
        
        # Si les quantités ne sont pas demandées, les supprimer
        if not with_quantities:
            ingredients = [{'name': ing['name']} for ing in ingredients]
        
        # Formater le résultat
        result = {
            "name": recipe_info.get("name", dish),
            "ingredients": ingredients,
            "with_quantities": with_quantities
        }
        
        logger.debug(f"Résultat de la liste d'ingrédients: {result}")
        return result
        
    except APIError as e:
        logger.error(f"Erreur API lors de la récupération des ingrédients: {str(e)}")
        raise Exception(f"Erreur lors de la récupération des ingrédients: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de la liste d'ingrédients: {str(e)}")
        raise


def register_handlers() -> Dict:
    """Enregistre les gestionnaires de commandes pour la catégorie 'recipe'.

    Returns:
        Dict: Dictionnaire associant les noms de commandes aux fonctions de gestion.
    """
    return {
        "recipe.show": handle_show_recipe,
        "recipe.ingredients": handle_recipe_ingredients
    }