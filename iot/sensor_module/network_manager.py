#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des connexions réseau pour les capteurs IoT du Vieux Moulin.

Ce module gère les connexions WiFi et Bluetooth pour transmettre les données 
des capteurs vers le serveur central. Il inclut des fonctionnalités de mise 
en cache local en cas de perte de connexion et de reconnexion automatique.

Classes:
    NetworkManager: Gère les connexions réseau et la transmission des données
    MQTTClient: Client MQTT pour la communication avec le serveur central
    DataCache: Système de mise en cache local pour les données

Exemples d'utilisation:
    >>> from network_manager import NetworkManager
    >>> network = NetworkManager(
    ...     wifi_ssid="LVM_NETWORK",
    ...     wifi_password="password123",
    ...     server_host="192.168.1.100",
    ...     device_id="friteuse_01"
    ... )
    >>> network.connect()
    >>> network.send_data({"temperature": 175.5, "oil_level": 8.2})
"""

import os
import time
import json
import logging
import threading
import queue
import tempfile
import socket
import ssl
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from pathlib import Path
import uuid

# Pour MQTT
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# Pour WiFi sur Raspberry Pi
try:
    import subprocess
    WIFI_CONTROL_AVAILABLE = True
except ImportError:
    WIFI_CONTROL_AVAILABLE = False

# Pour Bluetooth
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class DataCache:
    """
    Système de mise en cache local pour les données des capteurs.
    
    Cette classe permet de stocker temporairement les données en cas de 
    perte de connexion et les envoie au serveur lors de la reconnexion.
    """
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        max_cache_size_mb: float = 100.0,  # 100 MB par défaut
        max_entries: int = 10000
    ) -> None:
        """
        Initialise le système de cache.
        
        Args:
            cache_dir: Répertoire pour stocker les fichiers de cache
                      (si None, utilise un répertoire temporaire)
            max_cache_size_mb: Taille maximale du cache en Mo
            max_entries: Nombre maximal d'entrées dans le cache
        """
        # Définir le répertoire de cache
        if cache_dir is None:
            self.cache_dir = Path(tempfile.gettempdir()) / "lvm_sensor_cache"
        else:
            self.cache_dir = Path(cache_dir)
            
        # Créer le répertoire s'il n'existe pas
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convertir en octets
        self.max_entries = max_entries
        
        # Mémoire tampon pour les transactions en cours
        self.buffer: Dict[str, Any] = {}
        self.cache_lock = threading.Lock()
        
        logger.info(f"Cache initialisé dans {self.cache_dir} (max: {max_cache_size_mb}MB, {max_entries} entrées)")
        
        # Charger les anciennes entrées de cache si elles existent
        self._load_existing_cache()

    def _load_existing_cache(self) -> None:
        """
        Charge les entrées de cache existantes depuis le disque.
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            logger.info(f"{len(cache_files)} fichiers de cache trouvés")
            
            # Si trop d'entrées, nettoyer les plus anciennes
            if len(cache_files) > self.max_entries:
                # Trier par date de modification
                cache_files.sort(key=lambda f: f.stat().st_mtime)
                # Supprimer les entrées excédentaires (les plus anciennes)
                for file in cache_files[:(len(cache_files) - self.max_entries)]:
                    try:
                        file.unlink()
                        logger.debug(f"Entrée de cache ancienne supprimée: {file.name}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer l'entrée de cache: {e}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache existant: {e}")

    def add(self, data: Dict[str, Any], topic: str = "") -> str:
        """
        Ajoute des données au cache.
        
        Args:
            data: Données à mettre en cache
            topic: Sujet MQTT associé aux données (optionnel)
            
        Returns:
            str: Identifiant unique de l'entrée de cache
        """
        with self.cache_lock:
            # Générer un identifiant unique
            entry_id = str(uuid.uuid4())
            timestamp = time.time()
            
            # Créer l'entrée de cache avec métadonnées
            cache_entry = {
                "id": entry_id,
                "timestamp": timestamp,
                "topic": topic,
                "data": data
            }
            
            # Sauvegarder dans un fichier
            cache_file = self.cache_dir / f"{entry_id}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump(cache_entry, f)
                logger.debug(f"Données mises en cache: {cache_file}")
            except Exception as e:
                logger.error(f"Erreur lors de la mise en cache: {e}")
                return ""
            
            # Vérifier et maintenir la taille du cache
            self._manage_cache_size()
            
            return entry_id

    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une entrée du cache par son identifiant.
        
        Args:
            entry_id: Identifiant de l'entrée à récupérer
            
        Returns:
            Dict ou None si l'entrée n'existe pas
        """
        with self.cache_lock:
            cache_file = self.cache_dir / f"{entry_id}.json"
            
            if not cache_file.exists():
                return None
                
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du cache {entry_id}: {e}")
                return None

    def remove(self, entry_id: str) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            entry_id: Identifiant de l'entrée à supprimer
            
        Returns:
            bool: True si supprimé avec succès, False sinon
        """
        with self.cache_lock:
            cache_file = self.cache_dir / f"{entry_id}.json"
            
            if not cache_file.exists():
                return False
                
            try:
                os.remove(cache_file)
                logger.debug(f"Entrée de cache supprimée: {entry_id}")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du cache {entry_id}: {e}")
                return False

    def get_all_entries(self, sorted_by_time: bool = True) -> List[Dict[str, Any]]:
        """
        Récupère toutes les entrées du cache.
        
        Args:
            sorted_by_time: Si True, trie les entrées par timestamp
            
        Returns:
            Liste des entrées de cache
        """
        with self.cache_lock:
            entries = []
            
            try:
                cache_files = list(self.cache_dir.glob("*.json"))
                
                for cache_file in cache_files:
                    try:
                        with open(cache_file, 'r') as f:
                            entry = json.load(f)
                            entries.append(entry)
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture du cache {cache_file}: {e}")
                
                if sorted_by_time:
                    entries.sort(key=lambda e: e.get("timestamp", 0))
                    
                return entries
                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des entrées du cache: {e}")
                return []

    def clear(self) -> None:
        """
        Supprime toutes les entrées du cache.
        """
        with self.cache_lock:
            try:
                cache_files = list(self.cache_dir.glob("*.json"))
                for cache_file in cache_files:
                    try:
                        os.remove(cache_file)
                    except Exception as e:
                        logger.error(f"Impossible de supprimer {cache_file}: {e}")
                        
                logger.info(f"{len(cache_files)} entrées de cache supprimées")
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage du cache: {e}")

    def _manage_cache_size(self) -> None:
        """
        Gère la taille du cache pour ne pas dépasser les limites.
        Supprime les entrées les plus anciennes si nécessaire.
        """
        try:
            # Vérifier le nombre d'entrées
            cache_files = list(self.cache_dir.glob("*.json"))
            
            if len(cache_files) > self.max_entries:
                # Trier par date de modification (plus ancien en premier)
                cache_files.sort(key=lambda f: f.stat().st_mtime)
                
                # Supprimer les entrées excédentaires
                for file in cache_files[:(len(cache_files) - self.max_entries)]:
                    try:
                        os.remove(file)
                        logger.debug(f"Entrée de cache supprimée pour maintenir la limite: {file.name}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer l'entrée de cache: {e}")
            
            # Vérifier la taille totale du cache
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            
            if total_size > self.max_cache_size:
                # Recalculer les fichiers après les suppressions précédentes
                cache_files = list(self.cache_dir.glob("*.json"))
                cache_files.sort(key=lambda f: f.stat().st_mtime)
                
                # Supprimer les fichiers jusqu'à ce que la taille soit acceptable
                current_size = total_size
                for file in cache_files:
                    if current_size <= self.max_cache_size:
                        break
                        
                    file_size = file.stat().st_size
                    try:
                        os.remove(file)
                        current_size -= file_size
                        logger.debug(f"Entrée de cache supprimée pour libérer de l'espace: {file.name}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer l'entrée de cache: {e}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la gestion de la taille du cache: {e}")


