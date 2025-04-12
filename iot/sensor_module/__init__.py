#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des capteurs IoT pour Le Vieux Moulin.

Ce module fournit les composants pour la lecture et la transmission des données
des capteurs installés dans le restaurant Le Vieux Moulin, notamment
pour la gestion des stocks (bacs d'ingrédients, friteuse, etc.).

Modules:
    weight_sensor: Capteurs de poids pour les bacs d'ingrédients
    oil_level_sensor: Capteurs de niveau et qualité d'huile pour friteuse
    network_manager: Gestion des connexions réseau et transmission des données

Exemple d'utilisation:
    >>> from iot.sensor_module import WeightSensor, FryerMonitor, NetworkManager
    >>> # Initialiser les capteurs
    >>> farine_sensor = WeightSensor(name="bac_farine", dout_pin=5, sck_pin=6)
    >>> fryer = FryerMonitor(fryer_name="friteuse_principale", ...)
    >>> # Configurer le réseau
    >>> network = NetworkManager(device_id="cuisine_01", server_host="192.168.1.100")
    >>> # Démarrer les capteurs et transmettre les données
    >>> network.connect()
    >>> network.send_data(farine_sensor.get_status())
"""

__version__ = '1.0.0'
__author__ = 'Le Vieux Moulin'

# Exporter les classes principales pour faciliter l'importation
from .weight_sensor import WeightSensor, WeightSensorArray, HX711
from .oil_level_sensor import OilQualitySensor, OilLevelSensor, FryerMonitor
from .network_manager import NetworkManager, MQTTClient, DataCache

# Liste des modules à importer avec '*'
__all__ = [
    'WeightSensor',
    'WeightSensorArray',
    'HX711',
    'OilQualitySensor',
    'OilLevelSensor',
    'FryerMonitor',
    'NetworkManager',
    'MQTTClient',
    'DataCache'
]
