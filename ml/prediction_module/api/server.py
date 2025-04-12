#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serveur API FastAPI pour exposer les fonctionnalités des modèles prédictifs du restaurant Le Vieux Moulin.

Ce module implémente une API REST avec les endpoints nécessaires pour :
- Obtenir des prévisions de stocks
- Générer des suggestions de recettes
- Produire des prévisions financières
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, Query, Body, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ajout du chemin racine pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import des modèles
from prediction_module.models.stock_forecaster import StockForecaster
from prediction_module.models.recipe_recommender import RecipeRecommender
from prediction_module.models.financial_forecaster import FinancialForecaster

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Modèles Pydantic pour la validation des données

class StockForecastRequest(BaseModel):
    days_ahead: int = Field(default=7, ge=1, le=30, description="Nombre de jours à prévoir")
    ingredients: Optional[List[str]] = Field(default=None, description="Liste des ingrédients à prévoir (tous si non spécifié)")
    include_confidence: bool = Field(default=True, description="Inclure les intervalles de confiance")

class RecipeRequest(BaseModel):
    count: int = Field(default=3, ge=1, le=10, description="Nombre de suggestions à générer")
    recipe_type: Optional[str] = Field(default=None, description="Type de recette (pizza, plat, dessert, etc.)")
    available_ingredients: Optional[Dict[str, float]] = Field(default=None, description="Dictionnaire des ingrédients disponibles et leurs quantités")
    promotions: Optional[Dict[str, float]] = Field(default=None, description="Dictionnaire des ingrédients en promotion et leurs remises")
    exclude_ids: Optional[List[int]] = Field(default=None, description="Liste des IDs de recettes à exclure")

class FinancialForecastRequest(BaseModel):
    metrics: Optional[List[str]] = Field(default=None, description="Liste des métriques à prévoir")
    days_ahead: int = Field(default=30, ge=1, le=90, description="Nombre de jours à prévoir")
    include_components: bool = Field(default=False, description="Inclure les composantes des prévisions")
    detect_anomalies: bool = Field(default=False, description="Détecter les anomalies dans les données historiques récentes")


