#!/usr/bin/env python3
"""
Exemple d'utilisation du module de notification

Ce script illustre comment utiliser le gestionnaire de notifications
pour envoyer des emails et SMS aux clients.
"""

import os
import sys
import json
import datetime
import argparse

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config
from src.notification import NotificationManager


def load_config():
    """Charge la configuration depuis un fichier."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
    return Config(config_path)


def send_notification(manager, template, recipients, data=None, channels=None, schedule_time=None):
    """Envoie une notification via les canaux spécifiés."""
    # Préparer les données si non fournies
    if data is None:
        # Données d'exemple
        data = {
            "client": {
                "name": "Jean Dupont",
                "email": "jean.dupont@example.com"
            },
            "reservation": {
                "date": "15 avril 2025",
                "time": "20:00",
                "guests": 4
            },
            "offer": {
                "title": "Menu Dégustation",
                "description": "Un dessert offert pour votre réservation",
                "valid_until": "30 avril 2025"
            },
            "booking_link": "https://levieuxmoulin.fr/reservation?ref=email"
        }
    
    # Envoyer la notification
    result = manager.send_notification(
        template=template,
        recipients=recipients,
        data=data,
        channels=channels,
        schedule_time=schedule_time
    )
    
    print(f"Résultat de la notification: {json.dumps(result, indent=2)}")
    return result


def get_notification_status(manager, notification_id):
    """Récupère le statut d'une notification."""
    result = manager.get_notification_status(notification_id)
    print(f"Statut de la notification: {json.dumps(result, indent=2)}")
    return result


def cancel_notification(manager, notification_id):
    """Annule une notification programmée."""
    result = manager.cancel_scheduled_notification(notification_id)
    print(f"Annulation de la notification: {result}")
    return result


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Exemple d'utilisation du module de notification")
    parser.add_argument('--action', choices=['send', 'status', 'cancel'], default='send',
                      help='Action à effectuer: envoyer une notification, vérifier son statut ou l\'annuler')
    parser.add_argument('--template', type=str, default='special_offer',
                      help='Template à utiliser pour la notification')
    parser.add_argument('--recipients', type=str, nargs='+',
                      help='Destinataires de la notification (emails, numéros de téléphone, etc.)')
    parser.add_argument('--channels', type=str, nargs='+', default=['email'],
                      help='Canaux à utiliser pour la notification (email, sms, push)')
    parser.add_argument('--schedule', type=str,
                      help='Date et heure de notification programmée (format ISO: 2025-04-20T18:30:00)')
    parser.add_argument('--data', type=str,
                      help='Chemin vers un fichier JSON contenant les données pour le template')
    parser.add_argument('--notification-id', type=str,
                      help='ID de la notification pour les actions status et cancel')
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config()
    
    # Initialiser le gestionnaire
    manager = NotificationManager(config)
    
    # Charger les données si un fichier est spécifié
    data = None
    if args.data and os.path.exists(args.data):
        with open(args.data, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # Exécuter l'action demandée
    if args.action == 'send':
        # Vérifier les destinataires
        if not args.recipients:
            if not data or 'client' not in data or 'email' not in data['client']:
                args.recipients = ['client@example.com']
            else:
                args.recipients = [data['client']['email']]
                
        send_notification(
            manager,
            template=args.template,
            recipients=args.recipients,
            data=data,
            channels=args.channels,
            schedule_time=args.schedule
        )
    elif args.action == 'status':
        if not args.notification_id:
            print("Erreur: L'ID de notification est requis pour l'action 'status'")
            sys.exit(1)
        get_notification_status(manager, args.notification_id)
    elif args.action == 'cancel':
        if not args.notification_id:
            print("Erreur: L'ID de notification est requis pour l'action 'cancel'")
            sys.exit(1)
        cancel_notification(manager, args.notification_id)


if __name__ == "__main__":
    main()
