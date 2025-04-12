#!/usr/bin/env python3
"""
Exemple d'utilisation du module de réseaux sociaux

Ce script illustre comment utiliser le gestionnaire de réseaux sociaux
pour publier du contenu et récupérer des analytics.
"""

import os
import sys
import json
import datetime
import argparse

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common import Config
from src.social_media import SocialMediaManager


def load_config():
    """Charge la configuration depuis un fichier."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
    return Config(config_path)


def publish_content(manager, content_file=None, platforms=None, scheduled_time=None):
    """Publie du contenu sur les réseaux sociaux."""
    # Charger le contenu depuis un fichier ou utiliser un exemple par défaut
    if content_file and os.path.exists(content_file):
        with open(content_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
    else:
        # Contenu d'exemple
        content = {
            "title": "Plat du jour au Vieux Moulin",
            "body": "Aujourd'hui, notre chef vous propose une délicieuse paella aux fruits de mer. Venez la déguster dans le cadre chaleureux du Vieux Moulin. Réservations au 05.56.XX.XX.XX",
            "media_urls": ["https://example.com/images/paella.jpg"],
            "hashtags": ["vieuxmoulin", "gastronomie", "paella", "vensac"]
        }
    
    # Publier le contenu
    result = manager.publish_content(
        content=content,
        platforms=platforms,
        scheduled_time=scheduled_time
    )
    
    print(f"Résultat de la publication: {json.dumps(result, indent=2)}")
    return result


def get_analytics(manager, platform=None, start_date=None, end_date=None, post_ids=None):
    """Récupère des analytics sur les réseaux sociaux."""
    # Convertir les dates si elles sont fournies
    if start_date:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    
    if end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    # Récupérer les analytics
    result = manager.get_analytics(
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        post_ids=post_ids
    )
    
    print(f"Résultat des analytics: {json.dumps(result, indent=2)}")
    return result


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Exemple d'utilisation du module de réseaux sociaux")
    parser.add_argument('--action', choices=['publish', 'analytics'], default='publish',
                      help='Action à effectuer: publier du contenu ou récupérer des analytics')
    parser.add_argument('--content', type=str, help='Chemin vers un fichier JSON contenant le contenu à publier')
    parser.add_argument('--platforms', type=str, nargs='+', help='Plateformes cibles (facebook, instagram, etc.)')
    parser.add_argument('--schedule', type=str, help='Date et heure de publication programmée (format ISO: 2025-04-20T18:30:00)')
    parser.add_argument('--platform', type=str, help='Plateforme pour les analytics (facebook, instagram, etc.)')
    parser.add_argument('--start-date', type=str, help='Date de début pour les analytics (format: YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Date de fin pour les analytics (format: YYYY-MM-DD)')
    parser.add_argument('--post-ids', type=str, nargs='+', help='IDs des publications pour les analytics')
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config()
    
    # Initialiser le gestionnaire
    manager = SocialMediaManager(config)
    
    # Exécuter l'action demandée
    if args.action == 'publish':
        scheduled_time = args.schedule
        publish_content(manager, args.content, args.platforms, scheduled_time)
    elif args.action == 'analytics':
        get_analytics(manager, args.platform, args.start_date, args.end_date, args.post_ids)


if __name__ == "__main__":
    main()
