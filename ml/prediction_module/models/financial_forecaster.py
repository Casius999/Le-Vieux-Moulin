#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de prévision financière pour le restaurant Le Vieux Moulin.

Ce module implémente un système ensemble qui combine plusieurs modèles:
- Prophet pour la décomposition des séries temporelles et tendances à long terme
- XGBoost pour les variations à court terme
- Isolation Forest pour la détection d'anomalies financières

Il fournit des prévisions de métriques financières clés pour le module de comptabilité.
"""

import os
import json
import logging
import warnings
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Supprimer les avertissements obsolètes de Prophet
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialForecaster:
    """
    Système de prévision financière multi-modèle pour le restaurant.
    
    Cette classe implémente un système qui combine plusieurs approches:
    - Modélisation des tendances à long terme avec Prophet
    - Capture des variations à court terme avec XGBoost
    - Détection d'anomalies pour identifier les transactions inhabituelles
    
    Elle permet de prévoir différentes métriques financières comme le chiffre d'affaires,
    les coûts, les marges, etc.
    """
    
    def __init__(
        self,
        models_dir: str = None,
        financial_history_path: str = None,
        metrics: Optional[List[str]] = None,
        default_horizon: int = 30
    ):
        """
        Initialise le système de prévision financière.
        
        Args:
            models_dir: Répertoire contenant les modèles entraînés
            financial_history_path: Chemin vers l'historique financier
            metrics: Liste des métriques à prévoir (chiffre_affaires, couts, marge, etc.)
            default_horizon: Horizon de prévision par défaut en jours
        """
        self.models_dir = models_dir
        self.financial_history_path = financial_history_path
        self.default_horizon = default_horizon
        
        # Liste des métriques par défaut si non spécifiées
        self.metrics = metrics or [
            'chiffre_affaires', 'couts_ingredients', 'couts_personnel',
            'couts_fixes', 'marge_brute'
        ]
        
        # Attributs pour les modèles
        self.prophet_models = {}  # Modèles Prophet par métrique
        self.xgboost_models = {}  # Modèles XGBoost par métrique
        self.anomaly_detector = None  # Détecteur d'anomalies
        self.scalers = {}  # Scalers pour normaliser les données
        
        # Données financières
        self.financial_data = None
        
        # Chargement des données si le chemin est spécifié
        if financial_history_path and os.path.exists(financial_history_path):
            self._load_financial_data()
        
        # Chargement des modèles si le répertoire est spécifié
        if models_dir and os.path.exists(models_dir):
            self._load_models()
    
    def _load_financial_data(self) -> None:
        """
        Charge les données financières historiques.
        """
        try:
            logger.info(f"Chargement des données financières depuis {self.financial_history_path}")
            
            # Chargement du CSV ou autre format
            if self.financial_history_path.endswith('.csv'):
                self.financial_data = pd.read_csv(
                    self.financial_history_path, 
                    parse_dates=['date']
                )
            elif self.financial_history_path.endswith('.json'):
                self.financial_data = pd.read_json(self.financial_history_path)
                if 'date' in self.financial_data.columns:
                    self.financial_data['date'] = pd.to_datetime(self.financial_data['date'])
            else:
                raise ValueError(f"Format de fichier non pris en charge: {self.financial_history_path}")
            
            # Vérifier que toutes les métriques requises sont présentes
            missing_metrics = [m for m in self.metrics if m not in self.financial_data.columns]
            if missing_metrics:
                logger.warning(f"Métriques manquantes dans les données: {', '.join(missing_metrics)}")
            
            logger.info(f"Données financières chargées: {len(self.financial_data)} enregistrements")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données financières: {str(e)}")
            raise
    
    def _load_models(self) -> None:
        """
        Charge les modèles pré-entraînés pour chaque métrique.
        """
        try:
            logger.info(f"Chargement des modèles depuis {self.models_dir}")
            
            # Charger les modèles Prophet
            prophet_dir = os.path.join(self.models_dir, 'prophet')
            if os.path.exists(prophet_dir):
                for metric in self.metrics:
                    model_path = os.path.join(prophet_dir, f"{metric}_prophet.json")
                    if os.path.exists(model_path):
                        with open(model_path, 'r') as fin:
                            self.prophet_models[metric] = Prophet.from_json(json.load(fin))
                        logger.info(f"Modèle Prophet chargé pour {metric}")
            
            # Charger les modèles XGBoost
            xgboost_dir = os.path.join(self.models_dir, 'xgboost')
            if os.path.exists(xgboost_dir):
                for metric in self.metrics:
                    model_path = os.path.join(xgboost_dir, f"{metric}_xgboost.model")
                    if os.path.exists(model_path):
                        self.xgboost_models[metric] = xgb.Booster()
                        self.xgboost_models[metric].load_model(model_path)
                        logger.info(f"Modèle XGBoost chargé pour {metric}")
            
            # Charger le détecteur d'anomalies
            anomaly_path = os.path.join(self.models_dir, 'anomaly_detector.pkl')
            if os.path.exists(anomaly_path):
                import joblib
                self.anomaly_detector = joblib.load(anomaly_path)
                logger.info("Détecteur d'anomalies chargé")
            
            # Charger les scalers
            scalers_dir = os.path.join(self.models_dir, 'scalers')
            if os.path.exists(scalers_dir):
                import joblib
                for metric in self.metrics:
                    scaler_path = os.path.join(scalers_dir, f"{metric}_scaler.pkl")
                    if os.path.exists(scaler_path):
                        self.scalers[metric] = joblib.load(scaler_path)
                        logger.info(f"Scaler chargé pour {metric}")
            
            logger.info("Modèles chargés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {str(e)}")
            raise
    
    def _prepare_prophet_data(
        self,
        metric: str,
        start_date: datetime,
        days: int
    ) -> pd.DataFrame:
        """
        Prépare les données pour les prévisions avec Prophet.
        
        Args:
            metric: Nom de la métrique à prévoir
            start_date: Date de début de la prévision
            days: Nombre de jours à prévoir
            
        Returns:
            DataFrame formaté pour Prophet
        """
        # Créer un DataFrame avec les dates futures
        future = pd.DataFrame({
            'ds': [start_date + timedelta(days=i) for i in range(days)]
        })
        
        # Ajouter des caractéristiques contextuelles
        future['weekday'] = future['ds'].dt.weekday
        future['month'] = future['ds'].dt.month
        future['day'] = future['ds'].dt.day
        future['is_weekend'] = (future['weekday'] >= 5).astype(int)
        
        # Ajouter des indicateurs pour les périodes spéciales
        
        # Période estivale (haute saison pour un restaurant à Vensac)
        future['is_summer'] = ((future['month'] >= 6) & (future['month'] <= 8)).astype(int)
        
        # Vacances scolaires françaises (simplifié pour l'exemple)
        # Dans une implémentation réelle, ces dates seraient plus précises
        summer_holidays = ((future['month'] == 7) | (future['month'] == 8))
        winter_holidays = ((future['month'] == 12) & (future['day'] >= 20)) | ((future['month'] == 1) & (future['day'] <= 5))
        future['is_holiday'] = (summer_holidays | winter_holidays).astype(int)
        
        return future
    
    def _prepare_xgboost_data(
        self,
        metric: str,
        prophet_forecast: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Prépare les données pour les prévisions XGBoost à partir des résultats Prophet.
        
        Args:
            metric: Nom de la métrique à prévoir
            prophet_forecast: Résultats de la prévision Prophet
            
        Returns:
            DataFrame formaté pour XGBoost
        """
        # Extraire les caractéristiques pertinentes du forecast Prophet
        features = prophet_forecast[['ds', 'yhat', 'trend', 'weekly', 'yearly']]
        
        # Ajouter des caractéristiques temporelles
        features['weekday'] = features['ds'].dt.weekday
        features['month'] = features['ds'].dt.month
        features['day'] = features['ds'].dt.day
        features['is_weekend'] = (features['weekday'] >= 5).astype(int)
        
        # Période estivale
        features['is_summer'] = ((features['month'] >= 6) & (features['month'] <= 8)).astype(int)
        
        # Encodage one-hot pour certaines caractéristiques
        weekday_dummies = pd.get_dummies(features['weekday'], prefix='weekday')
        month_dummies = pd.get_dummies(features['month'], prefix='month')
        
        # Combiner toutes les caractéristiques
        final_features = pd.concat([features, weekday_dummies, month_dummies], axis=1)
        
        # Supprimer les colonnes inutiles pour XGBoost
        final_features = final_features.drop(['ds', 'weekday', 'month'], axis=1)
        
        return final_features
    
    def train_models(
        self,
        save_dir: Optional[str] = None,
        prophet_params: Optional[Dict] = None,
        xgboost_params: Optional[Dict] = None,
        retrain_anomaly_detector: bool = True
    ) -> Dict:
        """
        Entraîne les modèles de prévision financière.
        
        Args:
            save_dir: Répertoire où sauvegarder les modèles entraînés
            prophet_params: Paramètres pour les modèles Prophet
            xgboost_params: Paramètres pour les modèles XGBoost
            retrain_anomaly_detector: Réentraîner le détecteur d'anomalies
            
        Returns:
            Dictionnaire avec les performances d'entraînement
        """
        if self.financial_data is None:
            raise ValueError("Aucune donnée financière chargée pour l'entraînement.")
        
        # Paramètres par défaut
        default_prophet_params = {
            'changepoint_prior_scale': 0.05,
            'seasonality_prior_scale': 10,
            'holidays_prior_scale': 10,
            'daily_seasonality': False,
            'weekly_seasonality': True,
            'yearly_seasonality': True
        }
        
        default_xgboost_params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'verbosity': 0
        }
        
        # Utiliser les paramètres spécifiés ou les paramètres par défaut
        prophet_params = prophet_params or default_prophet_params
        xgboost_params = xgboost_params or default_xgboost_params
        
        # Répertoire de sauvegarde par défaut
        if save_dir is None:
            save_dir = os.path.join('models', 'financial')
            os.makedirs(save_dir, exist_ok=True)
        
        # Créer sous-répertoires
        prophet_dir = os.path.join(save_dir, 'prophet')
        xgboost_dir = os.path.join(save_dir, 'xgboost')
        scalers_dir = os.path.join(save_dir, 'scalers')
        
        os.makedirs(prophet_dir, exist_ok=True)
        os.makedirs(xgboost_dir, exist_ok=True)
        os.makedirs(scalers_dir, exist_ok=True)
        
        # Résultats d'entraînement
        training_results = {}
        
        # Entraîner les modèles pour chaque métrique
        for metric in self.metrics:
            if metric not in self.financial_data.columns:
                logger.warning(f"Métrique {metric} non trouvée dans les données, ignorer...")
                continue
            
            logger.info(f"Entraînement des modèles pour {metric}...")
            training_results[metric] = {}
            
            # Préparer les données
            df = self.financial_data[['date', metric]].copy()
            df.columns = ['ds', 'y']  # Format requis par Prophet
            
            # 1. Entraîner le modèle Prophet
            try:
                logger.info(f"Entraînement du modèle Prophet pour {metric}")
                model = Prophet(**prophet_params)
                model.fit(df)
                
                # Sauvegarder le modèle
                with open(os.path.join(prophet_dir, f"{metric}_prophet.json"), 'w') as fout:
                    json.dump(model.to_json(), fout)
                
                self.prophet_models[metric] = model
                training_results[metric]['prophet'] = True
                
            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement du modèle Prophet pour {metric}: {str(e)}")
                training_results[metric]['prophet'] = False
            
            # 2. Entraîner le modèle XGBoost avec les résidus de Prophet
            try:
                # Obtenir les prévisions in-sample de Prophet
                prophet_forecast = model.predict(df)
                
                # Calculer les résidus
                prophet_forecast = prophet_forecast.merge(df, on='ds', how='left')
                prophet_forecast['residuals'] = prophet_forecast['y'] - prophet_forecast['yhat']
                
                # Préparer les caractéristiques
                features = self._prepare_xgboost_data(metric, prophet_forecast)
                
                # Définir la cible (résidus)
                target = prophet_forecast['residuals']
                
                # Entraîner le modèle XGBoost
                logger.info(f"Entraînement du modèle XGBoost pour {metric}")
                dtrain = xgb.DMatrix(features, label=target)
                model_xgb = xgb.train(
                    xgboost_params,
                    dtrain,
                    num_boost_round=xgboost_params['n_estimators']
                )
                
                # Sauvegarder le modèle
                model_xgb.save_model(os.path.join(xgboost_dir, f"{metric}_xgboost.model"))
                
                self.xgboost_models[metric] = model_xgb
                training_results[metric]['xgboost'] = True
                
                # Créer et sauvegarder le scaler pour cette métrique
                import joblib
                scaler = StandardScaler()
                scaler.fit(features)
                joblib.dump(scaler, os.path.join(scalers_dir, f"{metric}_scaler.pkl"))
                self.scalers[metric] = scaler
                
            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement du modèle XGBoost pour {metric}: {str(e)}")
                training_results[metric]['xgboost'] = False
        
        # 3. Entraîner le détecteur d'anomalies
        if retrain_anomaly_detector:
            try:
                logger.info("Entraînement du détecteur d'anomalies")
                
                # Préparer les données pour la détection d'anomalies
                anomaly_data = self.financial_data[self.metrics].copy()
                
                # Normaliser les données
                scaler = StandardScaler()
                anomaly_data_scaled = scaler.fit_transform(anomaly_data)
                
                # Entraîner le modèle Isolation Forest
                model = IsolationForest(
                    contamination=0.02,  # 2% de données considérées comme anomalies
                    random_state=42
                )
                model.fit(anomaly_data_scaled)
                
                # Sauvegarder le modèle
                import joblib
                joblib.dump(model, os.path.join(save_dir, 'anomaly_detector.pkl'))
                joblib.dump(scaler, os.path.join(scalers_dir, 'anomaly_scaler.pkl'))
                
                self.anomaly_detector = model
                training_results['anomaly_detector'] = True
                
            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement du détecteur d'anomalies: {str(e)}")
                training_results['anomaly_detector'] = False
        
        logger.info("Entraînement des modèles financiers terminé")
        return training_results
    
    def predict(
        self,
        metrics: Optional[List[str]] = None,
        days_ahead: Optional[int] = None,
        start_date: Optional[datetime] = None,
        include_components: bool = False,
        detect_anomalies: bool = False
    ) -> Dict:
        """
        Génère des prévisions financières.
        
        Args:
            metrics: Liste des métriques à prévoir (utilise toutes les métriques disponibles si None)
            days_ahead: Nombre de jours à prévoir (utilise default_horizon si None)
            start_date: Date de début de la prévision (aujourd'hui si None)
            include_components: Inclure les composantes des prévisions (tendance, saisonnalité, etc.)
            detect_anomalies: Détecter les anomalies dans les données historiques récentes
            
        Returns:
            Dictionnaire avec les prévisions par métrique et par jour
        """
        # Vérifier que les modèles sont chargés
        if not self.prophet_models:
            raise ValueError("Aucun modèle Prophet chargé. Utilisez _load_models() avant de faire des prédictions.")
        
        # Paramètres par défaut
        if days_ahead is None:
            days_ahead = self.default_horizon
            
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Si metrics n'est pas spécifié, utiliser toutes les métriques disponibles
        if metrics is None:
            metrics = list(self.prophet_models.keys())
        else:
            # Vérifier que les métriques demandées sont disponibles
            for metric in metrics:
                if metric not in self.prophet_models:
                    logger.warning(f"Aucun modèle disponible pour la métrique {metric}")
        
        # Résultats des prévisions
        forecasts = {}
        
        # Générer les prévisions pour chaque métrique
        for metric in metrics:
            if metric not in self.prophet_models:
                continue
            
            logger.info(f"Génération des prévisions pour {metric}")
            
            # 1. Prévisions avec Prophet
            try:
                future = self._prepare_prophet_data(metric, start_date, days_ahead)
                prophet_forecast = self.prophet_models[metric].predict(future)
                
                # 2. Affiner avec XGBoost si disponible
                if metric in self.xgboost_models:
                    try:
                        # Préparer les caractéristiques pour XGBoost
                        xgb_features = self._prepare_xgboost_data(metric, prophet_forecast)
                        
                        # Prédire les résidus
                        dmatrix = xgb.DMatrix(xgb_features)
                        residuals = self.xgboost_models[metric].predict(dmatrix)
                        
                        # Ajuster les prévisions
                        prophet_forecast['yhat_adjusted'] = prophet_forecast['yhat'] + residuals
                        
                        # Utiliser les prévisions ajustées
                        forecast_values = prophet_forecast['yhat_adjusted'].values
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'ajustement XGBoost pour {metric}: {str(e)}")
                        forecast_values = prophet_forecast['yhat'].values
                else:
                    forecast_values = prophet_forecast['yhat'].values
                
                # Créer le résultat
                result = {
                    'dates': [d.strftime('%Y-%m-%d') for d in prophet_forecast['ds']],
                    'values': [float(v) for v in forecast_values],
                    'lower_bound': [float(v) for v in prophet_forecast['yhat_lower']],
                    'upper_bound': [float(v) for v in prophet_forecast['yhat_upper']]
                }
                
                # Ajouter les composantes si demandé
                if include_components:
                    result['components'] = {
                        'trend': [float(v) for v in prophet_forecast['trend']],
                        'weekly': [float(v) for v in prophet_forecast['weekly']],
                        'yearly': [float(v) for v in prophet_forecast['yearly']]
                    }
                
                forecasts[metric] = result
                
            except Exception as e:
                logger.error(f"Erreur lors de la prévision pour {metric}: {str(e)}")
                continue
        
        # Détecter les anomalies si demandé et si des données historiques sont disponibles
        if detect_anomalies and self.anomaly_detector and self.financial_data is not None:
            try:
                # Utiliser les 30 derniers jours pour la détection
                recent_data = self.financial_data.sort_values('date').tail(30)
                
                if len(recent_data) > 0:
                    # Sélectionner uniquement les métriques disponibles
                    anomaly_data = recent_data[metrics].copy()
                    
                    # Normaliser les données
                    scaler = StandardScaler()
                    anomaly_data_scaled = scaler.fit_transform(anomaly_data)
                    
                    # Détecter les anomalies
                    anomaly_scores = self.anomaly_detector.decision_function(anomaly_data_scaled)
                    anomaly_predictions = self.anomaly_detector.predict(anomaly_data_scaled)
                    
                    # Ajouter les résultats de détection d'anomalies
                    forecasts['anomalies'] = {
                        'dates': [d.strftime('%Y-%m-%d') for d in recent_data['date']],
                        'scores': [float(s) for s in anomaly_scores],
                        'is_anomaly': [int(p) == -1 for p in anomaly_predictions]
                    }
                    
                    # Compter les anomalies
                    num_anomalies = sum(1 for p in anomaly_predictions if p == -1)
                    logger.info(f"Détection d'anomalies: {num_anomalies} anomalies trouvées sur les 30 derniers jours")
                
            except Exception as e:
                logger.error(f"Erreur lors de la détection d'anomalies: {str(e)}")
        
        return forecasts
    
    def generate_financial_report(
        self,
        days_ahead: int = 30,
        start_date: Optional[datetime] = None,
        format: str = 'json'
    ) -> Dict:
        """
        Génère un rapport financier complet avec prévisions et analyses.
        
        Args:
            days_ahead: Nombre de jours à prévoir
            start_date: Date de début de la prévision (aujourd'hui si None)
            format: Format du rapport ('json' ou 'csv')
            
        Returns:
            Rapport financier complet
        """
        # Générer les prévisions de base
        forecasts = self.predict(
            days_ahead=days_ahead,
            start_date=start_date,
            include_components=True,
            detect_anomalies=True
        )
        
        # Calculer des métriques dérivées
        try:
            # S'assurer que toutes les métriques nécessaires sont disponibles
            required_metrics = ['chiffre_affaires', 'couts_ingredients', 'couts_personnel', 'couts_fixes']
            if all(metric in forecasts for metric in required_metrics):
                dates = forecasts['chiffre_affaires']['dates']
                num_days = len(dates)
                
                # Calculer la marge nette: CA - (coûts ingrédients + personnel + fixes)
                marge_nette = []
                for i in range(num_days):
                    ca = forecasts['chiffre_affaires']['values'][i]
                    ci = forecasts['couts_ingredients']['values'][i]
                    cp = forecasts['couts_personnel']['values'][i]
                    cf = forecasts['couts_fixes']['values'][i]
                    marge = ca - (ci + cp + cf)
                    marge_nette.append(marge)
                
                # Calculer le ratio de rentabilité (marge / CA)
                rentabilite = []
                for i in range(num_days):
                    ca = forecasts['chiffre_affaires']['values'][i]
                    if ca > 0:
                        ratio = marge_nette[i] / ca
                    else:
                        ratio = 0
                    rentabilite.append(ratio)
                
                # Ajouter ces métriques dérivées aux prévisions
                forecasts['marge_nette'] = {
                    'dates': dates,
                    'values': marge_nette
                }
                
                forecasts['rentabilite'] = {
                    'dates': dates,
                    'values': rentabilite
                }
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des métriques dérivées: {str(e)}")
        
        # Calculer des statistiques agrégées
        report = {
            'forecasts': forecasts,
            'summary': {}
        }
        
        # Récapitulatif sur différentes périodes
        periods = {
            'week1': 7,
            'week2': 14,
            'month': min(30, days_ahead)
        }
        
        for metric, data in forecasts.items():
            if metric == 'anomalies':
                continue
                
            report['summary'][metric] = {}
            
            for period_name, days in periods.items():
                if days <= len(data['values']):
                    period_values = data['values'][:days]
                    report['summary'][metric][period_name] = {
                        'total': sum(period_values),
                        'average': sum(period_values) / days,
                        'min': min(period_values),
                        'max': max(period_values)
                    }
        
        # Format CSV si demandé
        if format == 'csv':
            import io
            import csv
            
            # Pour chaque métrique, créer un CSV
            csv_outputs = {}
            
            for metric, data in forecasts.items():
                if metric == 'anomalies':
                    continue
                    
                output = io.StringIO()
                writer = csv.writer(output)
                
                # En-tête
                header = ['date', 'value']
                if 'lower_bound' in data:
                    header.extend(['lower_bound', 'upper_bound'])
                if 'components' in data:
                    header.extend(['trend', 'weekly', 'yearly'])
                
                writer.writerow(header)
                
                # Données
                for i, date in enumerate(data['dates']):
                    row = [date, data['values'][i]]
                    if 'lower_bound' in data:
                        row.extend([data['lower_bound'][i], data['upper_bound'][i]])
                    if 'components' in data:
                        row.extend([
                            data['components']['trend'][i],
                            data['components']['weekly'][i],
                            data['components']['yearly'][i]
                        ])
                    
                    writer.writerow(row)
                
                csv_outputs[metric] = output.getvalue()
                output.close()
            
            return csv_outputs
        
        # Sinon, retourner le format JSON
        return report


