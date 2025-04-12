#!/usr/bin/env python3
"""
Exemple d'utilisation du module de notifications

Ce script illustre comment utiliser le gestionnaire de notifications
pour envoyer des messages aux clients.
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
    """Envoie une notification aux destinataires."""
    # Préparer les données pour le template
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
                "description": "Un menu dégustation complet offert pour votre anniversaire",
                "valid_until": "30 avril 2025"
            },
            "booking_link": "https://levieuxmoulin.fr/reservation?utm_source=email&utm_campaign=birthday"
        }
    
    # Envoyer la notification
    result = manager.send_notification(
        template=template,
        recipients=recipients,
        data=data,
        channels=channels,
        schedule_time=schedule_time
    )
    
    print(f"Résultat de l'envoi: {json.dumps(result, indent=2)}")
    return result


def get_notification_status(manager, notification_id):
    """Récupère le statut d'une notification."""
    result = manager.get_notification_status(notification_id)
    print(f"Statut de la notification: {json.dumps(result, indent=2)}")
    return result


def cancel_notification(manager, notification_id):
    """Annule une notification programmée."""
    result = manager.cancel_scheduled_notification(notification_id)
    print(f"Résultat de l'annulation: {result}")
    return result


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Exemple d'utilisation du module de notifications")
    parser.add_argument('--action', choices=['send', 'status', 'cancel'], default='send',
                      help='Action à effectuer: envoyer une notification, récupérer son statut ou annuler')
    parser.add_argument('--template', type=str, default='reservation_confirmation',
                      help='Template à utiliser pour la notification')
    parser.add_argument('--recipients', type=str, nargs='+', 
                      help='Adresses email ou numéros de téléphone des destinataires')
    parser.add_argument('--channels', type=str, nargs='+', choices=['email', 'sms', 'push'],
                      help='Canaux à utiliser pour l\'envoi')
    parser.add_argument('--schedule', type=str, 
                      help='Date et heure d\'envoi programmée (format ISO: 2025-04-20T18:30:00)')
    parser.add_argument('--notification-id', type=str, 
                      help='ID de la notification pour obtenir son statut ou l\'annuler')
    parser.add_argument('--data-file', type=str,
                      help='Chemin vers un fichier JSON contenant les données pour le template')
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config()
    
    # Initialiser le gestionnaire
    manager = NotificationManager(config)
    
    # Charger les données si spécifiées
    data = None
    if args.data_file and os.path.exists(args.data_file):
        with open(args.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # Exécuter l'action demandée
    if args.action == 'send':
        # Vérifier qu'il y a au moins un destinataire
        if not args.recipients:
            print("Erreur: Vous devez spécifier au moins un destinataire avec --recipients")
            return
            
        # Convertir la date de programmation si nécessaire
        schedule_time = args.schedule
        
        send_notification(
            manager, 
            args.template, 
            args.recipients, 
            data, 
            args.channels, 
            schedule_time
        )
    elif args.action == 'status':
        if not args.notification_id:
            print("Erreur: Vous devez spécifier un ID de notification avec --notification-id")
            return
            
        get_notification_status(manager, args.notification_id)
    elif args.action == 'cancel':
        if not args.notification_id:
            print("Erreur: Vous devez spécifier un ID de notification avec --notification-id")
            return
            
        cancel_notification(manager, args.notification_id)


if __name__ == "__main__":
    main()
