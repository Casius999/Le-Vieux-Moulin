#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des capteurs de poids pour Le Vieux Moulin.

Ce module gère les cellules de charge utilisées pour mesurer le poids des ingrédients 
dans différents bacs de stockage du restaurant. Il utilise des cellules HX711 connectées 
à un ESP32 pour la mesure précise des poids.

Classes:
    WeightSensor: Classe principale pour gérer une cellule de charge individuelle
    WeightSensorArray: Gère plusieurs capteurs de poids simultanément

Exemples d'utilisation:
    >>> from weight_sensor import WeightSensor
    >>> sensor = WeightSensor(dout_pin=5, sck_pin=6, reference_unit=1253.4)
    >>> sensor.tare()  # Effectue la tare du capteur
    >>> weight = sensor.get_weight()  # Lit le poids en grammes
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
import RPi.GPIO as GPIO  # Pour Raspberry Pi
# Pour ESP32, utilisez plutôt machine.Pin
# from machine import Pin, ADC

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class HX711:
    """
    Classe d'interface pour le convertisseur analogique-numérique HX711.
    
    Cette classe gère la communication avec le chip HX711 connecté aux 
    cellules de charge.
    """
    
    def __init__(self, dout_pin: int, sck_pin: int, gain: int = 128) -> None:
        """
        Initialise l'interface HX711.
        
        Args:
            dout_pin: Numéro de pin GPIO pour la sortie de données
            sck_pin: Numéro de pin GPIO pour l'horloge
            gain: Gain de l'amplificateur (128, 64 ou 32)
        """
        # Configuration des pins
        self.sck = sck_pin
        self.dout = dout_pin
        
        # Valider le gain (doit être 128, 64 ou 32)
        if gain not in [128, 64, 32]:
            raise ValueError("Le gain doit être 128, 64 ou 32")
        
        self.gain = gain
        self.offset = 0
        self.scale = 1
        
        # Configuration pour Raspberry Pi
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dout, GPIO.IN)
        GPIO.setup(self.sck, GPIO.OUT)
        
        # Pour ESP32, utilisez plutôt:
        # self.sck_pin = Pin(sck_pin, Pin.OUT)
        # self.dout_pin = Pin(dout_pin, Pin.IN)
        
        logger.debug(f"HX711 initialisé avec DOUT={dout_pin}, SCK={sck_pin}, gain={gain}")
        
        # Réinitialiser le HX711
        self.reset()

    def reset(self) -> None:
        """Réinitialise le HX711."""
        GPIO.output(self.sck, False)
        time.sleep(0.1)
        
        # Activer le HX711
        ready = self.is_ready()
        if not ready:
            logger.warning("HX711 non prêt après reset. Vérifiez les connexions.")

    def is_ready(self) -> bool:
        """
        Vérifie si le HX711 est prêt à envoyer des données.
        
        Returns:
            bool: True si prêt, False sinon
        """
        return GPIO.input(self.dout) == 0

    def read(self) -> int:
        """
        Lit une valeur brute depuis le HX711.
        
        Returns:
            int: Valeur lue depuis le HX711
        
        Raises:
            TimeoutError: Si le capteur ne répond pas
        """
        # Attendre que le HX711 soit prêt
        timeout_counter = 0
        while not self.is_ready():
            timeout_counter += 1
            if timeout_counter > 100:  # ~1 seconde d'attente max
                raise TimeoutError("HX711 ne répond pas")
            time.sleep(0.01)
        
        # Lecture des 24 bits
        data = 0
        for i in range(24):
            GPIO.output(self.sck, True)
            time.sleep(0.000001)  # 1µs
            data = (data << 1) | GPIO.input(self.dout)
            GPIO.output(self.sck, False)
            time.sleep(0.000001)  # 1µs
        
        # Configuration du gain pour la prochaine lecture
        for i in range(1, 4):
            if i == self.gain:
                GPIO.output(self.sck, True)
            else:
                GPIO.output(self.sck, False)
            time.sleep(0.000001)  # 1µs
            GPIO.output(self.sck, False)
            time.sleep(0.000001)  # 1µs
        
        # Conversion en complément à 2
        if data & 0x800000:
            data = data - 0x1000000
        
        return data

    def read_average(self, times: int = 10) -> float:
        """
        Lit plusieurs valeurs et retourne la moyenne.
        
        Args:
            times: Nombre de lectures à moyenner
        
        Returns:
            float: Valeur moyenne lue
        """
        total = 0
        valid_readings = 0
        
        for _ in range(times):
            try:
                value = self.read()
                total += value
                valid_readings += 1
            except TimeoutError:
                logger.warning("Timeout pendant la lecture du HX711")
                continue
        
        if valid_readings == 0:
            raise RuntimeError("Impossible d'obtenir des lectures valides du HX711")
        
        return total / valid_readings

    def set_offset(self, offset: int) -> None:
        """
        Définit l'offset pour les lectures.
        
        Args:
            offset: Valeur à soustraire des lectures brutes
        """
        self.offset = offset

    def set_scale(self, scale: float) -> None:
        """
        Définit le facteur d'échelle pour convertir les lectures brutes en unités réelles.
        
        Args:
            scale: Facteur d'échelle
        """
        self.scale = scale

    def get_value(self, times: int = 5) -> float:
        """
        Lit une valeur corrigée de l'offset.
        
        Args:
            times: Nombre de lectures à moyenner
        
        Returns:
            float: Valeur corrigée
        """
        return self.read_average(times) - self.offset

    def get_units(self, times: int = 5) -> float:
        """
        Lit une valeur convertie dans les unités calibrées.
        
        Args:
            times: Nombre de lectures à moyenner
        
        Returns:
            float: Valeur convertie dans les unités calibrées
        """
        return self.get_value(times) / self.scale

    def tare(self, times: int = 15) -> None:
        """
        Définit l'offset actuel comme zéro.
        
        Args:
            times: Nombre de lectures à moyenner pour la tare
        """
        average = self.read_average(times)
        self.set_offset(average)
        logger.info(f"Tare effectuée avec succès. Nouvel offset: {average}")

    def power_down(self) -> None:
        """Met le HX711 en mode basse consommation."""
        GPIO.output(self.sck, False)
        GPIO.output(self.sck, True)
        time.sleep(0.0001)  # 100µs

    def power_up(self) -> None:
        """Réveille le HX711 du mode basse consommation."""
        GPIO.output(self.sck, False)
        time.sleep(0.0001)  # 100µs


