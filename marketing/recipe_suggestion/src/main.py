#!/usr/bin/env python3
"""
Module principal de suggestion de recettes pour Le Vieux Moulin.

Ce module orchestre le processus de génération de suggestions de recettes basées
sur les promotions fournisseurs, les tendances clients et l'inventaire actuel.
"""

import os
import sys
import logging
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('recipe_suggestion.log')
    ]
)
logger = logging.getLogger('recipe_suggestion')

# Import des modules internes
try:
    from api_connectors import provider_api
    from trend_analyzer import trend_service
    from recipe_generator import generator
    from promotion_manager import promotion_service
    logger.info("Modules importés avec succès")
except ImportError as e:
    logger.error(f"Erreur lors de l'importation des modules: {e}")
    sys.exit(1)

class RecipeSuggestionService:
    """Service principal de suggestion de recettes."""
    
    def __init__(self, config_path=None):
        """Initialise le service avec la configuration spécifiée."""
        self.config_path = config_path or os.path.join('config', 'settings.json')
        self.config = self._load_config()
        self.provider_api = provider_api.ProviderAPI(self.config)
        self.trend_analyzer = trend_service.TrendAnalyzer(self.config)
        self.recipe_generator = generator.RecipeGenerator(self.config)
        self.promotion_manager = promotion_service.PromotionManager(self.config)
        logger.info("Service de suggestion de recettes initialisé")
        
    def _load_config(self):
        """Charge la configuration depuis le fichier JSON."""
        try:
            with open(self.config_path, 'r') as file:
                config = json.load(file)
                logger.info(f"Configuration chargée depuis {self.config_path}")
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            # Utilisation d'une configuration par défaut en cas d'erreur
            return {
                "update_interval": 3600,  # 1 heure par défaut
                "providers": ["metro", "transgourmet", "pomona"],
                "recipe_categories": ["pizza", "plat_principal", "dessert"],
                "promotion_threshold": 15,  # % de réduction minimum
                "api_endpoints": {
                    "central_server": "http://localhost:8000/api",
                    "ml_service": "http://localhost:5000/api/predictions"
                }
            }
    
    def generate_daily_suggestions(self):
        """Génère les suggestions quotidiennes de recettes."""
        logger.info("Génération des suggestions quotidiennes...")
        
        # 1. Récupération des promotions fournisseurs
        promotions = self.provider_api.get_current_promotions()
        logger.info(f"Récupéré {len(promotions)} promotions fournisseurs")
        
        # 2. Analyse des tendances actuelles
        trends = self.trend_analyzer.get_current_trends()
        logger.info(f"Tendances actuelles analysées: {trends.get('top_trends', [])}")
        
        # 3. Génération des suggestions de recettes
        suggestions = self.recipe_generator.generate_suggestions(
            promotions=promotions,
            trends=trends,
            count=self.config.get("daily_suggestions_count", 3)
        )
        logger.info(f"Généré {len(suggestions)} suggestions de recettes")
        
        # 4. Création des promotions associées
        for suggestion in suggestions:
            promo = self.promotion_manager.create_promotion(suggestion)
            suggestion['promotion'] = promo
            logger.info(f"Promotion créée pour '{suggestion['name']}'")
        
        # 5. Stockage et exposition des suggestions
        self._save_suggestions(suggestions)
        self._publish_suggestions(suggestions)
        
        return suggestions
    
    def _save_suggestions(self, suggestions):
        """Enregistre les suggestions dans la base de données ou fichier."""
        timestamp = datetime.now().strftime("%Y%m%d")
        output_dir = Path("data/suggestions")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"suggestions_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(suggestions, f, indent=2)
        logger.info(f"Suggestions enregistrées dans {output_file}")
    
    def _publish_suggestions(self, suggestions):
        """Publie les suggestions sur le serveur central et autres interfaces."""
        try:
            # Exemple d'intégration avec le serveur central
            api_endpoint = self.config["api_endpoints"]["central_server"]
            # Ici, code pour envoyer les données au serveur central
            logger.info(f"Suggestions publiées sur {api_endpoint}")
            
            # Notification des autres modules
            # Code pour notifier le module UI, etc.
        except Exception as e:
            logger.error(f"Erreur lors de la publication des suggestions: {e}")
    
    def run_service(self, interval=None):
        """Exécute le service en continu avec l'intervalle spécifié."""
        update_interval = interval or self.config.get("update_interval", 3600)
        logger.info(f"Démarrage du service (intervalle: {update_interval} secondes)")
        
        try:
            while True:
                self.generate_daily_suggestions()
                logger.info(f"En attente pendant {update_interval} secondes")
                time.sleep(update_interval)
        except KeyboardInterrupt:
            logger.info("Service arrêté par l'utilisateur")
        except Exception as e:
            logger.error(f"Erreur dans le service: {e}")
            raise

def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description='Service de suggestion de recettes')
    parser.add_argument('--config', help='Chemin vers le fichier de configuration')
    parser.add_argument('--interval', type=int, help='Intervalle de mise à jour en secondes')
    parser.add_argument('--dev', action='store_true', help='Mode développement')
    return parser.parse_args()

def main():
    """Point d'entrée principal du service."""
    args = parse_arguments()
    
    # Configuration du mode développement
    if args.dev:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Mode développement activé")
    
    # Initialisation et exécution du service
    service = RecipeSuggestionService(args.config)
    
    if args.dev:
        # En mode dev, génère une suggestion et quitte
        suggestions = service.generate_daily_suggestions()
        print("\nSuggestions générées:")
        for i, sugg in enumerate(suggestions, 1):
            print(f"{i}. {sugg['name']} ({sugg['category']})")
            print(f"   Prix: {sugg['price']}€, Ingrédients: {', '.join(sugg['main_ingredients'])}")
            print(f"   Promotion: {sugg['promotion']['description']}\n")
    else:
        # En mode normal, exécute le service en continu
        service.run_service(args.interval)

if __name__ == "__main__":
    main()
