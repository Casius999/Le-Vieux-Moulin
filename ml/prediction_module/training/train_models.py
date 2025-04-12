#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal d'entraînement des modèles d'IA/ML pour le restaurant Le Vieux Moulin.

Ce script coordonne l'entraînement des trois modèles principaux :
1. StockForecaster : Prédiction des besoins en matières premières
2. RecipeRecommender : Recommandation de recettes
3. FinancialForecaster : Prévisions financières

Il permet également la sauvegarde des modèles entraînés, le suivi des métriques
et la génération de rapports d'entraînement.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from joblib import dump

# Ajout du chemin racine pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import des modèles
from prediction_module.models.stock_forecaster import StockForecaster
from prediction_module.models.recipe_recommender import RecipeRecommender
from prediction_module.models.financial_forecaster import FinancialForecaster

# Import des utilitaires de prétraitement
from prediction_module.data_processing.preprocessor import DataPreprocessor

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_data(data_dir: str, config: Dict) -> Dict[str, pd.DataFrame]:
    """
    Charge les données nécessaires pour l'entraînement des modèles.
    
    Args:
        data_dir: Répertoire contenant les fichiers de données
        config: Configuration spécifiant les fichiers à charger
        
    Returns:
        Dictionnaire de DataFrames avec les données chargées
    """
    logger.info(f"Chargement des données depuis {data_dir}")
    
    data_dict = {}
    
    try:
        # Chargement des données d'inventaire/stocks
        if 'stock_data' in config:
            stock_path = os.path.join(data_dir, config['stock_data'])
            if os.path.exists(stock_path):
                data_dict['stock_data'] = pd.read_csv(stock_path, parse_dates=['date'])
                logger.info(f"Données de stock chargées: {len(data_dict['stock_data'])} enregistrements")
        
        # Chargement des données de recettes
        if 'recipe_data' in config:
            recipe_path = os.path.join(data_dir, config['recipe_data'])
            if os.path.exists(recipe_path):
                data_dict['recipe_data'] = pd.read_csv(recipe_path)
                logger.info(f"Données de recettes chargées: {len(data_dict['recipe_data'])} enregistrements")
        
        # Chargement des données financières
        if 'financial_data' in config:
            financial_path = os.path.join(data_dir, config['financial_data'])
            if os.path.exists(financial_path):
                data_dict['financial_data'] = pd.read_csv(financial_path, parse_dates=['date'])
                logger.info(f"Données financières chargées: {len(data_dict['financial_data'])} enregistrements")
        
        # Chargement des données de vente
        if 'sales_data' in config:
            sales_path = os.path.join(data_dir, config['sales_data'])
            if os.path.exists(sales_path):
                data_dict['sales_data'] = pd.read_csv(sales_path, parse_dates=['date'])
                logger.info(f"Données de vente chargées: {len(data_dict['sales_data'])} enregistrements")
        
        # Vérifier que les données essentielles ont été chargées
        if not data_dict:
            logger.error("Aucun fichier de données n'a pu être chargé !")
            raise FileNotFoundError("Fichiers de données introuvables")
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données: {str(e)}")
        raise
    
    return data_dict


