#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests unitaires pour le modèle de prévision des stocks.

Ces tests vérifient que le modèle StockForecaster fonctionne correctement:
- Prévision avec différents paramètres
- Gestion des erreurs
- Comportement avec des données historiques variées
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Ajouter le répertoire parent au path pour permettre l'import des modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import du modèle à tester
from prediction_module.models.stock_forecaster import StockForecaster


class TestStockForecaster(unittest.TestCase):
    """
    Tests unitaires pour StockForecaster.
    """
    
    def setUp(self):
        """
        Préparation des tests: création des données factices et du modèle.
        """
        # Créer un jeu de données factice
        self.dates = pd.date_range(start='2024-01-01', periods=60)
        self.ingredients = ['farine', 'tomate', 'mozzarella', 'huile_olive']
        
        np.random.seed(42)
        self.data = np.random.normal(loc=[50, 30, 20, 5], scale=[10, 5, 3, 1], size=(60, 4))
        
        # Ajout de saisonnalité (plus de ventes le weekend)
        for i, date in enumerate(self.dates):
            if date.weekday() >= 5:  # Weekend
                self.data[i] *= 1.5
        
        self.historical_data = pd.DataFrame(self.data, index=self.dates, columns=self.ingredients)
        self.historical_data['date'] = self.dates
        
        # Initialiser le modèle sans chemin (sera simulé par les mocks)
        self.forecaster = StockForecaster(lookback_days=30)
        
        # Ajouter un modèle fictif (MockLSTMModel) au forecaster pour les tests
        from prediction_module.models.stock_forecaster import MockLSTMModel
        self.forecaster.model = MockLSTMModel()
    
    def test_initialization(self):
        """
        Teste l'initialisation du modèle avec différents paramètres.
        """
        # Test avec les paramètres par défaut
        forecaster = StockForecaster()
        self.assertEqual(forecaster.default_horizon, 7)
        self.assertEqual(forecaster.lookback_days, 30)
        
        # Test avec des paramètres personnalisés
        forecaster = StockForecaster(default_horizon=14, lookback_days=60)
        self.assertEqual(forecaster.default_horizon, 14)
        self.assertEqual(forecaster.lookback_days, 60)
    
    def test_predict_with_valid_data(self):
        """
        Teste la méthode de prédiction avec des données valides.
        """
        # Prédiction avec les paramètres par défaut
        predictions = self.forecaster.predict(
            historical_data=self.historical_data,
            ingredients=self.ingredients
        )
        
        # Vérifications basiques
        self.assertIsInstance(predictions, dict)
        self.assertEqual(len(predictions), 7)  # Horizon par défaut = 7 jours
        
        # Vérifier que chaque jour a des prédictions pour tous les ingrédients
        first_day = list(predictions.keys())[0]
        self.assertEqual(len(predictions[first_day]), len(self.ingredients))
        
        # Vérifier que les prédictions ont le format attendu
        for ingredient in self.ingredients:
            self.assertIn(ingredient, predictions[first_day])
            self.assertIn('mean', predictions[first_day][ingredient])
            self.assertIn('unit', predictions[first_day][ingredient])
    
    def test_predict_with_custom_horizon(self):
        """
        Teste la prédiction avec un horizon personnalisé.
        """
        days_ahead = 10
        predictions = self.forecaster.predict(
            historical_data=self.historical_data,
            days_ahead=days_ahead,
            ingredients=self.ingredients
        )
        
        # Vérifier le nombre de jours prédits
        self.assertEqual(len(predictions), days_ahead)
    
    def test_predict_with_subset_ingredients(self):
        """
        Teste la prédiction pour un sous-ensemble d'ingrédients.
        """
        subset = ['farine', 'tomate']
        predictions = self.forecaster.predict(
            historical_data=self.historical_data,
            ingredients=subset
        )
        
        # Vérifier que seuls les ingrédients demandés sont prédits
        first_day = list(predictions.keys())[0]
        self.assertEqual(len(predictions[first_day]), len(subset))
        for ingredient in subset:
            self.assertIn(ingredient, predictions[first_day])
    
    def test_predict_with_custom_start_date(self):
        """
        Teste la prédiction avec une date de début personnalisée.
        """
        start_date = datetime(2024, 5, 1)
        predictions = self.forecaster.predict(
            historical_data=self.historical_data,
            ingredients=self.ingredients,
            start_date=start_date
        )
        
        # Vérifier que la première date de prédiction est celle demandée
        first_day = list(predictions.keys())[0]
        self.assertEqual(first_day, start_date.strftime("%Y-%m-%d"))
    
    def test_predict_without_confidence_interval(self):
        """
        Teste la prédiction sans intervalle de confiance.
        """
        predictions = self.forecaster.predict(
            historical_data=self.historical_data,
            ingredients=self.ingredients,
            include_confidence=False
        )
        
        # Vérifier que les intervalles de confiance ne sont pas inclus
        first_day = list(predictions.keys())[0]
        first_ingredient = self.ingredients[0]
        self.assertIn('mean', predictions[first_day][first_ingredient])
        self.assertNotIn('lower', predictions[first_day][first_ingredient])
        self.assertNotIn('upper', predictions[first_day][first_ingredient])
        self.assertNotIn('confidence_interval', predictions[first_day][first_ingredient])
    
    def test_predict_with_insufficient_data(self):
        """
        Teste le comportement avec des données historiques insuffisantes.
        """
        # Créer un jeu de données trop court
        short_data = self.historical_data.iloc[:10].copy()
        
        # La prédiction devrait fonctionner quand même grâce au padding
        predictions = self.forecaster.predict(
            historical_data=short_data,
            ingredients=self.ingredients
        )
        
        # Vérifier que des prédictions sont générées malgré les données limitées
        self.assertIsInstance(predictions, dict)
        self.assertTrue(len(predictions) > 0)
    
    def test_error_handling_no_model(self):
        """
        Teste la gestion des erreurs quand aucun modèle n'est chargé.
        """
        # Créer un forecaster sans modèle
        forecaster = StockForecaster()
        forecaster.model = None
        
        # La prédiction devrait lever une exception
        with self.assertRaises(ValueError):
            forecaster.predict(
                historical_data=self.historical_data,
                ingredients=self.ingredients
            )
    
    def test_error_handling_missing_data(self):
        """
        Teste la gestion des erreurs quand les données historiques sont manquantes.
        """
        with self.assertRaises(ValueError):
            self.forecaster.predict(
                historical_data=None,
                ingredients=self.ingredients
            )
    
    @patch('prediction_module.models.stock_forecaster.logger')
    def test_logging(self, mock_logger):
        """
        Teste que les événements importants sont journalisés.
        """
        # Effectuer une prédiction
        self.forecaster.predict(
            historical_data=self.historical_data,
            ingredients=self.ingredients
        )
        
        # Vérifier que des logs ont été émis
        self.assertTrue(mock_logger.info.called)
        
        # Tester avec des données insuffisantes pour vérifier les logs d'avertissement
        short_data = self.historical_data.iloc[:10].copy()
        self.forecaster.predict(
            historical_data=short_data,
            ingredients=self.ingredients
        )
        self.assertTrue(mock_logger.warning.called)
    
    def test_batch_train_update(self):
        """
        Teste la méthode d'entraînement incrémental.
        """
        # Simuler de nouvelles données
        new_data = self.historical_data.copy()
        
        # La méthode devrait renvoyer des résultats d'entraînement
        history = self.forecaster.batch_train_update(new_data)
        
        # Vérifier le format des résultats
        self.assertIsInstance(history, dict)
        self.assertIn('loss', history)
        self.assertIn('val_loss', history)


if __name__ == '__main__':
    unittest.main()
