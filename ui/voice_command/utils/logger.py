#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration de la journalisation pour le module de commande vocale.

Ce module fournit une configuration uniforme des journaux pour tous les
composants du module de commande vocale.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


def setup_logger(name: str, level: int = logging.INFO, log_file: Optional[str] = None,
                 rotation: str = "daily", max_files: int = 7, format_str: Optional[str] = None) -> logging.Logger:
    """Configure et retourne un logger avec les paramètres spécifiés.

    Args:
        name (str): Nom du logger.
        level (int, optional): Niveau de journalisation (INFO, DEBUG, etc.).
        log_file (str, optional): Chemin du fichier journal. Si None, utilise
            uniquement la sortie console.
        rotation (str, optional): Type de rotation (none, size, daily, weekly).
        max_files (int, optional): Nombre maximal de fichiers journaux à conserver.
        format_str (str, optional): Format personnalisé pour les messages.

    Returns:
        logging.Logger: Le logger configuré.
    """
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Empêcher la propagation aux loggers parents
    
    # Nettoyer les handlers existants
    for handler in logger.handlers[:]:  # Copie de la liste pour éviter les problèmes de modification
        logger.removeHandler(handler)
    
    # Format par défaut
    if format_str is None:
        format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(format_str)
    
    # Ajouter un handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Ajouter un handler fichier si spécifié
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configurer le handler selon le type de rotation
        if rotation == "none":
            file_handler = logging.FileHandler(log_file)
        elif rotation == "size":
            # Rotation basée sur la taille (10 Mo par défaut)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=max_files
            )
        elif rotation in ["daily", "weekly"]:
            # Rotation basée sur le temps
            when = "D" if rotation == "daily" else "W0"  # W0 = lundi
            file_handler = TimedRotatingFileHandler(
                log_file, when=when, interval=1, backupCount=max_files
            )
        else:
            # Par défaut, rotation quotidienne
            file_handler = TimedRotatingFileHandler(
                log_file, when="D", interval=1, backupCount=max_files
            )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger