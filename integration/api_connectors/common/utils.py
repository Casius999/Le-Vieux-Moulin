"""Utilitaires communs pour les connecteurs API.

Ce module fournit des fonctions et classes utilitaires partagées
entre les différents connecteurs API.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, date

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None, config_dict: Optional[Dict] = None) -> Dict[str, Any]:
    """Charge la configuration depuis un fichier ou un dictionnaire.
    
    Args:
        config_path: Chemin vers le fichier de configuration (YAML ou JSON)
        config_dict: Dictionnaire de configuration (prioritaire sur config_path)
        
    Returns:
        Dictionnaire de configuration
        
    Raises:
        ConfigurationError: Si le chargement de la configuration échoue
    """
    if config_dict is not None:
        return config_dict
    
    if not config_path:
        raise ConfigurationError("Aucune configuration fournie (ni fichier, ni dictionnaire)")
    
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Fichier de configuration introuvable: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(f)
            elif config_path.endswith('.json'):
                return json.load(f)
            else:
                # Essayer d'abord YAML, puis JSON
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError:
                    # Réinitialiser la position de lecture du fichier
                    f.seek(0)
                    return json.load(f)
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ConfigurationError(f"Erreur de parsing du fichier de configuration: {str(e)}")
    except IOError as e:
        raise ConfigurationError(f"Erreur de lecture du fichier de configuration: {str(e)}")


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Fusionne deux configurations, avec override_config ayant la priorité.
    
    Args:
        base_config: Configuration de base
        override_config: Configuration de remplacement (prioritaire)
        
    Returns:
        Configuration fusionnée
    """
    result = base_config.copy()
    
    for key, override_value in override_config.items():
        # Si les deux sont des dictionnaires, on les fusionne récursivement
        if key in result and isinstance(result[key], dict) and isinstance(override_value, dict):
            result[key] = merge_configs(result[key], override_value)
        else:
            # Sinon, on remplace simplement la valeur
            result[key] = override_value
    
    return result


class JsonEncoder(json.JSONEncoder):
    """Encodeur JSON personnalisé pour gérer les types de données spéciaux."""
    
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        return super().default(obj)


def to_camel_case(snake_str: str) -> str:
    """Convertit une chaîne snake_case en camelCase.
    
    Args:
        snake_str: Chaîne en snake_case
        
    Returns:
        Chaîne en camelCase
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """Convertit une chaîne camelCase en snake_case.
    
    Args:
        camel_str: Chaîne en camelCase
        
    Returns:
        Chaîne en snake_case
    """
    import re
    # Ajoute un underscore avant chaque lettre majuscule et convertit en minuscules
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def transform_keys(obj: Any, transform_func: callable) -> Any:
    """Transforme récursivement les clés d'un dictionnaire ou d'une liste de dictionnaires.
    
    Args:
        obj: Objet à transformer (dict, list, etc.)
        transform_func: Fonction de transformation des clés
        
    Returns:
        Objet avec les clés transformées
    """
    if isinstance(obj, dict):
        return {transform_func(k): transform_keys(v, transform_func) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [transform_keys(i, transform_func) for i in obj]
    else:
        return obj


def keys_to_camel_case(obj: Any) -> Any:
    """Convertit toutes les clés d'un objet de snake_case en camelCase.
    
    Args:
        obj: Objet à transformer
        
    Returns:
        Objet avec les clés en camelCase
    """
    return transform_keys(obj, to_camel_case)


def keys_to_snake_case(obj: Any) -> Any:
    """Convertit toutes les clés d'un objet de camelCase en snake_case.
    
    Args:
        obj: Objet à transformer
        
    Returns:
        Objet avec les clés en snake_case
    """
    return transform_keys(obj, to_snake_case)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse une chaîne de date dans différents formats courants.
    
    Args:
        date_str: Chaîne de date à parser, ou None
        
    Returns:
        Objet datetime ou None si la chaîne est None
        
    Raises:
        ValueError: Si le format de date n'est pas reconnu
    """
    if not date_str:
        return None
    
    # Formats à essayer, du plus spécifique au plus général
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 avec millisecondes et Z
        "%Y-%m-%dT%H:%M:%SZ",     # ISO 8601 avec Z
        "%Y-%m-%dT%H:%M:%S.%f",   # ISO 8601 avec millisecondes
        "%Y-%m-%dT%H:%M:%S",      # ISO 8601 sans timezone
        "%Y-%m-%d %H:%M:%S.%f",   # Format SQL avec millisecondes
        "%Y-%m-%d %H:%M:%S",      # Format SQL sans millisecondes
        "%Y-%m-%d",               # Date seule
        "%d/%m/%Y %H:%M:%S",      # Format français avec heure
        "%d/%m/%Y",               # Format français sans heure
        "%m/%d/%Y %H:%M:%S",      # Format américain avec heure
        "%m/%d/%Y",               # Format américain sans heure
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Format de date non reconnu: {date_str}")


def set_nested_dict_value(d: Dict, key_path: str, value: Any) -> None:
    """Définit une valeur dans un dictionnaire imbriqué en utilisant un chemin de clés.
    
    Args:
        d: Dictionnaire à modifier
        key_path: Chemin de clés séparées par des points (ex: "config.api.timeout")
        value: Valeur à définir
    """
    keys = key_path.split('.')
    current = d
    
    # Parcourir toutes les clés sauf la dernière
    for key in keys[:-1]:
        # Si la clé n'existe pas ou n'est pas un dictionnaire, créer un nouveau dictionnaire
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    # Définir la valeur à la dernière clé
    current[keys[-1]] = value


def get_nested_dict_value(d: Dict, key_path: str, default: Any = None) -> Any:
    """Récupère une valeur dans un dictionnaire imbriqué en utilisant un chemin de clés.
    
    Args:
        d: Dictionnaire à parcourir
        key_path: Chemin de clés séparées par des points (ex: "config.api.timeout")
        default: Valeur par défaut si le chemin n'existe pas
        
    Returns:
        Valeur trouvée ou valeur par défaut
    """
    keys = key_path.split('.')
    current = d
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default
