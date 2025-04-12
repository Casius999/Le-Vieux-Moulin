"""Exceptions personnalisées pour les connecteurs API.

Ce module définit une hiérarchie d'exceptions pour catégoriser les différents
types d'erreurs qui peuvent survenir lors de l'utilisation des connecteurs API.
"""

class APIConnectorError(Exception):
    """Classe de base pour toutes les exceptions liées aux connecteurs API."""
    pass


class AuthenticationError(APIConnectorError):
    """Exception levée pour les problèmes d'authentification.
    
    Exemples:
    - Token expiré
    - Identifiants invalides
    - Autorisations insuffisantes
    """
    def __init__(self, message, service=None):
        self.service = service
        super().__init__(f"Erreur d'authentification{' pour ' + service if service else ''}: {message}")


class ConnectionError(APIConnectorError):
    """Exception levée pour les problèmes de connexion réseau.
    
    Exemples:
    - Timeout
    - Serveur inaccessible
    - Erreur DNS
    """
    def __init__(self, message, service=None, retryable=True):
        self.service = service
        self.retryable = retryable
        super().__init__(f"Erreur de connexion{' pour ' + service if service else ''}: {message}")


class RateLimitError(APIConnectorError):
    """Exception levée quand la limite de requêtes API est atteinte."""
    def __init__(self, message, service=None, retry_after=None):
        self.service = service
        self.retry_after = retry_after
        super().__init__(f"Limite de requêtes atteinte{' pour ' + service if service else ''}: {message}" + 
                         (f" (réessayer après {retry_after} secondes)" if retry_after else ""))


class ResourceNotFoundError(APIConnectorError):
    """Exception levée quand une ressource demandée n'existe pas (HTTP 404)."""
    def __init__(self, message, resource_type=None, resource_id=None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        details = ""
        if resource_type:
            details += f" {resource_type}"
        if resource_id:
            details += f" (ID: {resource_id})"
        super().__init__(f"Ressource non trouvée{details}: {message}")


class ValidationError(APIConnectorError):
    """Exception levée quand des données invalides sont envoyées à l'API."""
    def __init__(self, message, errors=None):
        self.errors = errors or {}
        error_details = ""
        if errors:
            error_details = " - " + ", ".join(f"{k}: {v}" for k, v in errors.items())
        super().__init__(f"Erreur de validation: {message}{error_details}")


class APIError(APIConnectorError):
    """Exception levée pour les autres erreurs API.
    
    Cette classe est utilisée pour les erreurs qui ne correspondent pas 
    aux catégories plus spécifiques ci-dessus.
    """
    def __init__(self, message, status_code=None, service=None, is_retriable=False):
        self.status_code = status_code
        self.service = service
        self.is_retriable = is_retriable
        
        status_info = f" (HTTP {status_code})" if status_code else ""
        service_info = f" pour {service}" if service else ""
        
        super().__init__(f"Erreur API{status_info}{service_info}: {message}")


class ConfigurationError(APIConnectorError):
    """Exception levée pour les problèmes de configuration."""
    def __init__(self, message, config_key=None):
        self.config_key = config_key
        key_info = f" (clé: {config_key})" if config_key else ""
        super().__init__(f"Erreur de configuration{key_info}: {message}")