class WeightSensor:
    """
    Classe de gestion d'un capteur de poids basé sur HX711.
    
    Cette classe offre une interface de haut niveau pour les cellules de charge,
    avec calibration, lecture de poids et statut.
    """
    
    def __init__(
        self, 
        name: str,
        dout_pin: int, 
        sck_pin: int, 
        reference_unit: float = 1.0,
        min_weight: float = 0.0,
        max_weight: float = 5000.0,
        unit: str = "g",
        moving_average_size: int = 5
    ) -> None:
        """
        Initialise un capteur de poids.
        
        Args:
            name: Nom identifiant le capteur (ex: "bac_farine")
            dout_pin: Pin de données du HX711
            sck_pin: Pin d'horloge du HX711
            reference_unit: Facteur de calibration (unités par valeur brute)
            min_weight: Poids minimum valide en unités calibrées
            max_weight: Poids maximum valide en unités calibrées
            unit: Unité de mesure ("g", "kg", etc.)
            moving_average_size: Taille de la fenêtre pour la moyenne mobile
        """
        self.name = name
        self.unit = unit
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.reference_unit = reference_unit
        self.moving_average_size = moving_average_size
        self.readings_history = []  # Pour la moyenne mobile
        
        # Initialisation du HX711
        self.hx = HX711(dout_pin, sck_pin)
        self.hx.set_scale(reference_unit)
        
        # Métadonnées du capteur
        self.last_reading_time = 0.0
        self.error_count = 0
        self.total_readings = 0
        
        logger.info(f"Capteur de poids '{name}' initialisé sur pins DOUT={dout_pin}, SCK={sck_pin}")

    def tare(self, times: int = 15) -> None:
        """
        Effectue la tare du capteur.
        
        Args:
            times: Nombre de lectures pour la tare
        """
        logger.info(f"Tare du capteur '{self.name}' en cours...")
        self.hx.tare(times)
        self.readings_history = []  # Réinitialiser l'historique après tare
        logger.info(f"Tare du capteur '{self.name}' terminée")

    def calibrate(self, known_weight: float, times: int = 15) -> float:
        """
        Calibre le capteur avec un poids connu.
        
        Args:
            known_weight: Poids de référence connu (dans l'unité spécifiée)
            times: Nombre de lectures pour la calibration
        
        Returns:
            float: Nouvelle valeur du facteur de calibration
        """
        logger.info(f"Calibration du capteur '{self.name}' avec poids de référence {known_weight}{self.unit}")
        self.tare(times)
        
        logger.info("Placez le poids de référence et attendez la stabilisation...")
        time.sleep(2)  # Attendre la stabilisation
        
        # Lire la valeur brute moyenne
        raw_value = self.hx.get_value(times)
        
        if abs(raw_value) < 1:
            logger.error("Valeur brute trop faible pour la calibration")
            raise ValueError("Valeur de calibration invalide")
        
        # Calculer le nouveau facteur de calibration
        new_reference_unit = raw_value / known_weight
        self.reference_unit = new_reference_unit
        self.hx.set_scale(new_reference_unit)
        
        logger.info(f"Calibration terminée, facteur = {new_reference_unit:.4f}")
        return new_reference_unit

    def get_raw_value(self, times: int = 3) -> float:
        """
        Lit la valeur brute du capteur (après soustraction de l'offset).
        
        Args:
            times: Nombre de lectures à moyenner
            
        Returns:
            float: Valeur brute
        """
        return self.hx.get_value(times)

    def get_weight(self, times: int = 3) -> float:
        """
        Lit le poids mesuré par le capteur.
        
        Args:
            times: Nombre de lectures à moyenner
            
        Returns:
            float: Poids dans l'unité configurée
        """
        try:
            weight = self.hx.get_units(times)
            weight = max(self.min_weight, min(weight, self.max_weight))  # Limiter aux bornes
            
            # Mettre à jour l'historique pour la moyenne mobile
            self.readings_history.append(weight)
            if len(self.readings_history) > self.moving_average_size:
                self.readings_history.pop(0)
            
            # Mettre à jour les statistiques
            self.last_reading_time = time.time()
            self.total_readings += 1
            
            return weight
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Erreur lors de la lecture du capteur '{self.name}': {e}")
            if self.readings_history:
                # En cas d'erreur, retourner la dernière valeur valide si disponible
                return self.readings_history[-1]
            return 0.0

    def get_moving_average(self) -> float:
        """
        Retourne la moyenne mobile des dernières lectures.
        
        Returns:
            float: Moyenne mobile
        """
        if not self.readings_history:
            return 0.0
        return sum(self.readings_history) / len(self.readings_history)

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du capteur.
        
        Returns:
            Dict: Informations sur l'état du capteur
        """
        return {
            "name": self.name,
            "unit": self.unit,
            "current_weight": self.get_moving_average() if self.readings_history else 0.0,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "reference_unit": self.reference_unit,
            "last_reading_time": self.last_reading_time,
            "error_count": self.error_count,
            "total_readings": self.total_readings,
            "reading_history": self.readings_history.copy() if len(self.readings_history) > 0 else []
        }

    def power_down(self) -> None:
        """Met le capteur en mode basse consommation."""
        self.hx.power_down()
        logger.debug(f"Capteur '{self.name}' mis en veille")

    def power_up(self) -> None:
        """Réveille le capteur du mode basse consommation."""
        self.hx.power_up()
        logger.debug(f"Capteur '{self.name}' réveillé")


class WeightSensorArray:
    """
    Gère un ensemble de capteurs de poids.
    
    Cette classe permet de gérer plusieurs capteurs de poids simultanément,
    facilitant l'intégration avec le système central.
    """
    
    def __init__(self) -> None:
        """Initialise un tableau de capteurs de poids vide."""
        self.sensors: Dict[str, WeightSensor] = {}
        logger.info("Tableau de capteurs de poids initialisé")

    def add_sensor(self, sensor: WeightSensor) -> None:
        """
        Ajoute un capteur au tableau.
        
        Args:
            sensor: Instance de WeightSensor à ajouter
        """
        if sensor.name in self.sensors:
            logger.warning(f"Capteur '{sensor.name}' remplacé dans le tableau")
        self.sensors[sensor.name] = sensor
        logger.info(f"Capteur '{sensor.name}' ajouté au tableau")

    def remove_sensor(self, sensor_name: str) -> None:
        """
        Retire un capteur du tableau.
        
        Args:
            sensor_name: Nom du capteur à retirer
        """
        if sensor_name in self.sensors:
            del self.sensors[sensor_name]
            logger.info(f"Capteur '{sensor_name}' retiré du tableau")
        else:
            logger.warning(f"Tentative de suppression d'un capteur inexistant: '{sensor_name}'")

    def get_sensor(self, sensor_name: str) -> Optional[WeightSensor]:
        """
        Récupère un capteur par son nom.
        
        Args:
            sensor_name: Nom du capteur à récupérer
        
        Returns:
            WeightSensor ou None si le capteur n'existe pas
        """
        return self.sensors.get(sensor_name)

    def get_all_weights(self) -> Dict[str, float]:
        """
        Lit les poids de tous les capteurs.
        
        Returns:
            Dict: Dictionnaire {nom_capteur: poids}
        """
        weights = {}
        for name, sensor in self.sensors.items():
            weights[name] = sensor.get_weight()
        return weights

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Récupère le statut de tous les capteurs.
        
        Returns:
            Dict: Dictionnaire {nom_capteur: statut}
        """
        statuses = {}
        for name, sensor in self.sensors.items():
            statuses[name] = sensor.get_status()
        return statuses

    def tare_all(self, times: int = 15) -> None:
        """
        Effectue la tare de tous les capteurs.
        
        Args:
            times: Nombre de lectures pour la tare
        """
        logger.info("Tare de tous les capteurs en cours...")
        for name, sensor in self.sensors.items():
            sensor.tare(times)
        logger.info("Tare de tous les capteurs terminée")

    def power_down_all(self) -> None:
        """Met tous les capteurs en mode basse consommation."""
        for sensor in self.sensors.values():
            sensor.power_down()
        logger.info("Tous les capteurs mis en veille")

    def power_up_all(self) -> None:
        """Réveille tous les capteurs du mode basse consommation."""
        for sensor in self.sensors.values():
            sensor.power_up()
        logger.info("Tous les capteurs réveillés")


