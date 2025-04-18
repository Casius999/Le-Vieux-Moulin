#!/usr/bin/env python3
"""
Script de configuration initiale pour le module de communication et d'automatisation marketing.

Ce script permet de configurer rapidement les éléments essentiels du module,
notamment les accès aux API des réseaux sociaux, les services de notification,
et les intégrations avec les autres modules du système.
"""

import os
import sys
import json
import logging
import argparse
import getpass
import shutil
from pathlib import Path

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('communication_setup')

# Chemin vers les fichiers de configuration
CONFIG_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))
DEFAULT_CONFIG = CONFIG_DIR / 'settings.default.json'
TARGET_CONFIG = CONFIG_DIR / 'settings.json'

# Chemins des autres fichiers de configuration
PLATFORMS_CONFIG = CONFIG_DIR / 'platforms.json'
TEMPLATES_CONFIG = CONFIG_DIR / 'templates.json'
DATA_MAPPINGS_CONFIG = CONFIG_DIR / 'data_mappings.json'

def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description='Configuration du module de communication')
    parser.add_argument('--non-interactive', action='store_true',
                      help='Mode non interactif (utilise les valeurs par défaut)')
    parser.add_argument('--config-file', type=str,
                      help='Chemin vers un fichier de configuration personnalisé')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    return parser.parse_args()

def create_directory_if_not_exists(path):
    """Crée un répertoire s'il n'existe pas déjà."""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Répertoire créé : {path}")
    return path

def copy_default_config():
    """Copie le fichier de configuration par défaut."""
    if not os.path.exists(DEFAULT_CONFIG):
        logger.error(f"Fichier de configuration par défaut introuvable : {DEFAULT_CONFIG}")
        return False
    
    if os.path.exists(TARGET_CONFIG):
        logger.warning(f"Le fichier de configuration existe déjà : {TARGET_CONFIG}")
        overwrite = input("Voulez-vous l'écraser ? (o/n) : ").lower() == 'o'
        if not overwrite:
            logger.info("Configuration existante conservée.")
            return False
    
    shutil.copy2(DEFAULT_CONFIG, TARGET_CONFIG)
    logger.info(f"Configuration par défaut copiée vers {TARGET_CONFIG}")
    return True

def load_config(config_file=None):
    """Charge la configuration depuis un fichier JSON."""
    file_path = config_file if config_file else TARGET_CONFIG
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration : {e}")
        return None

def save_config(config, config_file=None):
    """Enregistre la configuration dans un fichier JSON."""
    file_path = config_file if config_file else TARGET_CONFIG
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration enregistrée dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la configuration : {e}")
        return False

