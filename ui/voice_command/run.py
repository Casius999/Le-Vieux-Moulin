#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de lancement du module de commande vocale.

Ce script permet de démarrer facilement le module de commande vocale
avec différentes options de configuration.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import os
import sys
import argparse
from voice_command.app import VoiceCommandApp


def parse_arguments():
    """Analyse les arguments de ligne de commande.
    
    Returns:
        argparse.Namespace: Arguments analysés.
    """
    parser = argparse.ArgumentParser(description="Module de commande vocale pour Le Vieux Moulin")
    parser.add_argument("--config", help="Chemin vers le fichier de configuration")
    parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'écoute (défaut: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port d'écoute (défaut: 5000)")
    return parser.parse_args()


def main():
    """Point d'entrée principal du script de lancement."""
    args = parse_arguments()
    
    # Créer une instance de l'application
    app = VoiceCommandApp(config_path=args.config, debug=args.debug)
    
    try:
        # Démarrer l'application
        app.start()
        
        # Lancer le serveur web
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nInterruption détectée. Arrêt de l'application...")
        app.stop()
    except Exception as e:
        print(f"Erreur fatale: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
