#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestionnaires de commandes pour la catégorie 'equipment'.

Ce module contient les fonctions qui exécutent les commandes identifiées
liées aux équipements dans le système Le Vieux Moulin.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import logging
from typing import Dict, Any

from config import Config
from api_client import APIClient, APIError


logger = logging.getLogger("voice_command.command_handlers.equipment")


def handle_equipment_status(params: Dict[str, Any], config: Config) -> Dict:
    """Vérifie l'état d'un équipement.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'equipment'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec les informations sur l'équipement.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande equipment.status avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'equipment' not in params:
        raise ValueError("Paramètre 'equipment' manquant")
    
    equipment = params['equipment']
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Récupérer l'état de l'équipement via l'API
        equipment_info = api_client.get_equipment_status(equipment)
        
        # Formater le résultat
        result = {
            "name": equipment_info.get("name", equipment),
            "status": equipment_info.get("status", "unknown"),
            "temperature": equipment_info.get("temperature"),
            "last_maintenance": equipment_info.get("last_maintenance"),
            "next_maintenance": equipment_info.get("next_maintenance"),
            "details": equipment_info.get("details", {})
        }
        
        logger.debug(f"Résultat de la vérification d'équipement: {result}")
        return result
        
    except APIError as e:
        logger.error(f"Erreur API lors de la vérification d'équipement: {str(e)}")
        raise Exception(f"Erreur lors de la vérification de l'équipement: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de la vérification d'équipement: {str(e)}")
        raise


def handle_equipment_maintenance(params: Dict[str, Any], config: Config) -> Dict:
    """Signale un besoin de maintenance pour un équipement.

    Args:
        params (Dict): Paramètres de la commande, doit contenir 'equipment'.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec confirmation de la demande de maintenance.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande equipment.maintenance avec paramètres: {params}")
    
    # Vérifier les paramètres requis
    if 'equipment' not in params:
        raise ValueError("Paramètre 'equipment' manquant")
    
    equipment = params['equipment']
    priority = params.get('priority', 'high')
    
    # Créer un client API
    api_client = APIClient(config)
    
    try:
        # Envoyer la demande de maintenance via l'API
        # Note: Cette API est fictive et devrait être implémentée dans le système réel
        maintenance_data = {
            "type": "maintenance_request",
            "equipment": equipment,
            "priority": priority,
            "source": "voice_command",
            "device_id": config.get("device_id", "unknown")
        }
        
        # Simuler une réponse API réussie
        # Dans un système réel, cela serait une vraie requête API
        # response = api_client.request_maintenance(maintenance_data)
        
        result = {
            "status": "success",
            "message": f"Demande de maintenance enregistrée pour {equipment}",
            "request_id": "MNT-" + str(hash(equipment) % 10000),  # Simulation d'un ID de demande
            "priority": priority,
            "estimated_response": "24h"  # Simulation d'un délai de réponse
        }
        
        logger.debug(f"Résultat de la demande de maintenance: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la demande de maintenance: {str(e)}")
        raise


def register_handlers() -> Dict:
    """Enregistre les gestionnaires de commandes pour la catégorie 'equipment'.

    Returns:
        Dict: Dictionnaire associant les noms de commandes aux fonctions de gestion.
    """
    return {
        "equipment.status": handle_equipment_status,
        "equipment.maintenance": handle_equipment_maintenance
    }