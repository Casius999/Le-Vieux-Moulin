#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de prétraitement des données pour les modèles prédictifs du restaurant Le Vieux Moulin.

Ce module contient des classes et fonctions pour:
- Nettoyer les données brutes
- Normaliser les valeurs
- Créer des features avancées
- Gérer les valeurs manquantes
- Segmenter les données pour l'entraînement, la validation et le test
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Classe principale pour le prétraitement des données.
    
    Gère le nettoyage, la normalisation, et la segmentation des données
    pour les différents modèles de prédiction.
    """
    
    def __init__(
        self,
        scaling_method: str = 'standard',
        handle_outliers: bool = True,
        handle_missing: bool = True,
        time_features: bool = True
    ):
        """
        Initialise le préprocesseur de données.
        
        Args:
            scaling_method: Méthode de normalisation ('standard', 'minmax', 'robust', None)
            handle_outliers: Activer la détection et le traitement des valeurs aberrantes
            handle_missing: Activer la gestion des valeurs manquantes
            time_features: Créer des caractéristiques temporelles (jour de semaine, mois, etc.)
        """
        self.scaling_method = scaling_method
        self.handle_outliers = handle_outliers
        self.handle_missing = handle_missing
        self.time_features = time_features
        
        # Attributs pour les transformations
        self.scalers = {}
        self.outlier_params = {}
        self.categorical_mappings = {}
        
        logger.info(f"Préprocesseur initialisé avec scaling_method={scaling_method}, "
                    f"handle_outliers={handle_outliers}, handle_missing={handle_missing}")
    
    def fit_transform(
        self,
        data: pd.DataFrame,
        target_cols: Optional[List[str]] = None,
        date_col: Optional[str] = 'date',
        categorical_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Ajuste les transformations et les applique aux données.
        
        Args:
            data: DataFrame contenant les données brutes
            target_cols: Colonnes cibles pour les prédictions (qui devront être normalisées)
            date_col: Nom de la colonne de date
            categorical_cols: Liste des colonnes catégorielles à encoder
            
        Returns:
            DataFrame prétraité
        """
        if data.empty:
            logger.warning("DataFrame vide fourni pour le prétraitement")
            return data.copy()
        
        logger.info(f"Début du prétraitement pour {len(data)} lignes de données")
        
        # Copie des données pour éviter de modifier l'original
        processed_data = data.copy()
        
        # 1. Nettoyage de base
        processed_data = self._clean_data(processed_data)
        
        # 2. Gestion des valeurs manquantes
        if self.handle_missing:
            processed_data = self._handle_missing_values(processed_data, target_cols)
        
        # 3. Traitement des valeurs aberrantes
        if self.handle_outliers:
            processed_data = self._handle_outliers(processed_data, target_cols)
        
        # 4. Extraction de caractéristiques temporelles
        if self.time_features and date_col in processed_data.columns:
            processed_data = self._extract_time_features(processed_data, date_col)
        
        # 5. Encodage des variables catégorielles
        if categorical_cols:
            processed_data = self._encode_categorical(processed_data, categorical_cols)
        
        # 6. Normalisation des données numériques
        if target_cols and self.scaling_method:
            processed_data = self._scale_features(processed_data, target_cols)
        
        logger.info(f"Prétraitement terminé: {len(processed_data)} lignes, "
                   f"{len(processed_data.columns)} colonnes")
        
        return processed_data
    
    def transform(
        self,
        data: pd.DataFrame,
        target_cols: Optional[List[str]] = None,
        date_col: Optional[str] = 'date',
        categorical_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Applique les transformations ajustées à de nouvelles données.
        
        Args:
            data: DataFrame contenant les nouvelles données
            target_cols: Colonnes cibles pour les prédictions
            date_col: Nom de la colonne de date
            categorical_cols: Liste des colonnes catégorielles
            
        Returns:
            DataFrame prétraité
        """
        if data.empty:
            logger.warning("DataFrame vide fourni pour la transformation")
            return data.copy()
        
        logger.info(f"Transformation de {len(data)} lignes de données")
        
        # Copie des données pour éviter de modifier l'original
        processed_data = data.copy()
        
        # 1. Nettoyage de base
        processed_data = self._clean_data(processed_data)
        
        # 2. Gestion des valeurs manquantes (mode transformation)
        if self.handle_missing:
            processed_data = self._handle_missing_values(processed_data, target_cols, fit=False)
        
        # 3. Pas de traitement des outliers en mode transformation (pour éviter les biais)
        
        # 4. Extraction de caractéristiques temporelles
        if self.time_features and date_col in processed_data.columns:
            processed_data = self._extract_time_features(processed_data, date_col)
        
        # 5. Encodage des variables catégorielles
        if categorical_cols:
            processed_data = self._encode_categorical(processed_data, categorical_cols, fit=False)
        
        # 6. Normalisation des données numériques
        if target_cols and self.scaling_method and self.scalers:
            processed_data = self._scale_features(processed_data, target_cols, fit=False)
        
        return processed_data
    
    def inverse_transform(
        self,
        data: pd.DataFrame,
        target_cols: List[str]
    ) -> pd.DataFrame:
        """
        Inverse les transformations pour obtenir les valeurs originales.
        
        Args:
            data: DataFrame contenant les données transformées
            target_cols: Colonnes à dénormaliser
            
        Returns:
            DataFrame avec les valeurs dénormalisées
        """
        if data.empty:
            return data.copy()
        
        logger.info(f"Inversion des transformations pour {len(data)} lignes")
        
        # Copie des données
        restored_data = data.copy()
        
        # Inverser la normalisation
        if self.scaling_method and self.scalers:
            for col in target_cols:
                if col in self.scalers and col in restored_data.columns:
                    try:
                        # Extraire la colonne et la reformater pour l'inversion
                        col_data = restored_data[col].values.reshape(-1, 1)
                        # Inverser la normalisation
                        restored_values = self.scalers[col].inverse_transform(col_data)
                        # Remplacer les valeurs
                        restored_data[col] = restored_values.flatten()
                    except Exception as e:
                        logger.error(f"Erreur lors de l'inversion de la normalisation pour {col}: {str(e)}")
                        # Garder les valeurs originales en cas d'erreur
        
        return restored_data
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Effectue un nettoyage de base des données.
        
        Args:
            data: DataFrame à nettoyer
            
        Returns:
            DataFrame nettoyé
        """
        # Copie pour éviter de modifier l'original
        cleaned_data = data.copy()
        
        # 1. Supprimer les doublons
        initial_rows = len(cleaned_data)
        cleaned_data = cleaned_data.drop_duplicates()
        if len(cleaned_data) < initial_rows:
            logger.info(f"Suppression de {initial_rows - len(cleaned_data)} lignes dupliquées")
        
        # 2. Convertir les types de données appropriés
        # Conversion des dates
        date_columns = [col for col in cleaned_data.columns if 'date' in col.lower()]
        for col in date_columns:
            if col in cleaned_data.columns:
                try:
                    cleaned_data[col] = pd.to_datetime(cleaned_data[col])
                except Exception as e:
                    logger.warning(f"Impossible de convertir la colonne {col} en datetime: {str(e)}")
        
        # 3. Supprimer les espaces inutiles dans les chaînes
        string_columns = cleaned_data.select_dtypes(include=['object']).columns
        for col in string_columns:
            cleaned_data[col] = cleaned_data[col].str.strip() if isinstance(cleaned_data[col], pd.Series) else cleaned_data[col]
        
        return cleaned_data
    
    def _handle_missing_values(
        self,
        data: pd.DataFrame,
        target_cols: Optional[List[str]] = None,
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Gère les valeurs manquantes dans les données.
        
        Args:
            data: DataFrame contenant potentiellement des valeurs manquantes
            target_cols: Colonnes cibles pour les prédictions
            fit: Ajuster les valeurs de remplacement (True) ou utiliser celles existantes (False)
            
        Returns:
            DataFrame sans valeurs manquantes
        """
        # Copie pour éviter de modifier l'original
        filled_data = data.copy()
        
        # Vérifier s'il y a des valeurs manquantes
        missing_counts = filled_data.isnull().sum()
        total_missing = missing_counts.sum()
        
        if total_missing == 0:
            logger.info("Aucune valeur manquante détectée")
            return filled_data
        
        logger.info(f"Traitement de {total_missing} valeurs manquantes")
        
        # Pour les colonnes target, utilisation de méthodes plus sophistiquées
        if target_cols:
            for col in target_cols:
                if col in filled_data.columns and filled_data[col].isnull().sum() > 0:
                    # Mémoriser la stratégie d'imputation
                    if fit:
                        # Utiliser la médiane pour les variables numériques (plus robuste que la moyenne)
                        if np.issubdtype(filled_data[col].dtype, np.number):
                            fill_value = filled_data[col].median()
                            self.outlier_params[f"{col}_fill"] = fill_value
                        else:
                            # Mode pour les variables catégorielles
                            fill_value = filled_data[col].mode()[0]
                            self.outlier_params[f"{col}_fill"] = fill_value
                    else:
                        # Utiliser la valeur mémorisée
                        fill_value = self.outlier_params.get(f"{col}_fill", filled_data[col].median())
                    
                    # Remplacer les valeurs manquantes
                    filled_data[col] = filled_data[col].fillna(fill_value)
        
        # Pour les autres colonnes, utilisation de stratégies simples
        # Colonnes numériques
        numeric_cols = filled_data.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if col not in target_cols and filled_data[col].isnull().sum() > 0:
                filled_data[col] = filled_data[col].fillna(0)
        
        # Colonnes catégorielles
        categorical_cols = filled_data.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if filled_data[col].isnull().sum() > 0:
                filled_data[col] = filled_data[col].fillna('inconnu')
        
        # Vérification finale
        remaining_missing = filled_data.isnull().sum().sum()
        if remaining_missing > 0:
            logger.warning(f"{remaining_missing} valeurs manquantes persistent après traitement")
            # Dernière solution : supprimer les lignes avec des valeurs manquantes
            filled_data = filled_data.dropna()
        
        return filled_data
    
    def _handle_outliers(
        self,
        data: pd.DataFrame,
        target_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Détecte et traite les valeurs aberrantes.
        
        Args:
            data: DataFrame contenant potentiellement des valeurs aberrantes
            target_cols: Colonnes cibles pour les prédictions
            
        Returns:
            DataFrame avec valeurs aberrantes traitées
        """
        if not target_cols:
            return data.copy()
        
        # Copie pour éviter de modifier l'original
        cleaned_data = data.copy()
        
        for col in target_cols:
            if col in cleaned_data.columns and np.issubdtype(cleaned_data[col].dtype, np.number):
                # Méthode IQR (Interquartile Range) pour détecter les outliers
                Q1 = cleaned_data[col].quantile(0.25)
                Q3 = cleaned_data[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # Définir les limites (1.5 * IQR est une heuristique courante)
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Stocker les paramètres pour référence future
                self.outlier_params[f"{col}_lower"] = lower_bound
                self.outlier_params[f"{col}_upper"] = upper_bound
                
                # Compter les outliers
                outliers = ((cleaned_data[col] < lower_bound) | (cleaned_data[col] > upper_bound)).sum()
                
                if outliers > 0:
                    logger.info(f"Détection de {outliers} valeurs aberrantes dans la colonne {col}")
                    
                    # Remplacer les outliers par les limites (capping/winsorizing)
                    cleaned_data.loc[cleaned_data[col] < lower_bound, col] = lower_bound
                    cleaned_data.loc[cleaned_data[col] > upper_bound, col] = upper_bound
        
        return cleaned_data
    
    def _extract_time_features(
        self,
        data: pd.DataFrame,
        date_col: str = 'date'
    ) -> pd.DataFrame:
        """
        Extrait des caractéristiques temporelles à partir d'une colonne de date.
        
        Args:
            data: DataFrame contenant une colonne de date
            date_col: Nom de la colonne de date
            
        Returns:
            DataFrame avec les caractéristiques temporelles ajoutées
        """
        if date_col not in data.columns:
            logger.warning(f"Colonne de date '{date_col}' non trouvée")
            return data.copy()
        
        # Vérifier le type de la colonne
        if not pd.api.types.is_datetime64_any_dtype(data[date_col]):
            try:
                data[date_col] = pd.to_datetime(data[date_col])
            except Exception as e:
                logger.error(f"Impossible de convertir {date_col} en datetime: {str(e)}")
                return data.copy()
        
        # Copie pour éviter de modifier l'original
        enhanced_data = data.copy()
        
        # Extraire les caractéristiques temporelles basiques
        enhanced_data['day_of_week'] = enhanced_data[date_col].dt.dayofweek
        enhanced_data['day'] = enhanced_data[date_col].dt.day
        enhanced_data['month'] = enhanced_data[date_col].dt.month
        enhanced_data['year'] = enhanced_data[date_col].dt.year
        enhanced_data['is_weekend'] = (enhanced_data['day_of_week'] >= 5).astype(int)
        
        # Caractéristiques saisonnières plus avancées
        
        # Saisons (pour la France - hémisphère nord)
        # Hiver: décembre(12), janvier(1), février(2)
        # Printemps: mars(3), avril(4), mai(5)
        # Été: juin(6), juillet(7), août(8)
        # Automne: septembre(9), octobre(10), novembre(11)
        
        conditions = [
            (enhanced_data['month'].isin([12, 1, 2])),
            (enhanced_data['month'].isin([3, 4, 5])),
            (enhanced_data['month'].isin([6, 7, 8])),
            (enhanced_data['month'].isin([9, 10, 11]))
        ]
        seasons = ['winter', 'spring', 'summer', 'autumn']
        enhanced_data['season'] = np.select(conditions, seasons, default='unknown')
        
        # Créer des variables cycliques pour tenir compte de la nature circulaire du temps
        # Jour de la semaine (0-6) -> sin et cos
        enhanced_data['day_of_week_sin'] = np.sin(2 * np.pi * enhanced_data['day_of_week'] / 7)
        enhanced_data['day_of_week_cos'] = np.cos(2 * np.pi * enhanced_data['day_of_week'] / 7)
        
        # Mois (1-12) -> sin et cos
        enhanced_data['month_sin'] = np.sin(2 * np.pi * enhanced_data['month'] / 12)
        enhanced_data['month_cos'] = np.cos(2 * np.pi * enhanced_data['month'] / 12)
        
        logger.info(f"Extraction de caractéristiques temporelles: {len(enhanced_data.columns) - len(data.columns)} nouvelles colonnes")
        
        return enhanced_data
    
    def _encode_categorical(
        self,
        data: pd.DataFrame,
        categorical_cols: List[str],
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Encode les variables catégorielles.
        
        Args:
            data: DataFrame contenant des variables catégorielles
            categorical_cols: Liste des colonnes catégorielles à encoder
            fit: Ajuster les mappings (True) ou utiliser ceux existants (False)
            
        Returns:
            DataFrame avec variables catégorielles encodées
        """
        # Copie pour éviter de modifier l'original
        encoded_data = data.copy()
        
        # Pour chaque colonne catégorielle
        for col in categorical_cols:
            if col in encoded_data.columns:
                # Si la colonne est déjà numérique, sauter
                if np.issubdtype(encoded_data[col].dtype, np.number):
                    continue
                
                # Target encoding (moyenne de la variable cible par catégorie)
                # Une approche simple mais puissante pour les modèles de ML
                # Note: en mode transformation, utiliser les mappings précalculés
                
                if fit:
                    # Créer un mapping label -> index
                    unique_values = encoded_data[col].unique()
                    value_to_index = {value: i for i, value in enumerate(unique_values)}
                    self.categorical_mappings[col] = value_to_index
                else:
                    # Utiliser le mapping existant
                    value_to_index = self.categorical_mappings.get(col, {})
                    # Gérer les nouvelles catégories non vues pendant l'entraînement
                    for value in encoded_data[col].unique():
                        if value not in value_to_index:
                            # Assigner un index "inconnu"
                            value_to_index[value] = -1
                
                # Appliquer l'encodage
                encoded_data[col] = encoded_data[col].map(value_to_index)
                
                # Remplacer les NaN éventuels (catégories non trouvées)
                encoded_data[col] = encoded_data[col].fillna(-1)
        
        return encoded_data
    
    def _scale_features(
        self,
        data: pd.DataFrame,
        columns: List[str],
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Normalise les colonnes numériques.
        
        Args:
            data: DataFrame contenant des variables numériques
            columns: Liste des colonnes à normaliser
            fit: Ajuster les scalers (True) ou utiliser ceux existants (False)
            
        Returns:
            DataFrame avec variables normalisées
        """
        # Copie pour éviter de modifier l'original
        scaled_data = data.copy()
        
        # Pour chaque colonne à normaliser
        for col in columns:
            if col in scaled_data.columns and np.issubdtype(scaled_data[col].dtype, np.number):
                # Extraire les données pour la colonne
                col_data = scaled_data[col].values.reshape(-1, 1)
                
                if fit:
                    # Créer et ajuster le scaler approprié
                    if self.scaling_method == 'standard':
                        scaler = StandardScaler()
                    elif self.scaling_method == 'minmax':
                        scaler = MinMaxScaler()
                    else:
                        # Par défaut, StandardScaler
                        scaler = StandardScaler()
                    
                    # Ajuster le scaler
                    scaler.fit(col_data)
                    
                    # Stocker pour une utilisation ultérieure
                    self.scalers[col] = scaler
                
                # Transformer les données
                if col in self.scalers:
                    try:
                        scaled_values = self.scalers[col].transform(col_data)
                        scaled_data[col] = scaled_values.flatten()
                    except Exception as e:
                        logger.error(f"Erreur lors de la normalisation de {col}: {str(e)}")
        
        return scaled_data
    
    def split_data(
        self,
        data: pd.DataFrame,
        target_col: str,
        test_size: float = 0.2,
        val_size: float = 0.1,
        temporal: bool = True,
        date_col: str = 'date'
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Divise les données en ensembles d'entraînement, validation et test.
        
        Args:
            data: DataFrame contenant les données
            target_col: Nom de la colonne cible
            test_size: Proportion des données pour le test
            val_size: Proportion des données pour la validation
            temporal: Utiliser une division temporelle (True) ou aléatoire (False)
            date_col: Nom de la colonne de date (pour division temporelle)
            
        Returns:
            Tuple contenant (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        if target_col not in data.columns:
            raise ValueError(f"Colonne cible '{target_col}' non trouvée dans les données")
        
        # Séparation des features et de la cible
        X = data.drop(columns=[target_col])
        y = data[target_col]
        
        if temporal and date_col in data.columns:
            # Division temporelle (chronologique)
            logger.info("Utilisation d'une division temporelle des données")
            
            # Trier par date
            sorted_indices = data[date_col].argsort()
            X_sorted = X.iloc[sorted_indices]
            y_sorted = y.iloc[sorted_indices]
            
            # Calculer les points de division
            n = len(X_sorted)
            train_end = int(n * (1 - test_size - val_size))
            val_end = int(n * (1 - test_size))
            
            # Diviser les données
            X_train = X_sorted.iloc[:train_end]
            y_train = y_sorted.iloc[:train_end]
            
            X_val = X_sorted.iloc[train_end:val_end]
            y_val = y_sorted.iloc[train_end:val_end]
            
            X_test = X_sorted.iloc[val_end:]
            y_test = y_sorted.iloc[val_end:]
            
        else:
            # Division aléatoire
            logger.info("Utilisation d'une division aléatoire des données")
            
            # Premier split: train+val vs test
            X_temp, X_test, y_temp, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Second split: train vs val
            val_ratio = val_size / (1 - test_size)
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=val_ratio, random_state=42
            )
        
        logger.info(f"Division des données: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test


# Fonction de démonstration
def preprocess_data_example():
    """
    Exemple d'utilisation du préprocesseur de données.
    """
    # Création de données fictives
    np.random.seed(42)
    n_samples = 1000
    
    # Dates de janvier à décembre 2024
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', periods=n_samples)
    
    # Générer des données avec tendances et saisonnalité
    # Ventes plus élevées le weekend et en été
    weekday = dates.dayofweek
    is_weekend = (weekday >= 5).astype(int)
    month = dates.month
    summer_effect = np.where((month >= 6) & (month <= 8), 1.5, 1.0)
    
    # Chiffre d'affaires journalier
    base_sales = 1000
    weekend_boost = is_weekend * 500
    seasonal_effect = summer_effect * 300
    random_noise = np.random.normal(0, 100, n_samples)
    
    daily_sales = base_sales + weekend_boost + seasonal_effect + random_noise
    
    # Coûts (environ 40% du CA)
    costs = 0.4 * daily_sales + np.random.normal(0, 50, n_samples)
    
    # Type de jour (catégoriel)
    day_types = ['normal', 'weekend', 'holiday']
    day_type = np.random.choice(day_types, n_samples, p=[0.6, 0.28, 0.12])
    
    # Créer quelques valeurs manquantes et aberrantes
    daily_sales[np.random.choice(n_samples, 50, replace=False)] = np.nan
    costs[np.random.choice(n_samples, 30, replace=False)] = np.nan
    
    # Valeurs aberrantes
    outlier_indices = np.random.choice(n_samples, 20, replace=False)
    daily_sales[outlier_indices] = daily_sales[outlier_indices] * 3
    
    # Créer le DataFrame
    data = pd.DataFrame({
        'date': dates,
        'daily_sales': daily_sales,
        'costs': costs,
        'day_type': day_type
    })
    
    print("Données originales (aperçu):")
    print(data.head())
    print(f"\nStatistiques descriptives:\n{data.describe()}")
    print(f"\nValeurs manquantes:\n{data.isnull().sum()}")
    
    # Utiliser le préprocesseur
    preprocessor = DataPreprocessor(
        scaling_method='standard',
        handle_outliers=True,
        handle_missing=True,
        time_features=True
    )
    
    # Prétraiter les données
    processed_data = preprocessor.fit_transform(
        data,
        target_cols=['daily_sales', 'costs'],
        date_col='date',
        categorical_cols=['day_type']
    )
    
    print("\nDonnées prétraitées (aperçu):")
    print(processed_data.head())
    print(f"\nNouvelles colonnes: {set(processed_data.columns) - set(data.columns)}")
    print(f"\nValeurs manquantes après traitement: {processed_data.isnull().sum().sum()}")
    
    # Diviser les données
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.split_data(
        processed_data,
        target_col='daily_sales',
        temporal=True,
        date_col='date'
    )
    
    print(f"\nDimensions des ensembles de données:")
    print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
    print(f"X_val: {X_val.shape}, y_val: {y_val.shape}")
    print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")
    
    # Inverser les transformations
    original_scale = preprocessor.inverse_transform(
        pd.DataFrame({'daily_sales': y_test}),
        target_cols=['daily_sales']
    )
    
    print("\nValeurs originales après inversion de la normalisation (échantillon):")
    print(original_scale.head())


if __name__ == "__main__":
    # Exécuter l'exemple
    preprocess_data_example()
