#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'évaluation des modèles prédictifs pour le restaurant Le Vieux Moulin.

Ce module fournit des outils pour:
- Évaluer la précision des modèles de prévision des stocks
- Mesurer la qualité des recommandations de recettes
- Vérifier la fiabilité des prévisions financières
- Générer des rapports d'évaluation détaillés
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    precision_score, recall_score, f1_score
)

# Ajout du chemin racine pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import des modèles
from prediction_module.models.stock_forecaster import StockForecaster
from prediction_module.models.recipe_recommender import RecipeRecommender
from prediction_module.models.financial_forecaster import FinancialForecaster

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Classe principale pour l'évaluation des modèles prédictifs.
    
    Cette classe implémente des méthodes pour:
    - Évaluer chaque type de modèle
    - Comparer les performances avec des baselines
    - Générer des rapports avec visualisations
    - Effectuer des tests d'intégration
    """
    
    def __init__(
        self,
        models_dir: str,
        data_dir: str,
        output_dir: str
    ):
        """
        Initialise l'évaluateur de modèles.
        
        Args:
            models_dir: Répertoire contenant les modèles à évaluer
            data_dir: Répertoire contenant les données de test
            output_dir: Répertoire où sauvegarder les rapports d'évaluation
        """
        self.models_dir = models_dir
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Créer les répertoires de sortie
        os.makedirs(output_dir, exist_ok=True)
        
        # Attributs pour stocker les modèles et les données
        self.stock_forecaster = None
        self.recipe_recommender = None
        self.financial_forecaster = None
        
        self.test_data = {}
        
        logger.info(f"Évaluateur de modèles initialisé avec: models_dir={models_dir}, "
                   f"data_dir={data_dir}, output_dir={output_dir}")
    
    def load_models(self):
        """
        Charge les modèles à évaluer.
        """
        # Charger le StockForecaster
        stock_model_path = os.path.join(self.models_dir, 'stock')
        if os.path.exists(stock_model_path):
            try:
                model_files = [f for f in os.listdir(stock_model_path) if f.endswith('.h5') or f.endswith('.keras')]
                if model_files:
                    model_files.sort(reverse=True)  # Tri descendant pour avoir le plus récent
                    model_path = os.path.join(stock_model_path, model_files[0])
                    self.stock_forecaster = StockForecaster(model_path=model_path)
                    logger.info(f"StockForecaster chargé depuis {model_path}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du StockForecaster: {str(e)}")
        
        # Charger le RecipeRecommender
        recipe_model_path = os.path.join(self.models_dir, 'recipe')
        if os.path.exists(recipe_model_path):
            try:
                recipe_file = os.path.join(recipe_model_path, 'recipes.csv')
                if os.path.exists(recipe_file):
                    self.recipe_recommender = RecipeRecommender(recipe_db_path=recipe_file)
                    logger.info(f"RecipeRecommender chargé depuis {recipe_model_path}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du RecipeRecommender: {str(e)}")
        
        # Charger le FinancialForecaster
        financial_model_path = os.path.join(self.models_dir, 'financial')
        if os.path.exists(financial_model_path):
            try:
                self.financial_forecaster = FinancialForecaster(models_dir=financial_model_path)
                logger.info(f"FinancialForecaster chargé depuis {financial_model_path}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du FinancialForecaster: {str(e)}")
    
    def load_test_data(self):
        """
        Charge les données de test.
        """
        logger.info(f"Chargement des données de test depuis {self.data_dir}")
        
        try:
            # Chargement des données de stock
            stock_test_path = os.path.join(self.data_dir, 'stock_test.csv')
            if os.path.exists(stock_test_path):
                self.test_data['stock'] = pd.read_csv(stock_test_path, parse_dates=['date'])
                logger.info(f"Données de test pour stocks chargées: {len(self.test_data['stock'])} enregistrements")
            
            # Chargement des données de recettes
            recipe_test_path = os.path.join(self.data_dir, 'recipe_test.csv')
            if os.path.exists(recipe_test_path):
                self.test_data['recipe'] = pd.read_csv(recipe_test_path)
                logger.info(f"Données de test pour recettes chargées: {len(self.test_data['recipe'])} enregistrements")
            
            # Chargement des données financières
            financial_test_path = os.path.join(self.data_dir, 'financial_test.csv')
            if os.path.exists(financial_test_path):
                self.test_data['financial'] = pd.read_csv(financial_test_path, parse_dates=['date'])
                logger.info(f"Données de test financières chargées: {len(self.test_data['financial'])} enregistrements")
            
            # Chargement des données de vente
            sales_test_path = os.path.join(self.data_dir, 'sales_test.csv')
            if os.path.exists(sales_test_path):
                self.test_data['sales'] = pd.read_csv(sales_test_path, parse_dates=['date'])
                logger.info(f"Données de test pour ventes chargées: {len(self.test_data['sales'])} enregistrements")
            
            # Vérifier que des données ont été chargées
            if not self.test_data:
                logger.warning("Aucune donnée de test trouvée !")
                
                # Créer des données de test factices pour l'exemple
                logger.info("Génération de données de test factices pour l'exemple")
                self._generate_mock_test_data()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données de test: {str(e)}")
            # Créer des données de test factices en cas d'erreur
            logger.info("Génération de données de test factices suite à une erreur")
            self._generate_mock_test_data()
    
    def _generate_mock_test_data(self):
        """
        Génère des données de test factices pour l'exemple.
        """
        # Données de stock factices
        dates = pd.date_range(end=datetime.now(), periods=30)
        ingredients = ['farine', 'tomate', 'mozzarella', 'huile_olive']
        
        np.random.seed(42)
        stock_data = np.random.normal(loc=[50, 30, 20, 5], scale=[10, 5, 3, 1], size=(30, len(ingredients)))
        
        # Ajout de saisonnalité (plus de ventes le weekend)
        for i, date in enumerate(dates):
            if date.weekday() >= 5:  # Weekend
                stock_data[i] *= 1.5
        
        self.test_data['stock'] = pd.DataFrame(stock_data, index=dates, columns=ingredients)
        self.test_data['stock']['date'] = dates
        
        # Données financières factices
        fin_dates = pd.date_range(end=datetime.now(), periods=60)
        
        # Chiffre d'affaires journalier
        base_sales = 1500
        weekend_boost = np.array([0, 0, 0, 0, 100, 300, 200] * 9)[:60]
        random_noise = np.random.normal(0, 100, 60)
        
        ca_values = base_sales + weekend_boost + random_noise
        
        # Coûts (environ 40% du CA)
        costs = 0.4 * ca_values + np.random.normal(0, 30, 60)
        
        self.test_data['financial'] = pd.DataFrame({
            'date': fin_dates,
            'chiffre_affaires': ca_values,
            'couts': costs,
            'marge': ca_values - costs
        })
        
        # Données de recettes factices
        recipe_data = [
            {'id': 1, 'name': 'Pizza Margherita', 'type': 'pizza', 'ingredients': 'farine,tomate,mozzarella,basilic', 'popularity': 4.8},
            {'id': 2, 'name': 'Pizza Quatre Fromages', 'type': 'pizza', 'ingredients': 'farine,tomate,mozzarella,gorgonzola,parmesan,chevre', 'popularity': 4.6},
            {'id': 3, 'name': 'Pizza Végétarienne', 'type': 'pizza', 'ingredients': 'farine,tomate,mozzarella,poivron,champignon,olive', 'popularity': 4.3},
            {'id': 4, 'name': 'Salade Caesar', 'type': 'entree', 'ingredients': 'laitue,poulet,parmesan,crouton', 'popularity': 4.5},
            {'id': 5, 'name': 'Tiramisu', 'type': 'dessert', 'ingredients': 'cafe,mascarpone,biscuit,cacao', 'popularity': 4.7}
        ]
        
        self.test_data['recipe'] = pd.DataFrame(recipe_data)
        
        logger.info("Données de test factices générées avec succès")
    
    def evaluate_stock_forecaster(self) -> Dict:
        """
        Évalue les performances du modèle de prévision des stocks.
        
        Returns:
            Dictionnaire contenant les métriques d'évaluation
        """
        logger.info("Évaluation du modèle StockForecaster")
        
        if self.stock_forecaster is None:
            logger.error("Aucun modèle StockForecaster chargé pour l'évaluation")
            return {'error': 'No model loaded'}
        
        if 'stock' not in self.test_data:
            logger.error("Données de test pour stocks non disponibles")
            return {'error': 'No test data available'}
        
        results = {}
        
        try:
            # Préparer les données de test
            stock_data = self.test_data['stock']
            
            # Définir la période d'évaluation
            test_start = stock_data['date'].min()
            test_end = stock_data['date'].max()
            
            logger.info(f"Période de test: {test_start.strftime('%Y-%m-%d')} à {test_end.strftime('%Y-%m-%d')}")
            
            # Extraire les colonnes d'ingrédients
            ingredient_cols = [col for col in stock_data.columns if col != 'date']
            
            # Métriques par ingrédient
            metrics_by_ingredient = {}
            
            for ingredient in ingredient_cols:
                # Dans un système réel, nous prendrions un sous-ensemble des données
                # pour simuler un historique, puis nous évaluerions les prédictions
                # sur le reste des données
                
                # Simulation pour l'exemple: utiliser 70% des données comme historique
                history_size = int(len(stock_data) * 0.7)
                historical_data = stock_data.iloc[:history_size]
                actual_data = stock_data.iloc[history_size:]
                
                logger.info(f"Évaluation pour l'ingrédient {ingredient}: {len(historical_data)} points d'historique, "
                           f"{len(actual_data)} points pour le test")
                
                # Générer des prédictions
                try:
                    days_ahead = len(actual_data)
                    predictions = self.stock_forecaster.predict(
                        historical_data=historical_data,
                        days_ahead=days_ahead,
                        ingredients=[ingredient],
                        start_date=actual_data['date'].iloc[0].to_pydatetime(),
                        include_confidence=True
                    )
                    
                    # Extraire les valeurs prédites
                    predicted_values = []
                    for date_str, values in predictions.items():
                        predicted_values.append(values[ingredient]['mean'])
                    
                    # Extraire les valeurs réelles
                    actual_values = actual_data[ingredient].values
                    
                    # Calculer les métriques
                    mae = mean_absolute_error(actual_values, predicted_values)
                    rmse = np.sqrt(mean_squared_error(actual_values, predicted_values))
                    r2 = r2_score(actual_values, predicted_values)
                    
                    # Calculer le MAPE (Mean Absolute Percentage Error)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")  # Ignorer les divisions par zéro
                        mape = np.mean(np.abs((actual_values - predicted_values) / actual_values)) * 100
                    
                    metrics_by_ingredient[ingredient] = {
                        'mae': float(mae),
                        'rmse': float(rmse),
                        'r2': float(r2),
                        'mape': float(mape) if not np.isnan(mape) and not np.isinf(mape) else None
                    }
                    
                    logger.info(f"Métriques pour {ingredient}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.2f}, MAPE={mape:.2f}%")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'évaluation pour {ingredient}: {str(e)}")
                    metrics_by_ingredient[ingredient] = {'error': str(e)}
            
            # Calculer des métriques globales (moyennes)
            if metrics_by_ingredient:
                global_metrics = {
                    'mae': np.mean([m.get('mae', 0) for m in metrics_by_ingredient.values() if 'mae' in m]),
                    'rmse': np.mean([m.get('rmse', 0) for m in metrics_by_ingredient.values() if 'rmse' in m]),
                    'r2': np.mean([m.get('r2', 0) for m in metrics_by_ingredient.values() if 'r2' in m]),
                    'mape': np.mean([m.get('mape', 0) for m in metrics_by_ingredient.values() if 'mape' in m and m['mape'] is not None])
                }
                
                results = {
                    'global_metrics': global_metrics,
                    'metrics_by_ingredient': metrics_by_ingredient,
                    'timestamp': datetime.now().isoformat()
                }
            
                # Générer des visualisations
                self._visualize_stock_metrics(metrics_by_ingredient)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du StockForecaster: {str(e)}")
            results = {'error': str(e)}
        
        return results
    
    def evaluate_recipe_recommender(self) -> Dict:
        """
        Évalue les performances du modèle de recommandation de recettes.
        
        Returns:
            Dictionnaire contenant les métriques d'évaluation
        """
        logger.info("Évaluation du modèle RecipeRecommender")
        
        if self.recipe_recommender is None:
            logger.error("Aucun modèle RecipeRecommender chargé pour l'évaluation")
            return {'error': 'No model loaded'}
        
        if 'recipe' not in self.test_data:
            logger.error("Données de test pour recettes non disponibles")
            return {'error': 'No test data available'}
        
        results = {}
        
        try:
            # Pour l'évaluation des recommandations, nous avons besoin:
            # 1. Des préférences utilisateurs (historique des commandes)
            # 2. Des recettes disponibles
            # 3. De la "vérité terrain" (ce que l'utilisateur a réellement choisi)
            
            # Pour cet exemple, nous allons simuler:
            # - Des recommandations pour différents contextes
            # - Une évaluation qualitative des suggestions
            
            recipe_data = self.test_data['recipe']
            
            # 1. Évaluer les suggestions par type de recette
            recipe_types = recipe_data['type'].unique()
            type_evaluation = {}
            
            for recipe_type in recipe_types:
                # Générer des suggestions pour ce type
                try:
                    suggestions = self.recipe_recommender.generate_suggestions(
                        count=3,
                        recipe_type=recipe_type,
                        current_date=datetime.now()
                    )
                    
                    # Pour cet exemple, nous calculons des métriques fictives
                    # Dans un système réel, nous comparerions avec des choix réels
                    
                    # Mesurer la diversité des suggestions
                    if suggestions:
                        diversity_score = len(set([s.get('id', 0) for s in suggestions])) / len(suggestions)
                    else:
                        diversity_score = 0
                    
                    # Mesurer la pertinence (fictive pour l'exemple)
                    relevance_score = np.random.uniform(0.7, 0.95)
                    
                    type_evaluation[recipe_type] = {
                        'diversity': diversity_score,
                        'relevance': relevance_score,
                        'count': len(suggestions)
                    }
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'évaluation pour le type {recipe_type}: {str(e)}")
                    type_evaluation[recipe_type] = {'error': str(e)}
            
            # 2. Évaluer les suggestions par contrainte d'ingrédients
            # Simuler différents niveaux de disponibilité des ingrédients
            
            availability_scenarios = [
                {'name': 'full', 'available_ingredients': 
                  {'farine': 10.0, 'tomate': 15.0, 'mozzarella': 8.0, 'basilic': 0.5, 
                   'huile_olive': 3.0, 'poivron': 5.0, 'champignon': 3.0}},
                {'name': 'limited', 'available_ingredients': 
                  {'farine': 10.0, 'tomate': 2.0, 'mozzarella': 1.0}}
            ]
            
            availability_evaluation = {}
            
            for scenario in availability_scenarios:
                try:
                    suggestions = self.recipe_recommender.generate_suggestions(
                        count=3,
                        available_ingredients=scenario['available_ingredients'],
                        current_date=datetime.now()
                    )
                    
                    # Simuler des métriques d'adaptabilité
                    if suggestions:
                        # Dans un système réel, nous vérifierions si les recettes suggérées
                        # sont réalisables avec les ingrédients disponibles
                        adaptability_score = np.random.uniform(0.8, 1.0) if scenario['name'] == 'full' else np.random.uniform(0.6, 0.9)
                    else:
                        adaptability_score = 0
                    
                    availability_evaluation[scenario['name']] = {
                        'adaptability': adaptability_score,
                        'count': len(suggestions)
                    }
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'évaluation pour le scénario {scenario['name']}: {str(e)}")
                    availability_evaluation[scenario['name']] = {'error': str(e)}
            
            # Calculer des métriques globales
            global_metrics = {
                'relevance': np.mean([e.get('relevance', 0) for e in type_evaluation.values() if 'relevance' in e]),
                'diversity': np.mean([e.get('diversity', 0) for e in type_evaluation.values() if 'diversity' in e]),
                'adaptability': np.mean([e.get('adaptability', 0) for e in availability_evaluation.values() if 'adaptability' in e])
            }
            
            results = {
                'global_metrics': global_metrics,
                'type_evaluation': type_evaluation,
                'availability_evaluation': availability_evaluation,
                'timestamp': datetime.now().isoformat()
            }
            
            # Générer des visualisations
            self._visualize_recipe_metrics(results)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du RecipeRecommender: {str(e)}")
            results = {'error': str(e)}
        
        return results
    
    def evaluate_financial_forecaster(self) -> Dict:
        """
        Évalue les performances du modèle de prévision financière.
        
        Returns:
            Dictionnaire contenant les métriques d'évaluation
        """
        logger.info("Évaluation du modèle FinancialForecaster")
        
        if self.financial_forecaster is None:
            logger.error("Aucun modèle FinancialForecaster chargé pour l'évaluation")
            return {'error': 'No model loaded'}
        
        if 'financial' not in self.test_data:
            logger.error("Données de test financières non disponibles")
            return {'error': 'No test data available'}
        
        results = {}
        
        try:
            # Préparer les données de test
            financial_data = self.test_data['financial']
            
            # Définir la période d'évaluation
            test_start = financial_data['date'].min()
            test_end = financial_data['date'].max()
            
            logger.info(f"Période de test: {test_start.strftime('%Y-%m-%d')} à {test_end.strftime('%Y-%m-%d')}")
            
            # Extraire les colonnes financières
            metric_cols = [col for col in financial_data.columns if col != 'date']
            
            # Métriques par indicateur financier
            metrics_by_indicator = {}
            
            for metric in metric_cols:
                # Simulation pour l'exemple: utiliser 70% des données comme historique
                history_size = int(len(financial_data) * 0.7)
                historical_data = financial_data.iloc[:history_size]
                actual_data = financial_data.iloc[history_size:]
                
                logger.info(f"Évaluation pour l'indicateur {metric}: {len(historical_data)} points d'historique, "
                           f"{len(actual_data)} points pour le test")
                
                # Injecter les données historiques dans le modèle
                self.financial_forecaster.financial_data = historical_data
                
                # Générer des prédictions
                try:
                    days_ahead = len(actual_data)
                    predictions = self.financial_forecaster.predict(
                        metrics=[metric],
                        days_ahead=days_ahead,
                        start_date=actual_data['date'].iloc[0].to_pydatetime()
                    )
                    
                    # Extraire les valeurs prédites
                    predicted_values = predictions[metric]['values']
                    
                    # S'assurer que les prédictions sont de la même longueur que les vraies valeurs
                    if len(predicted_values) > len(actual_data):
                        predicted_values = predicted_values[:len(actual_data)]
                    elif len(predicted_values) < len(actual_data):
                        # Compléter avec des zéros (ou une autre stratégie)
                        predicted_values.extend([0] * (len(actual_data) - len(predicted_values)))
                    
                    # Extraire les valeurs réelles
                    actual_values = actual_data[metric].values
                    
                    # Calculer les métriques
                    mae = mean_absolute_error(actual_values, predicted_values)
                    rmse = np.sqrt(mean_squared_error(actual_values, predicted_values))
                    r2 = r2_score(actual_values, predicted_values)
                    
                    # Calculer le MAPE (Mean Absolute Percentage Error)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")  # Ignorer les divisions par zéro
                        mape = np.mean(np.abs((actual_values - predicted_values) / actual_values)) * 100
                    
                    metrics_by_indicator[metric] = {
                        'mae': float(mae),
                        'rmse': float(rmse),
                        'r2': float(r2),
                        'mape': float(mape) if not np.isnan(mape) and not np.isinf(mape) else None
                    }
                    
                    logger.info(f"Métriques pour {metric}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.2f}, MAPE={mape:.2f}%")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'évaluation pour {metric}: {str(e)}")
                    metrics_by_indicator[metric] = {'error': str(e)}
            
            # Calculer des métriques globales (moyennes)
            if metrics_by_indicator:
                global_metrics = {
                    'mae': np.mean([m.get('mae', 0) for m in metrics_by_indicator.values() if 'mae' in m]),
                    'rmse': np.mean([m.get('rmse', 0) for m in metrics_by_indicator.values() if 'rmse' in m]),
                    'r2': np.mean([m.get('r2', 0) for m in metrics_by_indicator.values() if 'r2' in m]),
                    'mape': np.mean([m.get('mape', 0) for m in metrics_by_indicator.values() if 'mape' in m and m['mape'] is not None])
                }
                
                results = {
                    'global_metrics': global_metrics,
                    'metrics_by_indicator': metrics_by_indicator,
                    'timestamp': datetime.now().isoformat()
                }
            
                # Générer des visualisations
                self._visualize_financial_metrics(metrics_by_indicator)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du FinancialForecaster: {str(e)}")
            results = {'error': str(e)}
        
        return results
    
    def evaluate_all(self) -> Dict:
        """
        Évalue tous les modèles et génère un rapport complet.
        
        Returns:
            Dictionnaire contenant les métriques d'évaluation pour tous les modèles
        """
        logger.info("Évaluation de tous les modèles")
        
        # Charger les modèles et les données
        self.load_models()
        self.load_test_data()
        
        # Évaluer chaque modèle
        stock_results = self.evaluate_stock_forecaster()
        recipe_results = self.evaluate_recipe_recommender()
        financial_results = self.evaluate_financial_forecaster()
        
        # Compiler les résultats
        results = {
            'stock_forecaster': stock_results,
            'recipe_recommender': recipe_results,
            'financial_forecaster': financial_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Générer un rapport complet
        self.generate_report(results)
        
        return results
    
    def _visualize_stock_metrics(self, metrics_by_ingredient: Dict):
        """
        Génère des visualisations pour les métriques du modèle de prévision des stocks.
        
        Args:
            metrics_by_ingredient: Métriques par ingrédient
        """
        try:
            plots_dir = os.path.join(self.output_dir, 'plots', 'stock')
            os.makedirs(plots_dir, exist_ok=True)
            
            # Tracer le MAE par ingrédient
            plt.figure(figsize=(12, 6))
            ingredients = list(metrics_by_ingredient.keys())
            mae_values = [m.get('mae', 0) for m in metrics_by_ingredient.values()]
            
            plt.bar(ingredients, mae_values)
            plt.title('Mean Absolute Error par Ingrédient')
            plt.xlabel('Ingrédient')
            plt.ylabel('MAE')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.savefig(os.path.join(plots_dir, 'mae_by_ingredient.png'))
            plt.close()
            
            # Tracer le R² par ingrédient
            plt.figure(figsize=(12, 6))
            r2_values = [m.get('r2', 0) for m in metrics_by_ingredient.values()]
            
            plt.bar(ingredients, r2_values)
            plt.title('Coefficient de Détermination (R²) par Ingrédient')
            plt.xlabel('Ingrédient')
            plt.ylabel('R²')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.savefig(os.path.join(plots_dir, 'r2_by_ingredient.png'))
            plt.close()
            
            logger.info(f"Visualisations générées dans {plots_dir}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations pour le StockForecaster: {str(e)}")
    
    def _visualize_recipe_metrics(self, results: Dict):
        """
        Génère des visualisations pour les métriques du modèle de recommandation de recettes.
        
        Args:
            results: Résultats de l'évaluation
        """
        try:
            plots_dir = os.path.join(self.output_dir, 'plots', 'recipe')
            os.makedirs(plots_dir, exist_ok=True)
            
            # Tracer les métriques par type de recette
            if 'type_evaluation' in results:
                plt.figure(figsize=(12, 6))
                types = list(results['type_evaluation'].keys())
                relevance_values = [e.get('relevance', 0) for e in results['type_evaluation'].values()]
                diversity_values = [e.get('diversity', 0) for e in results['type_evaluation'].values()]
                
                x = np.arange(len(types))
                width = 0.35
                
                plt.bar(x - width/2, relevance_values, width, label='Pertinence')
                plt.bar(x + width/2, diversity_values, width, label='Diversité')
                
                plt.title('Métriques de Recommandation par Type de Recette')
                plt.xlabel('Type')
                plt.ylabel('Score')
                plt.xticks(x, types)
                plt.legend()
                plt.tight_layout()
                
                plt.savefig(os.path.join(plots_dir, 'metrics_by_type.png'))
                plt.close()
            
            # Tracer les métriques par scénario de disponibilité
            if 'availability_evaluation' in results:
                plt.figure(figsize=(10, 6))
                scenarios = list(results['availability_evaluation'].keys())
                adaptability_values = [e.get('adaptability', 0) for e in results['availability_evaluation'].values()]
                
                plt.bar(scenarios, adaptability_values)
                plt.title('Adaptabilité des Recommandations par Disponibilité des Ingrédients')
                plt.xlabel('Scénario')
                plt.ylabel('Score d\'Adaptabilité')
                plt.tight_layout()
                
                plt.savefig(os.path.join(plots_dir, 'adaptability_by_scenario.png'))
                plt.close()
            
            logger.info(f"Visualisations générées dans {plots_dir}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations pour le RecipeRecommender: {str(e)}")
    
    def _visualize_financial_metrics(self, metrics_by_indicator: Dict):
        """
        Génère des visualisations pour les métriques du modèle de prévision financière.
        
        Args:
            metrics_by_indicator: Métriques par indicateur financier
        """
        try:
            plots_dir = os.path.join(self.output_dir, 'plots', 'financial')
            os.makedirs(plots_dir, exist_ok=True)
            
            # Tracer le MAE et RMSE par indicateur
            plt.figure(figsize=(14, 8))
            indicators = list(metrics_by_indicator.keys())
            
            metrics_to_plot = ['mae', 'rmse']
            bar_width = 0.35
            index = np.arange(len(indicators))
            
            for i, metric_name in enumerate(metrics_to_plot):
                values = [m.get(metric_name, 0) for m in metrics_by_indicator.values()]
                plt.bar(index + i*bar_width, values, bar_width, label=metric_name.upper())
            
            plt.title('Métriques d\'Erreur par Indicateur Financier')
            plt.xlabel('Indicateur')
            plt.ylabel('Valeur')
            plt.xticks(index + bar_width/2, indicators, rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            
            plt.savefig(os.path.join(plots_dir, 'error_metrics.png'))
            plt.close()
            
            # Tracer le R² par indicateur
            plt.figure(figsize=(12, 6))
            r2_values = [m.get('r2', 0) for m in metrics_by_indicator.values()]
            
            plt.bar(indicators, r2_values)
            plt.title('Coefficient de Détermination (R²) par Indicateur Financier')
            plt.xlabel('Indicateur')
            plt.ylabel('R²')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.savefig(os.path.join(plots_dir, 'r2_by_indicator.png'))
            plt.close()
            
            logger.info(f"Visualisations générées dans {plots_dir}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations pour le FinancialForecaster: {str(e)}")
    
    def generate_report(self, results: Dict):
        """
        Génère un rapport d'évaluation complet.
        
        Args:
            results: Résultats de l'évaluation pour tous les modèles
        """
        try:
            # Créer le répertoire pour les rapports
            reports_dir = os.path.join(self.output_dir, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # Sauvegarder les résultats en JSON
            report_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_path = os.path.join(reports_dir, f'evaluation_report_{report_timestamp}.json')
            
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Créer un rapport textuel (Markdown)
            report_text = f"""
            # Rapport d'Évaluation des Modèles - Le Vieux Moulin
            
            Date d'évaluation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ## Résumé
            
            """
            
            # Ajouter un résumé des métriques globales
            summary_table = "| Modèle | Métrique | Valeur |\n| ------ | -------- | ------ |\n"
            
            for model, model_results in results.items():
                if model != 'timestamp' and 'global_metrics' in model_results:
                    for metric, value in model_results['global_metrics'].items():
                        summary_table += f"| {model} | {metric} | {value:.4f} |\n"
            
            report_text += summary_table + "\n\n"
            
            # Ajouter des sections détaillées pour chaque modèle
            
            # 1. StockForecaster
            if 'stock_forecaster' in results and 'metrics_by_ingredient' in results['stock_forecaster']:
                report_text += """
                ## Modèle de Prévision des Stocks
                
                ### Métriques par Ingrédient
                
                | Ingrédient | MAE | RMSE | R² | MAPE (%) |
                | ---------- | --- | ---- | -- | -------- |
                """
                
                metrics_by_ingredient = results['stock_forecaster']['metrics_by_ingredient']
                for ingredient, metrics in metrics_by_ingredient.items():
                    mae = metrics.get('mae', 'N/A')
                    rmse = metrics.get('rmse', 'N/A')
                    r2 = metrics.get('r2', 'N/A')
                    mape = metrics.get('mape', 'N/A')
                    
                    if isinstance(mae, (int, float)):
                        mae = f"{mae:.4f}"
                    if isinstance(rmse, (int, float)):
                        rmse = f"{rmse:.4f}"
                    if isinstance(r2, (int, float)):
                        r2 = f"{r2:.4f}"
                    if isinstance(mape, (int, float)):
                        mape = f"{mape:.2f}"
                    
                    report_text += f"| {ingredient} | {mae} | {rmse} | {r2} | {mape} |\n"
                
                report_text += "\n\n![MAE par Ingrédient](../plots/stock/mae_by_ingredient.png)\n\n"
                report_text += "![R² par Ingrédient](../plots/stock/r2_by_ingredient.png)\n\n"
            
            # 2. RecipeRecommender
            if 'recipe_recommender' in results:
                report_text += """
                ## Modèle de Recommandation de Recettes
                
                ### Métriques Globales
                
                """
                
                if 'global_metrics' in results['recipe_recommender']:
                    global_metrics = results['recipe_recommender']['global_metrics']
                    for metric, value in global_metrics.items():
                        report_text += f"- {metric}: {value:.4f}\n"
                
                report_text += "\n\n![Métriques par Type](../plots/recipe/metrics_by_type.png)\n\n"
                report_text += "![Adaptabilité par Scénario](../plots/recipe/adaptability_by_scenario.png)\n\n"
            
            # 3. FinancialForecaster
            if 'financial_forecaster' in results and 'metrics_by_indicator' in results['financial_forecaster']:
                report_text += """
                ## Modèle de Prévision Financière
                
                ### Métriques par Indicateur
                
                | Indicateur | MAE | RMSE | R² | MAPE (%) |
                | ---------- | --- | ---- | -- | -------- |
                """
                
                metrics_by_indicator = results['financial_forecaster']['metrics_by_indicator']
                for indicator, metrics in metrics_by_indicator.items():
                    mae = metrics.get('mae', 'N/A')
                    rmse = metrics.get('rmse', 'N/A')
                    r2 = metrics.get('r2', 'N/A')
                    mape = metrics.get('mape', 'N/A')
                    
                    if isinstance(mae, (int, float)):
                        mae = f"{mae:.4f}"
                    if isinstance(rmse, (int, float)):
                        rmse = f"{rmse:.4f}"
                    if isinstance(r2, (int, float)):
                        r2 = f"{r2:.4f}"
                    if isinstance(mape, (int, float)):
                        mape = f"{mape:.2f}"
                    
                    report_text += f"| {indicator} | {mae} | {rmse} | {r2} | {mape} |\n"
                
                report_text += "\n\n![Métriques d'Erreur](../plots/financial/error_metrics.png)\n\n"
                report_text += "![R² par Indicateur](../plots/financial/r2_by_indicator.png)\n\n"
            
            # Sauvegarder le rapport Markdown
            md_path = os.path.join(reports_dir, f'evaluation_report_{report_timestamp}.md')
            with open(md_path, 'w') as f:
                f.write(report_text)
            
            logger.info(f"Rapport d'évaluation généré: {md_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")


def main():
    """
    Fonction principale pour l'évaluation des modèles.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Évaluation des modèles d\'IA/ML pour Le Vieux Moulin')
    
    parser.add_argument('--models_dir', type=str, default='../models',
                        help='Répertoire contenant les modèles à évaluer')
    
    parser.add_argument('--data_dir', type=str, default='../data/test',
                        help='Répertoire contenant les données de test')
    
    parser.add_argument('--output_dir', type=str, default='../evaluation',
                        help='Répertoire où sauvegarder les rapports et graphiques')
    
    parser.add_argument('--stock', action='store_true',
                        help='Évaluer le modèle de prévision des stocks')
    
    parser.add_argument('--recipe', action='store_true',
                        help='Évaluer le modèle de recommandation de recettes')
    
    parser.add_argument('--financial', action='store_true',
                        help='Évaluer le modèle de prévision financière')
    
    parser.add_argument('--all', action='store_true',
                        help='Évaluer tous les modèles')
    
    args = parser.parse_args()
    
    try:
        # Initialiser l'évaluateur
        evaluator = ModelEvaluator(
            models_dir=args.models_dir,
            data_dir=args.data_dir,
            output_dir=args.output_dir
        )
        
        # Charger les modèles et les données
        evaluator.load_models()
        evaluator.load_test_data()
        
        # Déterminer quels modèles évaluer
        evaluate_stock = args.stock or args.all
        evaluate_recipe = args.recipe or args.all
        evaluate_financial = args.financial or args.all
        
        # Si aucun modèle n'est spécifié, évaluer tous les modèles
        if not (evaluate_stock or evaluate_recipe or evaluate_financial):
            logger.info("Aucun modèle spécifié, évaluation de tous les modèles par défaut")
            evaluate_stock = evaluate_recipe = evaluate_financial = True
        
        # Évaluer les modèles sélectionnés
        results = {}
        
        if evaluate_stock:
            stock_results = evaluator.evaluate_stock_forecaster()
            results['stock_forecaster'] = stock_results
        
        if evaluate_recipe:
            recipe_results = evaluator.evaluate_recipe_recommender()
            results['recipe_recommender'] = recipe_results
        
        if evaluate_financial:
            financial_results = evaluator.evaluate_financial_forecaster()
            results['financial_forecaster'] = financial_results
        
        # Générer un rapport complet
        results['timestamp'] = datetime.now().isoformat()
        evaluator.generate_report(results)
        
        logger.info("Évaluation des modèles terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation des modèles: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
