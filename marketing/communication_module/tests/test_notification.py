"""
Tests unitaires pour le module de notification

Ce module contient les tests unitaires pour le gestionnaire
de notifications et ses adaptateurs.
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
from src.notification import NotificationManager


class TestNotificationManager(unittest.TestCase):
    """Tests pour le gestionnaire de notifications."""
    
    def setUp(self):
        """Préparation des tests."""
        # Créer une configuration de test
        self.config = {
            "notification": {
                "enabled": True,
                "default_channels": ["email"],
                "channels": {
                    "email": {
                        "enabled": True,
                        "provider": "test",
                        "from_email": "test@levieuxmoulin.fr",
                        "from_name": "Test Vieux Moulin"
                    },
                    "sms": {
                        "enabled": False
                    }
                },
                "templates": {
                    "test_template": {
                        "subject": "Test notification",
                        "body_html": "<p>Hello {{name}},</p><p>This is a test.</p>",
                        "sms_version": "Hello {{name}}, this is a test."
                    }
                }
            }
        }
        
        # Créer le gestionnaire de notifications avec la config de test
        with mock.patch('src.notification.adapters.get_adapter') as mock_get_adapter:
            # Créer un mock pour l'adaptateur email
            mock_email_adapter = mock.MagicMock()
            mock_email_adapter.send.return_value = "test_message_id"
            mock_email_adapter.schedule.return_value = "test_scheduled_id"
            
            # Configurer le mock get_adapter pour retourner notre adaptateur simulé
            mock_get_adapter.return_value = mock_email_adapter
            
            # Créer le gestionnaire
            self.notification_manager = NotificationManager(self.config)
            
            # Stocker les mocks pour vérification
            self.mock_get_adapter = mock_get_adapter
            self.mock_email_adapter = mock_email_adapter
    
    def test_send_notification_with_valid_template(self):
        """Teste l'envoi d'une notification avec un template valide."""
        # Préparer les données de test
        template = "test_template"
        recipient = "test@example.com"
        data = {"name": "John"}
        
        # Exécuter la fonction à tester
        result = self.notification_manager.send_notification(
            template=template,
            recipients=recipient,
            data=data
        )
        
        # Vérifier que l'adaptateur a été appelé avec les bons paramètres
        self.mock_email_adapter.send.assert_called_once()
        call_args = self.mock_email_adapter.send.call_args[0]
        
        # Vérifier que le destinataire est correct
        self.assertEqual(call_args[0], recipient)
        
        # Vérifier que le contenu contient le sujet
        self.assertIn("subject", call_args[1])
        self.assertEqual(call_args[1]["subject"], "Test notification")
        
        # Vérifier que le contenu du message contient le nom personnalisé
        self.assertIn("body", call_args[1])
        self.assertIn("John", call_args[1]["body"])
        
        # Vérifier le résultat de la fonction
        self.assertEqual(result["status"], "sent")
        self.assertIn("notification_id", result)
        self.assertIn("channels", result)
        self.assertIn("email", result["channels"])
    
    def test_send_notification_with_unknown_template(self):
        """Teste l'envoi d'une notification avec un template inconnu."""
        # Préparer les données de test
        template = "unknown_template"
        recipient = "test@example.com"
        
        # Vérifier que l'appel génère une erreur
        with self.assertRaises(ValueError):
            self.notification_manager.send_notification(
                template=template,
                recipients=recipient
            )
        
        # Vérifier que l'adaptateur n'a pas été appelé
        self.mock_email_adapter.send.assert_not_called()
    
    def test_schedule_notification(self):
        """Teste la programmation d'une notification."""
        # Préparer les données de test
        template = "test_template"
        recipient = "test@example.com"
        data = {"name": "John"}
        schedule_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        # Exécuter la fonction à tester
        result = self.notification_manager.send_notification(
            template=template,
            recipients=recipient,
            data=data,
            schedule_time=schedule_time
        )
        
        # Vérifier que l'adaptateur schedule a été appelé
        self.mock_email_adapter.schedule.assert_called_once()
        
        # Vérifier le résultat de la fonction
        self.assertEqual(result["status"], "scheduled")
        self.assertIn("scheduled_time", result)
    
    def test_send_notification_to_multiple_recipients(self):
        """Teste l'envoi d'une notification à plusieurs destinataires."""
        # Préparer les données de test
        template = "test_template"
        recipients = ["test1@example.com", "test2@example.com", "test3@example.com"]
        data = {"name": "Team"}
        
        # Exécuter la fonction à tester
        result = self.notification_manager.send_notification(
            template=template,
            recipients=recipients,
            data=data
        )
        
        # Vérifier que l'adaptateur a été appelé pour chaque destinataire
        self.assertEqual(self.mock_email_adapter.send.call_count, len(recipients))
        
        # Vérifier le résultat de la fonction
        self.assertEqual(result["status"], "sent")
        self.assertIn("channels", result)
        self.assertIn("email", result["channels"])
        self.assertEqual(len(result["channels"]["email"]["success"]), len(recipients))
    
    def test_send_notification_with_multiple_channels(self):
        """Teste l'envoi d'une notification sur plusieurs canaux."""
        # Modifier la configuration pour activer le canal SMS
        self.config["notification"]["channels"]["sms"]["enabled"] = True
        
        # Créer un mock pour l'adaptateur SMS
        mock_sms_adapter = mock.MagicMock()
        mock_sms_adapter.send.return_value = "test_sms_id"
        
        # Mettre à jour le mock get_adapter
        self.mock_get_adapter.side_effect = lambda channel, config: {
            "email": self.mock_email_adapter,
            "sms": mock_sms_adapter
        }.get(channel)
        
        # Recréer le gestionnaire avec la nouvelle configuration
        self.notification_manager = NotificationManager(self.config)
        
        # Préparer les données de test
        template = "test_template"
        recipient = "test@example.com"
        data = {"name": "John"}
        
        # Exécuter la fonction à tester avec plusieurs canaux
        result = self.notification_manager.send_notification(
            template=template,
            recipients=recipient,
            data=data,
            channels=["email", "sms"]
        )
        
        # Vérifier que les deux adaptateurs ont été appelés
        self.mock_email_adapter.send.assert_called_once()
        mock_sms_adapter.send.assert_called_once()
        
        # Vérifier le résultat de la fonction
        self.assertEqual(result["status"], "sent")
        self.assertIn("channels", result)
        self.assertIn("email", result["channels"])
        self.assertIn("sms", result["channels"])


if __name__ == '__main__':
    unittest.main()
