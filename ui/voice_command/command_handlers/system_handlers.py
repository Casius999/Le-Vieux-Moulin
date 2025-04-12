#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestionnaires de commandes pour la catégorie 'system'.

Ce module contient les fonctions qui exécutent les commandes système
comme l'aide, l'annulation ou la réinitialisation.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import logging
import os
import yaml
from typing import Dict, Any, List

from config import Config


logger = logging.getLogger("voice_command.command_handlers.system")


def handle_help(params: Dict[str, Any], config: Config) -> Dict:
    """Affiche l'aide sur les commandes disponibles.

    Args:
        params (Dict): Paramètres de la commande. Le paramètre 'topic' peut
            préciser un domaine spécifique d'aide.
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande avec les informations d'aide.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info(f"Exécution de la commande system.help avec paramètres: {params}")
    
    topic = params.get('topic', 'general')
    
    try:
        # Charger les commandes disponibles depuis le fichier de configuration
        commands_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "commands.yaml")
        if not os.path.exists(commands_file):
            commands_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "commands.example.yaml")
        
        with open(commands_file, 'r', encoding='utf-8') as file:
            commands_data = yaml.safe_load(file) or {}
        
        # Récupérer les commandes par catégorie
        available_commands: Dict[str, List[Dict]] = {}
        
        # Si un topic spécifique est demandé
        if topic != 'general' and topic in commands_data:
            category_data = commands_data[topic]
            available_commands[topic] = []
            
            for cmd_name, cmd_data in category_data.items():
                if isinstance(cmd_data, dict) and "patterns" in cmd_data:
                    command_info = {
                        "name": cmd_name,
                        "examples": cmd_data["patterns"][:2] if len(cmd_data["patterns"]) > 2 else cmd_data["patterns"],
                        "description": cmd_data.get("description", f"Commande {topic}.{cmd_name}")
                    }
                    available_commands[topic].append(command_info)
        else:
            # Toutes les catégories
            for category, category_data in commands_data.items():
                if not isinstance(category_data, dict):
                    continue
                    
                available_commands[category] = []
                
                for cmd_name, cmd_data in category_data.items():
                    if isinstance(cmd_data, dict) and "patterns" in cmd_data:
                        command_info = {
                            "name": cmd_name,
                            "examples": cmd_data["patterns"][:1],  # Une seule exemple pour ne pas surcharger
                            "description": cmd_data.get("description", f"Commande {category}.{cmd_name}")
                        }
                        available_commands[category].append(command_info)
        
        # Formater le résultat
        result = {
            "topic": topic,
            "available_commands": available_commands,
            "message": "Voici les commandes disponibles"
        }
        
        if topic != 'general' and topic not in commands_data:
            result["message"] = f"Aucune commande disponible pour la catégorie '{topic}'"
        
        logger.debug(f"Résultat de la demande d'aide: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'aide: {str(e)}")
        raise


def handle_cancel(params: Dict[str, Any], config: Config) -> Dict:
    """Annule l'opération en cours ou réinitialise l'état du système.

    Args:
        params (Dict): Paramètres de la commande (non utilisés).
        config (Config): Configuration du module.

    Returns:
        Dict: Résultat de la commande d'annulation.

    Raises:
        Exception: Si une erreur survient lors de l'exécution.
    """
    logger.info("Exécution de la commande system.cancel")
    
    # Dans un système réel, cela pourrait annuler des opérations en cours
    # ou réinitialiser certains états
    
    result = {
        "status": "success",
        "message": "Opération annulée"
    }
    
    logger.debug(f"Résultat de l'annulation: {result}")
    return result


def register_handlers() -> Dict:
    """Enregistre les gestionnaires de commandes pour la catégorie 'system'.

    Returns:
        Dict: Dictionnaire associant les noms de commandes aux fonctions de gestion.
    """
    return {
        "system.help": handle_help,
        "system.cancel": handle_cancel
    }