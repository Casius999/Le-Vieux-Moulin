"""
Module d'utilitaires communs

Ce module fournit des fonctions utilitaires utilisées
par les différents composants du module de communication.
"""

import time
import json
import logging
import functools
import datetime
from typing import Any, Dict, Callable, Optional, TypeVar, Union


# Type variable pour le décorateur retry_with_backoff
T = TypeVar('T')


def format_date(date_obj: Optional[Union[str, datetime.datetime]] = None, 
               format_str: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    """
    Formate une date en chaîne ISO 8601.
    
    Args:
        date_obj: Objet datetime ou chaîne à formater (utilise la date actuelle si None)
        format_str: Format de date à utiliser
        
    Returns:
        Chaîne de date formatée
    """
    if date_obj is None:
        date_obj = datetime.datetime.now(datetime.timezone.utc)
    elif isinstance(date_obj, str):
        try:
            # Tenter de parser la chaîne de date
            date_obj = datetime.datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except ValueError:
            # Si le format n'est pas reconnu, retourner la chaîne telle quelle
            return date_obj
    
    # Convertir en UTC si ce n'est pas déjà le cas
    if date_obj.tzinfo is None:
        date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)
    
    return date_obj.strftime(format_str)


def safe_json(obj: Any) -> str:
    """
    Convertit un objet en JSON en gérant les types non sérialisables.
    
    Args:
        obj: Objet à convertir en JSON
        
    Returns:
        Chaîne JSON
    """
    def json_serializer(o):
        """Gestionnaire pour les types non sérialisables en JSON."""
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        raise TypeError(f"Type non sérialisable: {type(o)}")
    
    return json.dumps(obj, default=json_serializer, ensure_ascii=False)


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0, 
                     exception_types: tuple = (Exception,)) -> Callable:
    """
    Décorateur pour réessayer une fonction avec un backoff exponentiel.
    
    Args:
        max_retries: Nombre maximal de tentatives
        backoff_factor: Facteur pour calculer le délai entre les tentatives
        exception_types: Types d'exceptions qui déclenchent une nouvelle tentative
        
    Returns:
        Fonction décorée
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    if attempt == max_retries:
                        logger.error(f"Échec après {max_retries} tentatives: {e}")
                        raise
                    
                    # Calculer le délai avec backoff exponentiel
                    delay = backoff_factor ** (attempt - 1)
                    logger.warning(f"Tentative {attempt} échouée: {e}. Nouvelle tentative dans {delay:.2f}s")
                    time.sleep(delay)
            
            # Cette ligne ne devrait jamais être atteinte
            return func(*args, **kwargs)
            
        return wrapper
    return decorator


def validate_phone_number(phone: str) -> bool:
    """
    Valide un numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone à valider
        
    Returns:
        True si le numéro est valide, False sinon
    """
    # Supprimer tous les caractères non numériques sauf le + au début
    clean_phone = phone.strip()
    if clean_phone.startswith('+'):
        clean_phone = '+' + ''.join(c for c in clean_phone[1:] if c.isdigit())
    else:
        clean_phone = ''.join(c for c in clean_phone if c.isdigit())
    
    # Vérifier la longueur (indicatif international + numéro)
    if len(clean_phone) < 8 or len(clean_phone) > 15:
        return False
    
    # Vérifier le format international
    if clean_phone.startswith('+'):
        return len(clean_phone) >= 9
    
    # Format national
    return len(clean_phone) >= 8


def validate_email(email: str) -> bool:
    """
    Valide une adresse email.
    
    Args:
        email: Adresse email à valider
        
    Returns:
        True si l'email est valide, False sinon
    """
    import re
    
    # Expression régulière basique pour la validation d'email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email))


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale en ajoutant un suffixe.
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale (incluant le suffixe)
        suffix: Suffixe à ajouter en cas de troncature
        
    Returns:
        Texte tronqué
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne deux dictionnaires récursivement.
    
    Args:
        dict1: Premier dictionnaire
        dict2: Second dictionnaire (ses valeurs ont priorité en cas de conflit)
        
    Returns:
        Nouveau dictionnaire fusionné
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def generate_unique_id(prefix: str = "") -> str:
    """
    Génère un identifiant unique avec un préfixe optionnel.
    
    Args:
        prefix: Préfixe à ajouter à l'identifiant
        
    Returns:
        Identifiant unique
    """
    import uuid
    
    unique_id = str(uuid.uuid4())
    
    if prefix:
        return f"{prefix}_{unique_id}"
    
    return unique_id


def sanitize_html(html: str) -> str:
    """
    Nettoie le HTML pour éviter les injections.
    
    Args:
        html: Chaîne HTML à nettoyer
        
    Returns:
        HTML nettoyé
    """
    import re
    
    # Suppression des scripts
    html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
    
    # Suppression des balises style
    html = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html, flags=re.IGNORECASE)
    
    # Suppression des attributs javascript:
    html = re.sub(r'on\w+="[^"]*"', '', html, flags=re.IGNORECASE)
    html = re.sub(r'on\w+=\'[^\']*\'', '', html, flags=re.IGNORECASE)
    
    # Suppression des liens javascript:
    html = re.sub(r'href="javascript:[^"]*"', 'href="#"', html, flags=re.IGNORECASE)
    html = re.sub(r'href=\'javascript:[^\']*\'', 'href="#"', html, flags=re.IGNORECASE)
    
    return html


def get_file_size(file_path: str) -> int:
    """
    Obtient la taille d'un fichier en octets.
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        Taille du fichier en octets
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    import os
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
    
    return os.path.getsize(file_path)


def get_mime_type(file_path: str) -> str:
    """
    Détermine le type MIME d'un fichier.
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        Type MIME du fichier
    """
    import mimetypes
    
    # Initialiser les types MIME
    mimetypes.init()
    
    # Obtenir le type MIME
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # Retourner le type MIME ou une valeur par défaut
    return mime_type or 'application/octet-stream'