class MQTTClient:
    """
    Client MQTT pour la communication avec le serveur central.
    
    Cette classe gère la connexion MQTT, la publication et la souscription 
    aux sujets, ainsi que la gestion des messages.
    """
    
    def __init__(
        self,
        client_id: str,
        broker_host: str,
        broker_port: int = 1883,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        ca_cert: Optional[str] = None,
        keepalive: int = 60
    ) -> None:
        """
        Initialise le client MQTT.
        
        Args:
            client_id: Identifiant unique du client
            broker_host: Adresse du broker MQTT
            broker_port: Port du broker MQTT
            user: Nom d'utilisateur pour l'authentification (optionnel)
            password: Mot de passe pour l'authentification (optionnel)
            use_tls: Si True, utilise TLS pour la connexion
            ca_cert: Chemin vers le certificat CA (si use_tls=True)
            keepalive: Intervalle keepalive en secondes
        """
        if not MQTT_AVAILABLE:
            raise ImportError("Le module paho-mqtt n'est pas disponible")
            
        self.client_id = client_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.ca_cert = ca_cert
        self.keepalive = keepalive
        
        # État interne
        self.connected = False
        self.reconnect_count = 0
        self.last_publish_time = 0.0
        self.message_count = 0
        
        # Callbacks configurables
        self.on_message_callback: Optional[Callable] = None
        
        # File d'attente pour les messages en cas de déconnexion
        self.message_queue = queue.Queue()
        self.max_queue_size = 1000
        
        # Initialisation du client MQTT
        self._init_client()
        
        logger.info(f"Client MQTT initialisé avec ID={client_id}, broker={broker_host}:{broker_port}")

    def _init_client(self) -> None:
        """
        Initialise le client MQTT et configure les callbacks.
        """
        # Créer le client avec un ID unique
        self.client = mqtt.Client(client_id=self.client_id)
        
        # Configurer les callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        # Configurer l'authentification si nécessaire
        if self.user and self.password:
            self.client.username_pw_set(self.user, self.password)
            
        # Configurer TLS si nécessaire
        if self.use_tls:
            self.client.tls_set(
                ca_certs=self.ca_cert,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS
            )

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback appelé lors de la connexion au broker.
        
        Args:
            client: Instance du client
            userdata: Données utilisateur
            flags: Drapeaux de réponse
            rc: Code de retour (0 = succès)
        """
        if rc == 0:
            self.connected = True
            self.reconnect_count = 0
            logger.info(f"Connecté au broker MQTT: {self.broker_host}:{self.broker_port}")
            
            # Souscrire aux sujets de contrôle
            control_topic = f"control/{self.client_id}/#"
            self.client.subscribe(control_topic)
            logger.debug(f"Souscrit au sujet de contrôle: {control_topic}")
            
            # Envoyer les messages en attente
            self._process_message_queue()
        else:
            connection_results = {
                0: "Connexion réussie",
                1: "Mauvaise version du protocole",
                2: "Identifiant client invalide",
                3: "Serveur indisponible",
                4: "Mauvais nom d'utilisateur ou mot de passe",
                5: "Non autorisé"
            }
            error_message = connection_results.get(rc, f"Erreur inconnue: {rc}")
            logger.error(f"Échec de connexion MQTT: {error_message}")

    def _on_disconnect(self, client, userdata, rc):
        """
        Callback appelé lors de la déconnexion du broker.
        
        Args:
            client: Instance du client
            userdata: Données utilisateur
            rc: Code de retour (0 = déconnexion volontaire)
        """
        self.connected = False
        
        if rc == 0:
            logger.info("Déconnecté du broker MQTT (déconnexion volontaire)")
        else:
            logger.warning(f"Déconnecté du broker MQTT avec code: {rc}, tentative de reconnexion...")
            self.reconnect_count += 1

    def _on_message(self, client, userdata, msg):
        """
        Callback appelé lors de la réception d'un message.
        
        Args:
            client: Instance du client
            userdata: Données utilisateur
            msg: Message MQTT reçu
        """
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            logger.debug(f"Message reçu sur {topic}: {payload}")
            
            # Si un callback personnalisé est défini, l'appeler
            if self.on_message_callback:
                self.on_message_callback(topic, payload)
                
            # Traiter les messages de contrôle
            if topic.startswith(f"control/{self.client_id}/"):
                command = topic.split('/')[-1]
                
                if command == "restart":
                    logger.info("Commande de redémarrage reçue")
                    # Ici on peut implémenter un redémarrage du dispositif
                    
                elif command == "configure":
                    try:
                        config = json.loads(payload)
                        logger.info(f"Nouvelle configuration reçue: {config}")
                        # Ici on peut appliquer la nouvelle configuration
                    except json.JSONDecodeError:
                        logger.error("Configuration reçue invalide: non JSON")
                        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message MQTT: {e}")

    def _on_publish(self, client, userdata, mid):
        """
        Callback appelé après la publication d'un message.
        
        Args:
            client: Instance du client
            userdata: Données utilisateur
            mid: ID du message
        """
        self.last_publish_time = time.time()
        self.message_count += 1
        logger.debug(f"Message publié avec succès, ID: {mid}")

    def connect(self) -> bool:
        """
        Connecte le client au broker MQTT.
        
        Returns:
            bool: True si connecté avec succès, False sinon
        """
        try:
            if self.connected:
                return True
                
            self.client.connect(
                host=self.broker_host,
                port=self.broker_port,
                keepalive=self.keepalive
            )
            
            # Démarrer la boucle de traitement des messages en arrière-plan
            self.client.loop_start()
            
            # Attendre que la connexion soit établie (max 5 secondes)
            timeout = time.time() + 5.0
            while not self.connected and time.time() < timeout:
                time.sleep(0.1)
                
            return self.connected
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion MQTT: {e}")
            return False

    def disconnect(self) -> None:
        """
        Déconnecte le client du broker MQTT.
        """
        if not self.connected:
            return
            
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Déconnecté du broker MQTT")
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion MQTT: {e}")

    def publish(
        self, 
        topic: str, 
        payload: Union[Dict[str, Any], str], 
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """
        Publie un message sur un sujet MQTT.
        
        Args:
            topic: Sujet MQTT
            payload: Contenu du message (dict ou str)
            qos: Qualité de service (0, 1 ou 2)
            retain: Si True, le message est conservé par le broker
            
        Returns:
            bool: True si publié avec succès, False sinon
        """
        # Convertir le payload en JSON si c'est un dictionnaire
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            
        if not self.connected:
            # Si déconnecté, mettre en file d'attente
            if self.message_queue.qsize() < self.max_queue_size:
                self.message_queue.put((topic, payload, qos, retain))
                logger.debug(f"Message mis en file d'attente pour {topic} (non connecté)")
                return False
            else:
                logger.warning("File d'attente de messages pleine, message perdu")
                return False
        
        try:
            info = self.client.publish(topic, payload, qos, retain)
            
            # La publication est réussie si le code de retour est 0
            return info.rc == 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur {topic}: {e}")
            
            # En cas d'erreur, mettre en file d'attente
            if self.message_queue.qsize() < self.max_queue_size:
                self.message_queue.put((topic, payload, qos, retain))
                logger.debug(f"Message mis en file d'attente pour {topic} (erreur de publication)")
                
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """
        Souscrit à un sujet MQTT.
        
        Args:
            topic: Sujet MQTT
            qos: Qualité de service (0, 1 ou 2)
            
        Returns:
            bool: True si souscrit avec succès, False sinon
        """
        if not self.connected:
            logger.warning(f"Impossible de souscrire à {topic}: non connecté")
            return False
            
        try:
            result, _ = self.client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Souscrit à {topic} avec QoS {qos}")
                return True
            else:
                logger.error(f"Échec de souscription à {topic}: code {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la souscription à {topic}: {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """
        Annule la souscription à un sujet MQTT.
        
        Args:
            topic: Sujet MQTT
            
        Returns:
            bool: True si désinscrit avec succès, False sinon
        """
        if not self.connected:
            logger.warning(f"Impossible de se désinscrire de {topic}: non connecté")
            return False
            
        try:
            result, _ = self.client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Désinscrit de {topic}")
                return True
            else:
                logger.error(f"Échec de désinscription de {topic}: code {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la désinscription de {topic}: {e}")
            return False

    def _process_message_queue(self) -> None:
        """
        Traite les messages en file d'attente.
        """
        if not self.connected:
            return
            
        queue_size = self.message_queue.qsize()
        if queue_size > 0:
            logger.info(f"Traitement de {queue_size} messages en file d'attente")
            
        while not self.message_queue.empty():
            try:
                topic, payload, qos, retain = self.message_queue.get(block=False)
                
                try:
                    self.client.publish(topic, payload, qos, retain)
                    logger.debug(f"Message en file d'attente publié sur {topic}")
                except Exception as e:
                    logger.error(f"Erreur lors de la publication du message en file d'attente: {e}")
                    # Remettre en file d'attente si possible
                    if self.message_queue.qsize() < self.max_queue_size:
                        self.message_queue.put((topic, payload, qos, retain))
                        
                self.message_queue.task_done()
                
            except queue.Empty:
                break

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne l'état du client MQTT.
        
        Returns:
            Dict: État du client MQTT
        """
        return {
            "client_id": self.client_id,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "connected": self.connected,
            "reconnect_count": self.reconnect_count,
            "last_publish_time": self.last_publish_time,
            "message_count": self.message_count,
            "queue_size": self.message_queue.qsize(),
            "using_tls": self.use_tls
        }


