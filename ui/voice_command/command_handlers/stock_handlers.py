#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestionnaires de commandes pour la catégorie 'stock'.

Ce module contient les fonctions qui exécutent les commandes identifiées
liées à la gestion des stocks dans le système Le Vieux Moulin.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import logging
from typing import Dict, Any

from config import Config
from api_client import APIClient, APIError


logger = logging.getLogger("voice_command.command_handlers.stock")


def handle_check_stock(params: Dict[str, Any], config: Config) -> Dict:
    """Vérifie le niveau de stock d'un ingrédient.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'ingredient'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec les informations de stock.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande stock.check avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'ingredient' not in params:
        raise ValueError("Paramètre 'ingredient' manquant")
    
    ingredient = params['ingredient']
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Récupérer le niveau de stock via l'API
        stock_info = api_client.get_stock_level(ingredient)
        
        # Formater le résultat
        result = {
            "ingredient": ingredient,
            "current": stock_info.get("level", 0),
            "max": stock_info.get("max_level", 100),
            "unit": stock_info.get("unit", "kg"),
            "status": stock_info.get("status", "unknown"),
            "last_updated": stock_info.get("last_updated")
        }
        
        logger.debug(f"Résultat de la vérification de stock: {result}")
        return result
        
    except APIError as e:
        logger.error(f"Erreur API lors de la vérification de stock: {str(e)}")
        raise Exception(f"Erreur lors de la vérification du stock: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de stock: {str(e)}")
        raise


def handle_alert_stock(params: Dict[str, Any], config: Config) -> Dict:
    """Signale un niveau critique de stock non détecté par les capteurs.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'ingredient'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec confirmation de l'alerte.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande stock.alert avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'ingredient' not in params:
        raise ValueError("Paramètre 'ingredient' manquant")
    
    ingredient = params['ingredient']
    priority = params.get('priority', 'normal')
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Envoyer l'alerte de stock via l'API
        # Note: Cette API est fictive et devrait être implémentée dans le système réel
        alert_data = {
            "type": "stock_alert",
            "ingredient": ingredient,
            "priority": priority,
            "source": "voice_command",
            "device_id": config.get("device_id", "unknown")
        }
        
        # Simuler une réponse API réussie
        # Dans un système réel, cela serait une vraie requête API
        # response = api_client.send_alert(alert_data)
        
        result = {
            "status": "success",
            "message": f"Alerte enregistrée pour {ingredient}",
            "alert_id": "ALT-" + str(hash(ingredient) % 10000),  # Simulation d'un ID d'alerte
            "priority": priority
        }
        
        logger.debug(f"Résultat de l'alerte de stock: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de l'alerte de stock: {str(e)}")
        raise


def handle_order_stock(params: Dict[str, Any], config: Config) -> Dict:
    """Demande une commande d'ingrédient auprès des fournisseurs.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'ingredient'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec les détails de la commande créée.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande stock.order avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'ingredient' not in params:
        raise ValueError("Paramètre 'ingredient' manquant")
    
    ingredient = params['ingredient']
    quantity = params.get('quantity')  # Peut être None, le système déterminera la quantité
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Demander une commande via l'API
        order_result = api_client.request_order(ingredient, quantity)
        
        # Formater le résultat
        result = {
            "order_id": order_result.get("order_id", "UNKNOWN"),
            "ingredient": ingredient,
            "quantity": order_result.get("quantity", quantity),
            "unit": order_result.get("unit", "kg"),
            "estimated_delivery": order_result.get("estimated_delivery"),
            "status": order_result.get("status", "created")
        }
        
        logger.debug(f"Résultat de la commande de stock: {result}")
        return result
        
    except APIError as e:
        logger.error(f"Erreur API lors de la commande de stock: {str(e)}")
        raise Exception(f"Erreur lors de la commande d'ingrédient: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de la commande de stock: {str(e)}")
        raise


def register_handlers() -> Dict:
    """Enregistre les gestionnaires de commandes pour la catégorie 'stock'.

    Returns:
        Dict: Dictionnaire associant les noms de commandes aux fonctions de gestion.
    """
    return {
        "stock.check": handle_check_stock,
        "stock.alert": handle_alert_stock,
        "stock.order": handle_order_stock
    }