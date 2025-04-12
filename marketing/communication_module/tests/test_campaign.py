"""
Tests unitaires pour le module de gestion des campagnes

Ce module contient les tests unitaires pour le gestionnaire
de campagnes marketing et ses fonctionnalités.
"""

import os
import sys
import unittest
from unittest import mock
import datetime
import json
import uuid

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config
from src.campaign_manager import CampaignManager


class TestCampaignManager(unittest.TestCase):
    """Tests pour le gestionnaire de campagnes marketing."""
    
    def setUp(self):
        """Préparation des tests."""
        # Créer une configuration de test
        self.config = {
            "campaign_manager": {
                "enabled": True,
                "analytics_retention_days": 30,
                "default_tracking_params": {
                    "utm_source": "test_source",
                    "utm_medium": "test_medium"
                },
                "segments": [
                    {
                        "id": "test_segment",
                        "name": "Segment de test",
                        "description": "Segment pour les tests unitaires"
                    }
                ]
            }
        }
        
        # Données de test pour une campagne
        self.test_campaign_data = {
            "name": "Campaign de test",
            "description": "Une campagne pour les tests unitaires",
            "start_date": "2025-05-01",
            "end_date": "2025-05-31",
            "budget": 1000.0,
            "currency": "EUR",
            "segments": ["test_segment"],
            "channels": [
                {
                    "type": "social_media",
                    "platforms": ["facebook", "instagram"],
                    "content": {
                        "title": "Offre spéciale test",
                        "body": "Ceci est une offre de test pour nos tests unitaires"
                    }
                }
            ]
        }
        
        # Mock pour les gestionnaires de canaux
        with mock.patch('src.campaign_manager.manager.SocialMediaManager') as mock_sm_manager, \
             mock.patch('src.campaign_manager.manager.NotificationManager') as mock_notif_manager:
             
            # Créer des mocks pour les gestionnaires
            self.mock_social_media_manager = mock.MagicMock()
            self.mock_notification_manager = mock.MagicMock()
            
            # Configurer les retours des mocks
            self.mock_social_media_manager.publish_content.return_value = {
                "status": "published",
                "publication_ids": {
                    "facebook": "fb_test_id",
                    "instagram": "ig_test_id"
                }
            }
            
            self.mock_notification_manager.send_notification.return_value = {
                "status": "sent",
                "notification_id": "notif_test_id"
            }
            
            # Configurer les constructeurs mock
            mock_sm_manager.return_value = self.mock_social_media_manager
            mock_notif_manager.return_value = self.mock_notification_manager
            
            # Créer le gestionnaire de campagnes
            self.campaign_manager = CampaignManager(self.config)
            
            # Remplacer la méthode de sauvegarde pour les tests
            self.campaign_manager._save_campaigns = mock.MagicMock()
            
            # Initialiser une base de données de test vide
            self.campaign_manager.campaigns_db = {}
    
    def test_create_campaign(self):
        """Teste la création d'une campagne."""
        # Exécuter la fonction à tester
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            result = self.campaign_manager.create_campaign(self.test_campaign_data)
        
        # Vérifier que la campagne a été correctement créée
        self.assertEqual(result["name"], "Campaign de test")
        self.assertEqual(result["status"], "draft")
        self.assertEqual(result["budget"], 1000.0)
        
        # Vérifier que l'ID est correct
        self.assertEqual(result["id"], "12345678-1234-5678-1234-567812345678")
        
        # Vérifier que la méthode de sauvegarde a été appelée
        self.campaign_manager._save_campaigns.assert_called_once()
        
        # Vérifier que la campagne est dans la base de données
        self.assertIn(result["id"], self.campaign_manager.campaigns_db)
    
    def test_create_campaign_missing_name(self):
        """Teste la création d'une campagne sans nom."""
        # Créer des données sans nom
        invalid_data = self.test_campaign_data.copy()
        invalid_data.pop("name")
        
        # Vérifier que cela lève une exception
        with self.assertRaises(ValueError):
            self.campaign_manager.create_campaign(invalid_data)
        
        # Vérifier que la méthode de sauvegarde n'a pas été appelée
        self.campaign_manager._save_campaigns.assert_not_called()
    
    def test_update_campaign(self):
        """Teste la mise à jour d'une campagne."""
        # Créer une campagne d'abord
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            campaign = self.campaign_manager.create_campaign(self.test_campaign_data)
            
        # Réinitialiser le mock de sauvegarde
        self.campaign_manager._save_campaigns.reset_mock()
        
        # Données de mise à jour
        update_data = {
            "name": "Campaign de test mise à jour",
            "description": "Description mise à jour",
            "budget": 1500.0
        }
        
        # Exécuter la fonction à tester
        result = self.campaign_manager.update_campaign(campaign["id"], update_data)
        
        # Vérifier que la campagne a été correctement mise à jour
        self.assertEqual(result["name"], "Campaign de test mise à jour")
        self.assertEqual(result["description"], "Description mise à jour")
        self.assertEqual(result["budget"], 1500.0)
        
        # Vérifier que certains champs n'ont pas été modifiés
        self.assertEqual(result["start_date"], "2025-05-01")
        
        # Vérifier que la méthode de sauvegarde a été appelée
        self.campaign_manager._save_campaigns.assert_called_once()
    
    def test_update_non_existent_campaign(self):
        """Teste la mise à jour d'une campagne inexistante."""
        # Exécuter la fonction à tester avec un ID inexistant
        result = self.campaign_manager.update_campaign("non_existent_id", {"name": "New name"})
        
        # Vérifier que le résultat est None
        self.assertIsNone(result)
        
        # Vérifier que la méthode de sauvegarde n'a pas été appelée
        self.campaign_manager._save_campaigns.assert_not_called()
    
    def test_delete_campaign(self):
        """Teste la suppression d'une campagne."""
        # Créer une campagne d'abord
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            campaign = self.campaign_manager.create_campaign(self.test_campaign_data)
            
        # Réinitialiser le mock de sauvegarde
        self.campaign_manager._save_campaigns.reset_mock()
        
        # Exécuter la fonction à tester
        result = self.campaign_manager.delete_campaign(campaign["id"])
        
        # Vérifier que la suppression a réussi
        self.assertTrue(result)
        
        # Vérifier que la campagne n'est plus dans la base de données
        self.assertNotIn(campaign["id"], self.campaign_manager.campaigns_db)
        
        # Vérifier que la méthode de sauvegarde a été appelée
        self.campaign_manager._save_campaigns.assert_called_once()
    
    def test_delete_non_existent_campaign(self):
        """Teste la suppression d'une campagne inexistante."""
        # Exécuter la fonction à tester avec un ID inexistant
        result = self.campaign_manager.delete_campaign("non_existent_id")
        
        # Vérifier que le résultat est False
        self.assertFalse(result)
        
        # Vérifier que la méthode de sauvegarde n'a pas été appelée
        self.campaign_manager._save_campaigns.assert_not_called()
    
    def test_start_campaign(self):
        """Teste le démarrage d'une campagne."""
        # Créer une campagne d'abord
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            campaign = self.campaign_manager.create_campaign(self.test_campaign_data)
            
        # Réinitialiser le mock de sauvegarde
        self.campaign_manager._save_campaigns.reset_mock()
        
        # Remplacer la méthode d'exécution des canaux par un mock
        self.campaign_manager._execute_campaign_channels = mock.MagicMock()
        
        # Exécuter la fonction à tester
        result = self.campaign_manager.start_campaign(campaign["id"])
        
        # Vérifier que le démarrage a réussi
        self.assertTrue(result)
        
        # Vérifier que le statut de la campagne a été mis à jour
        self.assertEqual(self.campaign_manager.campaigns_db[campaign["id"]]["status"], "active")
        
        # Vérifier que la méthode d'exécution des canaux a été appelée
        self.campaign_manager._execute_campaign_channels.assert_called_once()
        
        # Vérifier que la méthode de sauvegarde a été appelée
        self.campaign_manager._save_campaigns.assert_called_once()
    
    def test_start_campaign_without_channels(self):
        """Teste le démarrage d'une campagne sans canaux configurés."""
        # Créer une campagne sans canaux
        campaign_data = self.test_campaign_data.copy()
        campaign_data["channels"] = []
        
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            campaign = self.campaign_manager.create_campaign(campaign_data)
            
        # Réinitialiser le mock de sauvegarde
        self.campaign_manager._save_campaigns.reset_mock()
        
        # Vérifier que cela lève une exception
        with self.assertRaises(ValueError):
            self.campaign_manager.start_campaign(campaign["id"])
        
        # Vérifier que le statut de la campagne n'a pas été modifié
        self.assertEqual(self.campaign_manager.campaigns_db[campaign["id"]]["status"], "draft")
    
    def test_execute_social_media_channel(self):
        """Teste l'exécution d'un canal de réseaux sociaux."""
        # Créer un mock pour la campagne
        campaign = {
            "id": "test_campaign_id",
            "name": "Test Campaign",
            "tracking_params": {"utm_campaign": "test_campaign"}
        }
        
        # Créer un mock pour le canal
        channel = {
            "type": "social_media",
            "platforms": ["facebook", "instagram"],
            "content": {
                "body": "Test content with http://example.com/link"
            }
        }
        
        # Exécuter la méthode à tester
        self.campaign_manager._execute_social_media_channel(campaign, channel)
        
        # Vérifier que le gestionnaire de réseaux sociaux a été appelé
        self.mock_social_media_manager.publish_content.assert_called_once()
        
        # Vérifier que les paramètres corrects ont été passés
        args, kwargs = self.mock_social_media_manager.publish_content.call_args
        self.assertEqual(kwargs['platforms'], ["facebook", "instagram"])
        self.assertIn("body", kwargs['content'])
        
        # Vérifier que les paramètres de tracking ont été ajoutés à l'URL
        self.assertIn("utm_campaign=test_campaign_id", kwargs['content']["body"])
    
    def test_get_campaign_performance(self):
        """Teste la récupération des performances d'une campagne."""
        # Créer une campagne avec des canaux
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            campaign = self.campaign_manager.create_campaign(self.test_campaign_data)
        
        # Configurer les mocks pour les analytics
        self.mock_social_media_manager.get_analytics.return_value = {
            "platforms": {
                "facebook": {
                    "impressions": 500,
                    "engagement": 100
                },
                "instagram": {
                    "impressions": 300,
                    "engagement": 80
                }
            },
            "aggregated": {
                "impressions": 800,
                "engagement": 180
            }
        }
        
        # Exécuter la fonction à tester
        result = self.campaign_manager.get_campaign_performance(campaign["id"])
        
        # Vérifier que la fonction retourne les bonnes informations
        self.assertEqual(result["campaign_id"], campaign["id"])
        self.assertEqual(result["name"], "Campaign de test")
        self.assertIn("channels", result)
        self.assertIn("aggregated", result)
        
        # Vérifier que le gestionnaire de réseaux sociaux a été appelé
        self.mock_social_media_manager.get_analytics.assert_called_once()


if __name__ == '__main__':
    unittest.main()
