"""
Tests unitaires pour le module de réseaux sociaux

Ce module contient les tests unitaires pour le module de gestion
des réseaux sociaux.
"""

import os
import sys
import json
import unittest
from unittest import mock
import datetime

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config
from src.social_media import SocialMediaManager
from src.social_media.publishers import FacebookPublisher, InstagramPublisher


class TestSocialMediaManager(unittest.TestCase):
    """Tests pour le gestionnaire de réseaux sociaux."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        # Créer une configuration de test
        self.config = {
            "social_media": {
                "enabled": True,
                "default_platforms": ["facebook", "instagram"],
                "platforms": {
                    "facebook": {
                        "enabled": True,
                        "page_id": "test_page_id",
                        "app_id": "test_app_id",
                        "app_secret": "test_app_secret",
                        "access_token": "test_access_token"
                    },
                    "instagram": {
                        "enabled": True,
                        "business_account_id": "test_account_id",
                        "access_token": "test_access_token"
                    }
                }
            }
        }
        
        # Créer le gestionnaire
        with mock.patch('src.social_media.publishers.FacebookPublisher._setup_auth'), \
             mock.patch('src.social_media.publishers.InstagramPublisher._setup_auth'):
            self.manager = SocialMediaManager(self.config)
    
    def test_init(self):
        """Vérifie que le gestionnaire s'initialise correctement."""
        # Vérifier que les éditeurs sont créés pour les plateformes activées
        self.assertIn('facebook', self.manager.publishers)
        self.assertIn('instagram', self.manager.publishers)
        
        # Vérifier que les instances sont du bon type
        self.assertIsInstance(self.manager.publishers['facebook'], FacebookPublisher)
        self.assertIsInstance(self.manager.publishers['instagram'], InstagramPublisher)
    
    @mock.patch('src.social_media.publishers.FacebookPublisher.publish_post')
    @mock.patch('src.social_media.publishers.InstagramPublisher.publish_post')
    def test_publish_content(self, mock_instagram_publish, mock_facebook_publish):
        """Vérifie que la publication de contenu fonctionne correctement."""
        # Configurer les mocks
        mock_facebook_publish.return_value = "fb_12345"
        mock_instagram_publish.return_value = "ig_67890"
        
        # Préparer le contenu
        content = {
            "title": "Test",
            "body": "Ceci est un test",
            "media_urls": ["https://example.com/test.jpg"],
            "hashtags": ["test", "vieuxmoulin"]
        }
        
        # Publier sur toutes les plateformes par défaut
        result = self.manager.publish_content(content)
        
        # Vérifier que les méthodes ont été appelées
        mock_facebook_publish.assert_called_once()
        mock_instagram_publish.assert_called_once()
        
        # Vérifier le résultat
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["publication_ids"]["facebook"], "fb_12345")
        self.assertEqual(result["publication_ids"]["instagram"], "ig_67890")
    
    @mock.patch('src.social_media.publishers.FacebookPublisher.schedule_post')
    def test_schedule_content(self, mock_facebook_schedule):
        """Vérifie que la programmation de contenu fonctionne correctement."""
        # Configurer le mock
        mock_facebook_schedule.return_value = "fb_scheduled_12345"
        
        # Préparer le contenu et la date
        content = {
            "title": "Test programmé",
            "body": "Ceci est un test programmé",
            "media_urls": ["https://example.com/test.jpg"],
            "hashtags": ["test", "vieuxmoulin"]
        }
        scheduled_time = "2025-04-20T18:30:00"
        
        # Programmer sur Facebook uniquement
        result = self.manager.publish_content(
            content=content,
            platforms=["facebook"],
            scheduled_time=scheduled_time
        )
        
        # Vérifier que la méthode a été appelée
        mock_facebook_schedule.assert_called_once()
        
        # Vérifier le résultat
        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(result["publication_ids"]["facebook"], "fb_scheduled_12345")
        self.assertIn("scheduled_time", result)
    
    @mock.patch('src.social_media.publishers.FacebookPublisher.get_analytics')
    @mock.patch('src.social_media.publishers.InstagramPublisher.get_analytics')
    def test_get_analytics(self, mock_instagram_analytics, mock_facebook_analytics):
        """Vérifie que la récupération des analytics fonctionne correctement."""
        # Configurer les mocks
        mock_facebook_analytics.return_value = {
            "platform": "facebook",
            "page_metrics": {
                "impressions": 1000,
                "reach": 800,
                "engagement": 200
            }
        }
        mock_instagram_analytics.return_value = {
            "platform": "instagram",
            "page_metrics": {
                "impressions": 1500,
                "reach": 1200,
                "engagement": 300
            }
        }
        
        # Récupérer les analytics pour toutes les plateformes
        result = self.manager.get_analytics()
        
        # Vérifier que les méthodes ont été appelées
        mock_facebook_analytics.assert_called_once()
        mock_instagram_analytics.assert_called_once()
        
        # Vérifier le résultat
        self.assertIn("platforms", result)
        self.assertIn("facebook", result["platforms"])
        self.assertIn("instagram", result["platforms"])
        self.assertEqual(result["platforms"]["facebook"]["page_metrics"]["impressions"], 1000)
        self.assertEqual(result["platforms"]["instagram"]["page_metrics"]["impressions"], 1500)
    
    def test_create_promotional_content(self):
        """Vérifie que la création de contenu promotionnel fonctionne correctement."""
        # Préparer les données de promotion
        promotion_data = {
            "title": "Offre spéciale été",
            "description": "Profitez de notre menu estival à prix réduit",
            "validUntil": "31 août 2025",
            "hashtags": ["été", "promotion"]
        }
        
        # Créer le contenu promotionnel
        content = self.manager.create_promotional_content(promotion_data)
        
        # Vérifier le contenu généré
        self.assertEqual(content["title"], "Offre spéciale été")
        self.assertIn("Profitez de notre menu estival à prix réduit", content["body"])
        self.assertIn("vieuxmoulin", content["hashtags"])
        self.assertIn("été", content["hashtags"])
        self.assertIn("promotion", content["hashtags"])
    
    def test_invalid_platform(self):
        """Vérifie que l'utilisation d'une plateforme non configurée génère une erreur."""
        content = {
            "title": "Test",
            "body": "Ceci est un test"
        }
        
        # Tenter de publier sur une plateforme non configurée
        result = self.manager.publish_content(content, platforms=["twitter"])
        
        # Vérifier que le résultat contient une erreur
        self.assertIn("errors", result)
        self.assertIn("twitter", result["errors"])
        self.assertEqual(result["status"], "failed")
        

if __name__ == '__main__':
    unittest.main()
