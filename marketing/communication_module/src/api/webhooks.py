#!/usr/bin/env python3
"""
Gestionnaire de webhooks pour le module de communication.

Ce module implémente les points de terminaison pour recevoir les événements
des autres modules du système via des webhooks.
"""

import logging
import json
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify
from flask_restful import Resource

from src.common import Config
from src.integration import get_integrator


# Blueprint Flask pour les webhooks
webhook_bp = Blueprint('webhooks', __name__)

# Logger
logger = logging.getLogger("communication.webhooks")


class WebhookReceiver(Resource):
    """
    Point de terminaison API pour la réception des webhooks.
    """
    
    def __init__(self, config: Config):
        """
        Initialise le gestionnaire de webhooks.
        
        Args:
            config: Configuration du module
        """
        self.config = config
        self.integrator = get_integrator(config)
        self.webhook_secret = config.get("integration.webhook_secret", "")
    
    async def post(self):
        """
        Reçoit et traite un événement webhook.
        
        Returns:
            Réponse HTTP
        """
        try:
            # Vérifier l'authentification du webhook
            if not self._verify_webhook_auth():
                logger.warning("Tentative de webhook non authentifiée rejetée")
                return {"error": "Non autorisé"}, 401
            
            # Analyser le payload
            data = request.json
            if not data:
                return {"error": "Payload JSON manquant"}, 400
            
            # Extraire les informations essentielles
            event = data.get("event")
            source = data.get("source")
            payload = data.get("payload")
            
            if not event or not source or not payload:
                return {"error": "Payload webhook incomplet (event, source et payload requis)"}, 400
            
            # Enregistrer l'événement
            logger.info(f"Webhook reçu: {source}.{event}")
            
            # Transmettre l'événement à l'intégrateur système
            await self.integrator.handle_webhook(event, source, payload)
            
            return {"status": "success", "message": f"Événement {source}.{event} traité avec succès"}, 200
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook: {e}")
            return {"error": "Erreur interne lors du traitement du webhook"}, 500
    
    def _verify_webhook_auth(self) -> bool:
        """
        Vérifie l'authentification du webhook.
        
        Returns:
            True si l'authentification est valide
        """
        # Vérifier le secret dans l'en-tête
        auth_header = request.headers.get("X-Webhook-Secret")
        
        # Si aucun secret n'est configuré, accepter tous les webhooks (non recommandé en production)
        if not self.webhook_secret:
            logger.warning("Aucun secret webhook configuré, tous les webhooks sont acceptés")
            return True
        
        # Vérifier que le secret correspond
        return auth_header == self.webhook_secret


def validate_webhook_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Valide la structure d'un payload webhook.
    
    Args:
        payload: Payload à valider
        
    Returns:
        Message d'erreur si le payload est invalide, sinon None
    """
    required_fields = ["event", "source", "payload", "timestamp"]
    
    # Vérifier les champs requis
    for field in required_fields:
        if field not in payload:
            return f"Champ requis manquant: {field}"
    
    # Vérifier que l'événement est une chaîne
    if not isinstance(payload["event"], str):
        return "Le champ 'event' doit être une chaîne"
    
    # Vérifier que la source est une chaîne
    if not isinstance(payload["source"], str):
        return "Le champ 'source' doit être une chaîne"
    
    # Vérifier que le payload est un dictionnaire
    if not isinstance(payload["payload"], dict):
        return "Le champ 'payload' doit être un objet JSON"
    
    # Vérifier que le timestamp est une chaîne
    if not isinstance(payload["timestamp"], str):
        return "Le champ 'timestamp' doit être une chaîne"
    
    return None


@webhook_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    Point de terminaison Flask pour la réception des webhooks.
    
    Returns:
        Réponse HTTP
    """
    try:
        # Extraire le payload
        payload = request.json
        if not payload:
            logger.warning("Webhook reçu sans payload JSON")
            return jsonify({"error": "Payload JSON requis"}), 400
        
        # Valider le payload
        error = validate_webhook_payload(payload)
        if error:
            logger.warning(f"Validation du webhook échouée: {error}")
            return jsonify({"error": error}), 400
        
        # Récupérer l'intégrateur
        config = Config.get_instance()
        integrator = get_integrator(config)
        
        # Traiter l'événement
        event = payload["event"]
        source = payload["source"]
        event_payload = payload["payload"]
        
        # Appel asynchrone via asyncio
        import asyncio
        asyncio.run(integrator.handle_webhook(event, source, event_payload))
        
        logger.info(f"Webhook traité avec succès: {source}.{event}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}")
        return jsonify({"error": "Erreur interne lors du traitement du webhook"}), 500


def register_webhook_routes(api, config: Config):
    """
    Enregistre les routes webhook dans l'API.
    
    Args:
        api: API Flask-RESTful
        config: Configuration du module
    """
    # Ajouter la ressource RESTful
    api.add_resource(
        WebhookReceiver,
        '/api/communication/webhook',
        resource_class_kwargs={'config': config}
    )
    
    # Enregistrer le blueprint Flask
    from src.api.server import app
    app.register_blueprint(webhook_bp, url_prefix='/api/communication')
