#!/usr/bin/env python3
"""
Tests unitaires pour l'orchestrateur de communication.

Ce module contient les tests qui vérifient le fonctionnement 
de l'orchestrateur central du module de communication.
"""

import unittest
import asyncio
import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from src.common import Config
from src.orchestrator import CommunicationOrchestrator, get_orchestrator


class TestCommunicationOrchestrator(unittest.TestCase):
    """Tests pour la classe CommunicationOrchestrator."""

    def setUp(self):
        """Initialise l'environnement de test."""
        # Créer un mock de la configuration
        self.config = MagicMock(spec=Config)
        
        # Créer des mocks pour les managers
        self.social_media_mock = MagicMock()
        self.social_media_mock.publish_content_async = AsyncMock()
        
        self.notification_mock = MagicMock()
        self.notification_mock.send_notification_async = AsyncMock()
        
        self.campaign_mock = MagicMock()
        self.campaign_mock.start_campaign_async = AsyncMock()
        self.campaign_mock.get_campaign_info_async = AsyncMock(return_value={"id": "campaign_123", "status": "active"})
        
        self.menu_updater_mock = MagicMock()
        self.menu_updater_mock.update_menu_async = AsyncMock()
        
        # Patcher les imports pour utiliser les mocks
        self.patches = [
            patch('src.orchestrator.SocialMediaManager', return_value=self.social_media_mock),
            patch('src.orchestrator.NotificationManager', return_value=self.notification_mock),
            patch('src.orchestrator.CampaignManager', return_value=self.campaign_mock),
            patch('src.orchestrator.MenuUpdater', return_value=self.menu_updater_mock)
        ]
        
        for p in self.patches:
            p.start()
        
        # Créer l'instance à tester
        self.orchestrator = CommunicationOrchestrator(self.config)
        
        # Créer un événement loop asyncio pour les tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Nettoie l'environnement après les tests."""
        # Arrêter tous les patches
        for p in self.patches:
            p.stop()
        
        # Nettoyer le loop asyncio
        self.loop.close()

    def test_get_orchestrator_singleton(self):
        """Vérifie que get_orchestrator retourne toujours la même instance."""
        # Réinitialiser le singleton avant le test
        import src.orchestrator
        src.orchestrator._instance = None
        
        # Appeler get_orchestrator deux fois
        instance1 = get_orchestrator(self.config)
        instance2 = get_orchestrator(self.config)
        
        # Vérifier que les deux instances sont les mêmes
        self.assertIs(instance1, instance2)

    def test_publish_to_social_media(self):
        """Test de la méthode publish_to_social_media."""
        # Contenu de test
        content = {
            "title": "Test Post",
            "body": "This is a test post"
        }
        platforms = ["facebook", "instagram"]
        
        # Exécuter la méthode
        async def run_test():
            await self.orchestrator.publish_to_social_media(content, platforms)
            # Vérifier que la tâche a été mise en file d'attente
            self.assertEqual(self.orchestrator.task_queue.qsize(), 1)
            
            # Récupérer la tâche mise en file d'attente
            task = await self.orchestrator.task_queue.get()
            
            # Vérifier le contenu de la tâche
            self.assertEqual(task["type"], "publish")
            self.assertEqual(task["params"]["content"], content)
            self.assertEqual(task["params"]["platforms"], platforms)
        
        self.loop.run_until_complete(run_test())

    def test_send_notification(self):
        """Test de la méthode send_notification."""
        # Données de test
        template = "test_template"
        recipients = ["user1@example.com", "user2@example.com"]
        data = {"key": "value"}
        channels = ["email"]
        
        # Exécuter la méthode
        async def run_test():
            await self.orchestrator.send_notification(template, recipients, data, channels)
            # Vérifier que la tâche a été mise en file d'attente
            self.assertEqual(self.orchestrator.task_queue.qsize(), 1)
            
            # Récupérer la tâche mise en file d'attente
            task = await self.orchestrator.task_queue.get()
            
            # Vérifier le contenu de la tâche
            self.assertEqual(task["type"], "notify")
            self.assertEqual(task["params"]["template"], template)
            self.assertEqual(task["params"]["recipients"], recipients)
            self.assertEqual(task["params"]["data"], data)
            self.assertEqual(task["params"]["channels"], channels)
        
        self.loop.run_until_complete(run_test())

    def test_update_menu(self):
        """Test de la méthode update_menu."""
        # Données de test
        menu_data = {
            "name": "Test Menu",
            "categories": [
                {"name": "Entrées", "items": [
                    {"name": "Salade", "price": 8.50}
                ]}
            ]
        }
        platforms = ["website", "social_media"]
        
        # Exécuter la méthode
        async def run_test():
            await self.orchestrator.update_menu(menu_data, platforms)
            # Vérifier que la tâche a été mise en file d'attente
            self.assertEqual(self.orchestrator.task_queue.qsize(), 1)
            
            # Récupérer la tâche mise en file d'attente
            task = await self.orchestrator.task_queue.get()
            
            # Vérifier le contenu de la tâche
            self.assertEqual(task["type"], "update_menu")
            self.assertEqual(task["params"]["menu_data"], menu_data)
            self.assertEqual(task["params"]["platforms"], platforms)
        
        self.loop.run_until_complete(run_test())

    def test_manage_campaign(self):
        """Test de la méthode manage_campaign."""
        # Données de test
        action = "start"
        campaign_id = "campaign_123"
        
        # Exécuter la méthode
        async def run_test():
            await self.orchestrator.manage_campaign(action, campaign_id)
            # Vérifier que la tâche a été mise en file d'attente
            self.assertEqual(self.orchestrator.task_queue.qsize(), 1)
            
            # Récupérer la tâche mise en file d'attente
            task = await self.orchestrator.task_queue.get()
            
            # Vérifier le contenu de la tâche
            self.assertEqual(task["type"], "campaign")
            self.assertEqual(task["params"]["action"], action)
            self.assertEqual(task["params"]["campaign_id"], campaign_id)
        
        self.loop.run_until_complete(run_test())

    def test_register_webhook(self):
        """Test des méthodes register_webhook et unregister_webhook."""
        # Données de test
        event = "test_event"
        url = "https://example.com/webhook"
        
        # Enregistrer le webhook
        self.orchestrator.register_webhook(event, url)
        
        # Vérifier que le webhook est enregistré
        self.assertIn(event, self.orchestrator.webhooks)
        self.assertIn(url, self.orchestrator.webhooks[event])
        
        # Désinscrire le webhook
        self.orchestrator.unregister_webhook(event, url)
        
        # Vérifier que le webhook est désinscrit
        self.assertNotIn(url, self.orchestrator.webhooks[event])

    def test_task_handler_publish(self):
        """Test du gestionnaire de tâches de publication."""
        # Créer une tâche de test
        task = {
            "type": "publish",
            "params": {
                "content": {"title": "Test", "body": "Test content"},
                "platforms": ["facebook"],
                "id": "pub_123"
            }
        }
        
        # Exécuter le gestionnaire
        async def run_test():
            await self.orchestrator._handle_publish_task(task)
            
            # Vérifier que la méthode du manager a été appelée
            self.social_media_mock.publish_content_async.assert_called_once()
            
            # Vérifier les arguments
            args, kwargs = self.social_media_mock.publish_content_async.call_args
            self.assertEqual(kwargs["content"], task["params"]["content"])
            self.assertEqual(kwargs["platforms"], task["params"]["platforms"])
        
        self.loop.run_until_complete(run_test())

    def test_task_handler_notify(self):
        """Test du gestionnaire de tâches de notification."""
        # Créer une tâche de test
        task = {
            "type": "notify",
            "params": {
                "template": "test_template",
                "recipients": ["user@example.com"],
                "data": {"key": "value"},
                "channels": ["email"],
                "id": "notif_123"
            }
        }
        
        # Exécuter le gestionnaire
        async def run_test():
            await self.orchestrator._handle_notify_task(task)
            
            # Vérifier que la méthode du manager a été appelée
            self.notification_mock.send_notification_async.assert_called_once()
            
            # Vérifier les arguments
            args, kwargs = self.notification_mock.send_notification_async.call_args
            self.assertEqual(kwargs["template"], task["params"]["template"])
            self.assertEqual(kwargs["recipients"], task["params"]["recipients"])
            self.assertEqual(kwargs["data"], task["params"]["data"])
            self.assertEqual(kwargs["channels"], task["params"]["channels"])
        
        self.loop.run_until_complete(run_test())

    def test_task_handler_campaign(self):
        """Test du gestionnaire de tâches de campagne."""
        # Créer une tâche de test
        task = {
            "type": "campaign",
            "params": {
                "action": "start",
                "campaign_id": "campaign_123"
            }
        }
        
        # Exécuter le gestionnaire
        async def run_test():
            await self.orchestrator._handle_campaign_task(task)
            
            # Vérifier que la méthode du manager a été appelée
            self.campaign_mock.start_campaign_async.assert_called_once_with("campaign_123")
        
        self.loop.run_until_complete(run_test())

    def test_webhook_trigger(self):
        """Test du déclenchement des webhooks."""
        # Données de test
        event = "test_event"
        url = "https://example.com/webhook"
        data = {"test": "data"}
        
        # Enregistrer le webhook
        self.orchestrator.register_webhook(event, url)
        
        # Patcher la méthode qui envoie réellement le webhook
        with patch('asyncio.sleep') as mock_sleep:
            # Exécuter la méthode
            async def run_test():
                await self.orchestrator._trigger_webhooks(event, data)
                # Vérifier que le sleep a été appelé (simulation d'envoi)
                mock_sleep.assert_called()
            
            self.loop.run_until_complete(run_test())


