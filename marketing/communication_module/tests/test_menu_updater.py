"""
Tests unitaires pour le module de mise à jour des menus

Ce module contient les tests unitaires pour le gestionnaire
de mise à jour des menus sur différentes plateformes.
"""

import os
import sys
import unittest
from unittest import mock
import datetime
import json

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config
from src.menu_updater import MenuUpdater


class TestMenuUpdater(unittest.TestCase):
    """Tests pour le gestionnaire de mise à jour des menus."""
    
    def setUp(self):
        """Préparation des tests."""
        # Créer une configuration de test
        self.config = {
            "menu_updater": {
                "enabled": True,
                "update_frequency": "daily",
                "default_update_time": "10:00",
                "platforms": {
                    "website": {
                        "enabled": True,
                        "api_url": "https://test.levieuxmoulin.fr/api/menu",
                        "api_key": "test_api_key"
                    },
                    "google_business": {
                        "enabled": False
                    },
                    "thefork": {
                        "enabled": False
                    }
                }
            }
        }
        
        # Créer des données de menu de test
        self.test_menu = {
            "last_updated": "2025-04-12T20:30:00Z",
            "restaurant_name": "Le Vieux Moulin",
            "categories": [
                {
                    "id": "pizzas",
                    "name": "Pizzas",
                    "description": "Nos délicieuses pizzas cuites au feu de bois",
                    "items": [
                        {
                            "id": "margherita",
                            "name": "Margherita",
                            "description": "Sauce tomate, mozzarella et basilic",
                            "price": 10.50,
                            "allergens": ["gluten", "lactose"],
                            "vegetarian": True
                        }
                    ]
                }
            ]
        }
        
        # Créer le gestionnaire de menus avec des mocks pour les connecteurs
        with mock.patch('src.menu_updater.updater.WebsiteConnector') as mock_website_connector_class:
            # Créer un mock pour le connecteur website
            self.mock_website_connector = mock.MagicMock()
            self.mock_website_connector.update_menu.return_value = {"status": "success"}
            self.mock_website_connector.get_status.return_value = {"status": "active", "last_update": "2025-04-12T20:30:00Z"}
            
            # Configurer la classe mock pour retourner notre instance mock
            mock_website_connector_class.return_value = self.mock_website_connector
            
            # Créer le gestionnaire
            self.menu_updater = MenuUpdater(self.config)
    
    def test_update_menu_success(self):
        """Teste la mise à jour du menu avec succès."""
        # Exécuter la fonction à tester
        result = self.menu_updater.update_menu(self.test_menu)
        
        # Vérifier que le connecteur a été appelé avec les bons paramètres
        self.mock_website_connector.update_menu.assert_called_once()
        
        # Vérifier que le menu a été adapté correctement
        menu_arg = self.mock_website_connector.update_menu.call_args[0][0]
        self.assertEqual(menu_arg["restaurant_name"], "Le Vieux Moulin")
        self.assertEqual(len(menu_arg["categories"]), 1)
        self.assertEqual(menu_arg["categories"][0]["name"], "Pizzas")
        
        # Vérifier le résultat de la fonction
        self.assertEqual(result["status"], "updated")
        self.assertIn("platforms", result)
        self.assertIn("website", result["platforms"])
        self.assertEqual(result["platforms"]["website"]["status"], "success")
    
    def test_update_menu_with_specific_platforms(self):
        """Teste la mise à jour du menu sur des plateformes spécifiques."""
        # Activer Google Business pour ce test
        self.config["menu_updater"]["platforms"]["google_business"]["enabled"] = True
        
        # Créer un mock pour le connecteur Google Business
        with mock.patch('src.menu_updater.updater.GoogleBusinessConnector') as mock_gb_connector_class:
            mock_gb_connector = mock.MagicMock()
            mock_gb_connector.update_menu.return_value = {"status": "success"}
            mock_gb_connector_class.return_value = mock_gb_connector
            
            # Recréer le gestionnaire avec la nouvelle configuration
            self.menu_updater = MenuUpdater(self.config)
            
            # Exécuter la fonction à tester avec une plateforme spécifique
            result = self.menu_updater.update_menu(
                menu_data=self.test_menu,
                platforms=["website"]  # Seulement website, pas Google Business
            )
            
            # Vérifier que seul le connecteur website a été appelé
            self.mock_website_connector.update_menu.assert_called_once()
            
            # Vérifier que le connecteur Google Business n'a pas été appelé
            mock_gb_connector.update_menu.assert_not_called()
            
            # Vérifier le résultat de la fonction
            self.assertEqual(result["status"], "updated")
            self.assertIn("platforms", result)
            self.assertIn("website", result["platforms"])
            self.assertNotIn("google_business", result["platforms"])
    
    def test_update_menu_with_schedule(self):
        """Teste la programmation d'une mise à jour de menu."""
        # Préparer la date de programmation
        schedule_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        # Exécuter la fonction à tester
        result = self.menu_updater.update_menu(
            menu_data=self.test_menu,
            schedule_time=schedule_time
        )
        
        # Vérifier que le connecteur n'a pas été appelé (puisque c'est programmé)
        self.mock_website_connector.update_menu.assert_not_called()
        
        # Vérifier le résultat de la fonction
        self.assertEqual(result["status"], "scheduled")
        self.assertIn("scheduled_time", result)
    
    def test_get_menu_status(self):
        """Teste la récupération du statut des menus."""
        # Exécuter la fonction à tester
        result = self.menu_updater.get_menu_status()
        
        # Vérifier que le connecteur a été appelé
        self.mock_website_connector.get_status.assert_called_once()
        
        # Vérifier le résultat de la fonction
        self.assertIn("platforms", result)
        self.assertIn("website", result["platforms"])
        self.assertEqual(result["platforms"]["website"]["status"], "active")
    
    def test_sync_menu_from_source(self):
        """Teste la synchronisation du menu depuis une source externe."""
        # Exécuter la fonction à tester
        with mock.patch.object(self.menu_updater, 'update_menu') as mock_update:
            mock_update.return_value = {"status": "updated"}
            result = self.menu_updater.sync_menu_from_source()
            
            # Vérifier que update_menu a été appelé avec un menu non vide
            mock_update.assert_called_once()
            menu_arg = mock_update.call_args[0][0]
            self.assertIn("categories", menu_arg)
            self.assertIn("restaurant_name", menu_arg)
            
            # Vérifier le résultat de la fonction
            self.assertEqual(result["status"], "updated")


if __name__ == '__main__':
    unittest.main()
