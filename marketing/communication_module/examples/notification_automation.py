#!/usr/bin/env python3
"""
Exemple d'automatisation des notifications pour Le Vieux Moulin.

Ce script montre comment utiliser le module de communication pour envoyer
automatiquement des notifications aux clients par email et SMS.
"""

import os
import sys
import asyncio
import datetime
import logging
from typing import Dict, List, Any

# Ajout du répertoire parent au PYTHONPATH pour l'importation des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.common import Config, setup_logger
from src.orchestrator import get_orchestrator
from src.notification import NotificationManager


async def send_special_event_invitations():
    """
    Envoie des invitations pour un événement spécial du restaurant.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("notification_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Définition des données de l'événement
    event_data = {
        "event_name": "Soirée Dégustation de Vins du Médoc",
        "event_date": "24 mai 2025",
        "event_time": "19h30",
        "event_description": ("Rejoignez-nous pour une soirée exceptionnelle en compagnie "
                             "de vignerons locaux qui vous feront découvrir les meilleurs "
                             "crus du Médoc, accompagnés de délicieuses tapas préparées par notre chef."),
        "price": "45€ par personne",
        "reservation_link": "https://levieuxmoulin.fr/reservations/evenements/degustation-24-05"
    }
    
    # Liste des clients VIP (dans une implémentation réelle, ces données viendraient du CRM)
    vip_clients = [
        {"email": "client1@example.com", "phone": "+33612345678", "first_name": "Jean", "last_name": "Dupont"},
        {"email": "client2@example.com", "phone": "+33623456789", "first_name": "Marie", "last_name": "Martin"},
        {"email": "client3@example.com", "phone": "+33634567890", "first_name": "Pierre", "last_name": "Bernard"}
    ]
    
    # Extraction des emails et téléphones
    vip_emails = [client["email"] for client in vip_clients]
    vip_phones = [client["phone"] for client in vip_clients]
    
    # Envoi des invitations par email
    await orchestrator.send_notification(
        template="event_invitation",
        recipients=vip_emails,
        data={
            "restaurant_name": "Le Vieux Moulin",
            "event": event_data,
            # Ajout de variables pour la personnalisation
            "is_vip": True,
            "special_offer": "En tant que client privilégié, nous vous offrons un apéritif de bienvenue."
        },
        channels=["email"]
    )
    
    logger.info(f"Invitations envoyées par email à {len(vip_emails)} clients VIP")
    
    # Envoi d'un rappel par SMS 2 jours avant l'événement
    # (dans une implémentation réelle, cela serait programmé pour être envoyé au moment approprié)
    sms_reminder_data = {
        "message": f"Rappel: Soirée Dégustation de Vins du Médoc le 24/05 à 19h30. " +
                  f"Nous nous réjouissons de vous accueillir au Vieux Moulin!"
    }
    
    await orchestrator.send_notification(
        template="event_reminder_sms",
        recipients=vip_phones,
        data=sms_reminder_data,
        channels=["sms"]
    )
    
    logger.info(f"Rappels programmés par SMS pour {len(vip_phones)} clients VIP")


async def send_birthday_promotions():
    """
    Envoie des promotions d'anniversaire aux clients concernés.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("notification_example", "INFO")
    
    # Utilisation directe du gestionnaire de notifications
    notification_manager = NotificationManager(config)
    
    # Simulation de clients ayant leur anniversaire cette semaine
    # (dans une implémentation réelle, ces données viendraient du CRM)
    birthday_clients = [
        {"email": "client4@example.com", "phone": "+33645678901", "first_name": "Sophie", "last_name": "Petit", "birthday": "2025-04-20"},
        {"email": "client5@example.com", "phone": "+33656789012", "first_name": "Thomas", "last_name": "Dubois", "birthday": "2025-04-21"}
    ]
    
    # Pour chaque client, envoyer une promotion personnalisée
    for client in birthday_clients:
        # Personnalisation du message
        promotion_data = {
            "first_name": client["first_name"],
            "promotion_code": f"ANNI{client['first_name'].upper()}2025",
            "discount": "Un dessert offert",
            "valid_from": client["birthday"],
            "valid_until": (datetime.datetime.fromisoformat(client["birthday"]) + datetime.timedelta(days=15)).strftime("%Y-%m-%d"),
            "restaurant_name": "Le Vieux Moulin",
            "reservation_link": "https://levieuxmoulin.fr/reservations"
        }
        
        # Envoi par email et SMS
        await notification_manager.send_notification_async(
            template="birthday_promotion",
            recipients=[client["email"]],
            data=promotion_data,
            channels=["email"]
        )
        
        # Version SMS plus courte
        sms_data = {
            "first_name": client["first_name"],
            "promotion_code": promotion_data["promotion_code"],
            "discount": promotion_data["discount"],
            "valid_until": promotion_data["valid_until"]
        }
        
        await notification_manager.send_notification_async(
            template="birthday_promotion_sms",
            recipients=[client["phone"]],
            data=sms_data,
            channels=["sms"]
        )
        
        logger.info(f"Promotion d'anniversaire envoyée à {client['first_name']} {client['last_name']}")


