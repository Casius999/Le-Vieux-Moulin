"""Gestion de l'authentification pour les connecteurs API.

Ce module fournit des classes et fonctions pour gérer l'authentification
avec différents services via différentes méthodes (OAuth2, API Keys, etc.).
"""

import json
import os
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import aiohttp
from authlib.integrations.httpx_client import AsyncOAuth2Client

from .exceptions import AuthenticationError, ConfigurationError
from .http_client import RobustHTTPClient

logger = logging.getLogger(__name__)

class BaseAuthenticator(ABC):
    """Classe de base abstraite pour tous les authenticateurs API."""
    
    @abstractmethod
    async def authenticate(self) -> Dict[str, Any]:
        """Effectue l'authentification et retourne les informations d'accès.
        
        Returns:
            Dict avec les informations d'authentification (token, etc.)
            
        Raises:
            AuthenticationError: En cas d'échec d'authentification
        """
        pass
    
    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Vérifie si l'authenticateur a des credentials valides.
        
        Returns:
            True si authentifié et valide, False sinon
        """
        pass
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Retourne les en-têtes HTTP nécessaires pour l'authentification.
        
        Returns:
            Dict avec les en-têtes d'authentification à inclure dans les requêtes
        """
        pass
    
    @abstractmethod
    async def refresh_if_needed(self) -> bool:
        """Rafraîchit l'authentification si nécessaire.
        
        Returns:
            True si l'authentification a été rafraîchie, False sinon
        """
        pass


class ApiKeyAuthenticator(BaseAuthenticator):
    """Authenticateur utilisant une clé API."""
    
    def __init__(self, api_key: str, header_name: str = 'X-API-KEY'):
        """Initialise l'authenticateur par clé API.
        
        Args:
            api_key: La clé API à utiliser
            header_name: Le nom de l'en-tête HTTP pour la clé API
        """
        self.api_key = api_key
        self.header_name = header_name
    
    async def authenticate(self) -> Dict[str, Any]:
        """Pour l'authenticateur par clé API, pas besoin d'authentification active."""
        if not self.api_key:
            raise AuthenticationError("Clé API manquante")
        return {"api_key": self.api_key}
    
    async def is_authenticated(self) -> bool:
        """Vérifie si la clé API est définie."""
        return bool(self.api_key)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Retourne l'en-tête avec la clé API."""
        return {self.header_name: self.api_key}
    
    async def refresh_if_needed(self) -> bool:
        """Pas besoin de rafraîchissement pour les clés API."""
        return False


