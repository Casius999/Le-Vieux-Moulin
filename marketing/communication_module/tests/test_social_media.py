"""
Tests unitaires pour le module de réseaux sociaux.
"""

import os
import sys
import unittest
import json
import datetime
from unittest import mock

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config
from src.social_media import SocialMediaManager
from src.social_media.publishers.facebook import FacebookPublisher


class TestSocialMediaManager(unittest.TestCase):
    """Tests pour le gestionnaire de réseaux sociaux."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
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
        with mock.patch('src.social_media.publishers.facebook.FacebookPublisher._setup_auth') as mock_auth:
            with mock.patch('src.social_media.publishers.instagram.InstagramPublisher._setup_auth') as mock_auth2:
                self.manager = SocialMediaManager(self.config)
    
    def test_init(self):
        """Teste l'initialisation du gestionnaire."""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.default_platforms, ["facebook", "instagram"])
        self.assertIn("facebook", self.manager.publishers)
        self.assertIn("instagram", self.manager.publishers)
    
    def test_publish_content(self):
        """Teste la publication de contenu."""
        # Créer le contenu de test
        content = {
            "title": "Test Post",
            "body": "This is a test post for unit testing",
            "media_urls": ["https://example.com/image.jpg"],
            "hashtags": ["test", "unittest"]
        }
        
        # Mocker la méthode publish_post de FacebookPublisher
        with mock.patch.object(FacebookPublisher, 'publish_post', return_value="test_post_id") as mock_publish:
            # Appeler la méthode à tester
            result = self.manager.publish_content(content, platforms=["facebook"])
            
            # Vérifier que la méthode publish_post a été appelée correctement
            mock_publish.assert_called_once()
            args, kwargs = mock_publish.call_args
            self.assertEqual(args[0], content)
            
            # Vérifier le résultat
            self.assertEqual(result["status"], "published")
            self.assertIn("facebook", result["publication_ids"])
            self.assertEqual(result["publication_ids"]["facebook"], "test_post_id")
    
    def test_schedule_post(self):
        """Teste la programmation d'une publication."""
        # Créer le contenu de test
        content = {
            "title": "Scheduled Post",
            "body": "This is a scheduled post for unit testing",
            "media_urls": ["https://example.com/image.jpg"],
            "hashtags": ["test", "scheduled"]
        }
        
        # Date de programmation
        scheduled_time = datetime.datetime.now() + datetime.timedelta(days=1)
        
        # Mocker la méthode schedule_post de FacebookPublisher
        with mock.patch.object(FacebookPublisher, 'schedule_post', return_value="test_scheduled_id") as mock_schedule:
            # Appeler la méthode à tester
            result = self.manager.publish_content(content, platforms=["facebook"], scheduled_time=scheduled_time)
            
            # Vérifier que la méthode schedule_post a été appelée correctement
            mock_schedule.assert_called_once()
            args, kwargs = mock_schedule.call_args
            self.assertEqual(args[0], content)
            self.assertEqual(args[1], scheduled_time)
            
            # Vérifier le résultat
            self.assertEqual(result["status"], "scheduled")
            self.assertIn("facebook", result["publication_ids"])
            self.assertEqual(result["publication_ids"]["facebook"], "test_scheduled_id")
    
    def test_get_analytics(self):
        """Teste la récupération des analytics."""
        # Mocker la méthode get_analytics de FacebookPublisher
        mock_analytics = {
            "platform": "facebook",
            "page_metrics": {
                "impressions": 1000,
                "reach": 800,
                "engagement": 200
            }
        }
        
        with mock.patch.object(FacebookPublisher, 'get_analytics', return_value=mock_analytics) as mock_get_analytics:
            # Appeler la méthode à tester
            result = self.manager.get_analytics(platform="facebook")
            
            # Vérifier que la méthode get_analytics a été appelée correctement
            mock_get_analytics.assert_called_once()
            
            # Vérifier le résultat
            self.assertEqual(result["platforms"]["facebook"], mock_analytics)
    
    def test_create_promotional_content(self):
        """Teste la création de contenu promotionnel."""
        # Données de promotion
        promotion_data = {
            "title": "Special Offer",
            "description": "Get 20% off on all pizzas",
            "validUntil": "2025-04-30",
            "hashtags": ["pizza", "discount"]
        }
        
        # Appeler la méthode à tester
        result = self.manager.create_promotional_content(promotion_data)
        
        # Vérifier le contenu généré
        self.assertEqual(result["title"], "Special Offer")
        self.assertIn("Get 20% off on all pizzas", result["body"])
        self.assertIn("2025-04-30", result["body"])
        self.assertIn("pizza", result["hashtags"])
        self.assertIn("discount", result["hashtags"])
        self.assertIn("vieuxmoulin", result["hashtags"])


