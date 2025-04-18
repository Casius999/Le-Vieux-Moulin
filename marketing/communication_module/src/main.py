#!/usr/bin/env python3
"""
Point d'entrée principal du module de communication et d'automatisation marketing.

Ce script initialise et démarre tous les composants du module,
y compris le serveur API, les workers pour les tâches asynchrones,
et les planificateurs pour les actions programmées.
"""

import os
import sys
import argparse
import logging
import asyncio
from contextlib import contextmanager

# Ajout du répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config, setup_logger
from src.api import create_app
from src.social_media import SocialMediaManager
from src.notification import NotificationManager
from src.campaign_manager import CampaignManager
from src.menu_updater import MenuUpdater
from src.orchestrator import get_orchestrator
from src.integration import get_integrator


@contextmanager
def start_component(name, component):
    """Démarre un composant avec gestion d'erreur et nettoyage."""
    logger = logging.getLogger(f"communication.{name}")
    logger.info(f"Démarrage du composant {name}...")
    try:
        yield component
        logger.info(f"Composant {name} démarré avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du composant {name}: {e}")
        raise
    finally:
        logger.info(f"Arrêt du composant {name}...")


def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description="Module de communication et d'automatisation marketing")
    parser.add_argument('--config', type=str, default='../config/settings.json',
                      help='Chemin vers le fichier de configuration')
    parser.add_argument('--log-level', type=str, default='INFO',
                      help='Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--dev', action='store_true',
                      help='Mode développement avec auto-reload')
    return parser.parse_args()


async def async_main(args, config, logger):
    """Point d'entrée principal asynchrone de l'application"""
    try:
        # Initialisation des gestionnaires individuels
        social_media_manager = SocialMediaManager(config)
        notification_manager = NotificationManager(config)
        campaign_manager = CampaignManager(config)
        menu_updater = MenuUpdater(config)
        
        # Initialisation de l'orchestrateur
        orchestrator = get_orchestrator(config)
        await orchestrator.start()
        logger.info("Orchestrateur de communication démarré")
        
        # Initialisation de l'intégrateur système
        integrator = get_integrator(config)
        await integrator.start()
        logger.info("Intégrateur système démarré")
        
        # Création et configuration de l'application API
        app = create_app(config)
        
        # Démarrage du serveur API
        host = config.get('api.host', '0.0.0.0')
        port = config.get('api.port', 5000)
        
        if args.dev:
            logger.info("Mode développement activé avec auto-reload")
            # En mode dev, utiliser Flask avec l'option debug
            app.run(host=host, port=port, debug=True)
        else:
            # En production, utiliser gunicorn ou uvicorn
            import gunicorn.app.base
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                    
                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)
                            
                def load(self):
                    return self.application
            
            options = {
                'bind': f'{host}:{port}',
                'workers': config.get('api.workers', 4),
                'accesslog': '-',
                'errorlog': '-',
                'loglevel': args.log_level.lower(),
                'timeout': 120
            }
            
            StandaloneApplication(app, options).run()
            
    except Exception as e:
        logger.critical(f"Erreur critique lors du démarrage: {e}")
        sys.exit(1)


def main():
    """Point d'entrée principal de l'application"""
    # Parsing des arguments
    args = parse_arguments()
    
    # Configuration du logger
    logger = setup_logger("communication", args.log_level)
    logger.info("Démarrage du module de communication et d'automatisation marketing...")
    
    # Chargement de la configuration
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), args.config))
    config = Config(config_path)
    logger.info(f"Configuration chargée depuis {config_path}")
    
    # Démarrage de l'application asynchrone
    asyncio.run(async_main(args, config, logger))


if __name__ == "__main__":
    main()
