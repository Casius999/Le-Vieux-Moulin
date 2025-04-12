#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion du capteur de niveau d'huile pour Le Vieux Moulin.

Ce module gère le capteur ultrasonique et la sonde de température utilisés
pour mesurer le niveau et la qualité de l'huile dans la friteuse du restaurant.
Il fournit des mesures précises et des alertes en temps réel.

Classes:
    OilQualitySensor: Capteur de qualité d'huile basé sur la turbidité et la température
    OilLevelSensor: Capteur de niveau d'huile basé sur un capteur ultrasonique
    FryerMonitor: Classe principale qui combine niveau et qualité

Exemples d'utilisation:
    >>> from oil_level_sensor import FryerMonitor
    >>> monitor = FryerMonitor(
    ...     fryer_name="friteuse_principale",
    ...     ultrasonic_trigger_pin=23,
    ...     ultrasonic_echo_pin=24,
    ...     temp_pin=4,
    ...     turbidity_pin=17
    ... )
    >>> status = monitor.get_status()  # Obtient l'état complet de la friteuse
"""

import time
import logging
import math
from typing import Dict, List, Optional, Tuple, Union, Any
import RPi.GPIO as GPIO  # Pour Raspberry Pi
# Pour ESP32, utilisez plutôt machine.Pin
# from machine import Pin, ADC

# Configurez one-wire pour le capteur DS18B20
import os
import glob

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class OilQualitySensor:
    """
    Capteur de qualité d'huile basé sur la turbidité et la température.
    
    Ce capteur combine une sonde de température (DS18B20) et un capteur 
    de turbidité optique pour évaluer la qualité de l'huile.
    """
    
    # Constantes pour l'évaluation de la qualité
    MAX_TEMP = 180.0  # Température maximale acceptable en °C
    MIN_TEMP = 10.0   # Température minimale acceptable en °C
    MAX_USAGE_HOURS = 72.0  # Durée maximale recommandée d'utilisation de l'huile
    
    def __init__(
        self, 
        name: str,
        temp_pin: int, 
        turbidity_pin: Optional[int] = None, 
        temp_offset: float = 0.0
    ) -> None:
        """
        Initialise le capteur de qualité d'huile.
        
        Args:
            name: Nom identifiant le capteur (ex: "friteuse_principale_qualite")
            temp_pin: Pin GPIO pour le capteur de température DS18B20
            turbidity_pin: Pin GPIO pour le capteur de turbidité (optionnel)
            temp_offset: Correction de température à appliquer (en °C)
        """
        self.name = name
        self.temp_pin = temp_pin
        self.turbidity_pin = turbidity_pin
        self.temp_offset = temp_offset
        
        # Initialiser la sonde de température DS18B20
        self._init_temp_sensor()
        
        # Initialiser le capteur de turbidité si présent
        if self.turbidity_pin is not None:
            self._init_turbidity_sensor()
        
        # État interne du capteur
        self.last_reading_time = 0.0
        self.error_count = 0
        self.total_readings = 0
        self.usage_hours = 0.0  # Compteur d'heures d'utilisation depuis le dernier changement
        self.max_temp_recorded = 0.0
        self.readings_history = []  # Historique des lectures pour moyenne mobile
        
        logger.info(f"Capteur de qualité d'huile '{name}' initialisé avec temp_pin={temp_pin}, turbidity_pin={turbidity_pin}")

    def _init_temp_sensor(self) -> None:
        """
        Initialise le capteur de température DS18B20.
        
        Pour Raspberry Pi, configure le bus 1-Wire et détecte les capteurs.
        Pour ESP32, il faudrait adapter cette méthode.
        """
        # Initialiser le bus 1-Wire sur GPIO temp_pin
        os.system(f'modprobe w1-gpio gpiopin={self.temp_pin}')
        os.system('modprobe w1-therm')
        
        # Attendre l'initialisation
        time.sleep(1)
        
        # Rechercher les capteurs de température
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
        
        if not device_folders:
            logger.error(f"Aucun capteur DS18B20 trouvé sur le pin {self.temp_pin}")
            self.device_file = None
        else:
            self.device_file = device_folders[0] + '/w1_slave'
            logger.info(f"Capteur DS18B20 trouvé: {device_folders[0]}")

    def _init_turbidity_sensor(self) -> None:
        """
        Initialise le capteur de turbidité analogique.
        """
        # Pour Raspberry Pi, configurer comme entrée analogique via ADC externe
        GPIO.setup(self.turbidity_pin, GPIO.IN)
        
        # Pour ESP32 avec ADC intégré:
        # self.turbidity_adc = ADC(Pin(self.turbidity_pin))
        # self.turbidity_adc.atten(ADC.ATTN_11DB)  # Plage 0-3.3V

    def _read_temp_raw(self) -> Optional[List[str]]:
        """
        Lit les données brutes du capteur de température.
        
        Returns:
            Liste des lignes lues du capteur ou None en cas d'erreur
        """
        if self.device_file is None:
            return None
            
        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
            return lines
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du capteur de température: {e}")
            return None

    def read_temperature(self) -> Optional[float]:
        """
        Lit la température de l'huile en degrés Celsius.
        
        Returns:
            Température en °C ou None en cas d'erreur
        """
        lines = self._read_temp_raw()
        if lines is None:
            return None
            
        # Vérifier que la lecture est valide
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_temp_raw()
            if lines is None:
                return None
        
        # Extraire la température
        equals_pos = lines[1].find('t=')
        if equals_pos == -1:
            return None
            
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        
        # Appliquer l'offset de correction
        temp_c += self.temp_offset
        
        # Mettre à jour la température maximale enregistrée
        if temp_c > self.max_temp_recorded:
            self.max_temp_recorded = temp_c
            
        return temp_c

    def read_turbidity(self) -> Optional[float]:
        """
        Lit la turbidité de l'huile (clarté).
        
        Returns:
            Valeur de turbidité normalisée (0-100%) ou None si non disponible
            0% = très trouble, 100% = parfaitement claire
        """
        if self.turbidity_pin is None:
            return None
            
        try:
            # Cette implémentation dépend du type de capteur utilisé
            # Pour un capteur analogique sur ADC:
            
            # Faire plusieurs lectures pour stabiliser
            readings = []
            for _ in range(10):
                # Pour ESP32 avec ADC:
                # raw_value = self.turbidity_adc.read()
                
                # Simulation pour Raspberry Pi (remplacer par une lecture réelle)
                raw_value = 2048  # Valeur milieu de plage (12 bits)
                readings.append(raw_value)
                time.sleep(0.01)
                
            # Calculer la moyenne
            avg_value = sum(readings) / len(readings)
            
            # Normaliser à 0-100%
            # Supposons que 0 = très trouble et 4095 = parfaitement clair (12 bits)
            turbidity_percent = (avg_value / 4095) * 100
            
            return turbidity_percent
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la turbidité: {e}")
            return None

    def update_usage_hours(self, hours_increment: float) -> None:
        """
        Met à jour le compteur d'heures d'utilisation de l'huile.
        
        Args:
            hours_increment: Nombre d'heures à ajouter au compteur
        """
        self.usage_hours += hours_increment
        logger.debug(f"Compteur d'heures d'utilisation mis à jour: {self.usage_hours:.1f}h")

    def reset_usage_counter(self) -> None:
        """Réinitialise le compteur d'heures d'utilisation (après changement d'huile)."""
        self.usage_hours = 0.0
        self.max_temp_recorded = 0.0
        logger.info(f"Compteur d'utilisation d'huile réinitialisé pour '{self.name}'")

    def evaluate_quality(self, temp: Optional[float] = None, turbidity: Optional[float] = None) -> Dict[str, Any]:
        """
        Évalue la qualité globale de l'huile.
        
        Args:
            temp: Température en °C (si None, sera lue)
            turbidity: Turbidité normalisée (si None, sera lue si disponible)
            
        Returns:
            Dict: État de qualité avec évaluation et recommandations
        """
        # Lire les valeurs si non fournies
        if temp is None:
            temp = self.read_temperature()
            
        if turbidity is None and self.turbidity_pin is not None:
            turbidity = self.read_turbidity()
        
        # Initialiser l'état par défaut
        quality_state = {
            "quality_percent": 100.0,  # Diminuera selon les facteurs
            "temperature_status": "normal",
            "clarity_status": "unknown" if turbidity is None else "normal",
            "usage_status": "normal",
            "needs_replacement": False,
            "warnings": [],
            "temperature": temp,
            "turbidity": turbidity,
            "usage_hours": self.usage_hours,
            "max_temp_recorded": self.max_temp_recorded
        }
        
        # Évaluer la température
        if temp is not None:
            if temp > self.MAX_TEMP:
                quality_state["temperature_status"] = "critical"
                quality_state["quality_percent"] -= 40.0
                quality_state["warnings"].append(
                    f"Température critique ({temp:.1f}°C > {self.MAX_TEMP}°C)"
                )
                quality_state["needs_replacement"] = True
            elif temp > (self.MAX_TEMP * 0.9):
                quality_state["temperature_status"] = "warning"
                quality_state["quality_percent"] -= 20.0
                quality_state["warnings"].append(
                    f"Température élevée ({temp:.1f}°C)"
                )
        
        # Évaluer la turbidité (clarté)
        if turbidity is not None:
            if turbidity < 30.0:  # Très trouble
                quality_state["clarity_status"] = "critical"
                quality_state["quality_percent"] -= 30.0
                quality_state["warnings"].append(
                    f"Huile très trouble (clarté: {turbidity:.1f}%)"
                )
                quality_state["needs_replacement"] = True
            elif turbidity < 60.0:  # Trouble
                quality_state["clarity_status"] = "warning"
                quality_state["quality_percent"] -= 15.0
                quality_state["warnings"].append(
                    f"Huile trouble (clarté: {turbidity:.1f}%)"
                )
        
        # Évaluer les heures d'utilisation
        if self.usage_hours > self.MAX_USAGE_HOURS:
            quality_state["usage_status"] = "critical"
            quality_state["quality_percent"] -= 30.0
            quality_state["warnings"].append(
                f"Durée d'utilisation maximale dépassée ({self.usage_hours:.1f}h > {self.MAX_USAGE_HOURS}h)"
            )
            quality_state["needs_replacement"] = True
        elif self.usage_hours > (self.MAX_USAGE_HOURS * 0.8):
            quality_state["usage_status"] = "warning"
            quality_state["quality_percent"] -= 15.0
            quality_state["warnings"].append(
                f"Durée d'utilisation élevée ({self.usage_hours:.1f}h)"
            )
        
        # Limiter la qualité globale à 0-100%
        quality_state["quality_percent"] = max(0.0, min(100.0, quality_state["quality_percent"]))
        
        return quality_state

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne l'état complet du capteur de qualité d'huile.
        
        Returns:
            Dict: État complet avec lectures et évaluation
        """
        # Lire température et turbidité
        temp = self.read_temperature()
        turbidity = self.read_turbidity() if self.turbidity_pin is not None else None
        
        # Mettre à jour les statistiques
        self.last_reading_time = time.time()
        self.total_readings += 1
        
        # Évaluer la qualité
        quality_state = self.evaluate_quality(temp, turbidity)
        
        # Construire l'état complet
        status = {
            "name": self.name,
            "last_reading_time": self.last_reading_time,
            "error_count": self.error_count,
            "total_readings": self.total_readings,
            "quality_state": quality_state
        }
        
        return status


class OilLevelSensor:
    """
    Capteur de niveau d'huile basé sur un capteur ultrasonique.
    
    Utilise un capteur HC-SR04 pour mesurer la distance entre le haut 
    de la friteuse et la surface de l'huile.
    """
    
    # Vitesse du son dans l'air à température ambiante (en cm/µs)
    SOUND_VELOCITY = 0.0343
    
    def __init__(
        self, 
        name: str,
        trigger_pin: int, 
        echo_pin: int,
        fryer_depth: float = 20.0,  # cm
        min_level: float = 2.0,     # cm du fond
        max_level: float = 18.0,    # cm du fond
        max_capacity: float = 10.0, # litres
        sensor_height: float = 5.0, # cm au-dessus du bord
        moving_average_size: int = 5
    ) -> None:
        """
        Initialise le capteur de niveau d'huile.
        
        Args:
            name: Nom identifiant le capteur (ex: "friteuse_principale_niveau")
            trigger_pin: Pin GPIO pour le trigger du capteur ultrasonique
            echo_pin: Pin GPIO pour l'echo du capteur ultrasonique
            fryer_depth: Profondeur totale de la friteuse en cm
            min_level: Niveau minimum acceptable en cm depuis le fond
            max_level: Niveau maximum acceptable en cm depuis le fond
            max_capacity: Capacité maximale de la friteuse en litres
            sensor_height: Hauteur du capteur par rapport au bord supérieur en cm
            moving_average_size: Taille de la fenêtre pour la moyenne mobile
        """
        self.name = name
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.fryer_depth = fryer_depth
        self.min_level = min_level
        self.max_level = max_level
        self.max_capacity = max_capacity
        self.sensor_height = sensor_height
        self.moving_average_size = moving_average_size
        
        # Calculer la distance totale du capteur au fond
        self.total_distance = self.fryer_depth + self.sensor_height
        
        # Initialiser le capteur ultrasonique
        self._init_ultrasonic_sensor()
        
        # État interne du capteur
        self.last_reading_time = 0.0
        self.error_count = 0
        self.total_readings = 0
        self.readings_history = []  # Pour la moyenne mobile
        
        logger.info(f"Capteur de niveau d'huile '{name}' initialisé avec trigger_pin={trigger_pin}, echo_pin={echo_pin}")

    def _init_ultrasonic_sensor(self) -> None:
        """
        Initialise le capteur ultrasonique HC-SR04.
        """
        # Configuration pour Raspberry Pi
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Pour ESP32:
        # self.trigger = Pin(self.trigger_pin, Pin.OUT)
        # self.echo = Pin(self.echo_pin, Pin.IN)
        
        # Assurer que le trigger est bas
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.1)  # Attendre la stabilisation du capteur
        
        logger.debug(f"Capteur ultrasonique initialisé sur trigger={self.trigger_pin}, echo={self.echo_pin}")

    def measure_distance(self) -> Optional[float]:
        """
        Mesure la distance entre le capteur et la surface de l'huile.
        
        Returns:
            float: Distance en cm ou None en cas d'erreur
        """
        try:
            # Envoyer une impulsion de 10µs au trigger
            GPIO.output(self.trigger_pin, True)
            time.sleep(0.00001)  # 10µs
            GPIO.output(self.trigger_pin, False)
            
            # Mesurer le temps d'aller-retour de l'écho
            start_time = time.time()
            timeout = start_time + 1.0  # Timeout de 1 seconde
            
            # Attendre que l'écho devienne haut
            while GPIO.input(self.echo_pin) == 0:
                if time.time() > timeout:
                    raise TimeoutError("Timeout en attendant l'écho (montée)")
                pass
            
            pulse_start = time.time()
            
            # Attendre que l'écho devienne bas
            while GPIO.input(self.echo_pin) == 1:
                if time.time() > timeout:
                    raise TimeoutError("Timeout en attendant l'écho (descente)")
                pass
                
            pulse_end = time.time()
            
            # Calculer la durée de l'impulsion
            pulse_duration = pulse_end - pulse_start
            
            # Calculer la distance en cm
            distance = pulse_duration * 1000000 / 2 * self.SOUND_VELOCITY
            
            # Vérifier que la mesure est dans une plage raisonnable
            if distance < 0 or distance > 400:  # Limite du HC-SR04
                logger.warning(f"Mesure de distance hors plage: {distance:.2f} cm")
                return None
                
            return distance
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Erreur lors de la mesure de distance: {e}")
            return None

    def read_oil_level(self) -> Optional[float]:
        """
        Lit le niveau d'huile en cm depuis le fond de la friteuse.
        
        Returns:
            float: Niveau d'huile en cm depuis le fond ou None en cas d'erreur
        """
        # Mesurer la distance entre le capteur et la surface de l'huile
        distance = self.measure_distance()
        if distance is None:
            return None
            
        # Calculer le niveau d'huile: distance totale - distance mesurée = niveau depuis le fond
        oil_level = self.total_distance - distance
        
        # Limiter aux bornes physiques de la friteuse
        oil_level = max(0.0, min(oil_level, self.fryer_depth))
        
        # Mettre à jour l'historique pour la moyenne mobile
        self.readings_history.append(oil_level)
        if len(self.readings_history) > self.moving_average_size:
            self.readings_history.pop(0)
        
        # Mettre à jour les statistiques
        self.last_reading_time = time.time()
        self.total_readings += 1
        
        return oil_level

    def get_oil_volume(self) -> Optional[float]:
        """
        Estime le volume d'huile dans la friteuse en litres.
        
        Returns:
            float: Volume d'huile en litres ou None en cas d'erreur
        """
        oil_level = self.get_average_level()
        if oil_level is None:
            return None
            
        # Calculer le ratio de remplissage
        fill_ratio = oil_level / self.fryer_depth
        
        # Calculer le volume estimé
        volume = fill_ratio * self.max_capacity
        
        return volume

    def get_average_level(self) -> Optional[float]:
        """
        Retourne la moyenne mobile du niveau d'huile.
        
        Returns:
            float: Niveau moyen en cm depuis le fond ou None si aucune donnée
        """
        if not self.readings_history:
            return None
        return sum(self.readings_history) / len(self.readings_history)

    def evaluate_level(self) -> Dict[str, Any]:
        """
        Évalue le niveau d'huile et génère des alertes si nécessaire.
        
        Returns:
            Dict: État du niveau avec évaluation et alertes
        """
        level = self.get_average_level()
        
        # Initialiser l'état par défaut
        level_state = {
            "level_cm": level,
            "level_percent": None,
            "volume_liters": None,
            "status": "unknown" if level is None else "normal",
            "warnings": []
        }
        
        if level is not None:
            # Calculer le pourcentage de remplissage
            level_percent = (level / self.fryer_depth) * 100
            level_state["level_percent"] = level_percent
            
            # Calculer le volume
            volume = self.get_oil_volume()
            level_state["volume_liters"] = volume
            
            # Évaluer le niveau
            if level < self.min_level:
                level_state["status"] = "low"
                level_state["warnings"].append(
                    f"Niveau d'huile trop bas ({level:.1f} cm < {self.min_level} cm)"
                )
            elif level > self.max_level:
                level_state["status"] = "high"
                level_state["warnings"].append(
                    f"Niveau d'huile trop élevé ({level:.1f} cm > {self.max_level} cm)"
                )
        
        return level_state

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne l'état complet du capteur de niveau d'huile.
        
        Returns:
            Dict: État complet avec lectures et évaluation
        """
        # Faire une lecture fraîche
        self.read_oil_level()
        
        # Évaluer le niveau
        level_state = self.evaluate_level()
        
        # Construire l'état complet
        status = {
            "name": self.name,
            "last_reading_time": self.last_reading_time,
            "error_count": self.error_count,
            "total_readings": self.total_readings,
            "readings_history": self.readings_history.copy() if self.readings_history else [],
            "level_state": level_state
        }
        
        return status


class FryerMonitor:
    """
    Classe principale qui combine les capteurs de niveau et de qualité d'huile.
    
    Cette classe fournit une interface unifiée pour surveiller tous les aspects
    d'une friteuse: niveau d'huile, température, qualité, durée d'utilisation.
    """
    
    def __init__(
        self,
        fryer_name: str,
        ultrasonic_trigger_pin: int,
        ultrasonic_echo_pin: int,
        temp_pin: int,
        turbidity_pin: Optional[int] = None,
        fryer_depth: float = 20.0,  # cm
        min_level: float = 2.0,     # cm du fond
        max_level: float = 18.0,    # cm du fond
        max_capacity: float = 10.0  # litres
    ) -> None:
        """
        Initialise le moniteur de friteuse complet.
        
        Args:
            fryer_name: Nom identifiant la friteuse
            ultrasonic_trigger_pin: Pin GPIO pour le trigger du capteur ultrasonique
            ultrasonic_echo_pin: Pin GPIO pour l'echo du capteur ultrasonique
            temp_pin: Pin GPIO pour le capteur de température DS18B20
            turbidity_pin: Pin GPIO pour le capteur de turbidité (optionnel)
            fryer_depth: Profondeur totale de la friteuse en cm
            min_level: Niveau minimum acceptable en cm depuis le fond
            max_level: Niveau maximum acceptable en cm depuis le fond
            max_capacity: Capacité maximale de la friteuse en litres
        """
        self.name = fryer_name
        
        # Initialiser le capteur de niveau
        self.level_sensor = OilLevelSensor(
            name=f"{fryer_name}_level",
            trigger_pin=ultrasonic_trigger_pin,
            echo_pin=ultrasonic_echo_pin,
            fryer_depth=fryer_depth,
            min_level=min_level,
            max_level=max_level,
            max_capacity=max_capacity
        )
        
        # Initialiser le capteur de qualité
        self.quality_sensor = OilQualitySensor(
            name=f"{fryer_name}_quality",
            temp_pin=temp_pin,
            turbidity_pin=turbidity_pin
        )
        
        # État interne du moniteur
        self.last_oil_change = time.time()
        self.operating_status = "idle"  # idle, heating, ready, error
        self.last_update_time = 0.0
        
        logger.info(f"Moniteur de friteuse '{fryer_name}' initialisé avec succès")

    def update(self) -> None:
        """
        Met à jour les lectures de tous les capteurs.
        """
        # Lire le niveau d'huile
        self.level_sensor.read_oil_level()
        
        # Lire la température et la turbidité
        temp = self.quality_sensor.read_temperature()
        _ = self.quality_sensor.read_turbidity()
        
        # Mettre à jour l'état de fonctionnement
        if temp is not None:
            # Déterminer l'état basé sur la température
            if temp < 100.0:
                self.operating_status = "idle"
            elif temp < 160.0:
                self.operating_status = "heating"
            elif temp <= 180.0:
                self.operating_status = "ready"
            else:
                self.operating_status = "overheated"
        
        # Calculer le temps écoulé depuis la dernière mise à jour
        now = time.time()
        if self.last_update_time > 0:
            elapsed_hours = (now - self.last_update_time) / 3600.0
            
            # Si la friteuse est active (en chauffe ou prête), 
            # mettre à jour le compteur d'heures d'utilisation
            if self.operating_status in ["heating", "ready", "overheated"]:
                self.quality_sensor.update_usage_hours(elapsed_hours)
        
        self.last_update_time = now
        logger.debug(f"Mise à jour du moniteur '{self.name}' terminée. État: {self.operating_status}")

    def register_oil_change(self) -> None:
        """
        Enregistre un changement d'huile, réinitialisant les compteurs.
        """
        self.last_oil_change = time.time()
        self.quality_sensor.reset_usage_counter()
        logger.info(f"Changement d'huile enregistré pour '{self.name}'")

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne l'état complet de la friteuse.
        
        Returns:
            Dict: État complet avec niveau, qualité et statut opérationnel
        """
        # Mettre à jour les lectures
        self.update()
        
        # Obtenir les états des capteurs
        level_status = self.level_sensor.get_status()
        quality_status = self.quality_sensor.get_status()
        
        # Construire le statut complet
        status = {
            "name": self.name,
            "operating_status": self.operating_status,
            "last_update_time": self.last_update_time,
            "last_oil_change": self.last_oil_change,
            "time_since_oil_change": (time.time() - self.last_oil_change) / 3600.0,  # heures
            "level": level_status["level_state"],
            "quality": quality_status["quality_state"],
            "needs_attention": (
                level_status["level_state"]["status"] != "normal" or
                quality_status["quality_state"]["needs_replacement"]
            ),
            "warnings": (
                level_status["level_state"]["warnings"] +
                quality_status["quality_state"]["warnings"]
            )
        }
        
        return status


if __name__ == "__main__":
    # Exemple d'utilisation pour tests
    logger.setLevel(logging.DEBUG)
    logger.info("Test du module de capteur de niveau d'huile")
    
    try:
        # Tester le moniteur de friteuse complet
        fryer = FryerMonitor(
            fryer_name="test_friteuse",
            ultrasonic_trigger_pin=23,
            ultrasonic_echo_pin=24,
            temp_pin=4,
            turbidity_pin=17,
            fryer_depth=15.0,
            min_level=3.0,
            max_level=13.0,
            max_capacity=8.0
        )
        
        # Obtenir l'état complet
        status = fryer.get_status()
        logger.info(f"État de la friteuse: {status}")
        
        # Simuler un fonctionnement pendant quelques cycles
        for i in range(3):
            logger.info(f"Cycle de test {i+1}")
            fryer.update()
            time.sleep(1)
        
        # Simuler un changement d'huile
        logger.info("Simulation d'un changement d'huile")
        fryer.register_oil_change()
        
        # Vérifier l'état final
        final_status = fryer.get_status()
        logger.info(f"État final: {final_status}")
        
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
    finally:
        # Nettoyage
        GPIO.cleanup()
        logger.info("Test terminé, GPIO nettoyé")