def interactive_config_setup(config):
    """Configuration interactive des paramètres principaux."""
    logger.info("=== Configuration interactive du module de communication ===")
    
    # Paramètres généraux du restaurant
    print("\n--- Paramètres généraux ---")
    config["general"]["restaurant_name"] = input(f"Nom du restaurant [{config['general']['restaurant_name']}] : ") or config["general"]["restaurant_name"]
    config["general"]["base_url"] = input(f"URL du site web [{config['general']['base_url']}] : ") or config["general"]["base_url"]
    config["general"]["timezone"] = input(f"Fuseau horaire [{config['general']['timezone']}] : ") or config["general"]["timezone"]
    
    # Configuration de l'API
    print("\n--- Configuration de l'API ---")
    config["api"]["port"] = int(input(f"Port d'écoute de l'API [{config['api']['port']}] : ") or config["api"]["port"])
    
    # Configuration des bases de données
    print("\n--- Configuration de la base de données ---")
    config["database"]["host"] = input(f"Hôte DB [{config['database']['host']}] : ") or config["database']['host']
    config["database"]["port"] = int(input(f"Port DB [{config['database']['port']}] : ") or config["database"]["port"])
    config["database"]["database"] = input(f"Nom de la base [{config['database']['database']}] : ") or config["database"]["database"]
    config["database"]["user"] = input(f"Utilisateur DB [{config['database']['user']}] : ") or config["database"]["user"]
    config["database"]["password"] = getpass.getpass(f"Mot de passe DB : ") or config["database"]["password"]
    
    # Configuration des notifications
    print("\n--- Configuration des notifications par email ---")
    providers = ["sendgrid", "mailjet", "smtp"]
    print(f"Providers disponibles : {', '.join(providers)}")
    config["notification"]["email"]["provider"] = input(f"Provider d'email [{config['notification']['email']['provider']}] : ") or config["notification"]["email"]["provider"]
    config["notification"]["email"]["api_key"] = getpass.getpass(f"Clé API {config['notification']['email']['provider']} : ") or config["notification"]["email"]["api_key"]
    config["notification"]["email"]["from_email"] = input(f"Email expéditeur [{config['notification']['email']['from_email']}] : ") or config["notification"]["email"]["from_email"]
    config["notification"]["email"]["from_name"] = input(f"Nom expéditeur [{config['notification']['email']['from_name']}] : ") or config["notification"]["email"]["from_name"]
    
    # Configuration des SMS
    print("\n--- Configuration des notifications par SMS ---")
    sms_providers = ["twilio", "ovh", "nexmo"]
    print(f"Providers disponibles : {', '.join(sms_providers)}")
    config["notification"]["sms"]["provider"] = input(f"Provider SMS [{config['notification']['sms']['provider']}] : ") or config["notification"]["sms"]["provider"]
    config["notification"]["sms"]["account_sid"] = getpass.getpass(f"SID du compte {config['notification']['sms']['provider']} : ") or config["notification"]["sms"]["account_sid"]
    config["notification"]["sms"]["auth_token"] = getpass.getpass(f"Token d'auth {config['notification']['sms']['provider']} : ") or config["notification"]["sms"]["auth_token"]
    config["notification"]["sms"]["from_number"] = input(f"Numéro expéditeur [{config['notification']['sms']['from_number']}] : ") or config["notification"]["sms"]["from_number"]
    
    # Configuration des intégrations
    print("\n--- Configuration des intégrations ---")
    config["integration"]["central_api_url"] = input(f"URL API centrale [{config['integration']['central_api_url']}] : ") or config["integration"]["central_api_url"]
    config["integration"]["crm_api_url"] = input(f"URL API CRM [{config['integration']['crm_api_url']}] : ") or config["integration"]["crm_api_url"]
    config["integration"]["recipes_api_url"] = input(f"URL API recettes [{config['integration']['recipes_api_url']}] : ") or config["integration"]["recipes_api_url"]
    config["integration"]["webhook_secret"] = getpass.getpass(f"Secret pour les webhooks : ") or config["integration"]["webhook_secret"]
    
    # Configuration de sécurité
    print("\n--- Configuration de sécurité ---")
    config["security"]["api_key"] = getpass.getpass(f"Clé API pour l'authentification : ") or config["security"]["api_key"]
    config["security"]["jwt"]["secret"] = getpass.getpass(f"Secret JWT : ") or config["security"]["jwt"]["secret"]
    
    return config

def create_empty_platforms_config():
    """Crée un fichier de configuration de plateformes vide."""
    platforms_config = {
        "facebook": {
            "app_id": "",
            "app_secret": "",
            "page_id": "",
            "access_token": "",
            "api_version": "v18.0"
        },
        "instagram": {
            "business_account_id": "",
            "access_token": ""
        },
        "twitter": {
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "access_token_secret": ""
        }
    }
    
    try:
        with open(PLATFORMS_CONFIG, 'w') as f:
            json.dump(platforms_config, f, indent=2)
        logger.info(f"Fichier de configuration des plateformes créé : {PLATFORMS_CONFIG}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du fichier de configuration des plateformes : {e}")
        return False

def create_empty_templates_config():
    """Crée un fichier de configuration de templates vide."""
    templates_config = {
        "promotional_email": {
            "subject": "{{promo_title}} - Offre spéciale {{restaurant_name}}",
            "body_html": "<h1>{{promo_title}}</h1><p>Cher(e) {{customer.first_name}},</p><p>{{promo_description}}</p><p>Cette offre est valable jusqu'au {{valid_until}}.</p><p><a href='{{booking_link}}'>Réservez maintenant</a></p>"
        },
        "menu_update": {
            "subject": "Nouveau menu au {{restaurant_name}}",
            "body_html": "<h1>Notre nouveau menu est arrivé !</h1><p>Découvrez nos nouvelles créations et venez les déguster au {{restaurant_name}}.</p>{{#each menu_items}}<p><strong>{{this.name}}</strong> - {{this.price}}€<br>{{this.description}}</p>{{/each}}"
        },
        "event_invitation": {
            "subject": "{{event_name}} - Invitation spéciale",
            "body_html": "<h1>{{event_name}}</h1><p>Cher(e) {{customer.first_name}},</p><p>Nous avons le plaisir de vous inviter à notre {{event_name}} qui se tiendra le {{event_date}} à {{event_time}}.</p><p>{{event_description}}</p><p>Tarif : {{price}}</p><p><a href='{{reservation_link}}'>Réservez votre place</a></p>"
        }
    }
    
    try:
        with open(TEMPLATES_CONFIG, 'w') as f:
            json.dump(templates_config, f, indent=2)
        logger.info(f"Fichier de configuration des templates créé : {TEMPLATES_CONFIG}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du fichier de configuration des templates : {e}")
        return False

def create_data_mappings_config():
    """Crée un fichier de mappages de données."""
    mappings_config = {
        "recipe_to_post": {
            "name": "title",
            "description": "body",
            "image_url": "media_url",
            "price": "price_info",
            "ingredients": "ingredients_list",
            "preparation_time": "preparation_info"
        },
        "customer_to_recipient": {
            "email": "email",
            "phone": "phone",
            "first_name": "first_name",
            "last_name": "last_name",
            "preferences": "preferences"
        }
    }
    
    try:
        with open(DATA_MAPPINGS_CONFIG, 'w') as f:
            json.dump(mappings_config, f, indent=2)
        logger.info(f"Fichier de mappages de données créé : {DATA_MAPPINGS_CONFIG}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du fichier de mappages de données : {e}")
        return False

def test_database_connection(config):
    """Teste la connexion à la base de données."""
    logger.info("Test de la connexion à la base de données...")
    
    try:
        db_config = config["database"]
        db_type = db_config["type"]
        
        if db_type == "postgresql":
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=db_config["host"],
                    port=db_config["port"],
                    database=db_config["database"],
                    user=db_config["user"],
                    password=db_config["password"]
                )
                conn.close()
                logger.info("Connexion à la base de données PostgreSQL réussie")
                return True
            except ImportError:
                logger.warning("Module psycopg2 non installé. Impossible de tester la connexion PostgreSQL")
            except Exception as e:
                logger.error(f"Erreur de connexion à la base de données PostgreSQL : {e}")
        else:
            logger.warning(f"Type de base de données non pris en charge pour le test : {db_type}")
    
    except Exception as e:
        logger.error(f"Erreur lors du test de connexion à la base de données : {e}")
    
    return False

def test_redis_connection(config):
    """Teste la connexion à Redis."""
    logger.info("Test de la connexion à Redis...")
    
    try:
        cache_config = config["cache"]
        if cache_config["type"] == "redis":
            try:
                import redis
                r = redis.Redis(
                    host=cache_config["host"],
                    port=cache_config["port"],
                    db=cache_config["db"]
                )
                r.ping()
                logger.info("Connexion à Redis réussie")
                return True
            except ImportError:
                logger.warning("Module redis non installé. Impossible de tester la connexion Redis")
            except Exception as e:
                logger.error(f"Erreur de connexion à Redis : {e}")
        else:
            logger.warning(f"Type de cache non pris en charge pour le test : {cache_config['type']}")
    
    except Exception as e:
        logger.error(f"Erreur lors du test de connexion à Redis : {e}")
    
    return False

def test_rabbitmq_connection(config):
    """Teste la connexion à RabbitMQ."""
    logger.info("Test de la connexion à RabbitMQ...")
    
    try:
        queue_config = config["queue"]
        if queue_config["type"] == "rabbitmq":
            try:
                import pika
                credentials = pika.PlainCredentials(
                    username=queue_config["user"],
                    password=queue_config["password"]
                )
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=queue_config["host"],
                        port=queue_config["port"],
                        virtual_host=queue_config["vhost"],
                        credentials=credentials
                    )
                )
                connection.close()
                logger.info("Connexion à RabbitMQ réussie")
                return True
            except ImportError:
                logger.warning("Module pika non installé. Impossible de tester la connexion RabbitMQ")
            except Exception as e:
                logger.error(f"Erreur de connexion à RabbitMQ : {e}")
        else:
            logger.warning(f"Type de file d'attente non pris en charge pour le test : {queue_config['type']}")
    
    except Exception as e:
        logger.error(f"Erreur lors du test de connexion à RabbitMQ : {e}")
    
    return False

