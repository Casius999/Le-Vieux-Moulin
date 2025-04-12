#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de prédiction des besoins en matières premières pour le restaurant Le Vieux Moulin.

Ce module utilise un modèle LSTM pour prédire les besoins en ingrédients sur une période donnée,
en se basant sur l'historique des ventes, les données saisonnières et les événements spéciaux.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockForecaster:
    """
    Classe pour la prédiction des besoins en stocks basée sur un modèle LSTM.
    
    Cette classe gère le chargement du modèle, la préparation des données et la génération
    des prédictions pour les besoins futurs en matières premières.
    """
    
    def __init__(
        self,
        model_path: str = None,
        config_path: str = None,
        lookback_days: int = 30,
        default_horizon: int = 7
    ):
        """
        Initialise le prédicteur de stocks.
        
        Args:
            model_path: Chemin vers le modèle entraîné (h5 ou SavedModel)
            config_path: Chemin vers la configuration du modèle
            lookback_days: Nombre de jours d'historique à considérer
            default_horizon: Horizon de prédiction par défaut en jours
        """
        self.model_path = model_path
        self.config_path = config_path
        self.lookback_days = lookback_days
        self.default_horizon = default_horizon
        self.model = None
        self.scaler = None
        self.ingredient_metadata = {}
        
        # Chargement du modèle s'il est spécifié
        if model_path and os.path.exists(model_path):
            self._load_model()
        else:
            logger.warning(f"Aucun modèle trouvé à l'emplacement {model_path}. "
                          "Vous devrez charger un modèle avant de faire des prédictions.")
    
    def _load_model(self) -> None:
        """
        Charge le modèle et les métadonnées associées.
        """
        try:
            logger.info(f"Chargement du modèle depuis {self.model_path}")
            self.model = load_model(self.model_path)
            
            # Chargement des métadonnées si disponibles
            metadata_path = os.path.join(os.path.dirname(self.model_path), "metadata.json")
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                
                # Extraire les informations nécessaires
                self.ingredient_metadata = metadata.get("ingredients", {})
                
                # Charger le scaler si disponible
                scaler_path = metadata.get("scaler_path")
                if scaler_path and os.path.exists(scaler_path):
                    from joblib import load as joblib_load
                    self.scaler = joblib_load(scaler_path)
            
            logger.info("Modèle et métadonnées chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            raise
    
    def _prepare_data(
        self,
        historical_data: pd.DataFrame,
        ingredients: List[str]
    ) -> np.ndarray:
        """
        Prépare les données pour la prédiction.
        
        Args:
            historical_data: DataFrame avec l'historique des données
            ingredients: Liste des ingrédients à prédire
            
        Returns:
            Tableau numpy formaté pour l'entrée du modèle
        """
        # Vérifier que tous les ingrédients demandés sont disponibles
        available_ingredients = historical_data.columns.tolist()
        for ingredient in ingredients:
            if ingredient not in available_ingredients:
                logger.warning(f"Ingrédient '{ingredient}' non trouvé dans les données historiques")
                
        # Sélectionner uniquement les colonnes pertinentes
        filtered_data = historical_data[ingredients].copy()
        
        # Vérifier qu'il y a assez de données
        if len(filtered_data) < self.lookback_days:
            logger.warning(
                f"Données historiques insuffisantes. {len(filtered_data)} jours disponibles, "
                f"{self.lookback_days} requis. Padding avec des zéros."
            )
            # Padding si nécessaire
            padding_size = self.lookback_days - len(filtered_data)
            padding = pd.DataFrame(
                np.zeros((padding_size, len(ingredients))),
                columns=ingredients
            )
            filtered_data = pd.concat([padding, filtered_data], ignore_index=True)
        
        # Normaliser les données si un scaler est disponible
        if self.scaler:
            filtered_data_values = self.scaler.transform(filtered_data.values)
        else:
            # Normalisation simple si pas de scaler
            filtered_data_values = filtered_data.values / filtered_data.values.max(axis=0)
        
        # Prendre les derniers jours selon lookback_days
        input_data = filtered_data_values[-self.lookback_days:].reshape(1, self.lookback_days, len(ingredients))
        
        return input_data
    
    def _get_contextual_features(
        self,
        start_date: datetime,
        days_ahead: int
    ) -> np.ndarray:
        """
        Génère les caractéristiques contextuelles pour la période de prédiction.
        
        Args:
            start_date: Date de début de la prédiction
            days_ahead: Nombre de jours à prédire
            
        Returns:
            Tableau numpy avec les caractéristiques contextuelles
        """
        contextual_features = []
        
        for i in range(days_ahead):
            current_date = start_date + timedelta(days=i)
            
            # Caractéristiques temporelles
            day_of_week = current_date.weekday()  # 0-6 (lundi-dimanche)
            month = current_date.month  # 1-12
            is_weekend = 1 if day_of_week >= 5 else 0
            day_of_month = current_date.day  # 1-31
            
            # Pourrait être étendu avec des données externes (météo, événements, etc.)
            
            # Encodage one-hot du jour de la semaine
            dow_encoding = [0] * 7
            dow_encoding[day_of_week] = 1
            
            # Encodage one-hot du mois
            month_encoding = [0] * 12
            month_encoding[month - 1] = 1
            
            # Combinaison de toutes les caractéristiques
            features = dow_encoding + month_encoding + [is_weekend, day_of_month]
            contextual_features.append(features)
        
        return np.array(contextual_features).reshape(1, days_ahead, len(features))
    
    def predict(
        self,
        historical_data: Optional[pd.DataFrame] = None,
        days_ahead: int = None,
        ingredients: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        include_confidence: bool = True
    ) -> Dict:
        """
        Génère des prédictions pour les besoins futurs en ingrédients.
        
        Args:
            historical_data: DataFrame avec l'historique des données (optional si le modèle a accès aux données)
            days_ahead: Nombre de jours à prédire (utilise default_horizon si non spécifié)
            ingredients: Liste des ingrédients à prédire (tous les ingrédients disponibles si None)
            start_date: Date de début pour la prédiction (aujourd'hui si None)
            include_confidence: Inclure les intervalles de confiance dans les résultats
            
        Returns:
            Dictionnaire avec les prédictions par jour et par ingrédient
        """
        if self.model is None:
            raise ValueError("Aucun modèle chargé. Utilisez _load_model() avant de faire des prédictions.")
        
        # Paramètres par défaut
        if days_ahead is None:
            days_ahead = self.default_horizon
            
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Si historical_data n'est pas fourni, utiliser les données prédéfinies ou lever une erreur
        if historical_data is None:
            # Dans un système réel, on pourrait récupérer les données depuis une base de données
            raise ValueError("Les données historiques doivent être fournies pour la prédiction")
        
        # Si ingredients n'est pas spécifié, utiliser tous les ingrédients disponibles
        if ingredients is None:
            ingredients = list(historical_data.columns)
        
        # Préparer les données d'entrée
        input_data = self._prepare_data(historical_data, ingredients)
        
        # Obtenir les caractéristiques contextuelles
        contextual_features = self._get_contextual_features(start_date, days_ahead)
        
        # Faire la prédiction
        try:
            predictions = self.model.predict([input_data, contextual_features], verbose=0)
            
            # Dénormaliser si un scaler est disponible
            if self.scaler:
                # Reshape pour le format attendu par le scaler
                pred_reshaped = predictions.reshape(-1, len(ingredients))
                predictions_denorm = self.scaler.inverse_transform(pred_reshaped)
                predictions = predictions_denorm.reshape(days_ahead, len(ingredients))
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {str(e)}")
            raise
        
        # Organiser les résultats
        results = {}
        for i in range(days_ahead):
            date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            results[date_str] = {}
            
            for j, ingredient in enumerate(ingredients):
                # Base prediction for this ingredient
                pred_value = float(predictions[i, j])
                
                # Get metadata for this ingredient if available
                ing_metadata = self.ingredient_metadata.get(ingredient, {})
                unit = ing_metadata.get("unit", "unité")
                
                # Add confidence interval if requested
                if include_confidence:
                    # In a real system, this would be calculated based on model uncertainty
                    # Here we use a simplified approach: 10% margin
                    confidence_interval = abs(pred_value) * 0.1
                    
                    results[date_str][ingredient] = {
                        "mean": max(0, pred_value),  # Ensure non-negative
                        "lower": max(0, pred_value - confidence_interval),
                        "upper": pred_value + confidence_interval,
                        "confidence_interval": confidence_interval,
                        "unit": unit
                    }
                else:
                    results[date_str][ingredient] = {
                        "mean": max(0, pred_value),  # Ensure non-negative
                        "unit": unit
                    }
        
        return results
    
    def batch_train_update(
        self,
        new_data: pd.DataFrame,
        epochs: int = 5,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> Dict:
        """
        Met à jour le modèle avec de nouvelles données (apprentissage incrémental).
        
        Args:
            new_data: Nouvelles données pour l'entraînement
            epochs: Nombre d'époques pour l'entraînement
            batch_size: Taille du batch
            learning_rate: Taux d'apprentissage
            
        Returns:
            Historique d'entraînement
        """
        if self.model is None:
            raise ValueError("Aucun modèle chargé. Vous devez d'abord charger un modèle.")
        
        # Dans une implémentation réelle, nous préparerions les données et mettrions à jour le modèle
        # Pour cet exemple, nous simulons juste le processus
        
        logger.info(f"Mise à jour du modèle avec {len(new_data)} nouvelles observations")
        
        # Simulation de l'historique d'entraînement
        history = {
            'loss': [0.05, 0.04, 0.035, 0.033, 0.032],
            'val_loss': [0.06, 0.055, 0.05, 0.048, 0.047]
        }
        
        return history


# Fonction d'utilisation pour les tests
def example_usage():
    """
    Exemple d'utilisation du modèle StockForecaster.
    """
    # Création de données fictives pour l'exemple
    dates = pd.date_range(start='2025-01-01', periods=60)
    ingredients = ['farine', 'tomate', 'mozzarella', 'huile_olive']
    
    np.random.seed(42)
    data = np.random.normal(loc=[50, 30, 20, 5], scale=[10, 5, 3, 1], size=(60, 4))
    
    # Ajout de saisonnalité (plus de ventes le weekend)
    for i, date in enumerate(dates):
        if date.weekday() >= 5:  # Weekend
            data[i] *= 1.5
    
    historical_data = pd.DataFrame(data, index=dates, columns=ingredients)
    
    # Initialisation du modèle (sans chemin de modèle réel pour cet exemple)
    # Dans un cas réel, on chargerait un modèle préentraîné
    forecaster = StockForecaster(model_path=None)
    
    # Pour cet exemple, simulons un modèle simple
    forecaster.model = MockLSTMModel()
    
    # Prédiction
    try:
        predictions = forecaster.predict(
            historical_data=historical_data,
            days_ahead=7,
            ingredients=ingredients,
            start_date=datetime(2025, 3, 1)
        )
        
        # Affichage des résultats
        for day, items in predictions.items():
            print(f"\nPrévisions pour {day}:")
            for ingredient, values in items.items():
                print(f"  - {ingredient}: {values['mean']:.2f} {values['unit']} (±{values['confidence_interval']:.2f})")
    except Exception as e:
        print(f"Erreur lors de la prédiction: {str(e)}")


# Classe de substitution pour les tests - Simule un modèle LSTM
class MockLSTMModel:
    """Classe simulant un modèle LSTM pour les tests."""
    
    def predict(self, inputs, verbose=0):
        # Simuler une prédiction basique
        # Second input (contextual features) shape: (1, days_ahead, features)
        days_ahead = inputs[1].shape[1]
        num_ingredients = inputs[0].shape[2]
        
        # Generate fake predictions with some daily variations
        base_values = np.array([50, 30, 20, 5])[:num_ingredients]
        
        # Create variations for each day
        predictions = np.zeros((days_ahead, num_ingredients))
        for i in range(days_ahead):
            day_of_week = i % 7
            weekend_factor = 1.3 if day_of_week >= 5 else 1.0
            predictions[i] = base_values * weekend_factor * (1 + 0.05 * np.random.randn(num_ingredients))
        
        return predictions


if __name__ == "__main__":
    # Exécuter l'exemple d'utilisation si ce script est exécuté directement
    example_usage()
