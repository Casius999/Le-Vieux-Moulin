"""Module contenant la classe de base abstraite pour tous les connecteurs API.

Ce module définit BaseConnector, la classe parente de tous les connecteurs API
spécifiques (POS, fournisseurs, réservation, CRM).
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union

from .common.http_client import RobustHTTPClient
from .common.auth import BaseAuthenticator, create_authenticator
from .common.exceptions import ConfigurationError, AuthenticationError
from .common.utils import load_config
from .common.rate_limiter import RateLimiter, AdaptiveRateLimiter

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Classe de base abstraite pour tous les connecteurs API.
    
    Cette classe fournit les fonctionnalités communes à tous les connecteurs API,
    telles que la gestion de la configuration, l'authentification, et les requêtes HTTP.
    """
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict] = None):
        """Initialise le connecteur avec une configuration.
        
        Args:
            config_path: Chemin vers le fichier de configuration (YAML ou JSON)
            config_dict: Dictionnaire de configuration (prioritaire sur config_path)
            
        Raises:
            ConfigurationError: Si le chargement de la configuration échoue
        """
        self.config = load_config(config_path, config_dict)
        self.http_client = None
        self.authenticator = None
        self.rate_limiter = None
        self._connected = False
    
    def _validate_config(self) -> None:
        """Valide la configuration pour s'assurer que tous les champs requis sont présents.
        
        Raises:
            ConfigurationError: Si la configuration est invalide
        """
        required_sections = ['api', 'auth']
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Section '{section}' manquante dans la configuration")
        
        # Valider la section API
        api_config = self.config['api']
        if 'base_url' not in api_config:
            raise ConfigurationError("URL de base de l'API manquante dans la configuration", "api.base_url")
        
        # Valider la section Auth
        auth_config = self.config['auth']
        if 'method' not in auth_config:
            raise ConfigurationError("Méthode d'authentification manquante dans la configuration", "auth.method")
    
    def _init_http_client(self) -> None:
        """Initialise le client HTTP avec les paramètres de configuration."""
        api_config = self.config['api']
        connection_config = self.config.get('connection', {})
        
        self.http_client = RobustHTTPClient(
            base_url=api_config['base_url'],
            default_headers=api_config.get('default_headers', {}),
            timeout=connection_config.get('timeout', 30),
            max_retries=connection_config.get('max_retries', 3),
            retry_delay=connection_config.get('retry_delay', 2),
            pool_connections=connection_config.get('pool_connections', 10),
            pool_maxsize=connection_config.get('pool_maxsize', 10)
        )
    
    def _init_authenticator(self) -> None:
        """Initialise l'authenticateur avec les paramètres de configuration."""
        auth_config = self.config['auth']
        self.authenticator = create_authenticator(auth_config)
    
    def _init_rate_limiter(self) -> None:
        """Initialise le limiteur de débit avec les paramètres de configuration."""
        rate_limit_config = self.config.get('rate_limit', {})
        
        if rate_limit_config.get('adaptive', False):
            self.rate_limiter = AdaptiveRateLimiter(
                initial_rate=rate_limit_config.get('max_requests_per_minute', 60) / 60,
                period=1.0,  # 1 seconde
                burst=rate_limit_config.get('max_burst', None),
                max_delay=rate_limit_config.get('max_delay', None),
                safety_factor=rate_limit_config.get('safety_factor', 0.9)
            )
        else:
            self.rate_limiter = RateLimiter(
                rate=rate_limit_config.get('max_requests_per_minute', 60) / 60,
                period=1.0,  # 1 seconde
                burst=rate_limit_config.get('max_burst', None),
                max_delay=rate_limit_config.get('max_delay', None)
            )
    
    async def connect(self) -> None:
        """Initialise le connecteur et établit la connexion avec l'API.
        
        Cette méthode doit être appelée avant toute opération avec l'API.
        
        Raises:
            ConfigurationError: Si la configuration est invalide
            AuthenticationError: Si l'authentification échoue
        """
        # Valider la configuration
        self._validate_config()
        
        # Initialiser les composants
        self._init_http_client()
        self._init_authenticator()
        self._init_rate_limiter()
        
        # Authentifier
        try:
            await self.authenticator.authenticate()
            self._connected = True
            logger.info(f"Connecté à l'API {self.config['api'].get('name', self.__class__.__name__)}")
        except AuthenticationError as e:
            self._connected = False
            logger.error(f"Erreur d'authentification: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Ferme la connexion avec l'API."""
        if self.http_client:
            await self.http_client.close()
            self._connected = False
            logger.info(f"Déconnecté de l'API {self.config['api'].get('name', self.__class__.__name__)}")
    
    async def is_connected(self) -> bool:
        """Vérifie si le connecteur est connecté et authentifié.
        
        Returns:
            True si le connecteur est connecté et authentifié, False sinon
        """
        if not self._connected or not self.authenticator:
            return False
        
        return await self.authenticator.is_authenticated()
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          **kwargs) -> Any:
        """Effectue une requête HTTP authentifiée avec gestion du rate limiting.
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE, etc.)
            endpoint: Endpoint API (relatif ou absolu)
            **kwargs: Arguments additionnels pour la requête HTTP
            
        Returns:
            Réponse de l'API (généralement un dict ou une liste)
            
        Raises:
            AuthenticationError: Si l'authentification échoue
            ConnectionError: En cas de problème de connexion
            APIError: Pour les autres erreurs API
        """
        # Vérifier la connexion
        if not self._connected:
            await self.connect()
        
        # Rafraîchir l'authentification si nécessaire
        await self.authenticator.refresh_if_needed()
        
        # Ajouter les en-têtes d'authentification
        headers = kwargs.get('headers', {})
        auth_headers = self.authenticator.get_auth_headers()
        headers.update(auth_headers)
        kwargs['headers'] = headers
        
        # Appliquer le rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # Effectuer la requête
        response = await getattr(self.http_client, method.lower())(endpoint, **kwargs)
        
        # Mettre à jour le rate limiter si nécessaire
        if isinstance(self.rate_limiter, AdaptiveRateLimiter) and 'headers' in response:
            self.rate_limiter.update_from_headers(response['headers'])
        
        return response
    
    # Méthodes pratiques pour les différents types de requêtes
    
    async def get(self, endpoint: str, **kwargs) -> Any:
        """Effectue une requête GET authentifiée."""
        return await self._make_request('GET', endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Any:
        """Effectue une requête POST authentifiée."""
        return await self._make_request('POST', endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Any:
        """Effectue une requête PUT authentifiée."""
        return await self._make_request('PUT', endpoint, **kwargs)
    
    async def patch(self, endpoint: str, **kwargs) -> Any:
        """Effectue une requête PATCH authentifiée."""
        return await self._make_request('PATCH', endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Any:
        """Effectue une requête DELETE authentifiée."""
        return await self._make_request('DELETE', endpoint, **kwargs)
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Vérifie l'état de santé de l'API.
        
        Returns:
            True si l'API est fonctionnelle, False sinon
        """
        pass
    
    # Méthodes spéciales pour la gestion des contextes async
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
