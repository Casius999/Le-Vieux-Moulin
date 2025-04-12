#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Point d'entrée principal pour le module de prédiction IA/ML du restaurant Le Vieux Moulin.

Ce script permet d'interagir avec tous les composants du module de prédiction:
- Entraîner les modèles
- Générer des prédictions
- Évaluer les performances
- Démarrer l'API de prédiction

Exemples d'utilisation:
- `python -m prediction_module train --all` : Entraîne tous les modèles
- `python -m prediction_module serve` : Démarre le serveur API
- `python -m prediction_module evaluate` : Évalue les performances des modèles
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any

# Import des sous-modules
from prediction_module.training import train_models
from prediction_module.evaluation.model_evaluator import ModelEvaluator
from prediction_module.utils.common import setup_logging


def main():
    """
    Fonction principale qui analyse les arguments de ligne de commande et exécute
    l'action correspondante.
    """
    # Configurer le logger
    logger = setup_logging(
        log_file="prediction_module.log",
        console_level=logging.INFO,
        file_level=logging.DEBUG
    )
    
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(
        description="Module de prédiction IA/ML pour Le Vieux Moulin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python -m prediction_module train --all
  python -m prediction_module serve --host 0.0.0.0 --port 8000
  python -m prediction_module evaluate --models_dir ./models
        """
    )
    
    # Créer des sous-parseurs pour les différentes commandes
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # Sous-parseur pour la commande 'train'
    train_parser = subparsers.add_parser('train', help='Entraîner les modèles')
    train_parser.add_argument('--data_dir', type=str, default='./data',
                             help='Répertoire contenant les données d\'entraînement')
    train_parser.add_argument('--config', type=str, default='./config/training_config.json',
                             help='Fichier de configuration pour l\'entraînement')
    train_parser.add_argument('--models_dir', type=str, default='./models',
                             help='Répertoire où sauvegarder les modèles entraînés')
    train_parser.add_argument('--output_dir', type=str, default='./output',
                             help='Répertoire où sauvegarder les rapports et graphiques')
    train_parser.add_argument('--stock', action='store_true',
                             help='Entraîner le modèle de prévision des stocks')
    train_parser.add_argument('--recipe', action='store_true',
                             help='Entraîner le modèle de recommandation de recettes')
    train_parser.add_argument('--financial', action='store_true',
                             help='Entraîner le modèle de prévision financière')
    train_parser.add_argument('--all', action='store_true',
                             help='Entraîner tous les modèles')
    
    # Sous-parseur pour la commande 'serve'
    serve_parser = subparsers.add_parser('serve', help='Démarrer le serveur API')
    serve_parser.add_argument('--host', type=str, default='0.0.0.0',
                             help='Adresse IP sur laquelle écouter')
    serve_parser.add_argument('--port', type=int, default=8000,
                             help='Port sur lequel écouter')
    serve_parser.add_argument('--models_dir', type=str, default='./models',
                             help='Répertoire contenant les modèles')
    serve_parser.add_argument('--debug', action='store_true',
                             help='Activer le mode debug')
    
    # Sous-parseur pour la commande 'evaluate'
    eval_parser = subparsers.add_parser('evaluate', help='Évaluer les performances des modèles')
    eval_parser.add_argument('--models_dir', type=str, default='./models',
                             help='Répertoire contenant les modèles à évaluer')
    eval_parser.add_argument('--data_dir', type=str, default='./data/test',
                             help='Répertoire contenant les données de test')
    eval_parser.add_argument('--output_dir', type=str, default='./evaluation',
                             help='Répertoire où sauvegarder les rapports et graphiques')
    eval_parser.add_argument('--stock', action='store_true',
                             help='Évaluer le modèle de prévision des stocks')
    eval_parser.add_argument('--recipe', action='store_true',
                             help='Évaluer le modèle de recommandation de recettes')
    eval_parser.add_argument('--financial', action='store_true',
                             help='Évaluer le modèle de prévision financière')
    eval_parser.add_argument('--all', action='store_true',
                             help='Évaluer tous les modèles')
    
    # Sous-parseur pour la commande 'predict'
    predict_parser = subparsers.add_parser('predict', help='Générer des prédictions')
    predict_parser.add_argument('--type', type=str, required=True, choices=['stock', 'recipe', 'financial'],
                             help='Type de prédiction à générer')
    predict_parser.add_argument('--models_dir', type=str, default='./models',
                             help='Répertoire contenant les modèles')
    predict_parser.add_argument('--input', type=str, required=True,
                             help='Fichier de données d\'entrée ou requête JSON')
    predict_parser.add_argument('--output', type=str, default='prediction_result.json',
                             help='Fichier où sauvegarder les prédictions')
    predict_parser.add_argument('--format', type=str, default='json', choices=['json', 'csv'],
                             help='Format de sortie pour les prédictions')
    
    # Analyser les arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Exécuter la commande spécifiée
        if args.command == 'train':
            logger.info("Exécution de la commande 'train'")
            train_command(args)
        
        elif args.command == 'serve':
            logger.info("Exécution de la commande 'serve'")
            serve_command(args)
        
        elif args.command == 'evaluate':
            logger.info("Exécution de la commande 'evaluate'")
            evaluate_command(args)
        
        elif args.command == 'predict':
            logger.info("Exécution de la commande 'predict'")
            predict_command(args)
        
        else:
            logger.error(f"Commande inconnue: {args.command}")
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la commande '{args.command}': {str(e)}")
        raise


def train_command(args):
    """
    Exécute la commande 'train' pour entraîner les modèles.
    
    Args:
        args: Arguments de ligne de commande
    """
    # Réutiliser la fonction main() du module train_models
    sys.argv = [
        'train_models.py',
        f'--data_dir={args.data_dir}',
        f'--config={args.config}',
        f'--models_dir={args.models_dir}',
        f'--output_dir={args.output_dir}'
    ]
    
    # Ajouter les flags pour les modèles spécifiques
    if args.stock:
        sys.argv.append('--train_stock')
    if args.recipe:
        sys.argv.append('--train_recipe')
    if args.financial:
        sys.argv.append('--train_financial')
    if args.all:
        sys.argv.append('--train_all')
    
    # Exécuter la fonction main() du module train_models
    train_models.main()


def serve_command(args):
    """
    Exécute la commande 'serve' pour démarrer le serveur API.
    
    Args:
        args: Arguments de ligne de commande
    """
    # Importer le module api.server
    from prediction_module.api.server import app
    import uvicorn
    
    # Définir la variable d'environnement pour le répertoire des modèles
    os.environ["MODELS_DIR"] = os.path.abspath(args.models_dir)
    
    # Démarrer le serveur
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.debug
    )


def evaluate_command(args):
    """
    Exécute la commande 'evaluate' pour évaluer les performances des modèles.
    
    Args:
        args: Arguments de ligne de commande
    """
    # Créer un évaluateur
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
        logging.info("Aucun modèle spécifié, évaluation de tous les modèles par défaut")
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
    import datetime
    results['timestamp'] = datetime.datetime.now().isoformat()
    evaluator.generate_report(results)


def predict_command(args):
    """
    Exécute la commande 'predict' pour générer des prédictions.
    
    Args:
        args: Arguments de ligne de commande
    """
    import json
    import pandas as pd
    
    # Vérifier le type de prédiction
    if args.type == 'stock':
        # Import et initialisation du modèle de stock
        from prediction_module.models.stock_forecaster import StockForecaster
        
        # Chercher le modèle dans le répertoire spécifié
        model_path = os.path.join(args.models_dir, 'stock')
        model_files = [f for f in os.listdir(model_path) if f.endswith('.h5') or f.endswith('.keras')]
        if model_files:
            model_files.sort(reverse=True)  # Trier pour avoir le plus récent
            model_file = os.path.join(model_path, model_files[0])
            forecaster = StockForecaster(model_path=model_file)
        else:
            forecaster = StockForecaster()
        
        # Charger les données d'entrée
        if args.input.endswith('.csv'):
            historical_data = pd.read_csv(args.input, parse_dates=['date'])
        elif args.input.endswith('.json'):
            with open(args.input, 'r') as f:
                input_data = json.load(f)
            
            # Extraire les paramètres de la requête JSON
            days_ahead = input_data.get('days_ahead', 7)
            ingredients = input_data.get('ingredients', None)
            include_confidence = input_data.get('include_confidence', True)
            
            # Charger les données historiques si spécifiées
            if 'historical_data_path' in input_data:
                historical_data = pd.read_csv(input_data['historical_data_path'], parse_dates=['date'])
            else:
                # Créer des données factices pour la démonstration
                dates = pd.date_range(end=pd.Timestamp.now(), periods=60)
                ing_list = ingredients or ['farine', 'tomate', 'mozzarella', 'huile_olive']
                
                import numpy as np
                np.random.seed(42)
                data = np.random.normal(loc=[50, 30, 20, 5][:len(ing_list)], 
                                       scale=[10, 5, 3, 1][:len(ing_list)], 
                                       size=(60, len(ing_list)))
                
                # Ajout de saisonnalité
                for i, date in enumerate(dates):
                    if date.weekday() >= 5:  # Weekend
                        data[i] *= 1.5
                
                historical_data = pd.DataFrame(data, index=dates, columns=ing_list)
                historical_data['date'] = dates
        else:
            raise ValueError(f"Format de fichier d'entrée non pris en charge: {args.input}")
        
        # Générer les prédictions
        predictions = forecaster.predict(
            historical_data=historical_data,
            days_ahead=days_ahead if 'days_ahead' in locals() else 7,
            ingredients=ingredients if 'ingredients' in locals() else None,
            include_confidence=include_confidence if 'include_confidence' in locals() else True
        )
        
        # Sauvegarder les résultats
        with open(args.output, 'w') as f:
            json.dump(predictions, f, indent=2)
    
    elif args.type == 'recipe':
        # Import et initialisation du modèle de recommandation
        from prediction_module.models.recipe_recommender import RecipeRecommender
        
        # Chercher la base de recettes dans le répertoire spécifié
        recipe_path = os.path.join(args.models_dir, 'recipe')
        recipe_file = os.path.join(recipe_path, 'recipes.csv')
        
        if os.path.exists(recipe_file):
            recommender = RecipeRecommender(recipe_db_path=recipe_file)
        else:
            recommender = RecipeRecommender()
        
        # Charger les données d'entrée
        if args.input.endswith('.json'):
            with open(args.input, 'r') as f:
                input_data = json.load(f)
            
            # Extraire les paramètres de la requête JSON
            count = input_data.get('count', 3)
            recipe_type = input_data.get('recipe_type', None)
            available_ingredients = input_data.get('available_ingredients', None)
            promotions = input_data.get('promotions', None)
            exclude_ids = input_data.get('exclude_ids', None)
        else:
            raise ValueError(f"Format de fichier d'entrée non pris en charge: {args.input}")
        
        # Générer les suggestions
        suggestions = recommender.generate_suggestions(
            count=count,
            recipe_type=recipe_type,
            available_ingredients=available_ingredients,
            promotions=promotions,
            current_date=pd.Timestamp.now(),
            exclude_ids=exclude_ids
        )
        
        # Sauvegarder les résultats
        with open(args.output, 'w') as f:
            json.dump(suggestions, f, indent=2)
    
    elif args.type == 'financial':
        # Import et initialisation du modèle financier
        from prediction_module.models.financial_forecaster import FinancialForecaster
        
        # Chercher les modèles dans le répertoire spécifié
        financial_path = os.path.join(args.models_dir, 'financial')
        
        if os.path.exists(financial_path):
            forecaster = FinancialForecaster(models_dir=financial_path)
        else:
            forecaster = FinancialForecaster()
        
        # Charger les données d'entrée
        if args.input.endswith('.json'):
            with open(args.input, 'r') as f:
                input_data = json.load(f)
            
            # Extraire les paramètres de la requête JSON
            metrics = input_data.get('metrics', None)
            days_ahead = input_data.get('days_ahead', 30)
            include_components = input_data.get('include_components', False)
            detect_anomalies = input_data.get('detect_anomalies', False)
            
            # Charger les données historiques si spécifiées
            if 'financial_data_path' in input_data:
                financial_data = pd.read_csv(input_data['financial_data_path'], parse_dates=['date'])
                forecaster.financial_data = financial_data
        else:
            raise ValueError(f"Format de fichier d'entrée non pris en charge: {args.input}")
        
        # Générer les prédictions
        predictions = forecaster.predict(
            metrics=metrics,
            days_ahead=days_ahead,
            include_components=include_components,
            detect_anomalies=detect_anomalies
        )
        
        # Sauvegarder les résultats
        with open(args.output, 'w') as f:
            json.dump(predictions, f, indent=2)
    
    print(f"Prédictions générées et sauvegardées dans {args.output}")


if __name__ == "__main__":
    main()
