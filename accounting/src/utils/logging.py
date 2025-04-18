"""
Configuration du système de journalisation pour le module de comptabilité.

Ce module configure structlog pour fournir des logs structurés et lisibles.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import structlog
from structlog.processors import (JSONRenderer, StackInfoRenderer, TimeStamper,
                                 format_exc_info)

from src.config import settings


def configure_logging(
    level: Optional[str] = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_file: Optional[str] = None,
) -> structlog.BoundLogger:
    """
    Configure le système de journalisation.
    
    Args:
        level (str, optional): Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                              Par défaut, utilise le niveau défini dans les paramètres.
        log_to_console (bool, optional): Si True, affiche les logs dans la console. Par défaut à True.
        log_to_file (bool, optional): Si True, écrit les logs dans un fichier. Par défaut à True.
        log_file (str, optional): Chemin du fichier de log. Si None, utilise le chemin par défaut.
    
    Returns:
        structlog.BoundLogger: Logger configuré
    """
    # Déterminer le niveau de log
    level = level or getattr(settings.server, "log_level", "INFO")
    level = level.upper()
    
    # Créer le répertoire des logs si nécessaire
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurer le chemin du fichier de log
    if log_file is None:
        log_file = os.path.join(log_dir, "accounting.log")
    
    # Configurer les handlers
    handlers = []
    
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level))
        handlers.append(console_handler)
    
    if log_to_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        handlers.append(file_handler)
    
    # Configuration de base du logging
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(message)s",
        handlers=handlers
    )
    
    # Liste des processeurs pour structlog
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Processeurs supplémentaires pour la console (formatage plus lisible)
    if log_to_console:
        console_processors = list(shared_processors)
        console_processors.append(structlog.dev.ConsoleRenderer())
    
    # Processeurs pour le fichier (format JSON)
    file_processors = list(shared_processors)
    file_processors.append(structlog.processors.JSONRenderer())
    
    # Configuration de structlog
    structlog.configure(
        processors=console_processors if log_to_console else file_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Créer et retourner le logger
    logger = structlog.get_logger()
    
    logger.info(
        "Système de journalisation initialisé",
        level=level,
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        log_file=log_file
    )
    
    return logger


def log_request(request, response=None, error=None) -> Dict:
    """
    Formate un log de requête HTTP.
    
    Args:
        request: Requête HTTP
        response: Réponse HTTP (optionnel)
        error: Exception en cas d'erreur (optionnel)
    
    Returns:
        Dict: Informations structurées sur la requête/réponse
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": getattr(request, "method", "UNKNOWN"),
        "url": str(getattr(request, "url", "UNKNOWN")),
        "client_ip": getattr(request, "client.host", "UNKNOWN"),
        "user_agent": request.headers.get("user-agent", "UNKNOWN") if hasattr(request, "headers") else "UNKNOWN",
    }
    
    # Ajouter les informations de la réponse si disponible
    if response:
        log_data.update({
            "status_code": getattr(response, "status_code", 0),
            "processing_time_ms": getattr(response, "headers", {}).get("X-Process-Time", 0),
        })
    
    # Ajouter les informations d'erreur si disponible
    if error:
        log_data.update({
            "error": str(error),
            "error_type": error.__class__.__name__,
        })
    
    return log_data


def audit_log(user, action, resource_type, resource_id=None, details=None) -> Dict:
    """
    Crée une entrée de journal d'audit pour une action importante.
    
    Args:
        user: Utilisateur qui a effectué l'action
        action: Action effectuée (CREATE, UPDATE, DELETE, etc.)
        resource_type: Type de ressource affectée (REPORT, TRANSACTION, etc.)
        resource_id: ID de la ressource (optionnel)
        details: Détails supplémentaires (optionnel)
    
    Returns:
        Dict: Informations structurées sur l'action
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "resource_type": resource_type,
        "user_id": getattr(user, "id", "UNKNOWN"),
        "username": getattr(user, "username", "UNKNOWN"),
        "role": getattr(user, "role", "UNKNOWN"),
    }
    
    if resource_id:
        log_data["resource_id"] = resource_id
    
    if details:
        log_data["details"] = details
    
    # Journaliser l'action avec le logger d'audit
    audit_logger = structlog.get_logger("accounting.audit")
    audit_logger.info("audit_event", **log_data)
    
    return log_data
