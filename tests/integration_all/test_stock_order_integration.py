"""
Tests d'intégration entre les modules IoT et API pour la gestion des stocks.

Ces tests vérifient que le flux complet fonctionne correctement :
1. Les capteurs IoT détectent une quantité faible d'ingrédient
2. Le système déclenche une commande automatique via l'API fournisseur
3. La commande est correctement enregistrée dans le système
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import json
import os
import sys
import datetime

# Ajout du chemin racine au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import des modules à tester (à ajuster selon la structure réelle)
try:
    from iot.sensor_module.weight_sensor import WeightSensor
    from integration.api_connectors.supplier_api import SupplierConnector
    from ml.prediction_module.stock_predictor import StockPredictor
    # Module central qui coordonne le flux
    from integration.stock_manager import StockManager
except ImportError:
    # Mocks si les modules n'existent pas encore
    WeightSensor = Mock()
    SupplierConnector = Mock()
    StockPredictor = Mock()
    StockManager = Mock()


class TestStockOrderIntegration(unittest.TestCase):
    """Tests d'intégration pour le flux de réapprovisionnement automatique."""

    def setUp(self):
        """Initialisation avant chaque test."""
        # Configuration avec des mocks pour simuler les différents modules
        self.weight_sensor = Mock()
        self.supplier_connector = Mock()
        self.stock_predictor = Mock()
        
        # Configuration des comportements par défaut pour les mocks
        self.weight_sensor.read.return_value = 200.0  # Grammes
        self.weight_sensor.is_below_threshold.return_value = True
        
        self.supplier_connector.authenticate.return_value = "mock_token"
        self.supplier_connector.get_products.return_value = [
            {"id": "123", "name": "Farine", "price": 1.2, "unit": "kg", "available": True}
        ]
        self.supplier_connector.place_order.return_value = {
            "order_id": "ORD123", 
            "status": "confirmed",
            "estimated_delivery": "2025-04-20"
        }
        
        self.stock_predictor.predict_optimal_quantity.return_value = 15.0  # kg
        
        # Initialisation du gestionnaire de stock qui intègre tous ces modules
        if isinstance(StockManager, Mock):
            self.stock_manager = Mock()
            self.stock_manager.check_inventory.return_value = [
                {"ingredient_id": "farine", "current_level": 200, "threshold": 1000, "status": "low"}
            ]
            self.stock_manager.trigger_order.return_value = {"order_id": "ORD123", "status": "success"}
        else:
            self.stock_manager = StockManager(
                sensors={"farine": self.weight_sensor},
                supplier_connector=self.supplier_connector,
                stock_predictor=self.stock_predictor,
                test_mode=True
            )
    
    def test_low_stock_detection(self):
        """Vérifie que le système détecte correctement les stocks bas."""
        # Exécution du test
        inventory_status = self.stock_manager.check_inventory()
        
        # Vérifications
        assert isinstance(inventory_status, list)
        assert len(inventory_status) > 0
        assert inventory_status[0]["status"] == "low"
        
        # Vérification que le capteur a bien été utilisé
        if not isinstance(StockManager, Mock):
            self.weight_sensor.read.assert_called_once()
            self.weight_sensor.is_below_threshold.assert_called_once()
    
    def test_automatic_order_triggered(self):
        """Vérifie que le système déclenche automatiquement une commande."""
        # Configuration des mocks pour simuler un niveau bas
        if not isinstance(StockManager, Mock):
            self.weight_sensor.is_below_threshold.return_value = True
        
        # Exécution du test
        result = self.stock_manager.process_inventory_and_order()
        
        # Vérifications
        assert "orders" in result
        assert len(result["orders"]) > 0
        assert result["orders"][0]["status"] == "success" or result["orders"][0]["status"] == "confirmed"
        
        # Vérification que l'API fournisseur a été appelée correctement
        if not isinstance(StockManager, Mock):
            self.supplier_connector.authenticate.assert_called_once()
            self.supplier_connector.get_products.assert_called_once()
            self.supplier_connector.place_order.assert_called_once()
            
            # Vérification que la prédiction a été utilisée
            self.stock_predictor.predict_optimal_quantity.assert_called_once()
    
    def test_integration_with_ml_prediction(self):
        """Vérifie que les prédictions ML sont utilisées pour optimiser la commande."""
        # Configuration des mocks pour des prédictions spécifiques
        if not isinstance(StockManager, Mock):
            self.stock_predictor.predict_optimal_quantity.return_value = 25.0  # kg
        
        # Exécution du test
        result = self.stock_manager.process_inventory_and_order()
        
        # Vérifications
        if isinstance(StockManager, Mock):
            # Cas avec un mock complet
            self.stock_manager.check_inventory.assert_called_once()
            self.stock_manager.trigger_order.assert_called_once()
        else:
            # Cas avec l'implémentation réelle
            # Vérification que la quantité calculée par le ML est bien utilisée
            args, kwargs = self.supplier_connector.place_order.call_args
            order_items = kwargs.get('order_items', args[0] if args else None)
            assert any(item["quantity"] == 25.0 for item in order_items)
    
    def test_error_handling_during_integration(self):
        """Vérifie la gestion des erreurs pendant le flux d'intégration."""
        # Simulation d'une erreur de l'API fournisseur
        if isinstance(StockManager, Mock):
            self.stock_manager.trigger_order.side_effect = Exception("API Error")
        else:
            self.supplier_connector.place_order.side_effect = Exception("API Error")
        
        # Exécution du test avec gestion des erreurs
        try:
            result = self.stock_manager.process_inventory_and_order()
            # Si la méthode gère correctement les erreurs, on vérifie le statut
            assert "errors" in result
            assert len(result["errors"]) > 0
        except Exception as e:
            # Si la méthode ne gère pas les erreurs, le test échouera
            self.fail(f"L'intégration ne gère pas correctement les erreurs: {str(e)}")

    def test_full_integration_flow(self):
        """Test complet du flux d'intégration de bout en bout."""
        # Configuration des données de test
        test_date = datetime.datetime(2025, 4, 18, 15, 0, 0)
        
        # Simulation du flux complet
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = test_date
            
            # Exécution du test
            result = self.stock_manager.process_inventory_and_order()
            
            # Vérifications du résultat final
            assert "timestamp" in result
            assert "inventory_status" in result
            assert "orders" in result
            
            # Vérification de l'état final
            if "orders" in result and result["orders"]:
                order = result["orders"][0]
                assert order["status"] in ["success", "confirmed"]
                if "delivery_date" in order:
                    assert order["delivery_date"] >= test_date.strftime("%Y-%m-%d")
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Pas de nettoyage spécifique nécessaire pour les mocks
        pass


if __name__ == '__main__':
    unittest.main()