if __name__ == "__main__":
    # Exemple d'utilisation pour tests
    logger.setLevel(logging.DEBUG)
    logger.info("Test du module de capteurs de poids")
    
    try:
        # Test d'un capteur individuel
        sensor = WeightSensor(
            name="test_bac_farine",
            dout_pin=5,
            sck_pin=6,
            reference_unit=1.0,
            min_weight=0.0,
            max_weight=5000.0,
            unit="g"
        )
        
        logger.info("Effectuer la tare du capteur...")
        sensor.tare()
        
        logger.info("Lecture du poids...")
        for i in range(5):
            weight = sensor.get_weight()
            logger.info(f"Lecture {i+1}: {weight:.2f}{sensor.unit}")
            time.sleep(1)
        
        # Test du tableau de capteurs
        logger.info("Test du tableau de capteurs...")
        array = WeightSensorArray()
        array.add_sensor(sensor)
        
        # Ajouter un second capteur pour le test
        sensor2 = WeightSensor(
            name="test_bac_sucre",
            dout_pin=17,
            sck_pin=18,
            reference_unit=1.0,
            min_weight=0.0,
            max_weight=2000.0,
            unit="g"
        )
        array.add_sensor(sensor2)
        
        # Lire tous les poids
        weights = array.get_all_weights()
        logger.info(f"Poids de tous les capteurs: {weights}")
        
        # Obtenir tous les statuts
        statuses = array.get_all_statuses()
        logger.info(f"Statuts de tous les capteurs: {statuses}")
        
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
    finally:
        # Nettoyage
        GPIO.cleanup()
        logger.info("Test terminé, GPIO nettoyé")