class TestFacebookPublisher(unittest.TestCase):
    """Tests pour l'adaptateur Facebook."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Créer une configuration de test
        self.config = {
            "enabled": True,
            "page_id": "test_page_id",
            "app_id": "test_app_id",
            "app_secret": "test_app_secret",
            "access_token": "test_access_token"
        }
        
        # Créer le publisher avec un mock pour _setup_auth
        with mock.patch('src.social_media.publishers.facebook.FacebookPublisher._setup_auth'):
            self.publisher = FacebookPublisher(self.config)
            
            # Mocker les méthodes de stockage simulé
            self.publisher._save_post = mock.MagicMock()
            self.publisher._load_post = mock.MagicMock()
            self.publisher._delete_post_file = mock.MagicMock()
    
    def test_publish_post(self):
        """Teste la publication d'un post."""
        # Contenu du post
        content = {
            "body": "Test post content",
            "media_urls": ["https://example.com/image.jpg"]
        }
        
        # Appeler la méthode à tester
        post_id = self.publisher.publish_post(content)
        
        # Vérifier le résultat
        self.assertIsNotNone(post_id)
        self.assertTrue(post_id.startswith("fb_"))
        
        # Vérifier que _save_post a été appelé
        self.publisher._save_post.assert_called_once()
        args, kwargs = self.publisher._save_post.call_args
        self.assertEqual(args[0], post_id)
        self.assertEqual(args[1], content)
    
    def test_schedule_post(self):
        """Teste la programmation d'un post."""
        # Contenu du post
        content = {
            "body": "Scheduled post content",
            "media_urls": ["https://example.com/image.jpg"]
        }
        
        # Date de programmation
        scheduled_time = datetime.datetime.now() + datetime.timedelta(days=1)
        
        # Appeler la méthode à tester
        post_id = self.publisher.schedule_post(content, scheduled_time)
        
        # Vérifier le résultat
        self.assertIsNotNone(post_id)
        self.assertTrue(post_id.startswith("fb_scheduled_"))
        
        # Vérifier que _save_post a été appelé
        self.publisher._save_post.assert_called_once()
        args, kwargs = self.publisher._save_post.call_args
        self.assertEqual(args[0], post_id)
        self.assertEqual(args[1], content)
        self.assertEqual(args[2], None)  # targeting
        self.assertEqual(args[3], scheduled_time)
    
    def test_get_post(self):
        """Teste la récupération d'un post."""
        # ID du post
        post_id = "fb_test123"
        
        # Mocker le retour de _load_post
        mock_post = {
            "id": post_id,
            "content": {"body": "Test content"},
            "created_at": "2025-04-12T12:00:00Z",
            "status": "published"
        }
        self.publisher._load_post.return_value = mock_post
        
        # Appeler la méthode à tester
        result = self.publisher.get_post(post_id)
        
        # Vérifier le résultat
        self.assertEqual(result, mock_post)
        
        # Vérifier que _load_post a été appelé
        self.publisher._load_post.assert_called_once_with(post_id)
    
    def test_delete_post(self):
        """Teste la suppression d'un post."""
        # ID du post
        post_id = "fb_test123"
        
        # Mocker le retour de _delete_post_file
        self.publisher._delete_post_file.return_value = True
        
        # Appeler la méthode à tester
        result = self.publisher.delete_post(post_id)
        
        # Vérifier le résultat
        self.assertTrue(result)
        
        # Vérifier que _delete_post_file a été appelé
        self.publisher._delete_post_file.assert_called_once_with(post_id)
    
    def test_convert_targeting(self):
        """Teste la conversion des paramètres de ciblage."""
        # Paramètres de ciblage
        targeting = {
            "location": "Vensac",
            "radius": 20,
            "age_range": [25, 65],
            "interests": ["restaurant", "food"]
        }
        
        # Appeler la méthode à tester
        result = self.publisher._convert_targeting(targeting)
        
        # Vérifier le résultat
        self.assertIn("geo_locations", result)
        self.assertEqual(result["geo_locations"]["cities"][0]["name"], "Vensac")
        self.assertEqual(result["geo_locations"]["cities"][0]["radius"], 20)
        self.assertEqual(result["age_min"], 25)
        self.assertEqual(result["age_max"], 65)
        self.assertEqual(len(result["interests"]), 2)
        self.assertEqual(result["interests"][0]["name"], "restaurant")
        self.assertEqual(result["interests"][1]["name"], "food")


if __name__ == '__main__':
    unittest.main()
