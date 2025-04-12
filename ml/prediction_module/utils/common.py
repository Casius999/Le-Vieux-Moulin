#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fonctions et classes utilitaires communes pour tous les modèles prédictifs du restaurant Le Vieux Moulin.

Ce module contient des utilitaires pour:
- La gestion des journaux (logs)
- Les opérations d'entrée/sortie de données
- La configuration
- Les conversions et transformations communes
"""

import os
import json
import yaml
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any


def setup_logging(
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Configure un logger avec sortie console et fichier.
    
    Args:
        log_file: Chemin vers le fichier de log (si None, pas de fichier)
        console_level: Niveau de log pour la console
        file_level: Niveau de log pour le fichier
        
    Returns:
        Logger configuré
    """
    # Créer un formatteur
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Obtenir le logger racine
    logger = logging.getLogger('prediction_module')
    logger.setLevel(logging.DEBUG)  # Capture tous les niveaux
    
    # Supprimer les handlers existants pour éviter les doublons
    if logger.handlers:
        logger.handlers.clear()
    
    # Ajouter un handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Ajouter un handler fichier si spécifié
    if log_file:
        # Créer le répertoire si nécessaire
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: str) -> Dict:
    """
    Charge un fichier de configuration (JSON ou YAML).
    
    Args:
        config_path: Chemin vers le fichier de configuration
        
    Returns:
        Données de configuration
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")
    
    # Déterminer le format basé sur l'extension
    _, ext = os.path.splitext(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if ext.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif ext.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Format de configuration non pris en charge: {ext}")
    except Exception as e:
        raise Exception(f"Erreur lors du chargement de la configuration: {str(e)}")


def save_config(config: Dict, config_path: str) -> None:
    """
    Sauvegarde un dictionnaire de configuration dans un fichier (JSON ou YAML).
    
    Args:
        config: Données de configuration à sauvegarder
        config_path: Chemin où sauvegarder le fichier
    """
    # Créer le répertoire si nécessaire
    config_dir = os.path.dirname(config_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    # Déterminer le format basé sur l'extension
    _, ext = os.path.splitext(config_path)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            if ext.lower() in ['.yaml', '.yml']:
                yaml.dump(config, f, default_flow_style=False)
            elif ext.lower() == '.json':
                json.dump(config, f, indent=2)
            else:
                raise ValueError(f"Format de configuration non pris en charge: {ext}")
    except Exception as e:
        raise Exception(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")


def load_csv_data(
    file_path: str,
    date_columns: Optional[List[str]] = None,
    encoding: str = 'utf-8'
) -> pd.DataFrame:
    """
    Charge des données CSV avec gestion des colonnes de date.
    
    Args:
        file_path: Chemin vers le fichier CSV
        date_columns: Liste des colonnes à interpréter comme des dates
        encoding: Encodage du fichier
        
    Returns:
        DataFrame contenant les données
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier CSV non trouvé: {file_path}")
    
    try:
        # Si des colonnes de date sont spécifiées, utiliser parse_dates
        if date_columns:
            return pd.read_csv(file_path, parse_dates=date_columns, encoding=encoding)
        else:
            return pd.read_csv(file_path, encoding=encoding)
    except Exception as e:
        raise Exception(f"Erreur lors du chargement du CSV: {str(e)}")


def save_csv_data(
    data: pd.DataFrame,
    file_path: str,
    index: bool = False,
    encoding: str = 'utf-8'
) -> None:
    """
    Sauvegarde un DataFrame dans un fichier CSV.
    
    Args:
        data: DataFrame à sauvegarder
        file_path: Chemin où sauvegarder le fichier
        index: Inclure l'index dans le CSV
        encoding: Encodage du fichier
    """
    # Créer le répertoire si nécessaire
    file_dir = os.path.dirname(file_path)
    if file_dir and not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)
    
    try:
        data.to_csv(file_path, index=index, encoding=encoding)
    except Exception as e:
        raise Exception(f"Erreur lors de la sauvegarde du CSV: {str(e)}")