class TestOrchestratorIntegration(unittest.TestCase):
    """Tests d'intégration pour l'orchestrateur."""
    
    def setUp(self):
        """Initialise l'environnement de test."""
        # Créer un mock de la configuration
        self.config = MagicMock(spec=Config)
        
        # Créer l'instance à tester avec des mocks de dépendances
        self.patches = [
            patch('src.orchestrator.SocialMediaManager'),
            patch('src.orchestrator.NotificationManager'),
            patch('src.orchestrator.CampaignManager'),
            patch('src.orchestrator.MenuUpdater')
        ]
        
        self.mocks = [p.start() for p in self.patches]
        
        # Créer l'orchestrateur
        self.orchestrator = CommunicationOrchestrator(self.config)
        
        # Créer un événement loop asyncio pour les tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Nettoie l'environnement après les tests."""
        # Arrêter tous les patches
        for p in self.patches:
            p.stop()
        
        # Nettoyer le loop asyncio
        self.loop.close()
    
    def test_process_task_queue(self):
        """Test du traitement de la file d'attente des tâches."""
        # Patcher les gestionnaires de tâches
        handler_patch = patch.object(
            self.orchestrator, 
            '_handle_publish_task', 
            new_callable=AsyncMock
        )
        handler_mock = handler_patch.start()
        
        # Tâche de test
        test_task = {
            "type": "publish",
            "timestamp": datetime.datetime.now().isoformat(),
            "params": {"content": "test", "platforms": ["facebook"]}
        }
        
        # Fonction de test qui ajoute une tâche puis arrête le traitement
        async def run_test():
            # Créer une tâche de traitement de la file
            process_task = asyncio.create_task(self.orchestrator._process_task_queue())
            
            # Ajouter une tâche à la file
            await self.orchestrator.task_queue.put(test_task)
            
            # Attendre que la tâche soit traitée
            await asyncio.sleep(0.1)
            
            # Arrêter la tâche de traitement (en simulant une erreur)
            process_task.cancel()
            
            try:
                await process_task
            except asyncio.CancelledError:
                pass  # Attendu
            
            # Vérifier que le gestionnaire a été appelé
            handler_mock.assert_called_once_with(test_task)
        
        # Exécuter le test
        self.loop.run_until_complete(run_test())
        
        # Arrêter le patch
        handler_patch.stop()
    
    def test_start_method(self):
        """Test de la méthode start."""
        # Fonction de test
        async def run_test():
            # Patcher la méthode _start_managers
            with patch.object(self.orchestrator, '_start_managers', new_callable=AsyncMock) as start_mock:
                # Patcher la méthode _initialize_scheduled_tasks
                with patch.object(self.orchestrator, '_initialize_scheduled_tasks') as init_mock:
                    # Appeler la méthode start
                    await self.orchestrator.start()
                    
                    # Vérifier que les méthodes ont été appelées
                    start_mock.assert_called_once()
                    init_mock.assert_called_once()
        
        # Exécuter le test
        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()
