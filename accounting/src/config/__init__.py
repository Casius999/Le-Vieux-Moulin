"""
Module de configuration pour le module de comptabilité.
Centralise l'accès aux paramètres de configuration de l'application.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

# Recherche du fichier de configuration
CONFIG_PATHS = [
    # Ordre de priorité pour la recherche du fichier de configuration
    os.environ.get("ACCOUNTING_CONFIG_PATH"),  # Variable d'environnement prioritaire
    os.path.join(os.getcwd(), "config", "config.json"),  # Répertoire courant
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "config.json"),  # Relatif au module
    "/etc/levieuxmoulin/accounting/config.json",  # Installation système
]


# Modèles de configuration
class DatabaseConfig(BaseModel):
    """Configuration de la base de données."""
    host: str = "localhost"
    port: int = 5432
    database: str = "levieuxmoulin_accounting"
    user: str = "accounting_user"
    password: str = Field(..., exclude=True)  # Mot de passe exclu des logs/dumps
    pool_size: int = 10
    ssl_enabled: bool = False
    ssl_ca_cert: Optional[str] = None


class ServerConfig(BaseModel):
    """Configuration du serveur API."""
    host: str = "0.0.0.0"
    port: int = 8081
    debug: bool = False
    log_level: str = "info"
    workers: int = 4


class SecurityConfig(BaseModel):
    """Configuration de sécurité."""
    secret_key: str = Field(..., exclude=True)
    algorithm: str = "HS256"
    token_expire_minutes: int = 60
    ssl_enabled: bool = False
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None


class IntegrationConfig(BaseModel):
    """Configuration des intégrations avec les autres modules."""
    central_server_url: str
    api_key: str = Field(..., exclude=True)
    retry_attempts: int = 3
    timeout_seconds: int = 30


class ReportingConfig(BaseModel):
    """Configuration de la génération des rapports."""
    report_directory: str
    temp_directory: str
    default_format: str = "pdf"


class EmailConfig(BaseModel):
    """Configuration des notifications par email."""
    smtp_server: str
    smtp_port: int = 587
    username: str
    password: str = Field(..., exclude=True)
    default_sender: str
    use_tls: bool = True


class DataSourceConfig(BaseModel):
    """Configuration d'une source de données."""
    type: str  # api, file_import, webhook
    url: Optional[str] = None
    auth_type: Optional[str] = None
    refresh_interval_minutes: int = 60
    directory: Optional[str] = None
    file_pattern: Optional[str] = None
    import_schedule: Optional[str] = None  # Format cron


class DataSourcesConfig(BaseModel):
    """Configuration de toutes les sources de données."""
    pos: DataSourceConfig
    inventory: DataSourceConfig
    suppliers: DataSourceConfig
    payroll: DataSourceConfig


class Settings(BaseModel):
    """Configuration globale de l'application."""
    database: DatabaseConfig
    server: ServerConfig
    security: SecurityConfig
    integration: IntegrationConfig
    reporting: ReportingConfig
    email: EmailConfig
    data_sources: DataSourcesConfig


def load_config() -> Settings:
    """
    Charge la configuration depuis le fichier de configuration.
    Recherche le fichier dans les emplacements pré-définis.
    
    Returns:
        Settings: Instance de la configuration globale
    
    Raises:
        FileNotFoundError: Si aucun fichier de configuration n'est trouvé
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide
        ValueError: Si la configuration est invalide
    """
    # Recherche du fichier de configuration
    config_file = None
    for path in CONFIG_PATHS:
        if path and os.path.isfile(path):
            config_file = path
            break
    
    if not config_file:
        raise FileNotFoundError("Aucun fichier de configuration trouvé.")
    
    # Chargement du fichier
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    
    # Création de l'instance de configuration
    return Settings(**config_data)


# Création de l'instance de configuration globale
settings = load_config()
