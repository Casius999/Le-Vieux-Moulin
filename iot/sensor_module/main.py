#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal pour le système de capteurs IoT du restaurant Le Vieux Moulin.

Ce script illustre l'utilisation complète du module de capteurs IoT en créant
une configuration de surveillance pour plusieurs bacs d'ingrédients et la friteuse,
puis en transmettant ces données au serveur central via le gestionnaire réseau.

Il peut être utilisé comme point de départ pour l'implémentation réelle, ou
comme exemple pour comprendre l'utilisation de l'ensemble des modules.

Usage:
    python main.py [--config CONFIG_FILE] [--log-level {DEBUG,INFO,WARNING,ERROR}]

Arguments:
    --config : Chemin vers un fichier de configuration JSON (facultatif)
    --log-level : Niveau de journalisation (par défaut: INFO)

Exemple de fichier de configuration:
    {
        "device_id": "cuisine_principale",
        "server": {
            "host": "192.168.1.100",
            "mqtt_port": 1883,
            "mqtt_use_tls": false
        },
        "network": {
            "type": "wifi",
            "ssid": "LVM_Network",
            "password": "password123"
        },
        "sensors": {
            "weight": [
                {
                    "name": "bac_farine",
                    "pins": {"dout": 5, "sck": 6},
                    "reference_unit": 2145.3,
                    "min_weight": 0.0,
                    "max_weight": 5000.0
                },
                {
                    "name": "bac_sucre",
                    "pins": {"dout": 17, "sck": 18},
                    "reference_unit": 1998.7,
                    "min_weight": 0.0,
                    "max_weight": 2000.0
                }
            ],
            "fryer": {
                "name": "friteuse_principale",
                "ultrasonic": {"trigger": 23, "echo": 24},
                "temp_pin": 4,
                "turbidity_pin": 17,
                "depth": 15.0
            }
        },
        "update_interval": 60
    }
