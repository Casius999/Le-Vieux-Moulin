#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration du module d'optimisation des plannings.

Ce fichier contient toutes les constantes et paramètres configurables
du système de planification et d'optimisation des horaires du personnel
pour le restaurant "Le Vieux Moulin".
"""

import os
import json
import logging
from datetime import time

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

# Création des répertoires s'ils n'existent pas
for directory in [DATA_DIR, LOG_DIR, EXPORT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Configuration du logger
LOG_LEVEL = os.environ.get("STAFFING_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOG_DIR, "staffing_scheduler.log")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("staffing_scheduler")

# Configuration de la base de données
DATABASE = {
    "type": os.environ.get("DB_TYPE", "postgresql"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "vieux_moulin"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "ssl_mode": os.environ.get("DB_SSL_MODE", "prefer")
}

# Configuration de l'API
API_CONFIG = {
    "host": os.environ.get("API_HOST", "0.0.0.0"),
    "port": int(os.environ.get("API_PORT", 5002)),
    "debug": os.environ.get("API_DEBUG", "False").lower() == "true",
    "auth_required": os.environ.get("API_AUTH_REQUIRED", "True").lower() == "true",
    "cors_origins": os.environ.get("API_CORS_ORIGINS", "*").split(","),
    "rate_limit": int(os.environ.get("API_RATE_LIMIT", 100))
}

# Configuration de l'interface web
WEBAPP_CONFIG = {
    "host": os.environ.get("WEBAPP_HOST", "0.0.0.0"),
    "port": int(os.environ.get("WEBAPP_PORT", 5003)),
    "debug": os.environ.get("WEBAPP_DEBUG", "False").lower() == "true",
    "secret_key": os.environ.get("WEBAPP_SECRET_KEY", "vieux-moulin-staff-scheduler-secret"),
    "session_lifetime": int(os.environ.get("WEBAPP_SESSION_LIFETIME", 8)) * 3600  # en secondes
}

# URLs des services d'intégration
INTEGRATION = {
    "prediction_api_url": os.environ.get("PREDICTION_API_URL", "http://localhost:8000"),
    "reservation_api_url": os.environ.get("RESERVATION_API_URL", "http://localhost:5001"),
    "accounting_api_url": os.environ.get("ACCOUNTING_API_URL", "http://localhost:5004"),
    "notification_api_url": os.environ.get("NOTIFICATION_API_URL", "http://localhost:5005")
}

# Contraintes légales et règles d'optimisation
SCHEDULING_CONSTRAINTS = {
    # Contraintes temporelles légales
    "min_rest_hours": float(os.environ.get("MIN_REST_HOURS", 11.0)),  # Heures minimum de repos entre deux services
    "max_daily_hours": float(os.environ.get("MAX_DAILY_HOURS", 10.0)),  # Heures maximum par jour
    "max_weekly_hours": float(os.environ.get("MAX_WEEKLY_HOURS", 48.0)),  # Heures maximum par semaine
    "max_consecutive_days": int(os.environ.get("MAX_CONSECUTIVE_DAYS", 6)),  # Jours de travail maximum consécutifs
    
    # Pauses
    "break_after_hours": float(os.environ.get("BREAK_AFTER_HOURS", 4.5)),  # Pause après X heures de travail
    "min_break_duration": float(os.environ.get("MIN_BREAK_DURATION", 0.5)),  # Durée minimum de pause (heures)
    
    # Plages horaires par défaut
    "default_shifts": {
        "matin": {
            "start": time(9, 0),
            "end": time(16, 0)
        },
        "soir": {
            "start": time(16, 0),
            "end": time(23, 30)
        },
        "jour_complet": {
            "start": time(9, 0),
            "end": time(23, 30)
        }
    }
}

# Configuration des postes et des ratios de personnel
STAFFING_CONFIGURATION = {
    "roles": {
        "chef": {
            "min_per_shift": 1,
            "max_per_shift": 3,
            "customer_ratio": 0,  # Non lié au nombre de clients
            "priority": 10  # Plus élevé = plus prioritaire dans l'affectation
        },
        "sous_chef": {
            "min_per_shift": 0,
            "max_per_shift": 2,
            "customer_ratio": 0.02,  # 1 pour 50 clients
            "priority": 9
        },
        "chef_de_rang": {
            "min_per_shift": 1,
            "max_per_shift": 3,
            "customer_ratio": 0.04,  # 1 pour 25 clients
            "priority": 8
        },
        "serveur": {
            "min_per_shift": 2,
            "max_per_shift": 10,
            "customer_ratio": 0.1,  # 1 pour 10 clients
            "priority": 7
        },
        "barman": {
            "min_per_shift": 0,
            "max_per_shift": 2,
            "customer_ratio": 0.05,  # 1 pour 20 clients
            "priority": 6
        },
        "plongeur": {
            "min_per_shift": 1,
            "max_per_shift": 3,
            "customer_ratio": 0.03,  # 1 pour ~33 clients
            "priority": 5
        },
        "hôte": {
            "min_per_shift": 0,
            "max_per_shift": 2,
            "customer_ratio": 0.04,  # 1 pour 25 clients
            "priority": 6
        }
    },
    
    # Coefficients d'ajustement selon le jour de la semaine (1.0 = base)
    "day_factors": {
        0: 0.8,  # Lundi
        1: 0.8,  # Mardi
        2: 0.9,  # Mercredi
        3: 1.0,  # Jeudi
        4: 1.2,  # Vendredi
        5: 1.5,  # Samedi
        6: 1.3   # Dimanche
    },
    
    # Coefficients pour événements spéciaux
    "special_events": {
        "default": 1.2,
        "holiday": 1.5,
        "promotion": 1.3,
        "private_event": 1.1
    }
}

# Configuration de l'algorithme d'optimisation génétique
OPTIMIZATION_CONFIG = {
    "population_size": int(os.environ.get("OPT_POPULATION_SIZE", 100)),
    "generations": int(os.environ.get("OPT_GENERATIONS", 50)),
    "mutation_rate": float(os.environ.get("OPT_MUTATION_RATE", 0.1)),
    "crossover_rate": float(os.environ.get("OPT_CROSSOVER_RATE", 0.8)),
    "elitism_count": int(os.environ.get("OPT_ELITISM_COUNT", 5)),
    
    # Poids des différents objectifs dans la fonction de fitness
    "weights": {
        "coverage": float(os.environ.get("WEIGHT_COVERAGE", 0.4)),  # Couverture des besoins
        "preferences": float(os.environ.get("WEIGHT_PREFERENCES", 0.3)),  # Préférences employés
        "cost": float(os.environ.get("WEIGHT_COST", 0.2)),  # Coût salarial
        "stability": float(os.environ.get("WEIGHT_STABILITY", 0.1))  # Stabilité par rapport aux anciens plannings
    },
    
    # Paramètres de performance
    "parallel_processing": os.environ.get("OPT_PARALLEL", "True").lower() == "true",
    "max_workers": int(os.environ.get("OPT_MAX_WORKERS", 4)),
    "timeout_seconds": int(os.environ.get("OPT_TIMEOUT", 120))
}

# Configuration des notifications
NOTIFICATION_CONFIG = {
    "enabled": os.environ.get("NOTIFICATIONS_ENABLED", "True").lower() == "true",
    "email": {
        "enabled": os.environ.get("EMAIL_NOTIFICATIONS", "True").lower() == "true",
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.example.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
        "smtp_user": os.environ.get("SMTP_USER", "notifications@vieuxmoulin.fr"),
        "smtp_password": os.environ.get("SMTP_PASSWORD", ""),
        "from_address": os.environ.get("EMAIL_FROM", "planning@vieuxmoulin.fr"),
        "subject_prefix": "[Le Vieux Moulin] "
    },
    "sms": {
        "enabled": os.environ.get("SMS_NOTIFICATIONS", "False").lower() == "true",
        "provider": os.environ.get("SMS_PROVIDER", "twilio"),
        "account_id": os.environ.get("SMS_ACCOUNT_ID", ""),
        "auth_token": os.environ.get("SMS_AUTH_TOKEN", ""),
        "from_number": os.environ.get("SMS_FROM", "")
    }
}

# Fonction d'aide pour charger une configuration personnalisée depuis un fichier JSON
def load_custom_config(config_file):
    """
    Charge une configuration personnalisée depuis un fichier JSON.
    
    Args:
        config_file (str): Chemin vers le fichier de configuration
        
    Returns:
        dict: Configuration chargée
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
                logger.info(f"Configuration personnalisée chargée depuis {config_file}")
                return custom_config
        else:
            logger.warning(f"Fichier de configuration {config_file} introuvable")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        return {}

# Charger une configuration personnalisée si définie
CUSTOM_CONFIG_PATH = os.environ.get("CUSTOM_CONFIG_PATH", "")
if CUSTOM_CONFIG_PATH:
    custom_config = load_custom_config(CUSTOM_CONFIG_PATH)
    
    # Mettre à jour les configurations avec les valeurs personnalisées
    # (implémenter une logique de fusion récursive si nécessaire)
