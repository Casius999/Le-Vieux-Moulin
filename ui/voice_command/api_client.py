#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client API pour communication avec le serveur central.

Ce module gère la communication avec le serveur central du système via REST API
et WebSockets pour les mises à jour en temps réel.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import json
import time
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Union

import requests
import websocket

from config import Config


class APIError(Exception):
    """Exception levée pour les erreurs API."""
    pass


class APIClient:
    """Client pour communication avec le serveur central."""

    def __init__(self, config: Config):
        """Initialise le client API.

        Args:
            config (Config): Configuration du module.
        """
        self.logger = logging.getLogger("voice_command.api_client")
        self.config = config
        
        # Paramètres de connexion
        self.host = config.get("server.host")
        self.api_port = config.get("server.api_port", 8080)
        self.ws_port = config.get("server.websocket_port", 8081)
        self.use_ssl = config.get("server.use_ssl", True)
        self.api_key = config.get("server.api_key", "")
        self.device_id = config.get("device_id", "tablette_unknown")
        
        # État de la connexion
        self.is_connected = False
        self.ws_client = None
        self.ws_thread = None
        self.ws_reconnect_timeout = 1.0
        self.max_reconnect_timeout = 30.0
        
        # Cache pour le mode hors-ligne
        self.offline_queue = []
        self.offline_mode = config.get("network.offline_mode.enabled", True)
        self.max_queue_size = config.get("network.offline_mode.cache_size", 100)
        
        # Callbacks
        self.on_message = None
        self.on_connection_change = None

    def connect(self) -> bool:
        """Connecte le client au serveur.

        Returns:
            bool: True si la connexion est établie, False sinon.
        """
        self.logger.info(f"Tentative de connexion au serveur {self.host}:{self.api_port}")
        
        # Tester la connexion API REST
        if not self._test_api_connection():
            self.logger.warning("Impossible de se connecter au serveur API REST")
            if self.offline_mode:
                self.logger.info("Mode hors-ligne activé")
                return True
            return False
            
        # Initialiser la connexion WebSocket
        self._connect_websocket()
        
        # Synchroniser les données en cache (si mode hors-ligne)
        if self.offline_mode and self.offline_queue:
            self._sync_offline_data()
            
        return self.is_connected

    def disconnect(self) -> None:
        """Déconnecte le client du serveur."""
        self.logger.info("Déconnexion du serveur")
        
        # Fermer la connexion WebSocket
        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None
            
        # Attendre la fin du thread WebSocket si nécessaire
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2.0)
            
        self.is_connected = False
        self._notify_connection_change()

    def get_stock_level(self, ingredient: str) -> Dict:
        """Récupère le niveau de stock d'un ingrédient.

        Args:
            ingredient (str): Nom de l'ingrédient.

        Returns:
            Dict: Informations sur le niveau de stock.

        Raises:
            APIError: Si une erreur survient.
        """
        endpoint = f"api/stock/{ingredient}"
        return self._request("GET", endpoint)

    def get_equipment_status(self, equipment: str) -> Dict:
        """Récupère l'état d'un équipement.

        Args:
            equipment (str): Nom de l'équipement.

        Returns:
            Dict: Informations sur l'état de l'équipement.

        Raises:
            APIError: Si une erreur survient.
        """
        endpoint = f"api/equipment/{equipment}"
        return self._request("GET", endpoint)

    def get_recipe(self, dish: str) -> Dict:
        """Récupère la recette d'un plat.

        Args:
            dish (str): Nom du plat.

        Returns:
            Dict: Détails de la recette.

        Raises:
            APIError: Si une erreur survient.
        """
        endpoint = f"api/recipes/{dish}"
        return self._request("GET", endpoint)

    def request_order(self, ingredient: str, quantity: Optional[float] = None) -> Dict:
        """Demande une commande d'ingrédient auprès des fournisseurs.

        Args:
            ingredient (str): Nom de l'ingrédient à commander.
            quantity (float, optional): Quantité à commander.
                Si None, la quantité sera déterminée par le système.

        Returns:
            Dict: Détails de la commande créée.

        Raises:
            APIError: Si une erreur survient.
        """
        endpoint = "api/orders"
        data = {
            "ingredient": ingredient,
            "source": "voice_command",
            "device_id": self.device_id
        }
        if quantity is not None:
            data["quantity"] = float(quantity)
            
        return self._request("POST", endpoint, data)

    def set_on_message(self, callback: Callable[[Dict], None]) -> None:
        """Définit le callback pour les messages WebSocket.

        Args:
            callback: Fonction prenant en paramètre le message reçu.
        """
        self.on_message = callback

    def set_on_connection_change(self, callback: Callable[[bool], None]) -> None:
        """Définit le callback pour les changements d'état de connexion.

        Args:
            callback: Fonction prenant en paramètre l'état de connexion (bool).
        """
        self.on_connection_change = callback

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Exécute une requête API REST.

        Args:
            method (str): Méthode HTTP (GET, POST, PUT, DELETE).
            endpoint (str): Point d'accès API (sans le préfixe http/host).
            data (Dict, optional): Données à envoyer en JSON.

        Returns:
            Dict: Réponse du serveur.

        Raises:
            APIError: Si une erreur survient.
        """
        protocol = "https" if self.use_ssl else "http"
        url = f"{protocol}://{self.host}:{self.api_port}/{endpoint}"
        headers = self._get_headers()
        
        # Vérifier si en mode hors-ligne
        if not self.is_connected and self.offline_mode and method != "GET":
            self.logger.debug(f"Mode hors-ligne: mise en file d'attente de la requête {method} {endpoint}")
            self._queue_offline_request(method, endpoint, data)
            return {"status": "queued", "message": "Request queued for offline processing"}
        
        try:
            self.logger.debug(f"Exécution de la requête {method} {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise APIError(f"Méthode non supportée: {method}")
                
            # Vérifier la réponse
            if response.status_code >= 200 and response.status_code < 300:
                return response.json()
            else:
                error_msg = f"Erreur API: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise APIError(error_msg)
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur de connexion: {str(e)}")
            
            # Passer en mode hors-ligne si nécessaire
            if self.is_connected:
                self.is_connected = False
                self._notify_connection_change()
                
            # Mettre en file d'attente si ce n'est pas une requête GET
            if self.offline_mode and method != "GET":
                self._queue_offline_request(method, endpoint, data)
                
            raise APIError(f"Erreur de connexion: {str(e)}")

    def _test_api_connection(self) -> bool:
        """Teste la connexion au serveur API.

        Returns:
            bool: True si la connexion est établie, False sinon.
        """
        protocol = "https" if self.use_ssl else "http"
        url = f"{protocol}://{self.host}:{self.api_port}/api/status"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                self.is_connected = True
                self._notify_connection_change()
                return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur lors du test de connexion: {str(e)}")
            
        # Échec de connexion
        self.is_connected = False
        self._notify_connection_change()
        return False

    def _get_headers(self) -> Dict[str, str]:
        """Génère les en-têtes pour les requêtes API.

        Returns:
            Dict: En-têtes HTTP.
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"VoiceCommand-{self.device_id}",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers

    def _connect_websocket(self) -> None:
        """Initialise la connexion WebSocket au serveur."""
        protocol = "wss" if self.use_ssl else "ws"
        ws_url = f"{protocol}://{self.host}:{self.ws_port}/ws?device={self.device_id}"
        
        # Fermer toute connexion existante
        if self.ws_client:
            self.ws_client.close()
            
        # Créer la nouvelle connexion
        self.logger.debug(f"Initialisation de la connexion WebSocket: {ws_url}")
        self.ws_client = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close,
            header=self._get_ws_headers()
        )
        
        # Démarrer la connexion dans un thread séparé
        self.ws_thread = threading.Thread(target=self.ws_client.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def _get_ws_headers(self) -> List[str]:
        """Génère les en-têtes pour la connexion WebSocket.

        Returns:
            List[str]: En-têtes au format 'Clé: Valeur'.
        """
        headers = []
        
        if self.api_key:
            headers.append(f"Authorization: Bearer {self.api_key}")
            
        return headers

    def _on_ws_open(self, ws: websocket.WebSocketApp) -> None:
        """Gestionnaire d'événement d'ouverture de WebSocket.

        Args:
            ws: Instance WebSocketApp.
        """
        self.logger.info("Connexion WebSocket établie")
        self.is_connected = True
        self.ws_reconnect_timeout = 1.0  # Réinitialiser le timeout de reconnexion
        self._notify_connection_change()
        
        # Envoyer un message d'identification
        self._send_ws_message({
            "type": "connect",
            "device_id": self.device_id,
            "module": "voice_command"
        })

    def _on_ws_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Gestionnaire d'événement de message WebSocket.

        Args:
            ws: Instance WebSocketApp.
            message: Message reçu.
        """
        try:
            data = json.loads(message)
            self.logger.debug(f"Message WebSocket reçu: {data.get('type')}")
            
            # Notifier via le callback s'il est défini
            if self.on_message:
                self.on_message(data)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur de décodage JSON du message: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message WebSocket: {str(e)}")

    def _on_ws_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Gestionnaire d'événement d'erreur WebSocket.

        Args:
            ws: Instance WebSocketApp.
            error: Erreur survenue.
        """
        self.logger.error(f"Erreur WebSocket: {str(error)}")

    def _on_ws_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """Gestionnaire d'événement de fermeture WebSocket.

        Args:
            ws: Instance WebSocketApp.
            close_status_code: Code de statut de fermeture.
            close_msg: Message de fermeture.
        """
        self.logger.info(f"Connexion WebSocket fermée: {close_status_code} - {close_msg}")
        
        # Marquer comme déconnecté si la fermeture n'est pas volontaire
        if self.is_connected:
            self.is_connected = False
            self._notify_connection_change()
            
            # Tenter une reconnexion après un délai
            reconnect_seconds = min(self.ws_reconnect_timeout, self.max_reconnect_timeout)
            self.logger.info(f"Tentative de reconnexion dans {reconnect_seconds} secondes...")
            
            threading.Timer(reconnect_seconds, self._reconnect_websocket).start()
            
            # Augmenter le délai pour la prochaine tentative (backoff exponentiel)
            self.ws_reconnect_timeout = min(self.ws_reconnect_timeout * 2, self.max_reconnect_timeout)

    def _reconnect_websocket(self) -> None:
        """Tente de rétablir la connexion WebSocket."""
        if not self.is_connected:
            self.logger.info("Tentative de reconnexion WebSocket...")
            self._connect_websocket()

    def _send_ws_message(self, data: Dict) -> bool:
        """Envoie un message via WebSocket.

        Args:
            data: Données à envoyer (sera sérialisé en JSON).

        Returns:
            bool: True si le message a été envoyé, False sinon.
        """
        if not self.is_connected or not self.ws_client:
            self.logger.debug("Impossible d'envoyer le message: non connecté")
            return False
            
        try:
            message = json.dumps(data)
            self.ws_client.send(message)
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message WebSocket: {str(e)}")
            return False

    def _queue_offline_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> None:
        """Ajoute une requête à la file d'attente pour traitement hors-ligne.

        Args:
            method: Méthode HTTP.
            endpoint: Point d'accès API.
            data: Données de la requête.
        """
        # Limiter la taille de la file d'attente
        if len(self.offline_queue) >= self.max_queue_size:
            self.logger.warning(f"File d'attente hors-ligne pleine ({self.max_queue_size} requêtes), suppression de la plus ancienne")
            self.offline_queue.pop(0)  # Supprimer la requête la plus ancienne
            
        # Ajouter la nouvelle requête
        self.offline_queue.append({
            "method": method,
            "endpoint": endpoint,
            "data": data,
            "timestamp": time.time()
        })
        
        self.logger.debug(f"Requête ajoutée à la file d'attente hors-ligne ({len(self.offline_queue)} en attente)")

    def _sync_offline_data(self) -> None:
        """Synchronise les données mises en file d'attente en mode hors-ligne."""
        if not self.offline_queue:
            return
            
        self.logger.info(f"Synchronisation des données hors-ligne ({len(self.offline_queue)} requêtes)")
        
        # Copier la file d'attente avant traitement (pour éviter les problèmes de concurrence)
        queue_copy = list(self.offline_queue)
        self.offline_queue = []
        
        # Traiter les requêtes
        for request in queue_copy:
            try:
                self.logger.debug(f"Traitement de la requête hors-ligne: {request['method']} {request['endpoint']}")
                self._request(request["method"], request["endpoint"], request["data"])
            except APIError as e:
                self.logger.error(f"Erreur lors de la synchronisation: {str(e)}")
                # Remettre en file d'attente en cas d'erreur
                self._queue_offline_request(request["method"], request["endpoint"], request["data"])

    def _notify_connection_change(self) -> None:
        """Notifie du changement d'état de connexion via le callback."""
        if self.on_connection_change:
            self.on_connection_change(self.is_connected)
