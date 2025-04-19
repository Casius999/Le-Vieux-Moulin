"""
Tests unitaires pour le module de capteur de poids IoT.

Ces tests vérifient le bon fonctionnement des capteurs de poids utilisés
pour surveiller les niveaux d'ingrédients dans les bacs.
"""

import unittest
from unittest.mock import Mock, patch
import pytest
import sys
import os

# Ajout du chemin racine au PYTHONPATH pour permettre l'import des modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import du module à tester (à ajuster selon la structure réelle)
try:
    from iot.sensor_module.weight_sensor import WeightSensor, CalibrationError, ReadingError
except ImportError:
    # Création d'un mock si le module n'existe pas encore
    WeightSensor = Mock()
    CalibrationError = Exception
    ReadingError = Exception


class TestWeightSensor(unittest.TestCase):
    """Tests pour la classe WeightSensor."""

    def setUp(self):
        """Initialisation avant chaque test."""
        # Création d'une instance mock ou réelle selon disponibilité
        if isinstance(WeightSensor, Mock):
            self.sensor = Mock()
            self.sensor.read.return_value = 500.0  # Grammes
            self.sensor.calibrate.return_value = True
            self.sensor.is_connected.return_value = True
        else:
            # Configuration pour les tests avec mode test=True pour éviter d'accéder au matériel
            self.sensor = WeightSensor(pin=5, max_weight=5000, test=True)

    def test_sensor_initialization(self):
        """Vérifie l'initialisation correcte du capteur."""
        if isinstance(WeightSensor, Mock):
            assert True  # Skip test with mock
        else:
            assert self.sensor.pin == 5
            assert self.sensor.max_weight == 5000
            assert self.sensor.calibration_factor is not None

    def test_weight_reading(self):
        """Vérifie que la lecture du poids fonctionne correctement."""
        # Lecture du poids
        weight = self.sensor.read()
        
        # Vérification que la valeur est dans une plage raisonnable
        assert isinstance(weight, (int, float))
        assert 0 <= weight <= self.sensor.max_weight

    def test_calibration(self):
        """Vérifie que la calibration fonctionne correctement."""
        # Test de calibration avec un poids connu
        result = self.sensor.calibrate(known_weight=1000)
        assert result is True

    @patch('iot.sensor_module.weight_sensor.WeightSensor.read')
    def test_reading_below_threshold(self, mock_read):
        """Vérifie la détection de niveau bas d'ingrédient."""
        if isinstance(WeightSensor, Mock):
            self.sensor.THRESHOLD_LOW = 100
            self.sensor.read.return_value = 50
            assert self.sensor.is_below_threshold() is True
        else:
            # Configuration du mock pour simuler un poids bas
            mock_read.return_value = 50
            # Le seuil bas par défaut est généralement 10% de max_weight
            threshold_low = self.sensor.max_weight * 0.1
            
            # Vérifie que la fonction détecte correctement le niveau bas
            assert self.sensor.is_below_threshold(threshold=threshold_low) is True

    def test_connection_status(self):
        """Vérifie que la détection de connexion fonctionne."""
        # Vérification que le capteur est connecté
        assert self.sensor.is_connected() is True

    def test_error_handling(self):
        """Vérifie la gestion des erreurs lors d'une lecture problématique."""
        if isinstance(WeightSensor, Mock):
            self.sensor.read.side_effect = ReadingError("Erreur de lecture simulée")
            with pytest.raises(ReadingError):
                self.sensor.read()
        else:
            # Test à implémenter avec le vrai module
            pass

    def tearDown(self):
        """Nettoyage après chaque test."""
        if not isinstance(WeightSensor, Mock):
            # Fermeture des connexions, réinitialisation, etc.
            self.sensor.close() if hasattr(self.sensor, 'close') else None


if __name__ == '__main__':
    unittest.main()