def finalize_setup():
    """Finalise la configuration en affichant des messages et instructions."""
    print("\n=== Configuration terminée ===")
    print("\nPour démarrer le module de communication :")
    print("  1. Vérifiez que tous les services nécessaires sont en cours d'exécution (PostgreSQL, Redis, RabbitMQ)")
    print("  2. Configurez les accès aux API des réseaux sociaux dans config/platforms.json")
    print("  3. Personnalisez les templates de notification dans config/templates.json si nécessaire")
    print("  4. Exécutez le module : python src/main.py")
    print("\nPour configurer les accès aux API des réseaux sociaux :")
    print("  1. Créez des applications développeur sur Facebook, Instagram, Twitter, etc.")
    print("  2. Obtenez les clés API et tokens d'accès")
    print("  3. Mettez à jour le fichier config/platforms.json avec ces informations")
    
    print("\nConsultez la documentation pour plus d'informations :")
    print("  - README.md : Documentation générale du module")
    print("  - COMMUNICATION.md : Documentation technique détaillée")
    print("  - examples/ : Exemples d'utilisation du module")
    
    print("\nPour toute question ou assistance supplémentaire, consultez la documentation.")

def main():
    """Fonction principale du script de configuration."""
    args = parse_arguments()
    
    # Configurer le niveau de log
    logger.setLevel(getattr(logging, args.log_level))
    
    # Créer le répertoire de configuration s'il n'existe pas
    create_directory_if_not_exists(CONFIG_DIR)
    
    # Si un fichier de configuration personnalisé est spécifié
    if args.config_file:
        if not os.path.exists(args.config_file):
            logger.error(f"Fichier de configuration personnalisé introuvable : {args.config_file}")
            return 1
        
        # Copier le fichier de configuration personnalisé
        shutil.copy2(args.config_file, TARGET_CONFIG)
        logger.info(f"Configuration personnalisée copiée depuis {args.config_file}")
    else:
        # Copier la configuration par défaut
        if not copy_default_config():
            if not os.path.exists(TARGET_CONFIG):
                logger.error("Impossible de créer le fichier de configuration")
                return 1
    
    # Charger la configuration
    config = load_config()
    if not config:
        logger.error("Impossible de charger la configuration")
        return 1
    
    # Configuration interactive
    if not args.non_interactive:
        config = interactive_config_setup(config)
        
        # Enregistrer la configuration mise à jour
        if not save_config(config):
            logger.error("Impossible d'enregistrer la configuration")
            return 1
    
    # Créer les fichiers de configuration supplémentaires s'ils n'existent pas
    if not os.path.exists(PLATFORMS_CONFIG):
        create_empty_platforms_config()
    
    if not os.path.exists(TEMPLATES_CONFIG):
        create_empty_templates_config()
    
    if not os.path.exists(DATA_MAPPINGS_CONFIG):
        create_data_mappings_config()
    
    # Tester les connexions aux services externes
    if not args.non_interactive:
        test_choice = input("\nVoulez-vous tester les connexions aux services (base de données, Redis, RabbitMQ) ? (o/n) : ").lower()
        if test_choice == 'o':
            test_database_connection(config)
            test_redis_connection(config)
            test_rabbitmq_connection(config)
    
    # Finaliser et afficher les instructions
    finalize_setup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