# Fonction d'utilisation pour les tests
def example_usage():
    """
    Exemple d'utilisation du modèle FinancialForecaster.
    """
    # Création de données fictives pour l'exemple
    dates = pd.date_range(start='2024-01-01', periods=450)  # Environ 15 mois d'historique
    
    np.random.seed(42)
    
    # Simuler le chiffre d'affaires avec tendance, saisonnalité et bruit
    ca_base = 1500  # CA quotidien de base
    ca_trend = np.linspace(0, 500, len(dates))  # Tendance à la hausse
    
    # Saisonnalité hebdomadaire (weekend plus élevé)
    ca_weekly = np.array([0, 0, 0, 0, 100, 300, 200] * (len(dates) // 7 + 1))[:len(dates)]
    
    # Saisonnalité annuelle (été plus élevé)
    days_in_year = 365
    ca_yearly = 300 * np.sin(2 * np.pi * np.arange(len(dates)) / days_in_year - 0.5 * np.pi)
    
    # Bruit aléatoire
    ca_noise = np.random.normal(0, 100, len(dates))
    
    # Chiffre d'affaires total
    ca_values = ca_base + ca_trend + ca_weekly + ca_yearly + ca_noise
    ca_values = np.maximum(ca_values, 0)  # Pas de CA négatif
    
    # Coûts des ingrédients (environ 30% du CA)
    couts_ingredients = 0.3 * ca_values + np.random.normal(0, 30, len(dates))
    couts_ingredients = np.maximum(couts_ingredients, 0)
    
    # Coûts de personnel (fixe avec légère variation)
    couts_personnel_base = 500
    couts_personnel = couts_personnel_base + 0.1 * ca_values + np.random.normal(0, 20, len(dates))
    
    # Coûts fixes
    couts_fixes = np.ones(len(dates)) * 300 + np.random.normal(0, 10, len(dates))
    
    # Créer le DataFrame
    data = {
        'date': dates,
        'chiffre_affaires': ca_values,
        'couts_ingredients': couts_ingredients,
        'couts_personnel': couts_personnel,
        'couts_fixes': couts_fixes,
        'marge_brute': ca_values - couts_ingredients
    }
    
    financial_data = pd.DataFrame(data)
    
    # Initialiser le modèle et injecter les données
    forecaster = FinancialForecaster()
    forecaster.financial_data = financial_data
    
    # Pour cet exemple, créons des modèles simples directement
    # Dans un cas réel, on entraînerait et sauvegarderait les modèles
    
    # Modèle Prophet simplifié pour le chiffre d'affaires
    try:
        print("Entraînement d'un modèle Prophet simplifié...")
        
        # Préparer les données pour Prophet
        df = financial_data[['date', 'chiffre_affaires']].copy()
        df.columns = ['ds', 'y']
        
        # Créer et entraîner un modèle Prophet simplifié
        model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True
        )
        model.fit(df)
        
        # Injecter le modèle
        forecaster.prophet_models['chiffre_affaires'] = model
        
        # Générer des prévisions
        print("\nGénération des prévisions financières pour les 30 prochains jours:")
        predictions = forecaster.predict(
            metrics=['chiffre_affaires'],
            days_ahead=30,
            start_date=datetime(2025, 4, 1)
        )
        
        # Afficher les résultats
        for metric, forecast in predictions.items():
            print(f"\nPrévisions pour {metric}:")
            for i in range(min(7, len(forecast['dates']))):  # Afficher les 7 premiers jours
                date = forecast['dates'][i]
                value = forecast['values'][i]
                lower = forecast.get('lower_bound', [0] * len(forecast['dates']))[i]
                upper = forecast.get('upper_bound', [0] * len(forecast['dates']))[i]
                
                print(f"  {date}: {value:.2f} € (intervalle: {lower:.2f} € - {upper:.2f} €)")
            
            # Totaux
            total = sum(forecast['values'])
            print(f"\n  Total prévu sur 30 jours: {total:.2f} €")
            print(f"  Moyenne journalière: {total/30:.2f} €")
    
    except Exception as e:
        print(f"Erreur lors de l'exemple d'utilisation: {str(e)}")


if __name__ == "__main__":
    # Exécuter l'exemple d'utilisation si ce script est exécuté directement
    example_usage()