class BasicAuthAuthenticator(BaseAuthenticator):
    """Authenticateur utilisant l'authentification HTTP Basic Auth."""
    
    def __init__(self, username: str, password: str):
        """Initialise l'authenticateur Basic Auth.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
        """
        import base64
        self.username = username
        self.password = password
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded}"
    
    async def authenticate(self) -> Dict[str, Any]:
        """Pour Basic Auth, pas besoin d'authentification active."""
        if not self.username or not self.password:
            raise AuthenticationError("Identifiants incomplets pour Basic Auth")
        return {"type": "basic_auth", "username": self.username}
    
    async def is_authenticated(self) -> bool:
        """Vérifie si les identifiants sont définis."""
        return bool(self.username and self.password)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Retourne l'en-tête d'authentification Basic."""
        return {"Authorization": self.auth_header}
    
    async def refresh_if_needed(self) -> bool:
        """Pas besoin de rafraîchissement pour Basic Auth."""
        return False


class OAuth2ClientCredentialsAuthenticator(BaseAuthenticator):
    """Authenticateur OAuth2 utilisant le flow Client Credentials."""
    
    def __init__(self, 
                 token_url: str,
                 client_id: str,
                 client_secret: str,
                 scope: Optional[str] = None,
                 token_storage_path: Optional[str] = None):
        """Initialise l'authenticateur OAuth2 Client Credentials.
        
        Args:
            token_url: URL pour obtenir un token
            client_id: ID client OAuth2
            client_secret: Secret client OAuth2
            scope: Portée d'accès (optionnel)
            token_storage_path: Chemin pour stocker le token (optionnel)
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token_storage_path = token_storage_path
        self.token_data = None
        self.token_expires_at = 0
    
    async def _load_token_from_storage(self) -> bool:
        """Charge le token depuis le stockage persistant.
        
        Returns:
            True si un token valide a été chargé, False sinon
        """
        if not self.token_storage_path or not os.path.exists(self.token_storage_path):
            return False
        
        try:
            with open(self.token_storage_path, 'r') as f:
                self.token_data = json.load(f)
            
            # Vérifier si le token contient une date d'expiration
            if 'expires_at' in self.token_data:
                self.token_expires_at = self.token_data['expires_at']
                # Si le token est expiré, on ne le considère pas comme valide
                if self.token_expires_at <= time.time():
                    return False
            elif 'expires_in' in self.token_data:
                # Si on a seulement expires_in, on ne peut pas savoir quand le token a été créé
                # donc on ne peut pas déterminer s'il est valide
                return False
            
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erreur lors du chargement du token: {str(e)}")
            return False
    
    async def _save_token_to_storage(self):
        """Sauvegarde le token dans le stockage persistant."""
        if not self.token_storage_path or not self.token_data:
            return
        
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.token_storage_path)), exist_ok=True)
            with open(self.token_storage_path, 'w') as f:
                json.dump(self.token_data, f)
            os.chmod(self.token_storage_path, 0o600)  # Permissions restrictives
        except IOError as e:
            logger.warning(f"Erreur lors de la sauvegarde du token: {str(e)}")
    
    async def authenticate(self) -> Dict[str, Any]:
        """Obtient un token OAuth2 avec le flow Client Credentials.
        
        Returns:
            Dict avec les informations du token (access_token, etc.)
            
        Raises:
            AuthenticationError: En cas d'échec d'authentification
        """
        # Essayer de charger un token existant
        if await self._load_token_from_storage() and self.is_token_valid():
            return self.token_data
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
                
                if self.scope:
                    payload["scope"] = self.scope
                
                async with session.post(self.token_url, data=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationError(
                            f"Échec d'authentification OAuth2 (HTTP {response.status}): {error_text}"
                        )
                    
                    self.token_data = await response.json()
                    
                    # Calculer la date d'expiration absolue
                    if 'expires_in' in self.token_data:
                        self.token_expires_at = time.time() + int(self.token_data['expires_in'])
                        self.token_data['expires_at'] = self.token_expires_at
                    
                    # Sauvegarder le token
                    await self._save_token_to_storage()
                    
                    return self.token_data
                    
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Erreur de connexion lors de l'authentification OAuth2: {str(e)}")
    
    def is_token_valid(self) -> bool:
        """Vérifie si le token actuel est valide et non expiré."""
        if not self.token_data or not self.token_data.get('access_token'):
            return False
        
        # Ajout d'une marge de sécurité (30 secondes)
        return self.token_expires_at > time.time() + 30
    
    async def is_authenticated(self) -> bool:
        """Vérifie si l'authentification est valide."""
        return self.is_token_valid()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Retourne l'en-tête d'authentification avec le Bearer token."""
        if not self.token_data or not self.token_data.get('access_token'):
            return {}
        
        return {"Authorization": f"Bearer {self.token_data['access_token']}"}
    
    async def refresh_if_needed(self) -> bool:
        """Rafraîchit le token s'il est expiré ou va bientôt expirer.
        
        Returns:
            True si le token a été rafraîchi, False sinon
        """
        if not self.is_token_valid():
            await self.authenticate()
            return True
        return False


class OAuth2AuthorizationCodeAuthenticator(BaseAuthenticator):
    """Authenticateur OAuth2 utilisant le flow Authorization Code."""
    
    def __init__(self, 
                 authorization_url: str,
                 token_url: str,
                 client_id: str,
                 client_secret: str,
                 redirect_uri: str,
                 scope: Optional[str] = None,
                 token_storage_path: Optional[str] = None,
                 use_pkce: bool = True):
        """Initialise l'authenticateur OAuth2 Authorization Code.
        
        Args:
            authorization_url: URL pour l'autorisation utilisateur
            token_url: URL pour obtenir/rafraîchir un token
            client_id: ID client OAuth2
            client_secret: Secret client OAuth2
            redirect_uri: URI de redirection après autorisation
            scope: Portée d'accès (optionnel)
            token_storage_path: Chemin pour stocker le token (optionnel)
            use_pkce: Utiliser l'extension PKCE pour plus de sécurité
        """
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.token_storage_path = token_storage_path
        self.use_pkce = use_pkce
        self.token_data = None
        self.token_expires_at = 0
    
    async def _load_token_from_storage(self) -> bool:
        """Charge le token depuis le stockage persistant.
        
        Returns:
            True si un token valide a été chargé, False sinon
        """
        if not self.token_storage_path or not os.path.exists(self.token_storage_path):
            return False
        
        try:
            with open(self.token_storage_path, 'r') as f:
                self.token_data = json.load(f)
            
            # Vérifier si le token contient une date d'expiration
            if 'expires_at' in self.token_data:
                self.token_expires_at = self.token_data['expires_at']
                # Si le token est expiré, on ne le considère pas comme valide
                if self.token_expires_at <= time.time():
                    # Mais s'il y a un refresh_token, on peut quand même l'utiliser
                    return 'refresh_token' in self.token_data
            elif 'expires_in' in self.token_data:
                # Si on a seulement expires_in, on ne peut pas savoir quand le token a été créé
                # donc on ne peut pas déterminer s'il est valide
                return 'refresh_token' in self.token_data
            
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erreur lors du chargement du token: {str(e)}")
            return False
    
    async def _save_token_to_storage(self):
        """Sauvegarde le token dans le stockage persistant."""
        if not self.token_storage_path or not self.token_data:
            return
        
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.token_storage_path)), exist_ok=True)
            with open(self.token_storage_path, 'w') as f:
                json.dump(self.token_data, f)
            os.chmod(self.token_storage_path, 0o600)  # Permissions restrictives
        except IOError as e:
            logger.warning(f"Erreur lors de la sauvegarde du token: {str(e)}")
    
    def create_authorization_url(self) -> Tuple[str, str]:
        """Génère l'URL d'autorisation pour redirection utilisateur.
        
        Returns:
            Tuple (url, state) où url est l'URL d'autorisation et state est un état à conserver
        """
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
        kwargs = {}
        if self.use_pkce:
            kwargs['code_challenge_method'] = 'S256'
        
        uri, state = client.create_authorization_url(
            self.authorization_url,
            **kwargs
        )
        
        return uri, state
    
    async def fetch_token(self, code: str) -> Dict[str, Any]:
        """Échange le code d'autorisation contre un token.
        
        Args:
            code: Code d'autorisation reçu après redirection
            
        Returns:
            Dict avec les informations du token
            
        Raises:
            AuthenticationError: En cas d'échec d'échange de code
        """
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri
        )
        
        try:
            self.token_data = await client.fetch_token(
                self.token_url,
                code=code
            )
            
            # Calculer la date d'expiration absolue
            if 'expires_in' in self.token_data:
                self.token_expires_at = time.time() + int(self.token_data['expires_in'])
                self.token_data['expires_at'] = self.token_expires_at
            
            # Sauvegarder le token
            await self._save_token_to_storage()
            
            return self.token_data
            
        except Exception as e:
            raise AuthenticationError(f"Échec d'échange du code d'autorisation: {str(e)}")
    
    async def refresh_token(self) -> Dict[str, Any]:
        """Rafraîchit le token d'accès en utilisant le refresh token.
        
        Returns:
            Dict avec les informations du nouveau token
            
        Raises:
            AuthenticationError: En cas d'échec de rafraîchissement
        """
        if not self.token_data or 'refresh_token' not in self.token_data:
            raise AuthenticationError("Pas de refresh token disponible")
        
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token=self.token_data
        )
        
        try:
            self.token_data = await client.refresh_token(
                self.token_url,
                refresh_token=self.token_data['refresh_token']
            )
            
            # Calculer la date d'expiration absolue
            if 'expires_in' in self.token_data:
                self.token_expires_at = time.time() + int(self.token_data['expires_in'])
                self.token_data['expires_at'] = self.token_expires_at
            
            # Sauvegarder le token
            await self._save_token_to_storage()
            
            return self.token_data
            
        except Exception as e:
            raise AuthenticationError(f"Échec de rafraîchissement du token: {str(e)}")
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authentifie en utilisant un token existant ou en rafraîchissant.
        
        Note: Cette méthode ne peut pas effectuer le flow complet d'autorisation
        car il nécessite une interaction utilisateur. Utilisez create_authorization_url
        et fetch_token pour l'autorisation initiale.
        
        Returns:
            Dict avec les informations du token
            
        Raises:
            AuthenticationError: Si aucun token n'est disponible ou si le rafraîchissement échoue
        """
        # Essayer de charger un token existant
        has_token = await self._load_token_from_storage()
        
        if has_token:
            # Si le token est expiré mais qu'un refresh token est disponible, on rafraîchit
            if self.token_expires_at <= time.time() + 30 and 'refresh_token' in self.token_data:
                return await self.refresh_token()
            # Sinon, si le token est valide, on le renvoie
            elif self.token_expires_at > time.time() + 30:
                return self.token_data
        
        # Si on arrive ici, c'est qu'on n'a pas de token valide et qu'on ne peut pas en obtenir un
        # automatiquement (il faudrait une interaction utilisateur)
        raise AuthenticationError(
            "Authentification impossible sans interaction utilisateur. "
            "Utilisez create_authorization_url et fetch_token pour l'autorisation initiale."
        )
    
    def is_token_valid(self) -> bool:
        """Vérifie si le token actuel est valide et non expiré."""
        if not self.token_data or not self.token_data.get('access_token'):
            return False
        
        # Ajout d'une marge de sécurité (30 secondes)
        return self.token_expires_at > time.time() + 30
    
    async def is_authenticated(self) -> bool:
        """Vérifie si l'authentification est valide."""
        return self.is_token_valid() or ('refresh_token' in (self.token_data or {}))
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Retourne l'en-tête d'authentification avec le Bearer token."""
        if not self.token_data or not self.token_data.get('access_token'):
            return {}
        
        return {"Authorization": f"Bearer {self.token_data['access_token']}"}
    
    async def refresh_if_needed(self) -> bool:
        """Rafraîchit le token s'il est expiré ou va bientôt expirer.
        
        Returns:
            True si le token a été rafraîchi, False sinon
            
        Raises:
            AuthenticationError: Si le rafraîchissement échoue
        """
        if not self.is_token_valid() and self.token_data and 'refresh_token' in self.token_data:
            await self.refresh_token()
            return True
        return False


def create_authenticator(auth_config: Dict[str, Any]) -> BaseAuthenticator:
    """Crée un authenticateur en fonction de la configuration.
    
    Args:
        auth_config: Configuration d'authentification
        
    Returns:
        Un authenticateur correspondant à la méthode spécifiée
        
    Raises:
        ConfigurationError: Si la configuration est invalide ou la méthode non supportée
    """
    auth_method = auth_config.get("method")
    
    if not auth_method:
        raise ConfigurationError("Méthode d'authentification non spécifiée", "method")
    
    if auth_method == "api_key":
        if "api_key" not in auth_config:
            raise ConfigurationError("Clé API manquante dans la configuration", "api_key")
        
        return ApiKeyAuthenticator(
            api_key=auth_config["api_key"],
            header_name=auth_config.get("header_name", "X-API-KEY")
        )
    
    elif auth_method == "basic_auth":
        if "username" not in auth_config or "password" not in auth_config:
            raise ConfigurationError("Identifiants incomplets pour Basic Auth", "username/password")
        
        return BasicAuthAuthenticator(
            username=auth_config["username"],
            password=auth_config["password"]
        )
    
    elif auth_method == "oauth2_client_credentials":
        required_fields = ["token_url", "client_id", "client_secret"]
        for field in required_fields:
            if field not in auth_config:
                raise ConfigurationError(f"Champ requis manquant pour OAuth2 Client Credentials: {field}", field)
        
        return OAuth2ClientCredentialsAuthenticator(
            token_url=auth_config["token_url"],
            client_id=auth_config["client_id"],
            client_secret=auth_config["client_secret"],
            scope=auth_config.get("scope"),
            token_storage_path=auth_config.get("token_path")
        )
    
    elif auth_method == "oauth2_authorization_code":
        required_fields = ["authorization_url", "token_url", "client_id", "client_secret", "redirect_uri"]
        for field in required_fields:
            if field not in auth_config:
                raise ConfigurationError(f"Champ requis manquant pour OAuth2 Authorization Code: {field}", field)
        
        return OAuth2AuthorizationCodeAuthenticator(
            authorization_url=auth_config["authorization_url"],
            token_url=auth_config["token_url"],
            client_id=auth_config["client_id"],
            client_secret=auth_config["client_secret"],
            redirect_uri=auth_config["redirect_uri"],
            scope=auth_config.get("scope"),
            token_storage_path=auth_config.get("token_path"),
            use_pkce=auth_config.get("use_pkce", True)
        )
    
    else:
        raise ConfigurationError(f"Méthode d'authentification non supportée: {auth_method}", "method")
