"""Client HTTP robuste pour les connexions API.

Ce module fournit un client HTTP asynchrone avec gestion des erreurs,
reconnexions automatiques et autres fonctionnalités avancées.
"""

import aiohttp
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple

from .exceptions import (
    ConnectionError, 
    RateLimitError, 
    ResourceNotFoundError,
    ValidationError,
    APIError
)

logger = logging.getLogger(__name__)

class RobustHTTPClient:
    """Client HTTP asynchrone avec gestion avancée des erreurs et reconnexions."""
    
    def __init__(self, 
                 base_url: str = None,
                 default_headers: Dict[str, str] = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: int = 2,
                 retry_codes: List[int] = None,
                 pool_connections: int = 10,
                 pool_maxsize: int = 10):
        """Initialise le client HTTP robuste.
        
        Args:
            base_url: URL de base pour toutes les requêtes (optionnel)
            default_headers: En-têtes par défaut à inclure dans toutes les requêtes
            timeout: Timeout des requêtes en secondes
            max_retries: Nombre maximum de tentatives en cas d'erreur temporaire
            retry_delay: Délai initial entre les tentatives (en secondes)
            retry_codes: Liste des codes HTTP qui déclenchent une nouvelle tentative
            pool_connections: Nombre de connexions à maintenir dans le pool
            pool_maxsize: Nombre maximum de connexions dans le pool
        """
        self.base_url = base_url.rstrip('/') if base_url else ''
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_codes = retry_codes or [408, 429, 500, 502, 503, 504]
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        self._session = None
    
    async def _ensure_session(self):
        """Assure qu'une session HTTP active existe."""
        if self._session is None or self._session.closed:
            conn = aiohttp.TCPConnector(
                limit=self.pool_connections,
                limit_per_host=self.pool_maxsize
            )
            self._session = aiohttp.ClientSession(connector=conn)
        return self._session
    
    async def close(self):
        """Ferme la session HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _build_url(self, endpoint: str) -> str:
        """Construit l'URL complète à partir de l'endpoint."""
        if not endpoint.startswith(('http://', 'https://')):
            # Si l'endpoint ne commence pas par http:// ou https://,
            # on le considère comme relatif à base_url
            if endpoint.startswith('/'):
                url = f"{self.base_url}{endpoint}"
            else:
                url = f"{self.base_url}/{endpoint}"
        else:
            # Sinon, on utilise l'URL complète fournie
            url = endpoint
        return url
    
    def _prepare_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Prépare les en-têtes pour la requête en combinant les en-têtes par défaut et spécifiques."""
        result = self.default_headers.copy()
        if headers:
            result.update(headers)
        return result
    
    def _handle_response_error(self, response: aiohttp.ClientResponse, content: str = None):
        """Traite les réponses d'erreur HTTP et lève les exceptions appropriées."""
        status = response.status
        service = response.url.host
        
        # Tentative de parsage du contenu JSON pour plus de détails
        error_detail = content or "Pas de détails disponibles"
        
        if status == 401 or status == 403:
            raise AuthenticationError(f"Non autorisé (HTTP {status}): {error_detail}", service=service)
        
        elif status == 404:
            raise ResourceNotFoundError(f"Ressource non trouvée: {error_detail}")
        
        elif status == 422:
            # Erreur de validation, souvent avec des détails dans le corps
            raise ValidationError(f"Données invalides: {error_detail}")
        
        elif status == 429:
            # Rate limiting
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                try:
                    retry_after = int(retry_after)
                except ValueError:
                    # Parfois Retry-After est une date, pas un nombre de secondes
                    retry_after = None
            
            raise RateLimitError(
                f"Trop de requêtes: {error_detail}", 
                service=service,
                retry_after=retry_after
            )
        
        else:
            # Autres erreurs API
            is_retriable = status in self.retry_codes
            raise APIError(
                f"Erreur inattendue: {error_detail}", 
                status_code=status,
                service=service,
                is_retriable=is_retriable
            )
    
    async def request(self, 
                      method: str, 
                      endpoint: str, 
                      params: Dict[str, Any] = None, 
                      data: Any = None,
                      json: Any = None,
                      headers: Dict[str, str] = None,
                      timeout: int = None,
                      max_retries: int = None) -> Any:
        """Effectue une requête HTTP avec gestion des erreurs et reconnexion automatique.
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE, etc.)
            endpoint: Endpoint API (relatif ou absolu)
            params: Paramètres de requête
            data: Données de formulaire à envoyer
            json: Données JSON à envoyer
            headers: En-têtes HTTP spécifiques à cette requête
            timeout: Timeout spécifique pour cette requête (ou None pour la valeur par défaut)
            max_retries: Nombre maximum de tentatives pour cette requête (ou None pour la valeur par défaut)
            
        Returns:
            Les données de réponse (généralement JSON)
            
        Raises:
            ConnectionError: En cas de problème de connexion
            AuthenticationError: En cas de problème d'authentification
            RateLimitError: En cas de dépassement de limite de requêtes
            ResourceNotFoundError: Si la ressource demandée n'existe pas
            ValidationError: Si les données envoyées sont invalides
            APIError: Pour les autres erreurs API
        """
        url = self._build_url(endpoint)
        prepared_headers = self._prepare_headers(headers)
        session = await self._ensure_session()
        
        actual_timeout = aiohttp.ClientTimeout(total=timeout or self.timeout)
        actual_max_retries = max_retries if max_retries is not None else self.max_retries
        
        retry_count = 0
        last_exception = None
        
        while retry_count <= actual_max_retries:
            try:
                start_time = time.time()
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=prepared_headers,
                    timeout=actual_timeout
                ) as response:
                    response_time = time.time() - start_time
                    logger.debug(
                        f"{method} {url} → {response.status} en {response_time:.2f}s"
                    )
                    
                    # Gestion des erreurs HTTP
                    if response.status >= 400:
                        content = await response.text()
                        self._handle_response_error(response, content)
                    
                    # Récupération du contenu
                    if response.content_type == 'application/json':
                        return await response.json()
                    else:
                        return await response.text()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Erreurs de connexion et timeouts
                last_exception = e
                retry_count += 1
                
                if retry_count <= actual_max_retries:
                    # Attente avec backoff exponentiel
                    wait_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.warning(
                        f"Erreur de connexion lors de la requête {method} {url}: {str(e)}. "
                        f"Nouvelle tentative {retry_count}/{actual_max_retries} dans {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Nombre maximum de tentatives atteint
                    logger.error(
                        f"Échec définitif après {actual_max_retries} tentatives pour {method} {url}: {str(e)}"
                    )
                    raise ConnectionError(f"Échec de connexion après {actual_max_retries} tentatives: {str(e)}")
            
            except (RateLimitError, APIError) as e:
                # Pour certaines erreurs API (comme rate limiting), on peut réessayer
                if hasattr(e, 'is_retriable') and e.is_retriable and retry_count < actual_max_retries:
                    retry_count += 1
                    
                    # Si RateLimitError a retry_after, utiliser cette valeur
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait_time = e.retry_after
                    else:
                        wait_time = self.retry_delay * (2 ** (retry_count - 1))
                    
                    logger.warning(
                        f"Erreur API retriable lors de la requête {method} {url}: {str(e)}. "
                        f"Nouvelle tentative {retry_count}/{actual_max_retries} dans {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Erreur non retriable ou nombre maximum de tentatives atteint
                    raise
        
        # Si on arrive ici, c'est qu'on a échoué après toutes les tentatives
        raise ConnectionError(f"Échec de la requête après {actual_max_retries} tentatives", 
                              retryable=False)
    
    # Méthodes de commodité pour les différents types de requêtes
    
    async def get(self, endpoint, **kwargs):
        """Effectue une requête GET."""
        return await self.request('GET', endpoint, **kwargs)
    
    async def post(self, endpoint, **kwargs):
        """Effectue une requête POST."""
        return await self.request('POST', endpoint, **kwargs)
    
    async def put(self, endpoint, **kwargs):
        """Effectue une requête PUT."""
        return await self.request('PUT', endpoint, **kwargs)
    
    async def patch(self, endpoint, **kwargs):
        """Effectue une requête PATCH."""
        return await self.request('PATCH', endpoint, **kwargs)
    
    async def delete(self, endpoint, **kwargs):
        """Effectue une requête DELETE."""
        return await self.request('DELETE', endpoint, **kwargs)
    
    # Méthode spéciale pour la gestion des contextes async
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