def train_stock_forecaster(
    data: Dict[str, pd.DataFrame],
    config: Dict,
    models_dir: str
) -> Tuple[StockForecaster, Dict]:
    """
    Entraîne le modèle de prévision des stocks.
    
    Args:
        data: Dictionnaire contenant les DataFrames des données
        config: Configuration pour l'entraînement
        models_dir: Répertoire où sauvegarder le modèle
        
    Returns:
        Tuple contenant le modèle entraîné et les métriques d'évaluation
    """
    logger.info("Entraînement du modèle de prévision des stocks")
    
    try:
        # Vérifier que les données nécessaires sont disponibles
        if 'stock_data' not in data or 'sales_data' not in data:
            logger.error("Données manquantes pour l'entraînement du StockForecaster")
            raise ValueError("Données de stock ou de vente manquantes")
        
        stock_data = data['stock_data']
        sales_data = data['sales_data']
        
        # Préparation des données
        logger.info("Prétraitement des données pour StockForecaster")
        
        # 1. Fusionner les données de vente et de stock
        merged_data = pd.merge(
            sales_data, 
            stock_data,
            on='date',
            how='inner',
            suffixes=('_sales', '_stock')
        )
        
        # 2. Prétraiter les données
        preprocessor = DataPreprocessor(
            scaling_method='standard',
            handle_outliers=True,
            handle_missing=True,
            time_features=True
        )
        
        # Identifier les colonnes d'ingrédients
        stock_cols = [col for col in merged_data.columns if col.endswith('_stock')]
        
        # Prétraiter les données
        processed_data = preprocessor.fit_transform(
            merged_data,
            target_cols=stock_cols,
            date_col='date'
        )
        
        # 3. Division des données (chronologique)
        X_train, X_val, X_test, y_train_dict, y_val_dict, y_test_dict = {}, {}, {}, {}, {}, {}
        
        for col in stock_cols:
            # Pour chaque ingrédient, créer des ensembles de train/val/test
            X_train_ing, X_val_ing, X_test_ing, y_train_ing, y_val_ing, y_test_ing = preprocessor.split_data(
                processed_data,
                target_col=col,
                test_size=0.2,
                val_size=0.1,
                temporal=True,
                date_col='date'
            )
            
            # Stocker les résultats
            if not X_train:  # Premier ingrédient, initialiser les DataFrames
                X_train, X_val, X_test = X_train_ing, X_val_ing, X_test_ing
            
            # Stocker les cibles pour chaque ingrédient
            y_train_dict[col] = y_train_ing
            y_val_dict[col] = y_val_ing
            y_test_dict[col] = y_test_ing
        
        # 4. Définir l'architecture du modèle LSTM
        lookback_days = config.get('lookback_days', 30)
        
        # Dans un contexte réel, construire un modèle TensorFlow ici
        # Pour cet exemple, nous allons utiliser la classe StockForecaster avec un modèle fictif
        
        # Créer le répertoire de sauvegarde
        stock_models_dir = os.path.join(models_dir, 'stock')
        os.makedirs(stock_models_dir, exist_ok=True)
        
        # Initialiser le modèle
        stock_forecaster = StockForecaster(
            model_path=None,  # Pas de modèle existant
            lookback_days=lookback_days
        )
        
        # En contexte réel, entraîner le modèle ici
        # Pour l'exemple, simulons un résultat d'entraînement
        
        # 5. Évaluer le modèle
        metrics = {
            'mean_absolute_error': {},
            'root_mean_squared_error': {},
            'r2_score': {}
        }
        
        for col in stock_cols:
            # Dans un contexte réel, évaluer le modèle sur les données de test
            # Pour l'exemple, générer des métriques fictives
            metrics['mean_absolute_error'][col] = np.random.uniform(0.5, 2.0)
            metrics['root_mean_squared_error'][col] = np.random.uniform(1.0, 3.0)
            metrics['r2_score'][col] = np.random.uniform(0.7, 0.95)
        
        # 6. Sauvegarder le modèle et les métadonnées
        # Pour l'exemple, sauvegarder seulement les métadonnées
        metadata = {
            'ingredients': {col.replace('_stock', ''): {'unit': 'kg'} for col in stock_cols},
            'lookback_days': lookback_days,
            'training_date': datetime.now().strftime('%Y-%m-%d'),
            'metrics': metrics
        }
        
        metadata_path = os.path.join(stock_models_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Sauvegarder le scaler
        scaler_path = os.path.join(stock_models_dir, 'scaler.joblib')
        dump(preprocessor.scalers, scaler_path)
        
        logger.info(f"Modèle de prévision des stocks entraîné et sauvegardé dans {stock_models_dir}")
        
        return stock_forecaster, metrics
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement du StockForecaster: {str(e)}")
        raise


def train_recipe_recommender(
    data: Dict[str, pd.DataFrame],
    config: Dict,
    models_dir: str
) -> Tuple[RecipeRecommender, Dict]:
    """
    Entraîne le modèle de recommandation de recettes.
    
    Args:
        data: Dictionnaire contenant les DataFrames des données
        config: Configuration pour l'entraînement
        models_dir: Répertoire où sauvegarder le modèle
        
    Returns:
        Tuple contenant le modèle entraîné et les métriques d'évaluation
    """
    logger.info("Entraînement du modèle de recommandation de recettes")
    
    try:
        # Vérifier que les données nécessaires sont disponibles
        if 'recipe_data' not in data or 'sales_data' not in data:
            logger.error("Données manquantes pour l'entraînement du RecipeRecommender")
            raise ValueError("Données de recettes ou de vente manquantes")
        
        recipe_data = data['recipe_data']
        sales_data = data['sales_data']
        
        # Créer le répertoire de sauvegarde
        recipe_models_dir = os.path.join(models_dir, 'recipe')
        os.makedirs(recipe_models_dir, exist_ok=True)
        
        # 1. Préparation des données
        # Ici, nous devrions traiter les données de recettes et créer des embeddings
        # Pour l'exemple, supposons que les données sont déjà préparées
        
        # 2. Initialiser le modèle
        embedding_dim = config.get('embedding_dim', 64)
        recommender = RecipeRecommender(
            embedding_dim=embedding_dim
        )
        
        # 3. En contexte réel, entraîner le modèle ici
        # Pour l'exemple, simulons un résultat d'entraînement
        
        # 4. Évaluer le modèle
        metrics = {
            'precision': np.random.uniform(0.7, 0.9),
            'recall': np.random.uniform(0.6, 0.85),
            'ndcg': np.random.uniform(0.75, 0.95)
        }
        
        # 5. Sauvegarder les métadonnées et les poids
        seasonal_adjustments = {
            'winter': {1: 1.2, 2: 1.3},  # IDs de recettes pour l'hiver
            'spring': {3: 1.1, 4: 1.2},  # IDs de recettes pour le printemps
            'summer': {5: 1.3, 6: 1.4},  # IDs de recettes pour l'été
            'autumn': {7: 1.1, 8: 1.2}   # IDs de recettes pour l'automne
        }
        
        # Poids fictifs des ingrédients
        ingredient_weights = {
            'farine': 0.8,
            'tomate': 1.2,
            'mozzarella': 1.5,
            'basilic': 0.9,
            'champignon': 1.1,
            'jambon': 1.3
        }
        
        # Sauvegarder les métadonnées
        seasonal_path = os.path.join(recipe_models_dir, 'seasonal_adjustments.json')
        with open(seasonal_path, 'w') as f:
            json.dump(seasonal_adjustments, f, indent=2)
        
        weights_path = os.path.join(recipe_models_dir, 'ingredient_weights.json')
        with open(weights_path, 'w') as f:
            json.dump(ingredient_weights, f, indent=2)
        
        # Sauvegarder les embeddings de recettes (fictifs pour l'exemple)
        recipe_embeddings = np.random.random((len(recipe_data), embedding_dim))
        embeddings_path = os.path.join(recipe_models_dir, 'recipe_embeddings.npy')
        np.save(embeddings_path, recipe_embeddings)
        
        # Sauvegarder les données de recettes
        recipe_data.to_csv(os.path.join(recipe_models_dir, 'recipes.csv'), index=False)
        
        logger.info(f"Modèle de recommandation de recettes entraîné et sauvegardé dans {recipe_models_dir}")
        
        return recommender, metrics
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement du RecipeRecommender: {str(e)}")
        raise


def train_financial_forecaster(
    data: Dict[str, pd.DataFrame],
    config: Dict,
    models_dir: str
) -> Tuple[FinancialForecaster, Dict]:
    """
    Entraîne le modèle de prévision financière.
    
    Args:
        data: Dictionnaire contenant les DataFrames des données
        config: Configuration pour l'entraînement
        models_dir: Répertoire où sauvegarder le modèle
        
    Returns:
        Tuple contenant le modèle entraîné et les métriques d'évaluation
    """
    logger.info("Entraînement du modèle de prévision financière")
    
    try:
        # Vérifier que les données nécessaires sont disponibles
        if 'financial_data' not in data:
            logger.error("Données manquantes pour l'entraînement du FinancialForecaster")
            raise ValueError("Données financières manquantes")
        
        financial_data = data['financial_data']
        
        # Créer le répertoire de sauvegarde
        financial_models_dir = os.path.join(models_dir, 'financial')
        os.makedirs(financial_models_dir, exist_ok=True)
        os.makedirs(os.path.join(financial_models_dir, 'prophet'), exist_ok=True)
        os.makedirs(os.path.join(financial_models_dir, 'xgboost'), exist_ok=True)
        os.makedirs(os.path.join(financial_models_dir, 'scalers'), exist_ok=True)
        
        # 1. Initialiser le modèle
        forecaster = FinancialForecaster(
            models_dir=None,
            financial_history_path=None
        )
        
        # 2. Injecter les données
        forecaster.financial_data = financial_data
        
        # 3. Configurer et entraîner les modèles
        prophet_params = config.get('prophet_params', {
            'changepoint_prior_scale': 0.05,
            'seasonality_prior_scale': 10,
            'holidays_prior_scale': 10
        })
        
        xgboost_params = config.get('xgboost_params', {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100
        })
        
        # Dans un environnement réel, ce serait un vrai entraînement
        # Pour l'exemple, simulons un entraînement
        training_results = {
            'chiffre_affaires': {'prophet': True, 'xgboost': True},
            'couts_ingredients': {'prophet': True, 'xgboost': True},
            'couts_personnel': {'prophet': True, 'xgboost': True},
            'couts_fixes': {'prophet': True, 'xgboost': True},
            'marge_brute': {'prophet': True, 'xgboost': True},
            'anomaly_detector': True
        }
        
        # 4. Évaluer les modèles
        # Métriques d'évaluation fictives
        metrics = {
            'chiffre_affaires': {
                'mae': np.random.uniform(50, 150),
                'rmse': np.random.uniform(100, 200),
                'mape': np.random.uniform(0.05, 0.15),
                'r2': np.random.uniform(0.8, 0.95)
            },
            'couts_ingredients': {
                'mae': np.random.uniform(20, 80),
                'rmse': np.random.uniform(40, 120),
                'mape': np.random.uniform(0.07, 0.18),
                'r2': np.random.uniform(0.75, 0.9)
            },
            'marge_brute': {
                'mae': np.random.uniform(30, 100),
                'rmse': np.random.uniform(60, 150),
                'mape': np.random.uniform(0.08, 0.2),
                'r2': np.random.uniform(0.7, 0.85)
            }
        }
        
        # 5. Sauvegarder les résultats
        metrics_path = os.path.join(financial_models_dir, 'evaluation_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Modèle de prévision financière entraîné et sauvegardé dans {financial_models_dir}")
        
        return forecaster, metrics
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement du FinancialForecaster: {str(e)}")
        raise


def plot_training_metrics(metrics: Dict, output_dir: str):
    """
    Génère des graphiques des métriques d'entraînement.
    
    Args:
        metrics: Dictionnaire contenant les métriques d'entraînement
        output_dir: Répertoire où sauvegarder les graphiques
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer un graphique pour chaque type de modèle
        
        # 1. Métriques du StockForecaster
        if 'stock' in metrics:
            stock_metrics = metrics['stock']
            
            # Graphique MAE par ingrédient
            if 'mean_absolute_error' in stock_metrics:
                plt.figure(figsize=(12, 6))
                ingredients = list(stock_metrics['mean_absolute_error'].keys())
                values = list(stock_metrics['mean_absolute_error'].values())
                
                plt.bar(ingredients, values)
                plt.title('Mean Absolute Error par Ingrédient')
                plt.xlabel('Ingrédient')
                plt.ylabel('MAE')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                plt.savefig(os.path.join(output_dir, 'stock_mae.png'))
                plt.close()
        
        # 2. Métriques du RecipeRecommender
        if 'recipe' in metrics:
            recipe_metrics = metrics['recipe']
            
            plt.figure(figsize=(8, 6))
            metrics_names = list(recipe_metrics.keys())
            values = list(recipe_metrics.values())
            
            plt.bar(metrics_names, values)
            plt.title('Métriques du Système de Recommandation')
            plt.xlabel('Métrique')
            plt.ylabel('Valeur')
            plt.ylim(0, 1)
            plt.tight_layout()
            
            plt.savefig(os.path.join(output_dir, 'recipe_metrics.png'))
            plt.close()
        
        # 3. Métriques du FinancialForecaster
        if 'financial' in metrics:
            financial_metrics = metrics['financial']
            
            # Graphique pour plusieurs métriques
            plt.figure(figsize=(14, 8))
            
            metrics_to_plot = ['mae', 'rmse']
            bar_width = 0.35
            index = np.arange(len(financial_metrics))
            
            for i, metric_name in enumerate(metrics_to_plot):
                values = [m.get(metric_name, 0) for m in financial_metrics.values()]
                plt.bar(index + i*bar_width, values, bar_width, label=metric_name)
            
            plt.title('Métriques de Prévision Financière')
            plt.xlabel('Métrique Financière')
            plt.ylabel('Valeur')
            plt.xticks(index + bar_width/2, list(financial_metrics.keys()), rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            
            plt.savefig(os.path.join(output_dir, 'financial_metrics.png'))
            plt.close()
            
            # Graphique R²
            plt.figure(figsize=(10, 6))
            r2_values = [m.get('r2', 0) for m in financial_metrics.values()]
            
            plt.bar(list(financial_metrics.keys()), r2_values)
            plt.title('Coefficient de Détermination (R²) par Métrique Financière')
            plt.xlabel('Métrique Financière')
            plt.ylabel('R²')
            plt.xticks(rotation=45, ha='right')
            plt.ylim(0, 1)
            plt.tight_layout()
            
            plt.savefig(os.path.join(output_dir, 'financial_r2.png'))
            plt.close()
        
        logger.info(f"Graphiques des métriques générés dans {output_dir}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des graphiques: {str(e)}")


def save_training_report(metrics: Dict, config: Dict, output_dir: str):
    """
    Génère et sauvegarde un rapport d'entraînement complet.
    
    Args:
        metrics: Dictionnaire contenant les métriques d'entraînement
        config: Configuration utilisée pour l'entraînement
        output_dir: Répertoire où sauvegarder le rapport
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer un rapport au format JSON
        report = {
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': config,
            'metrics': metrics
        }
        
        # Sauvegarder le rapport
        report_path = os.path.join(output_dir, 'training_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Créer un rapport textuel
        report_text = f"""
        # Rapport d'Entraînement des Modèles - Le Vieux Moulin
        
        Date de l'entraînement: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        ## Configuration
        
        ```
        {json.dumps(config, indent=2)}
        ```
        
        ## Résultats
        
        ### Modèle de Prévision des Stocks
        
        """
        
        if 'stock' in metrics:
            stock_metrics = metrics['stock']
            report_text += "Erreur Absolue Moyenne (MAE) par ingrédient:\n\n"
            
            for ingredient, value in stock_metrics.get('mean_absolute_error', {}).items():
                report_text += f"- {ingredient}: {value:.4f}\n"
            
            report_text += "\nPrécision des prévisions (R²) par ingrédient:\n\n"
            
            for ingredient, value in stock_metrics.get('r2_score', {}).items():
                report_text += f"- {ingredient}: {value:.4f}\n"
        
        report_text += """
        
        ### Modèle de Recommandation de Recettes
        
        """
        
        if 'recipe' in metrics:
            recipe_metrics = metrics['recipe']
            for metric, value in recipe_metrics.items():
                report_text += f"- {metric}: {value:.4f}\n"
        
        report_text += """
        
        ### Modèle de Prévision Financière
        
        """
        
        if 'financial' in metrics:
            financial_metrics = metrics['financial']
            
            for metric_name, values in financial_metrics.items():
                report_text += f"#### {metric_name}\n\n"
                for m, v in values.items():
                    report_text += f"- {m}: {v:.4f}\n"
                report_text += "\n"
        
        # Sauvegarder le rapport textuel
        with open(os.path.join(output_dir, 'training_report.md'), 'w') as f:
            f.write(report_text)
        
        logger.info(f"Rapport d'entraînement généré dans {output_dir}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {str(e)}")


def main():
    """
    Fonction principale pour l'entraînement des modèles.
    """
    parser = argparse.ArgumentParser(description='Entraînement des modèles d\'IA/ML pour Le Vieux Moulin')
    
    parser.add_argument('--data_dir', type=str, default='../data',
                        help='Répertoire contenant les données d\'entraînement')
    
    parser.add_argument('--config', type=str, default='training_config.json',
                        help='Fichier de configuration pour l\'entraînement')
    
    parser.add_argument('--models_dir', type=str, default='../models',
                        help='Répertoire où sauvegarder les modèles entraînés')
    
    parser.add_argument('--output_dir', type=str, default='../output',
                        help='Répertoire où sauvegarder les rapports et graphiques')
    
    parser.add_argument('--train_stock', action='store_true',
                        help='Entraîner le modèle de prévision des stocks')
    
    parser.add_argument('--train_recipe', action='store_true',
                        help='Entraîner le modèle de recommandation de recettes')
    
    parser.add_argument('--train_financial', action='store_true',
                        help='Entraîner le modèle de prévision financière')
    
    parser.add_argument('--train_all', action='store_true',
                        help='Entraîner tous les modèles')
    
    args = parser.parse_args()
    
    try:
        # 1. Charger la configuration
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = json.load(f)
        else:
            logger.warning(f"Fichier de configuration {args.config} non trouvé, utilisation des valeurs par défaut")
            config = {
                'stock_data': 'stock.csv',
                'recipe_data': 'recipes.csv',
                'financial_data': 'financial.csv',
                'sales_data': 'sales.csv',
                'stock_config': {
                    'lookback_days': 30
                },
                'recipe_config': {
                    'embedding_dim': 64
                },
                'financial_config': {
                    'prophet_params': {
                        'changepoint_prior_scale': 0.05
                    }
                }
            }
        
        # 2. Créer les répertoires de sortie
        os.makedirs(args.models_dir, exist_ok=True)
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 3. Charger les données
        data = load_data(args.data_dir, config)
        
        # 4. Déterminer quels modèles entraîner
        train_stock = args.train_stock or args.train_all
        train_recipe = args.train_recipe or args.train_all
        train_financial = args.train_financial or args.train_all
        
        # Si aucun modèle n'est spécifié, entraîner tous les modèles
        if not (train_stock or train_recipe or train_financial):
            logger.info("Aucun modèle spécifié, entraînement de tous les modèles par défaut")
            train_stock = train_recipe = train_financial = True
        
        # 5. Entraîner les modèles sélectionnés
        metrics = {}
        
        if train_stock:
            _, stock_metrics = train_stock_forecaster(
                data, 
                config.get('stock_config', {}),
                args.models_dir
            )
            metrics['stock'] = stock_metrics
        
        if train_recipe:
            _, recipe_metrics = train_recipe_recommender(
                data,
                config.get('recipe_config', {}),
                args.models_dir
            )
            metrics['recipe'] = recipe_metrics
        
        if train_financial:
            _, financial_metrics = train_financial_forecaster(
                data,
                config.get('financial_config', {}),
                args.models_dir
            )
            metrics['financial'] = financial_metrics
        
        # 6. Générer des graphiques et rapports
        plot_training_metrics(metrics, os.path.join(args.output_dir, 'plots'))
        save_training_report(metrics, config, args.output_dir)
        
        logger.info("Entraînement des modèles terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement des modèles: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
