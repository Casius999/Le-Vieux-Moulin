#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interface utilisateur pour le module de commande vocale.

Ce module gère l'interface utilisateur de la tablette murale, permettant au personnel
de visualiser et d'interagir avec le système de commande vocale.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import os
import time
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Union

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_bootstrap import Bootstrap5

from config import Config


class UIManager:
    """Gestionnaire d'interface utilisateur pour la tablette murale."""

    def __init__(self, config: Config):
        """Initialise l'interface utilisateur.

        Args:
            config (Config): Configuration du module.
        """
        self.logger = logging.getLogger("voice_command.ui_interface")
        self.config = config
        
        # Paramètres UI
        self.theme = config.get("ui.theme", "kitchen")
        self.font_size = config.get("ui.font_size", "large")
        self.high_contrast = config.get("ui.high_contrast", False)
        self.display_timeout = config.get("ui.display_timeout", 60)
        self.history_size = config.get("ui.history_size", 20)
        
        # Paramètres feedback
        self.audio_feedback = config.get("ui.feedback.audio", True)
        self.visual_feedback = config.get("ui.feedback.visual", True)
        self.haptic_feedback = config.get("ui.feedback.haptic", False)
        
        # Application Flask et SocketIO
        self.app = Flask(__name__, 
                         template_folder=os.path.join(os.path.dirname(__file__), "templates"),
                         static_folder=os.path.join(os.path.dirname(__file__), "static"))
        self.app.config["SECRET_KEY"] = config.get("ui.secret_key", "dev_key_change_in_production")
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        Bootstrap5(self.app)
        
        # État de l'interface
        self.is_running = False
        self.command_history = []
        self.last_activity = time.time()
        self.screen_timeout_thread = None
        self.screen_active = True
        
        # Callbacks
        self.on_listen = None
        self.on_stop = None
        self.on_exit = None
        self.on_command_confirm = None
        
        # Initialisation des routes et événements
        self._setup_routes()
        self._setup_socketio_events()
        
        self.logger.info("Interface utilisateur initialisée")

    def start(self) -> None:
        """Prépare l'interface utilisateur pour démarrage."""
        self.logger.info("Préparation de l'interface utilisateur...")
        self.is_running = True
        self.screen_active = True
        self.last_activity = time.time()
        
        # Démarrer la surveillance du timeout d'affichage
        if self.display_timeout > 0:
            self.screen_timeout_thread = threading.Thread(target=self._monitor_screen_timeout)
            self.screen_timeout_thread.daemon = True
            self.screen_timeout_thread.start()

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
        """Démarre le serveur Flask pour l'interface.

        Args:
            host (str, optional): Hôte d'écoute. Défaut à "0.0.0.0" (toutes les interfaces).
            port (int, optional): Port d'écoute. Défaut à 5000.
            debug (bool, optional): Mode debug Flask. Défaut à False.
        """
        self.logger.info(f"Démarrage du serveur UI sur {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

    def stop(self) -> None:
        """Arrête l'interface utilisateur."""
        self.logger.info("Arrêt de l'interface utilisateur")
        self.is_running = False
        
        # Arrêt propre du serveur Flask dans un environnement de production
        if hasattr(self, "_server") and self._server:
            self._server.shutdown()

    def set_on_listen_callback(self, callback: Callable[[], None]) -> None:
        """Définit le callback pour le bouton d'écoute.

        Args:
            callback: Fonction à appeler lors de l'activation de l'écoute.
        """
        self.on_listen = callback

    def set_on_stop_callback(self, callback: Callable[[], None]) -> None:
        """Définit le callback pour le bouton d'arrêt.

        Args:
            callback: Fonction à appeler lors de l'arrêt de l'écoute.
        """
        self.on_stop = callback

    def set_on_exit_callback(self, callback: Callable[[], None]) -> None:
        """Définit le callback pour le bouton de sortie.

        Args:
            callback: Fonction à appeler lors de la demande de sortie.
        """
        self.on_exit = callback

    def update_status(self, status: str) -> None:
        """Met à jour le statut affiché dans l'interface.

        Args:
            status (str): Message de statut à afficher.
        """
        self.logger.debug(f"Mise à jour du statut: {status}")
        self._wake_screen()  # Réveiller l'écran si nécessaire
        self.socketio.emit("status_update", {"status": status})

    def update_recognized_text(self, text: str, confidence: float) -> None:
        """Affiche le texte reconnu par la reconnaissance vocale.

        Args:
            text (str): Texte reconnu.
            confidence (float): Indice de confiance (0.0-1.0).
        """
        self.logger.debug(f"Affichage du texte reconnu: '{text}' (confiance: {confidence:.2f})")
        self._wake_screen()
        
        # Formater le niveau de confiance en pourcentage
        confidence_percent = int(confidence * 100)
        
        # Envoyer à l'interface
        self.socketio.emit("speech_recognized", {
            "text": text,
            "confidence": confidence_percent
        })
        
        # Retour audio si activé
        if self.audio_feedback:
            self.socketio.emit("play_sound", {"sound": "speech_recognized"})

    def update_command(self, command: str, params: Dict) -> None:
        """Affiche une commande identifiée.

        Args:
            command (str): Nom de la commande identifiée.
            params (Dict): Paramètres de la commande.
        """
        self.logger.debug(f"Affichage de la commande: {command}")
        self._wake_screen()
        
        # Formater le nom de la commande pour l'affichage
        command_parts = command.split('.')
        display_category = command_parts[0] if len(command_parts) > 0 else ""
        display_name = command_parts[1] if len(command_parts) > 1 else command_parts[0]
        
        # Envoyer à l'interface
        self.socketio.emit("command_identified", {
            "command": command,
            "display_category": display_category,
            "display_name": display_name,
            "params": params
        })
        
        # Retour audio si activé
        if self.audio_feedback:
            self.socketio.emit("play_sound", {"sound": "command_identified"})

    def update_command_result(self, command: str, params: Dict, result: Dict) -> None:
        """Affiche le résultat d'une commande.

        Args:
            command (str): Nom de la commande exécutée.
            params (Dict): Paramètres utilisés.
            result (Dict): Résultat de l'exécution.
        """
        self.logger.debug(f"Affichage du résultat de la commande: {command}")
        self._wake_screen()
        
        # Ajouter à l'historique des commandes
        command_entry = {
            "timestamp": time.time(),
            "command": command,
            "params": params,
            "result": result,
            "status": "success"
        }
        self._add_to_history(command_entry)
        
        # Envoyer à l'interface
        self.socketio.emit("command_result", {
            "command": command,
            "params": params,
            "result": result
        })
        
        # Retour audio si activé
        if self.audio_feedback:
            self.socketio.emit("play_sound", {"sound": "command_success"})

    def show_error(self, title: str, message: str) -> None:
        """Affiche un message d'erreur.

        Args:
            title (str): Titre de l'erreur.
            message (str): Description détaillée.
        """
        self.logger.debug(f"Affichage de l'erreur: {title} - {message}")
        self._wake_screen()
        
        # Envoyer à l'interface
        self.socketio.emit("show_error", {
            "title": title,
            "message": message
        })
        
        # Retour audio si activé
        if self.audio_feedback:
            self.socketio.emit("play_sound", {"sound": "error"})

    def request_confirmation(self, command: str, params: Dict, callback: Callable[[str, Dict, bool], None]) -> None:
        """Demande une confirmation à l'utilisateur pour exécuter une commande.

        Args:
            command (str): Nom de la commande à confirmer.
            params (Dict): Paramètres de la commande.
            callback: Fonction appelée avec (command, params, confirmed).
        """
        self.logger.debug(f"Demande de confirmation pour la commande: {command}")
        self._wake_screen()
        
        # Enregistrer le callback
        self.on_command_confirm = callback
        
        # Formater le nom de la commande pour l'affichage
        command_parts = command.split('.')
        display_category = command_parts[0] if len(command_parts) > 0 else ""
        display_name = command_parts[1] if len(command_parts) > 1 else command_parts[0]
        
        # Envoyer à l'interface
        self.socketio.emit("request_confirmation", {
            "command": command,
            "display_category": display_category,
            "display_name": display_name,
            "params": params
        })
        
        # Retour audio si activé
        if self.audio_feedback:
            self.socketio.emit("play_sound", {"sound": "confirmation_needed"})

    def _setup_routes(self) -> None:
        """Configure les routes de l'application Flask."""
        @self.app.route('/')
        def index():
            """Page principale de l'interface."""
            self._wake_screen()
            return render_template(
                'index.html',
                theme=self.theme,
                font_size=self.font_size,
                high_contrast=self.high_contrast,
                location=self.config.get("location", "cuisine"),
                device_id=self.config.get("device_id", "tablette_unknown")
            )
        
        @self.app.route('/history')
        def history():
            """Page d'historique des commandes."""
            self._wake_screen()
            return render_template(
                'history.html',
                theme=self.theme,
                font_size=self.font_size,
                high_contrast=self.high_contrast,
                history=self.command_history
            )
        
        @self.app.route('/settings')
        def settings():
            """Page de paramètres."""
            self._wake_screen()
            return render_template(
                'settings.html',
                theme=self.theme,
                font_size=self.font_size,
                high_contrast=self.high_contrast,
                config=self.config
            )
        
        @self.app.route('/api/history')
        def api_history():
            """API pour récupérer l'historique des commandes."""
            return jsonify(self.command_history)
        
        @self.app.route('/api/settings', methods=['GET', 'POST'])
        def api_settings():
            """API pour récupérer ou modifier les paramètres."""
            if request.method == 'POST':
                data = request.json
                if 'theme' in data:
                    self.theme = data['theme']
                if 'font_size' in data:
                    self.font_size = data['font_size']
                if 'high_contrast' in data:
                    self.high_contrast = data['high_contrast']
                if 'audio_feedback' in data:
                    self.audio_feedback = data['audio_feedback']
                if 'visual_feedback' in data:
                    self.visual_feedback = data['visual_feedback']
                if 'haptic_feedback' in data:
                    self.haptic_feedback = data['haptic_feedback']
                
                # Mise à jour de la configuration
                self.config.set("ui.theme", self.theme)
                self.config.set("ui.font_size", self.font_size)
                self.config.set("ui.high_contrast", self.high_contrast)
                self.config.set("ui.feedback.audio", self.audio_feedback)
                self.config.set("ui.feedback.visual", self.visual_feedback)
                self.config.set("ui.feedback.haptic", self.haptic_feedback)
                
                # Enregistrer les modifications
                try:
                    self.config.save()
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)})
                
                return jsonify({"success": True})
            else:
                return jsonify({
                    "theme": self.theme,
                    "font_size": self.font_size,
                    "high_contrast": self.high_contrast,
                    "audio_feedback": self.audio_feedback,
                    "visual_feedback": self.visual_feedback,
                    "haptic_feedback": self.haptic_feedback
                })

    def _setup_socketio_events(self) -> None:
        """Configure les événements SocketIO."""
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.debug("Nouvelle connexion WebSocket établie")
            self._wake_screen()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.debug("Connexion WebSocket fermée")
        
        @self.socketio.on('start_listening')
        def handle_start_listening():
            self.logger.debug("Commande de démarrage d'écoute reçue")
            self._wake_screen()
            if self.on_listen:
                self.on_listen()
        
        @self.socketio.on('stop_listening')
        def handle_stop_listening():
            self.logger.debug("Commande d'arrêt d'écoute reçue")
            self._wake_screen()
            if self.on_stop:
                self.on_stop()
        
        @self.socketio.on('exit_app')
        def handle_exit():
            self.logger.debug("Commande de sortie reçue")
            if self.on_exit:
                self.on_exit()
        
        @self.socketio.on('confirmation_response')
        def handle_confirmation(data):
            self.logger.debug(f"Réponse de confirmation reçue: {data}")
            self._wake_screen()
            if self.on_command_confirm and 'command' in data and 'params' in data and 'confirmed' in data:
                self.on_command_confirm(data['command'], data['params'], data['confirmed'])
        
        @self.socketio.on('user_activity')
        def handle_user_activity():
            self._wake_screen()

    def _add_to_history(self, entry: Dict) -> None:
        """Ajoute une entrée à l'historique des commandes.

        Args:
            entry (Dict): Détails de la commande à ajouter.
        """
        # Limiter la taille de l'historique
        if len(self.command_history) >= self.history_size:
            self.command_history.pop(0)  # Supprimer l'entrée la plus ancienne
            
        self.command_history.append(entry)
        self.socketio.emit("history_updated", {"history": self.command_history})

    def _wake_screen(self) -> None:
        """Réveille l'écran et réinitialise le minuteur de mise en veille."""
        self.last_activity = time.time()
        
        if not self.screen_active and self.display_timeout > 0:
            self.logger.debug("Réveil de l'écran")
            self.screen_active = True
            self.socketio.emit("screen_wake")

    def _monitor_screen_timeout(self) -> None:
        """Surveille l'inactivité et met l'écran en veille si nécessaire."""
        self.logger.debug("Démarrage de la surveillance de mise en veille de l'écran")
        
        while self.is_running and self.display_timeout > 0:
            time.sleep(1.0)  # Vérifier toutes les secondes
            
            inactivity_time = time.time() - self.last_activity
            
            # Mettre en veille après la période d'inactivité
            if self.screen_active and inactivity_time >= self.display_timeout:
                self.logger.debug(f"Mise en veille de l'écran après {inactivity_time:.1f}s d'inactivité")
                self.screen_active = False
                self.socketio.emit("screen_sleep")
