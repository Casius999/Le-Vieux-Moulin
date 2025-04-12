"""
Tests unitaires pour le module de génération de recettes.

Ce module contient les tests unitaires pour vérifier le bon
fonctionnement du générateur de suggestions de recettes.
"""

import unittest
import json
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Ajout du chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import des modules à tester
from src.recipe_generator import RecipeGenerator


class TestRecipeGenerator(unittest.TestCase):
    """Tests pour la classe RecipeGenerator."""

    def setUp(self):
        """Initialisation avant chaque test."""
        # Configuration de test
        self.test_config = {
            "update_interval": 3600,
            "daily_suggestions_count": 3,
            "provider_cache_timeout": 1800,
            "promotion_threshold": 15,
            "providers": ["test_provider"],
            "recipe_categories": ["pizza", "plat_principal", "dessert"]
        }
        
        # Création du générateur avec mocks
        with patch('src.recipe_generator.generator.open', unittest.mock.mock_open(read_data='{}')):
            with patch('json.load', return_value={}):
                with patch('os.makedirs'):
                    self.generator = RecipeGenerator(self.test_config)
                    
                    # Mock des méthodes internes
                    self.generator._load_base_recipes = MagicMock(return_value=self._get_mock_recipes())
                    self.generator._load_ingredient_combinations = MagicMock(return_value=self._get_mock_combinations())
                    self.generator._load_previous_suggestions = MagicMock(return_value=[])

    def _get_mock_recipes(self):
        """Retourne des recettes fictives pour les tests."""
        return {
            "pizza": [
                {
                    "name": "Test Pizza",
                    "ingredients": ["sauce tomate", "mozzarella", "basilic"],
                    "base_price": 10.0,
                    "category": "test"
                }
            ],
            "plat_principal": [
                {
                    "name": "Test Plat",
                    "ingredients": ["ingrédient 1", "ingrédient 2"],
                    "base_price": 15.0,
                    "category": "test"
                }
            ]
        }
        
    def _get_mock_combinations(self):
        """Retourne des combinaisons d'ingrédients fictives pour les tests."""
        return {
            "affinities": {
                "tomate": ["mozzarella", "basilic"],
                "mozzarella": ["tomate", "basilic"],
                "ingrédient 1": ["ingrédient 2"]
            },
            "popular_combinations": [
                ["tomate", "mozzarella", "basilic"],
                ["ingrédient 1", "ingrédient 2"]
            ]
        }
        
    def _get_mock_promotions(self):
        """Retourne des promotions fictives pour les tests."""
        return [
            {
                "provider_id": "test_provider",
                "provider_name": "Test Provider",
                "promotion_id": "promo1",
                "ingredient": "tomate",
                "discount_percentage": 20,
                "original_price": 10.0,
                "discounted_price": 8.0,
                "days_until_expiry": 5,
                "available_quantity": 100
            },
            {
                "provider_id": "test_provider",
                "provider_name": "Test Provider",
                "promotion_id": "promo2",
                "ingredient": "mozzarella",
                "discount_percentage": 15,
                "original_price": 12.0,
                "discounted_price": 10.2,
                "days_until_expiry": 3,
                "available_quantity": 50
            }
        ]
        
    def _get_mock_trends(self):
        """Retourne des tendances fictives pour les tests."""
        return {
            "keywords": [
                {"term": "healthy", "category": "concept", "score": 0.8},
                {"term": "basilic", "category": "ingredient", "score": 0.7}
            ],
            "popular_dishes": [
                {"name": "Pizza Margherita", "ingredients": ["tomate", "mozzarella", "basilic"]}
            ],
            "ingredients_trend": [
                {"name": "tomate", "score": 0.9},
                {"name": "mozzarella", "score": 0.8}
            ],
            "consider_seasonal": True
        }

    def test_initialization(self):
        """Teste l'initialisation correcte du générateur."""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.config, self.test_config)
        self.assertIsNotNone(self.generator.base_recipes)
        self.assertIsNotNone(self.generator.ingredient_combinations)
        self.assertIsNotNone(self.generator.previous_suggestions)

    def test_score_promotional_ingredients(self):
        """Teste la fonction de scoring des ingrédients en promotion."""
        promotions = self._get_mock_promotions()
        
        with patch('src.recipe_generator.generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 4, 1)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            # Test de la méthode
            scored_ingredients = self.generator._score_promotional_ingredients(promotions)
            
            # Vérifications
            self.assertIn('tomate', scored_ingredients)
            self.assertIn('mozzarella', scored_ingredients)
            self.assertGreater(scored_ingredients['tomate'], 0)
            self.assertGreater(scored_ingredients['mozzarella'], 0)

    def test_extract_trending_ingredients(self):
        """Teste l'extraction des ingrédients tendance."""
        trends = self._get_mock_trends()
        
        # Test de la méthode
        trending_ingredients = self.generator._extract_trending_ingredients(trends)
        
        # Vérifications
        self.assertIn('basilic', trending_ingredients)
        self.assertIn('tomate', trending_ingredients)
        self.assertIn('mozzarella', trending_ingredients)

    def test_identify_opportunities(self):
        """Teste l'identification des opportunités."""
        promo_ingredients = {'tomate': 0.9, 'mozzarella': 0.8, 'oignon': 0.6}
        trending_ingredients = ['tomate', 'basilic', 'mozzarella']
        
        # Test de la méthode
        opportunities = self.generator._identify_opportunities(promo_ingredients, trending_ingredients)
        
        # Vérifications
        self.assertGreater(len(opportunities), 0)
        self.assertEqual(opportunities[0]['ingredient'], 'tomate')  # Meilleur score
        self.assertIn('tomate', [o['ingredient'] for o in opportunities])
        self.assertIn('mozzarella', [o['ingredient'] for o in opportunities])

    def test_adapt_existing_recipes(self):
        """Teste l'adaptation des recettes existantes."""
        opportunities = [
            {'ingredient': 'tomate', 'combined_score': 0.9, 'promo_score': 0.8, 'trend_score': 1.0},
            {'ingredient': 'mozzarella', 'combined_score': 0.8, 'promo_score': 0.7, 'trend_score': 1.0}
        ]
        
        # Mock de la fonction _are_ingredients_compatible pour toujours retourner True
        with patch.object(self.generator, '_are_ingredients_compatible', return_value=True):
            # Mock de la fonction _find_complementary_ingredient
            with patch.object(self.generator, '_find_complementary_ingredient', return_value='basilic'):
                # Test de la méthode
                adapted_recipes = self.generator._adapt_existing_recipes(opportunities, 2)
                
                # Vérifications
                self.assertGreater(len(adapted_recipes), 0)
                self.assertIn('ingredients', adapted_recipes[0])
                self.assertIn('tomate', adapted_recipes[0]['ingredients'])

    def test_generate_suggestions(self):
        """Teste la génération complète de suggestions."""
        promotions = self._get_mock_promotions()
        trends = self._get_mock_trends()
        
        # Mocks pour les fonctions internes
        with patch.object(self.generator, '_score_promotional_ingredients', return_value={'tomate': 0.9, 'mozzarella': 0.8}):
            with patch.object(self.generator, '_extract_trending_ingredients', return_value=['tomate', 'basilic', 'mozzarella']):
                with patch.object(self.generator, '_identify_opportunities', return_value=[
                    {'ingredient': 'tomate', 'combined_score': 0.9, 'promo_score': 0.8, 'trend_score': 1.0},
                    {'ingredient': 'mozzarella', 'combined_score': 0.8, 'promo_score': 0.7, 'trend_score': 1.0}
                ]):
                    with patch.object(self.generator, '_adapt_existing_recipes', return_value=[
                        {
                            'name': 'Pizza Tomate Spéciale',
                            'ingredients': ['tomate', 'mozzarella', 'basilic'],
                            'category': 'pizza',
                            'base_price': 12.0
                        }
                    ]):
                        with patch.object(self.generator, '_create_new_combinations', return_value=[
                            {
                                'name': 'Nouvelle Pizza Mozzarella',
                                'ingredients': ['mozzarella', 'tomate', 'basilic'],
                                'category': 'pizza',
                                'is_new_creation': True
                            }
                        ]):
                            with patch.object(self.generator, '_ensure_diversity', return_value=[
                                {
                                    'name': 'Pizza Tomate Spéciale',
                                    'ingredients': ['tomate', 'mozzarella', 'basilic'],
                                    'category': 'pizza',
                                    'base_price': 12.0
                                },
                                {
                                    'name': 'Nouvelle Pizza Mozzarella',
                                    'ingredients': ['mozzarella', 'tomate', 'basilic'],
                                    'category': 'pizza',
                                    'is_new_creation': True
                                }
                            ]):
                                with patch.object(self.generator, '_finalize_suggestions', return_value=[
                                    {
                                        'name': 'Pizza Tomate Spéciale',
                                        'category': 'pizza',
                                        'main_ingredients': ['tomate', 'mozzarella', 'basilic'],
                                        'price': 11.0,
                                        'description': 'Une délicieuse pizza avec des tomates fraîches.'
                                    },
                                    {
                                        'name': 'Nouvelle Pizza Mozzarella',
                                        'category': 'pizza',
                                        'main_ingredients': ['mozzarella', 'tomate', 'basilic'],
                                        'price': 12.0,
                                        'description': 'Une création originale avec de la mozzarella de qualité.'
                                    }
                                ]):
                                    # Test de la méthode
                                    suggestions = self.generator.generate_suggestions(promotions, trends, 2)
                                    
                                    # Vérifications
                                    self.assertEqual(len(suggestions), 2)
                                    self.assertEqual(suggestions[0]['name'], 'Pizza Tomate Spéciale')
                                    self.assertEqual(suggestions[1]['name'], 'Nouvelle Pizza Mozzarella')
                                    self.assertEqual(len(suggestions[0]['main_ingredients']), 3)
                                    self.assertEqual(suggestions[0]['category'], 'pizza')


if __name__ == '__main__':
    unittest.main()