class NetworkManager:
    """
    Gestionnaire de connexions réseau pour les capteurs IoT.
    
    Cette classe gère les connexions WiFi et Bluetooth, ainsi que 
    la transmission des données vers le serveur central.
    """
    
    # Constantes pour les types de connexion
    CONN_TYPE_WIFI = "wifi"
    CONN_TYPE_BT = "bluetooth"
    CONN_TYPE_ETHERNET = "ethernet"
    
    def __init__(
        self,
        device_id: str,
        server_host: str,
        mqtt_port: int = 1883,
        mqtt_use_tls: bool = False,
        mqtt_user: Optional[str] = None,
        mqtt_password: Optional[str] = None,
        wifi_ssid: Optional[str] = None,
        wifi_password: Optional[str] = None,
        connection_type: str = CONN_TYPE_WIFI,
        bt_server_mac: Optional[str] = None,
        cache_dir: Optional[str] = None,
        max_cache_size_mb: float = 100.0
    ) -> None:
        """
        Initialise le gestionnaire de réseau.
        
        Args:
            device_id: Identifiant unique du dispositif
            server_host: Adresse du serveur central
            mqtt_port: Port du broker MQTT
            mqtt_use_tls: Si True, utilise TLS pour MQTT
            mqtt_user: Nom d'utilisateur MQTT (optionnel)
            mqtt_password: Mot de passe MQTT (optionnel)
            wifi_ssid: SSID du réseau WiFi (pour le type wifi)
            wifi_password: Mot de passe WiFi (pour le type wifi)
            connection_type: Type de connexion (wifi, bluetooth, ethernet)
            bt_server_mac: Adresse MAC du serveur Bluetooth (pour le type bluetooth)
            cache_dir: Répertoire pour le cache de données
            max_cache_size_mb: Taille maximale du cache en Mo
        """
        self.device_id = device_id
        self.server_host = server_host
        self.mqtt_port = mqtt_port
        self.mqtt_use_tls = mqtt_use_tls
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.connection_type = connection_type
        self.bt_server_mac = bt_server_mac
        
        # Valider le type de connexion
        if connection_type not in [self.CONN_TYPE_WIFI, self.CONN_TYPE_BT, self.CONN_TYPE_ETHERNET]:
            raise ValueError(f"Type de connexion non supporté: {connection_type}")
            
        # Vérifier les paramètres requis selon le type de connexion
        if connection_type == self.CONN_TYPE_WIFI and (wifi_ssid is None or wifi_password is None):
            raise ValueError("SSID et mot de passe WiFi requis pour le type de connexion wifi")
            
        if connection_type == self.CONN_TYPE_BT and bt_server_mac is None:
            raise ValueError("Adresse MAC du serveur requise pour le type de connexion bluetooth")
        
        # Initialiser le cache
        self.cache = DataCache(cache_dir=cache_dir, max_cache_size_mb=max_cache_size_mb)
        
        # Variables d'état
        self.connected = False
        self.mqtt_client = None
        self.bt_sock = None
        self.connection_attempts = 0
        self.last_connection_time = 0.0
        self.last_data_sent_time = 0.0
        
        # Thread pour la vérification périodique de la connexion
        self.connection_check_thread = None
        self.connection_check_running = False
        
        logger.info(f"Gestionnaire réseau initialisé pour {device_id} (type: {connection_type})")

    def connect(self) -> bool:
        """
        Établit la connexion réseau.
        
        Returns:
            bool: True si connecté avec succès, False sinon
        """
        if self.connected:
            return True
            
        self.connection_attempts += 1
        self.last_connection_time = time.time()
        
        try:
            # Établir la connexion réseau selon le type
            if self.connection_type == self.CONN_TYPE_WIFI:
                success = self._connect_wifi()
            elif self.connection_type == self.CONN_TYPE_BT:
                success = self._connect_bluetooth()
            else:  # Ethernet ou autre
                # Pour Ethernet, on suppose que la connexion est déjà établie
                success = self._check_internet_connection()
                
            if not success:
                logger.error("Échec de connexion réseau")
                return False
                
            # Si connecté au réseau, initialiser MQTT
            if MQTT_AVAILABLE:
                self.mqtt_client = MQTTClient(
                    client_id=f"lvm_{self.device_id}",
                    broker_host=self.server_host,
                    broker_port=self.mqtt_port,
                    user=self.mqtt_user,
                    password=self.mqtt_password,
                    use_tls=self.mqtt_use_tls
                )
                
                # Connecter MQTT
                mqtt_success = self.mqtt_client.connect()
                if not mqtt_success:
                    logger.error("Échec de connexion MQTT")
                    return False
                    
                # Souscrire aux commandes
                control_topic = f"control/{self.device_id}/#"
                self.mqtt_client.subscribe(control_topic)
            
            self.connected = True
            logger.info(f"Connecté au réseau ({self.connection_type}) et au serveur MQTT")
            
            # Démarrer le thread de vérification de connexion
            self._start_connection_check()
            
            # Envoyer les données en cache
            self._send_cached_data()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            return False

    def disconnect(self) -> None:
        """
        Déconnecte du réseau.
        """
        # Arrêter le thread de vérification
        self._stop_connection_check()
        
        try:
            # Déconnecter MQTT
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                
            # Déconnecter Bluetooth
            if self.bt_sock:
                self.bt_sock.close()
                self.bt_sock = None
                
            # Pour WiFi, on pourrait désactiver l'interface
            
            self.connected = False
            logger.info("Déconnecté du réseau")
            
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")

    def send_data(
        self, 
        data: Dict[str, Any],
        topic: Optional[str] = None,
        qos: int = 0
    ) -> bool:
        """
        Envoie des données au serveur central.
        
        Args:
            data: Données à envoyer
            topic: Sujet MQTT (si None, utilise un sujet par défaut)
            qos: Qualité de service MQTT (0, 1 ou 2)
            
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        # Utiliser un sujet par défaut si non spécifié
        if topic is None:
            topic = f"data/{self.device_id}"
            
        # Ajouter un timestamp et device_id aux données
        enriched_data = data.copy()
        enriched_data["timestamp"] = time.time()
        enriched_data["device_id"] = self.device_id
        
        try:
            # Si connecté et MQTT disponible, envoyer directement
            if self.connected and self.mqtt_client:
                success = self.mqtt_client.publish(topic, enriched_data, qos)
                
                if success:
                    self.last_data_sent_time = time.time()
                    logger.debug(f"Données envoyées avec succès sur {topic}")
                    return True
                else:
                    logger.warning(f"Échec d'envoi MQTT sur {topic}, mise en cache")
            else:
                logger.debug(f"Non connecté, mise en cache des données pour {topic}")
                
            # Si non connecté ou échec MQTT, mettre en cache
            self.cache.add(enriched_data, topic)
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données: {e}")
            
            # En cas d'erreur, mettre en cache
            self.cache.add(enriched_data, topic)
            return False

    def _connect_wifi(self) -> bool:
        """
        Établit la connexion WiFi.
        
        Returns:
            bool: True si connecté avec succès, False sinon
        """
        if not WIFI_CONTROL_AVAILABLE:
            logger.warning("Contrôle WiFi non disponible (manque subprocess)")
            return self._check_internet_connection()
            
        try:
            # Vérifier si déjà connecté au bon réseau
            if self._check_wifi_connected():
                logger.info(f"Déjà connecté au réseau WiFi {self.wifi_ssid}")
                return True
                
            logger.info(f"Tentative de connexion au réseau WiFi {self.wifi_ssid}...")
            
            # Pour Raspberry Pi, utiliser wpa_supplicant
            # Pour plus de sécurité, on pourrait utiliser un fichier temporaire
            wpa_config = f"""
            network={{
                ssid="{self.wifi_ssid}"
                psk="{self.wifi_password}"
                key_mgmt=WPA-PSK
            }}
            """
            
            # Écrire la configuration dans un fichier temporaire
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(wpa_config)
                
            try:
                # Reconfigurer wpa_supplicant
                subprocess.run(
                    ["wpa_cli", "-i", "wlan0", "reconfigure"],
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                
                # Attendre la connexion
                for attempt in range(30):  # Attendre 30 secondes max
                    if self._check_wifi_connected():
                        logger.info(f"Connecté au réseau WiFi {self.wifi_ssid}")
                        return True
                    time.sleep(1)
                    
                logger.error(f"Impossible de se connecter au réseau WiFi {self.wifi_ssid}")
                return False
                
            finally:
                # Supprimer le fichier temporaire
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                
        except Exception as e:
            logger.error(f"Erreur lors de la connexion WiFi: {e}")
            return False

    def _check_wifi_connected(self) -> bool:
        """
        Vérifie si le WiFi est connecté au réseau configuré.
        
        Returns:
            bool: True si connecté, False sinon
        """
        try:
            # Pour Raspberry Pi
            result = subprocess.run(
                ["iwgetid", "-r"], 
                check=False,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                current_ssid = result.stdout.decode().strip()
                return current_ssid == self.wifi_ssid
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification WiFi: {e}")
            return False

    def _connect_bluetooth(self) -> bool:
        """
        Établit la connexion Bluetooth.
        
        Returns:
            bool: True si connecté avec succès, False sinon
        """
        if not BLUETOOTH_AVAILABLE:
            logger.error("Bluetooth non disponible (manque le module bluetooth)")
            return False
            
        try:
            # Créer une socket Bluetooth
            self.bt_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # Se connecter au serveur
            port = 1  # Port RFCOMM par défaut
            self.bt_sock.connect((self.bt_server_mac, port))
            
            logger.info(f"Connecté au serveur Bluetooth {self.bt_server_mac}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion Bluetooth: {e}")
            
            if self.bt_sock:
                self.bt_sock.close()
                self.bt_sock = None
                
            return False

    def _check_internet_connection(self) -> bool:
        """
        Vérifie si une connexion Internet est disponible.
        
        Returns:
            bool: True si connecté à Internet, False sinon
        """
        try:
            # Tenter de se connecter au serveur configuré
            socket.create_connection((self.server_host, self.mqtt_port), timeout=5)
            return True
        except OSError:
            return False

    def _start_connection_check(self) -> None:
        """
        Démarre un thread pour vérifier périodiquement la connexion.
        """
        if self.connection_check_thread is not None and self.connection_check_thread.is_alive():
            return
            
        self.connection_check_running = True
        self.connection_check_thread = threading.Thread(
            target=self._connection_check_worker,
            daemon=True
        )
        self.connection_check_thread.start()
        logger.debug("Thread de vérification de connexion démarré")

    def _stop_connection_check(self) -> None:
        """
        Arrête le thread de vérification de connexion.
        """
        self.connection_check_running = False
        
        if self.connection_check_thread and self.connection_check_thread.is_alive():
            self.connection_check_thread.join(timeout=2.0)
            logger.debug("Thread de vérification de connexion arrêté")

    def _connection_check_worker(self) -> None:
        """
        Fonction exécutée par le thread de vérification de connexion.
        Vérifie périodiquement la connexion et tente de se reconnecter si nécessaire.
        """
        check_interval = 60.0  # Vérifier toutes les 60 secondes
        
        while self.connection_check_running:
            try:
                # Vérifier la connexion réseau
                if not self._check_internet_connection():
                    logger.warning("Connexion Internet perdue, tentative de reconnexion...")
                    self.connected = False
                    
                    # Tenter de se reconnecter
                    self.connect()
                elif self.mqtt_client and not self.mqtt_client.connected:
                    logger.warning("Connexion MQTT perdue, tentative de reconnexion...")
                    self.mqtt_client.connect()
                
                # Si connecté, essayer d'envoyer les données en cache
                if self.connected:
                    self._send_cached_data()
                    
            except Exception as e:
                logger.error(f"Erreur dans le thread de vérification: {e}")
                
            # Attendre avant la prochaine vérification
            for _ in range(int(check_interval * 10)):
                if not self.connection_check_running:
                    break
                time.sleep(0.1)

    def _send_cached_data(self) -> None:
        """
        Tente d'envoyer les données en cache.
        """
        if not self.connected or not self.mqtt_client:
            return
            
        try:
            # Récupérer toutes les entrées du cache, triées par temps
            cached_entries = self.cache.get_all_entries(sorted_by_time=True)
            
            if not cached_entries:
                return
                
            logger.info(f"Tentative d'envoi de {len(cached_entries)} entrées en cache")
            
            for entry in cached_entries:
                # Récupérer les données
                entry_id = entry.get("id")
                topic = entry.get("topic", f"data/{self.device_id}")
                data = entry.get("data", {})
                
                # Tenter de publier
                success = self.mqtt_client.publish(topic, data)
                
                if success:
                    # Si réussi, supprimer du cache
                    self.cache.remove(entry_id)
                    logger.debug(f"Donnée en cache envoyée et supprimée: {entry_id}")
                else:
                    # Si échec, arrêter pour réessayer plus tard
                    logger.warning("Échec d'envoi des données en cache, nouvel essai plus tard")
                    break
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données en cache: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne l'état du gestionnaire réseau.
        
        Returns:
            Dict: État complet du gestionnaire réseau
        """
        status = {
            "device_id": self.device_id,
            "connection_type": self.connection_type,
            "connected": self.connected,
            "server_host": self.server_host,
            "mqtt_port": self.mqtt_port,
            "connection_attempts": self.connection_attempts,
            "last_connection_time": self.last_connection_time,
            "last_data_sent_time": self.last_data_sent_time,
            "internet_available": self._check_internet_connection(),
            "cached_data_count": len(self.cache.get_all_entries())
        }
        
        # Ajouter les infos WiFi si applicable
        if self.connection_type == self.CONN_TYPE_WIFI:
            status["wifi_ssid"] = self.wifi_ssid
            status["wifi_connected"] = self._check_wifi_connected()
            
        # Ajouter les infos MQTT si disponible
        if self.mqtt_client:
            status["mqtt"] = self.mqtt_client.get_status()
            
        return status


if __name__ == "__main__":
    # Exemple d'utilisation pour tests
    logger.setLevel(logging.DEBUG)
    logger.info("Test du module de gestion réseau")
    
    try:
        # Tester le gestionnaire réseau
        network = NetworkManager(
            device_id="test_device_01",
            server_host="192.168.1.100",  # Adresse à adapter
            mqtt_port=1883,
            wifi_ssid="Le_Vieux_Moulin_Network",
            wifi_password="password123",
            connection_type=NetworkManager.CONN_TYPE_WIFI
        )
        
        # Tenter de se connecter
        connected = network.connect()
        logger.info(f"Connexion réussie: {connected}")
        
        if connected:
            # Envoyer des données de test
            test_data = {
                "temperature": 175.5,
                "oil_level": 8.2,
                "quality": 85.0,
                "sensor_id": "fryer_01"
            }
            
            sent = network.send_data(test_data, topic="data/test_device_01/fryer")
            logger.info(f"Données envoyées: {sent}")
            
            # Afficher le statut
            status = network.get_status()
            logger.info(f"Statut du gestionnaire réseau: {status}")
            
            # Déconnexion
            network.disconnect()
            logger.info("Déconnecté")
        
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