def generate_date_features(date_series: pd.Series) -> pd.DataFrame:
    """
    Génère des caractéristiques temporelles à partir d'une série de dates.
    
    Args:
        date_series: Série pandas contenant des dates
        
    Returns:
        DataFrame avec les caractéristiques temporelles extraites
    """
    if not pd.api.types.is_datetime64_any_dtype(date_series):
        try:
            date_series = pd.to_datetime(date_series)
        except:
            raise ValueError("La série fournie ne peut pas être convertie en dates")
    
    features = pd.DataFrame({
        'day': date_series.dt.day,
        'month': date_series.dt.month,
        'year': date_series.dt.year,
        'day_of_week': date_series.dt.dayofweek,
        'is_weekend': (date_series.dt.dayofweek >= 5).astype(int),
        'quarter': date_series.dt.quarter
    })
    
    # Ajouter des variables cycliques pour capturer la saisonnalité
    features['day_of_week_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
    features['day_of_week_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
    features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
    features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
    
    # Déterminer la saison (pour l'hémisphère nord)
    conditions = [
        (features['month'].isin([12, 1, 2])),
        (features['month'].isin([3, 4, 5])),
        (features['month'].isin([6, 7, 8])),
        (features['month'].isin([9, 10, 11]))
    ]
    seasons = ['winter', 'spring', 'summer', 'autumn']
    features['season'] = np.select(conditions, seasons, default='unknown')
    
    return features


def get_season(date: datetime) -> str:
    """
    Détermine la saison d'une date pour l'hémisphère nord.
    
    Args:
        date: Date à évaluer
        
    Returns:
        Nom de la saison ('winter', 'spring', 'summer', 'autumn')
    """
    month = date.month
    
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:  # 9, 10, 11
        return 'autumn'


def is_high_season(date: datetime) -> bool:
    """
    Détermine si une date correspond à la haute saison pour un restaurant en Gironde.
    
    Args:
        date: Date à évaluer
        
    Returns:
        True si c'est la haute saison, False sinon
    """
    month = date.month
    
    # Haute saison: juin à septembre (saison touristique)
    if month >= 6 and month <= 9:
        return True
    
    # Vacances de fin d'année (approximatif)
    if month == 12 and date.day >= 20:
        return True
    if month == 1 and date.day <= 5:
        return True
    
    return False


def calculate_moving_average(
    data: pd.Series,
    window: int = 7,
    min_periods: int = 1
) -> pd.Series:
    """
    Calcule la moyenne mobile d'une série temporelle.
    
    Args:
        data: Série de données numériques
        window: Taille de la fenêtre (en nombre de points)
        min_periods: Nombre minimum de valeurs requises
        
    Returns:
        Série contenant les moyennes mobiles
    """
    return data.rolling(window=window, min_periods=min_periods).mean()


def detect_outliers(
    data: pd.Series,
    method: str = 'iqr',
    threshold: float = 1.5
) -> pd.Series:
    """
    Détecte les valeurs aberrantes dans une série.
    
    Args:
        data: Série de données numériques
        method: Méthode de détection ('iqr' ou 'zscore')
        threshold: Seuil pour la détection
        
    Returns:
        Masque booléen (True pour les outliers)
    """
    if method == 'iqr':
        # Méthode IQR (écart interquartile)
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        return (data < lower_bound) | (data > upper_bound)
    
    elif method == 'zscore':
        # Méthode Z-score
        mean = data.mean()
        std = data.std()
        z_scores = (data - mean) / std
        return z_scores.abs() > threshold
    
    else:
        raise ValueError(f"Méthode de détection d'outliers non reconnue: {method}")


class ModelVersion:
    """
    Classe pour gérer les versions des modèles selon le semantic versioning.
    """
    
    def __init__(self, major: int = 0, minor: int = 1, patch: int = 0):
        """
        Initialise une version de modèle.
        
        Args:
            major: Version majeure (changements incompatibles API)
            minor: Version mineure (fonctionnalités rétrocompatibles)
            patch: Version patch (corrections de bugs)
        """
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __str__(self) -> str:
        """
        Représentation en chaîne de caractères.
        
        Returns:
            Version au format 'MAJOR.MINOR.PATCH'
        """
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def bump_major(self) -> 'ModelVersion':
        """
        Incrémente la version majeure et réinitialise les versions mineures et patch.
        
        Returns:
            Instance mise à jour
        """
        self.major += 1
        self.minor = 0
        self.patch = 0
        return self
    
    def bump_minor(self) -> 'ModelVersion':
        """
        Incrémente la version mineure et réinitialise la version patch.
        
        Returns:
            Instance mise à jour
        """
        self.minor += 1
        self.patch = 0
        return self
    
    def bump_patch(self) -> 'ModelVersion':
        """
        Incrémente la version patch.
        
        Returns:
            Instance mise à jour
        """
        self.patch += 1
        return self
    
    @classmethod
    def from_string(cls, version_str: str) -> 'ModelVersion':
        """
        Crée une instance à partir d'une chaîne de version.
        
        Args:
            version_str: Chaîne au format 'MAJOR.MINOR.PATCH'
            
        Returns:
            Instance de ModelVersion
        """
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError("Format de version invalide. Utiliser 'MAJOR.MINOR.PATCH'")
        
        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
            return cls(major, minor, patch)
        except ValueError:
            raise ValueError("Les composants de version doivent être des entiers")
    
    def to_dict(self) -> Dict[str, int]:
        """
        Convertit la version en dictionnaire.
        
        Returns:
            Dictionnaire avec les composants de version
        """
        return {
            'major': self.major,
            'minor': self.minor,
            'patch': self.patch
        }
    
    @classmethod
    def from_dict(cls, version_dict: Dict[str, int]) -> 'ModelVersion':
        """
        Crée une instance à partir d'un dictionnaire.
        
        Args:
            version_dict: Dictionnaire avec les composants de version
            
        Returns:
            Instance de ModelVersion
        """
        return cls(
            major=version_dict.get('major', 0),
            minor=version_dict.get('minor', 1),
            patch=version_dict.get('patch', 0)
        )


def validate_json_schema(data: Dict, schema: Dict) -> Tuple[bool, Optional[str]]:
    """
    Valide des données JSON contre un schéma JSON Schema.
    
    Args:
        data: Données à valider
        schema: Schéma JSON Schema
        
    Returns:
        Tuple (est_valide, message_erreur)
    """
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erreur de validation: {str(e)}"


if __name__ == "__main__":
    # Exemple d'utilisation des utilitaires
    logger = setup_logging("example.log")
    logger.info("Test des utilitaires communs")
    
    # Exemple de dates et caractéristiques
    dates = pd.date_range(start='2024-01-01', periods=10)
    date_features = generate_date_features(dates)
    print("Caractéristiques extraites des dates:")
    print(date_features.head())
    
    # Exemple de détection d'outliers
    data = pd.Series([1, 2, 3, 4, 100, 5, 6, 7])
    outliers = detect_outliers(data)
    print(f"\nDétection d'outliers: {outliers}")
    
    # Exemple de gestion de version
    version = ModelVersion(1, 2, 3)
    print(f"\nVersion initiale: {version}")
    version.bump_minor()
    print(f"Après bump_minor: {version}")