async def send_menu_update_notifications():
    """
    Notifie les clients d'une mise à jour du menu.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("notification_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Détails du nouveau menu
    new_menu = {
        "name": "Menu d'Été 2025",
        "start_date": "2025-06-01",
        "description": "Découvrez notre nouvelle carte estivale avec des produits frais et locaux",
        "highlights": [
            "Gaspacho de tomates anciennes et burrata",
            "Pavé de thon mi-cuit et ses légumes grillés",
            "Fraisier aux agrumes et basilic"
        ]
    }
    
    # Récupération des clients abonnés aux mises à jour de menu
    # (dans une implémentation réelle, ces données viendraient du CRM)
    subscribed_clients = get_subscribed_clients("menu_updates")
    
    if not subscribed_clients:
        logger.warning("Aucun client abonné aux mises à jour de menu")
        return
    
    # Extraction des emails
    emails = [client["email"] for client in subscribed_clients]
    
    # Envoi de la notification
    await orchestrator.send_notification(
        template="menu_update",
        recipients=emails,
        data={
            "restaurant_name": "Le Vieux Moulin",
            "menu": new_menu,
            "preview_link": "https://levieuxmoulin.fr/menu-ete-2025",
            "reservation_link": "https://levieuxmoulin.fr/reservations"
        },
        channels=["email"]
    )
    
    logger.info(f"Notification de mise à jour du menu envoyée à {len(emails)} clients")


async def setup_automated_campaign():
    """
    Configure une campagne automatisée pour les clients inactifs.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("notification_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Définition des paramètres de la campagne
    campaign_data = {
        "name": "Réengagement clients inactifs",
        "description": "Campagne pour réactiver les clients n'ayant pas visité le restaurant depuis 3 mois",
        "start_date": "2025-05-01T00:00:00Z",
        "end_date": "2025-06-01T00:00:00Z",
        "target_audience": ["inactive_3months"],
        "message_sequence": [
            {
                "day": 1,
                "channel": "email",
                "template": "miss_you",
                "subject": "Vous nous manquez au Vieux Moulin !"
            },
            {
                "day": 5,
                "channel": "sms",
                "template": "special_offer_sms"
            },
            {
                "day": 12,
                "channel": "email",
                "template": "exclusive_offer",
                "subject": "Une offre exclusive, juste pour vous"
            }
        ],
        "promotion": {
            "code": "RETOUR2025",
            "discount": "15% sur l'addition",
            "valid_until": "2025-06-15"
        }
    }
    
    # Création de la campagne automatisée
    await orchestrator.manage_campaign(
        action="create",
        campaign_id=None,  # Sera généré automatiquement
        campaign_data=campaign_data
    )
    
    logger.info(f"Campagne de réengagement configurée: {campaign_data['name']}")
    
    # Configuration des métriques de suivi
    tracking_metrics = [
        "email_open_rate",
        "click_through_rate",
        "conversion_rate",
        "revenue_generated"
    ]
    
    logger.info(f"Métriques de suivi configurées: {', '.join(tracking_metrics)}")


def get_subscribed_clients(subscription_type):
    """
    Récupère les clients abonnés à un type de communication spécifique.
    
    Args:
        subscription_type: Type d'abonnement (ex: "menu_updates", "promotions")
        
    Returns:
        Liste des clients abonnés
    """
    # Dans une implémentation réelle, cette fonction interrogerait le CRM
    # Ici, nous retournons des données factices
    
    if subscription_type == "menu_updates":
        return [
            {"email": "client1@example.com", "first_name": "Jean", "last_name": "Dupont"},
            {"email": "client6@example.com", "first_name": "Émilie", "last_name": "Fournier"},
            {"email": "client7@example.com", "first_name": "Luc", "last_name": "Girard"}
        ]
    elif subscription_type == "promotions":
        return [
            {"email": "client2@example.com", "first_name": "Marie", "last_name": "Martin"},
            {"email": "client3@example.com", "first_name": "Pierre", "last_name": "Bernard"},
            {"email": "client8@example.com", "first_name": "Julie", "last_name": "Moreau"}
        ]
    else:
        return []


async def main():
    """
    Fonction principale exécutant les exemples.
    """
    # Configuration du logger
    logger = setup_logger("notification_example", "INFO")
    logger.info("Démarrage des exemples d'automatisation des notifications...")
    
    # Exécution des exemples
    await send_special_event_invitations()
    await send_birthday_promotions()
    await send_menu_update_notifications()
    await setup_automated_campaign()
    
    logger.info("Exemples terminés avec succès")


if __name__ == "__main__":
    # Exécution du code asynchrone
    asyncio.run(main())
