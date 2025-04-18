#!/usr/bin/env python3
"""
Point d'entrée principal du module de comptabilité avancé du Vieux Moulin.

Ce module démarre le serveur API, initialise les connexions aux sources de données
et programme les tâches récurrentes (génération de rapports, synchronisation, etc.).
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI

from src.api.routes import setup_routes
from src.config import settings
from src.core.scheduler import setup_scheduler
from src.db.database import init_db
from src.utils.logging import configure_logging

# Configuration du logger
logger = configure_logging()

# Création de l'application FastAPI
app = FastAPI(
    title="Module Comptabilité - Le Vieux Moulin",
    description="API de gestion comptable avancée pour le restaurant Le Vieux Moulin",
    version="1.0.0"
)

# Gestion des événements de l'application
@app.on_event("startup")
async def startup_event():
    """Exécuté au démarrage de l'application."""
    logger.info("Démarrage du module de comptabilité")
    
    # Initialisation de la base de données
    await init_db()
    
    # Configuration des routes API
    setup_routes(app)
    
    # Configuration du planificateur de tâches
    setup_scheduler()
    
    logger.info("Module de comptabilité démarré avec succès")

@app.on_event("shutdown")
async def shutdown_event():
    """Exécuté à l'arrêt de l'application."""
    logger.info("Arrêt du module de comptabilité")

# Point d'entrée pour l'exécution directe
def main():
    """Point d'entrée principal pour l'exécution du module."""
    try:
        uvicorn.run(
            "src.main:app",
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.debug,
            log_level=settings.server.log_level.lower(),
            access_log=True,
            ssl_keyfile=settings.security.ssl_key if settings.security.ssl_enabled else None,
            ssl_certfile=settings.security.ssl_cert if settings.security.ssl_enabled else None
        )
    except Exception as e:
        logger.error(f"Erreur au démarrage du serveur: {e}")
        sys.exit(1)

# Gestion des signaux pour un arrêt propre
def handle_exit(signum, frame):
    """Gestionnaire de signal pour un arrêt propre de l'application."""
    logger.info(f"Signal reçu: {signum}, arrêt en cours...")
    sys.exit(0)

if __name__ == "__main__":
    # Configuration des gestionnaires de signaux
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Démarrage de l'application
    main()
