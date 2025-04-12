"""
Serveur API pour le module de communication

Ce module fournit le serveur API REST qui expose les fonctionnalités
du module de communication et d'automatisation marketing.
"""

import os
import logging
from typing import Dict, Any, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Api
from werkzeug.exceptions import HTTPException

from ..common import Config


def create_app(config: Optional[Config] = None) -> Flask:
    """
    Crée et configure l'application Flask.
    
    Args:
        config: Configuration du serveur (si None, charge depuis l'environnement)
        
    Returns:
        Application Flask configurée
    """
    app = Flask(__name__)
    
    # Configuration du logger
    logger = logging.getLogger("communication.api")
    
    # Charger la configuration
    if config is None:
        # Charger depuis les variables d'environnement ou fichier par défaut
        config_path = os.environ.get('COMMUNICATION_CONFIG', '../config/settings.json')
        config = Config(config_path)
    
    # Stocker la configuration dans l'application
    app.config['COMMUNICATION_CONFIG'] = config
    
    # Configurer CORS si activé
    if config.get('api.cors.enabled', False):
        origins = config.get('api.cors.allowed_origins', ["*"])
        methods = config.get('api.cors.allowed_methods', ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        headers = config.get('api.cors.allowed_headers', ["Content-Type", "Authorization", "X-API-Key"])
        
        CORS(app, resources={r"/api/*": {"origins": origins, "methods": methods, "allow_headers": headers}})
        logger.info(f"CORS activé avec origins={origins}")
    
    # Création de l'API
    api = Api(app, prefix="/api")
    
    # Enregistrer les routes
    from .routes import register_routes
    register_routes(api, config)
    
    # Configuration des gestionnaires d'erreur
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Gestionnaire pour les erreurs HTTP."""
        response = jsonify({
            "status": "error",
            "message": error.description,
            "code": error.code
        })
        response.status_code = error.code
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Gestionnaire pour les erreurs non-HTTP."""
        logger.exception("Erreur non gérée: %s", str(error))
        
        response = jsonify({
            "status": "error",
            "message": "Une erreur interne est survenue",
            "code": 500
        })
        response.status_code = 500
        return response
    
    # Route de statut
    @app.route('/api/status')
    def status():
        """Point de terminaison de vérification d'état."""
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "api": "communication_module"
        })
    
    # Route de documentation Swagger (si activée)
    if config.get('api.swagger.enabled', True):
        @app.route('/api/docs')
        def api_docs():
            """Point de terminaison pour la documentation de l'API."""
            # Dans une implémentation réelle, cela servirait la documentation Swagger
            return jsonify({
                "message": "Documentation API",
                "swagger_url": "/api/swagger.json"
            })
    
    logger.info("Serveur API initialisé avec succès")
    return app