# Création de l'application FastAPI
app = FastAPI(
    title="API de Prédiction - Le Vieux Moulin",
    description="API pour les modèles prédictifs du restaurant Le Vieux Moulin",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À remplacer par les domaines autorisés en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour les modèles (chargés à la demande)
stock_forecaster = None
recipe_recommender = None
financial_forecaster = None

# Chemins des modèles
MODELS_DIR = os.environ.get("MODELS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models')))
STOCK_MODEL_PATH = os.path.join(MODELS_DIR, 'stock')
RECIPE_MODEL_PATH = os.path.join(MODELS_DIR, 'recipe')
FINANCIAL_MODEL_PATH = os.path.join(MODELS_DIR, 'financial')

# Fonctions de chargement des modèles (lazy loading)

def get_stock_forecaster():
    """
    Charge le modèle de prévision des stocks si nécessaire.
    
    Returns:
        Instance de StockForecaster
    """
    global stock_forecaster
    if stock_forecaster is None:
        logger.info(f"Chargement du modèle StockForecaster depuis {STOCK_MODEL_PATH}")
        try:
            # Chercher le modèle le plus récent
            model_files = [f for f in os.listdir(STOCK_MODEL_PATH) if f.endswith('.h5') or f.endswith('.keras')]
            if model_files:
                model_files.sort(reverse=True)  # Tri descendant pour avoir le plus récent
                model_path = os.path.join(STOCK_MODEL_PATH, model_files[0])
                stock_forecaster = StockForecaster(model_path=model_path)
            else:
                # Si pas de modèle trouvé, utiliser l'implémentation de base
                logger.warning("Aucun modèle StockForecaster trouvé, utilisation de l'implémentation par défaut")
                stock_forecaster = StockForecaster()
        except Exception as e:
            logger.error(f"Erreur lors du chargement du StockForecaster: {str(e)}")
            # Créer une instance de base en cas d'erreur
            stock_forecaster = StockForecaster()
    
    return stock_forecaster

def get_recipe_recommender():
    """
    Charge le modèle de recommandation de recettes si nécessaire.
    
    Returns:
        Instance de RecipeRecommender
    """
    global recipe_recommender
    if recipe_recommender is None:
        logger.info(f"Chargement du modèle RecipeRecommender depuis {RECIPE_MODEL_PATH}")
        try:
            # Chercher le fichier de recettes
            recipe_file = os.path.join(RECIPE_MODEL_PATH, 'recipes.csv')
            
            # Chercher les embeddings et métadonnées
            embeddings_file = os.path.join(RECIPE_MODEL_PATH, 'recipe_embeddings.npy')
            
            if os.path.exists(recipe_file):
                recipe_recommender = RecipeRecommender(recipe_db_path=recipe_file)
            else:
                # Si pas de données trouvées, utiliser l'implémentation de base
                logger.warning("Données RecipeRecommender non trouvées, utilisation de l'implémentation par défaut")
                recipe_recommender = RecipeRecommender()
        except Exception as e:
            logger.error(f"Erreur lors du chargement du RecipeRecommender: {str(e)}")
            # Créer une instance de base en cas d'erreur
            recipe_recommender = RecipeRecommender()
    
    return recipe_recommender

def get_financial_forecaster():
    """
    Charge le modèle de prévision financière si nécessaire.
    
    Returns:
        Instance de FinancialForecaster
    """
    global financial_forecaster
    if financial_forecaster is None:
        logger.info(f"Chargement du modèle FinancialForecaster depuis {FINANCIAL_MODEL_PATH}")
        try:
            # Vérifier si le répertoire existe
            if os.path.exists(FINANCIAL_MODEL_PATH):
                financial_forecaster = FinancialForecaster(models_dir=FINANCIAL_MODEL_PATH)
            else:
                # Si pas de modèle trouvé, utiliser l'implémentation de base
                logger.warning("Modèles FinancialForecaster non trouvés, utilisation de l'implémentation par défaut")
                financial_forecaster = FinancialForecaster()
        except Exception as e:
            logger.error(f"Erreur lors du chargement du FinancialForecaster: {str(e)}")
            # Créer une instance de base en cas d'erreur
            financial_forecaster = FinancialForecaster()
    
    return financial_forecaster


# Routes API

@app.get("/")
async def root():
    """
    Page d'accueil de l'API.
    """
    return {
        "message": "API de Prédiction - Le Vieux Moulin",
        "version": "1.0.0",
        "endpoints": [
            "/api/stock/forecast",
            "/api/recipes/suggest",
            "/api/finance/forecast"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Vérification de l'état de santé de l'API.
    """
    # Vérifier l'accès aux modèles
    models_available = {
        "stock_forecaster": os.path.exists(STOCK_MODEL_PATH),
        "recipe_recommender": os.path.exists(RECIPE_MODEL_PATH),
        "financial_forecaster": os.path.exists(FINANCIAL_MODEL_PATH)
    }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_available": models_available
    }

@app.post("/api/stock/forecast")
async def forecast_stock(request: StockForecastRequest, response: Response):
    """
    Génère des prévisions pour les besoins en stocks.
    
    Args:
        request: Paramètres de la requête (jours, ingrédients, etc.)
        
    Returns:
        Prévisions des besoins en stocks par jour et par ingrédient
    """
    logger.info(f"Requête de prévision de stock reçue: {request.dict()}")
    
    try:
        # Obtenir le modèle
        forecaster = get_stock_forecaster()
        
        # Dans un contexte réel, nous chargerions les données historiques depuis une base de données
        # Pour cette démonstration, nous allons simuler des données
        
        # Simulation des données historiques
        dates = pd.date_range(end=datetime.now(), periods=60)
        ingredients = request.ingredients or ['farine', 'tomate', 'mozzarella', 'huile_olive']
        
        np.random.seed(42)
        data = np.random.normal(loc=[50, 30, 20, 5], scale=[10, 5, 3, 1], size=(60, len(ingredients)))
        
        # Ajout de saisonnalité (plus de ventes le weekend)
        for i, date in enumerate(dates):
            if date.weekday() >= 5:  # Weekend
                data[i] *= 1.5
        
        historical_data = pd.DataFrame(data, index=dates, columns=ingredients)
        
        # Générer les prévisions
        predictions = forecaster.predict(
            historical_data=historical_data,
            days_ahead=request.days_ahead,
            ingredients=ingredients,
            include_confidence=request.include_confidence
        )
        
        # Formater les résultats pour l'API
        results = {
            "forecast": predictions,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_version": getattr(forecaster, "model_version", "1.0.0"),
                "days_ahead": request.days_ahead
            }
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors de la prévision des stocks: {str(e)}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}

@app.post("/api/recipes/suggest")
async def suggest_recipes(request: RecipeRequest, response: Response):
    """
    Génère des suggestions de recettes basées sur le contexte actuel.
    
    Args:
        request: Paramètres de la requête (type, ingrédients disponibles, etc.)
        
    Returns:
        Liste des recettes suggérées avec explications
    """
    logger.info(f"Requête de suggestion de recettes reçue: {request.dict()}")
    
    try:
        # Obtenir le modèle
        recommender = get_recipe_recommender()
        
        # Générer les suggestions
        suggestions = recommender.generate_suggestions(
            count=request.count,
            recipe_type=request.recipe_type,
            available_ingredients=request.available_ingredients,
            promotions=request.promotions,
            current_date=datetime.now(),
            exclude_ids=request.exclude_ids
        )
        
        # Formater les résultats pour l'API
        results = {
            "suggestions": suggestions,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "recipe_type": request.recipe_type or "all",
                "count": len(suggestions)
            }
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des suggestions de recettes: {str(e)}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}

@app.post("/api/finance/forecast")
async def forecast_finance(request: FinancialForecastRequest, response: Response):
    """
    Génère des prévisions financières.
    
    Args:
        request: Paramètres de la requête (métriques, jours, etc.)
        
    Returns:
        Prévisions financières par jour et par métrique
    """
    logger.info(f"Requête de prévision financière reçue: {request.dict()}")
    
    try:
        # Obtenir le modèle
        forecaster = get_financial_forecaster()
        
        # Générer les prévisions
        predictions = forecaster.predict(
            metrics=request.metrics,
            days_ahead=request.days_ahead,
            start_date=datetime.now(),
            include_components=request.include_components,
            detect_anomalies=request.detect_anomalies
        )
        
        # Formater les résultats pour l'API
        results = {
            "forecast": predictions,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "days_ahead": request.days_ahead,
                "metrics": request.metrics or "all"
            }
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors de la prévision financière: {str(e)}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}


# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Démarrage du serveur API sur {host}:{port}")
    uvicorn.run("server:app", host=host, port=port, reload=True)