"""

import os
import json
import time
import logging
import argparse
import signal
import threading
from typing import Dict, List, Any, Optional

# Importer les modules de capteurs
from weight_sensor import WeightSensor, WeightSensorArray
from oil_level_sensor import FryerMonitor
from network_manager import NetworkManager

# Configurer le logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LVM_IoT")

# Variables globales
running = True
config = {}
weight_sensors = None
fryer_monitor = None
network = None


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Charge la configuration depuis un fichier JSON.
    
    Args:
        config_file: Chemin vers le fichier de configuration
        
    Returns:
        Dict: Configuration chargée
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Fichier de configuration introuvable: {config_file}")
        
    with open(config_file, 'r') as f:
        return json.load(f)


def setup_default_config() -> Dict[str, Any]:
    """
    Crée une configuration par défaut.
    
    Returns:
        Dict: Configuration par défaut
    """
    return {
        "device_id": "lvm_kitchen_01",
        "server": {
            "host": "localhost",
            "mqtt_port": 1883,
            "mqtt_use_tls": False
        },
        "network": {
            "type": "wifi",
            "ssid": "LVM_Network",
            "password": "password123"
        },
        "sensors": {
            "weight": [
                {
                    "name": "bac_farine",
                    "pins": {"dout": 5, "sck": 6},
                    "reference_unit": 2145.3,
                    "min_weight": 0.0,
                    "max_weight": 5000.0
                }
            ],
            "fryer": {
                "name": "friteuse_principale",
                "ultrasonic": {"trigger": 23, "echo": 24},
                "temp_pin": 4,
                "turbidity_pin": 17,
                "depth": 15.0
            }
        },
        "update_interval": 60  # Secondes
    }


def setup_sensors(config: Dict[str, Any]) -> None:
    """
    Configure et initialise tous les capteurs selon la configuration.
    
    Args:
        config: Configuration du système
    """
    global weight_sensors, fryer_monitor
    
    logger.info("Initialisation des capteurs...")
    
    # Initialiser le tableau de capteurs de poids
    weight_sensors = WeightSensorArray()
    
    # Ajouter les capteurs de poids configurés
    for sensor_config in config.get("sensors", {}).get("weight", []):
        try:
            sensor = WeightSensor(
                name=sensor_config["name"],
                dout_pin=sensor_config["pins"]["dout"],
                sck_pin=sensor_config["pins"]["sck"],
                reference_unit=sensor_config.get("reference_unit", 1.0),
                min_weight=sensor_config.get("min_weight", 0.0),
                max_weight=sensor_config.get("max_weight", 5000.0),
                unit=sensor_config.get("unit", "g")
            )
            
            # Effectuer la tare initiale
            sensor.tare()
            
            # Ajouter au tableau
            weight_sensors.add_sensor(sensor)
            logger.info(f"Capteur de poids '{sensor_config['name']}' initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du capteur '{sensor_config['name']}': {e}")
    
    # Initialiser le moniteur de friteuse s'il est configuré
    fryer_config = config.get("sensors", {}).get("fryer")
    if fryer_config:
        try:
            fryer_monitor = FryerMonitor(
                fryer_name=fryer_config["name"],
                ultrasonic_trigger_pin=fryer_config["ultrasonic"]["trigger"],
                ultrasonic_echo_pin=fryer_config["ultrasonic"]["echo"],
                temp_pin=fryer_config["temp_pin"],
                turbidity_pin=fryer_config.get("turbidity_pin"),
                fryer_depth=fryer_config.get("depth", 20.0),
                min_level=fryer_config.get("min_level", 2.0),
                max_level=fryer_config.get("max_level", 18.0)
            )
            logger.info(f"Moniteur de friteuse '{fryer_config['name']}' initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du moniteur de friteuse: {e}")
            fryer_monitor = None


def setup_network(config: Dict[str, Any]) -> None:
    """
    Configure et initialise le gestionnaire réseau.
    
    Args:
        config: Configuration du système
    """
    global network
    
    logger.info("Initialisation du réseau...")
    
    try:
        # Récupérer les paramètres de configuration
        device_id = config.get("device_id", "lvm_device")
        server_host = config.get("server", {}).get("host", "localhost")
        mqtt_port = config.get("server", {}).get("mqtt_port", 1883)
        mqtt_use_tls = config.get("server", {}).get("mqtt_use_tls", False)
        mqtt_user = config.get("server", {}).get("mqtt_user")
        mqtt_password = config.get("server", {}).get("mqtt_password")
        
        # Configuration réseau
        network_type = config.get("network", {}).get("type", "wifi")
        wifi_ssid = config.get("network", {}).get("ssid")
        wifi_password = config.get("network", {}).get("password")
        bt_server_mac = config.get("network", {}).get("bt_server_mac")
        
        # Initialiser le gestionnaire réseau
        network = NetworkManager(
            device_id=device_id,
            server_host=server_host,
            mqtt_port=mqtt_port,
            mqtt_use_tls=mqtt_use_tls,
            mqtt_user=mqtt_user,
            mqtt_password=mqtt_password,
            wifi_ssid=wifi_ssid,
            wifi_password=wifi_password,
            connection_type=network_type,
            bt_server_mac=bt_server_mac
        )
        
        # Tenter de se connecter
        connected = network.connect()
        if connected:
            logger.info("Connexion réseau établie avec succès")
        else:
            logger.warning("Impossible d'établir la connexion réseau, les données seront mises en cache")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du réseau: {e}")
        network = None


def send_sensor_data() -> None:
    """
    Collecte et envoie les données de tous les capteurs.
    """
    if network is None:
        logger.error("Réseau non initialisé, impossible d'envoyer les données")
        return
        
    try:
        # Collecter et envoyer les données des capteurs de poids
        if weight_sensors:
            # Récupérer tous les poids
            weights_data = weight_sensors.get_all_weights()
            
            # Enrichir avec des métadonnées
            data = {
                "timestamp": time.time(),
                "type": "weight_sensors",
                "data": weights_data
            }
            
            # Envoyer au serveur
            network.send_data(data, topic=f"data/{config['device_id']}/weight")
            logger.debug(f"Données de poids envoyées: {len(weights_data)} capteurs")
            
        # Collecter et envoyer les données de la friteuse
        if fryer_monitor:
            # Récupérer l'état complet
            fryer_status = fryer_monitor.get_status()
            
            # Simplifier pour l'envoi
            data = {
                "timestamp": time.time(),
                "type": "fryer",
                "name": fryer_status["name"],
                "operating_status": fryer_status["operating_status"],
                "level": fryer_status["level"],
                "quality": fryer_status["quality"],
                "needs_attention": fryer_status["needs_attention"],
                "warnings": fryer_status["warnings"]
            }
            
            # Envoyer au serveur
            network.send_data(data, topic=f"data/{config['device_id']}/fryer")
            logger.debug(f"Données de friteuse envoyées: {fryer_status['name']}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des données: {e}")


def data_collection_thread(interval: int) -> None:
    """
    Thread principal pour la collecte et l'envoi périodique des données.
    
    Args:
        interval: Intervalle en secondes entre les envois
    """
    logger.info(f"Démarrage du thread de collecte de données (intervalle: {interval}s)")
    
    while running:
        try:
            # Collecter et envoyer les données
            send_sensor_data()
            
            # Attendre l'intervalle spécifié
            for _ in range(interval * 10):  # Diviser en petits intervalles pour réagir plus vite à l'arrêt
                if not running:
                    break
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Erreur dans le thread de collecte: {e}")
            time.sleep(5)  # Attente courte en cas d'erreur


def cleanup() -> None:
    """
    Nettoie les ressources avant la fermeture.
    """
    logger.info("Nettoyage des ressources...")
    
    # Déconnecter le réseau
    if network:
        network.disconnect()
    
    # Mettre en veille les capteurs
    if weight_sensors:
        weight_sensors.power_down_all()


def signal_handler(sig, frame) -> None:
    """
    Gestionnaire de signal pour arrêter proprement l'application.
    """
    global running
    logger.info("Signal d'arrêt reçu, fermeture en cours...")
    running = False


def main() -> None:
    """
    Fonction principale du script.
    """
    global config, running
    
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Système de capteurs IoT pour Le Vieux Moulin")
    parser.add_argument("--config", help="Chemin vers le fichier de configuration")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="INFO", help="Niveau de journalisation")
    args = parser.parse_args()
    
    # Configurer le niveau de journalisation
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Charger la configuration
    try:
        if args.config:
            config = load_config(args.config)
            logger.info(f"Configuration chargée depuis {args.config}")
        else:
            config = setup_default_config()
            logger.info("Configuration par défaut utilisée")
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        return
    
    # Configurer le gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialiser les capteurs
        setup_sensors(config)
        
        # Initialiser le réseau
        setup_network(config)
        
        # Démarrer le thread de collecte de données
        update_interval = config.get("update_interval", 60)
        collection_thread = threading.Thread(
            target=data_collection_thread,
            args=(update_interval,),
            daemon=True
        )
        collection_thread.start()
        
        # Boucle principale (attente d'arrêt)
        logger.info("Système démarré, appuyez sur Ctrl+C pour arrêter")
        while running:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}")
    finally:
        # Nettoyage final
        running = False
        cleanup()
        logger.info("Système arrêté")


if __name__ == "__main__":
    main()
