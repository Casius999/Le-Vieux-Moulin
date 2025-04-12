"""Limitation de débit pour les appels API.

Ce module fournit des mécanismes pour limiter le taux de requêtes
envoyées aux APIs afin de respecter les limites imposées par les
services externes.
"""

import asyncio
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List, Tuple, Any, Callable

logger = logging.getLogger(__name__)

class RateLimiter:
    """Limiteur de débit basé sur des buckets de jetons.
    
    Cette classe implémente un algorithme de "token bucket", où un nombre
    fixe de "jetons" est ajouté périodiquement, et chaque requête
    consomme un jeton. Si aucun jeton n'est disponible, la requête est
    mise en attente jusqu'à ce qu'un jeton devienne disponible.
    """
    
    def __init__(self, 
                 rate: float, 
                 period: float = 1.0,
                 burst: Optional[int] = None,
                 max_delay: Optional[float] = None):
        """Initialise le limiteur de débit.
        
        Args:
            rate: Nombre de requêtes autorisées par période
            period: Durée de la période en secondes (par défaut: 1 seconde)
            burst: Nombre maximum de requêtes en rafale (par défaut: égal à rate)
            max_delay: Délai maximum d'attente en secondes (par défaut: aucune limite)
        """
        self.rate = rate
        self.period = period
        self.burst = burst if burst is not None else int(rate)
        self.max_delay = max_delay
        
        self._tokens = self.burst  # Nombre initial de jetons
        self._last_update = time.monotonic()  # Dernier rafraîchissement des jetons
        self._lock = asyncio.Lock()  # Verrou pour les opérations sur les jetons
    
    async def acquire(self, tokens: int = 1) -> None:
        """Acquiert le nombre spécifié de jetons, en attendant si nécessaire.
        
        Args:
            tokens: Nombre de jetons à acquérir (par défaut: 1)
            
        Raises:
            asyncio.TimeoutError: Si le délai maximum d'attente est dépassé
        """
        if tokens <= 0:
            return
        
        async with self._lock:
            # Calculer le temps d'attente nécessaire
            wait_time = await self._calculate_wait_time(tokens)
            
            # Vérifier si le délai d'attente dépasse le maximum autorisé
            if self.max_delay is not None and wait_time > self.max_delay:
                raise asyncio.TimeoutError(
                    f"Le délai d'attente pour les jetons ({wait_time:.2f}s) "
                    f"dépasse le maximum autorisé ({self.max_delay:.2f}s)"
                )
            
            # Attendre si nécessaire
            if wait_time > 0:
                logger.debug(f"Rate limiter: attente de {wait_time:.2f}s pour {tokens} jetons")
                await asyncio.sleep(wait_time)
            
            # Mettre à jour les jetons et l'horodatage
            self._tokens -= tokens
            self._last_update = time.monotonic()
    
    async def _calculate_wait_time(self, tokens: int) -> float:
        """Calcule le temps d'attente nécessaire pour obtenir les jetons.
        
        Args:
            tokens: Nombre de jetons à acquérir
            
        Returns:
            Temps d'attente en secondes (0 si les jetons sont immédiatement disponibles)
        """
        # Mettre à jour le nombre de jetons disponibles en fonction du temps écoulé
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst, self._tokens + elapsed * (self.rate / self.period))
        self._last_update = now
        
        # Si suffisamment de jetons sont disponibles, pas d'attente
        if self._tokens >= tokens:
            return 0
        
        # Sinon, calculer le temps nécessaire pour obtenir les jetons manquants
        return (tokens - self._tokens) * (self.period / self.rate)


class MultiRateLimiter:
    """Gestionnaire de plusieurs limiteurs de débit.
    
    Cette classe permet de gérer plusieurs limiteurs de débit pour
    différentes ressources ou endpoints d'un même service.
    """
    
    def __init__(self, default_rate: float = float('inf'), default_period: float = 1.0):
        """Initialise le gestionnaire de limiteurs de débit.
        
        Args:
            default_rate: Taux par défaut pour les ressources sans limiteur spécifique
            default_period: Période par défaut en secondes
        """
        self.default_rate = default_rate
        self.default_period = default_period
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()
    
    def add_limiter(self, 
                   resource: str, 
                   rate: float, 
                   period: float = 1.0, 
                   burst: Optional[int] = None,
                   max_delay: Optional[float] = None) -> None:
        """Ajoute un limiteur de débit pour une ressource spécifique.
        
        Args:
            resource: Identifiant de la ressource (ex: "api.exemple.com/users")
            rate: Nombre de requêtes autorisées par période
            period: Durée de la période en secondes
            burst: Nombre maximum de requêtes en rafale
            max_delay: Délai maximum d'attente en secondes
        """
        self._limiters[resource] = RateLimiter(
            rate=rate,
            period=period,
            burst=burst,
            max_delay=max_delay
        )
    
    async def get_limiter(self, resource: str) -> RateLimiter:
        """Obtient ou crée un limiteur de débit pour une ressource.
        
        Args:
            resource: Identifiant de la ressource
            
        Returns:
            Limiteur de débit pour la ressource
        """
        if resource not in self._limiters:
            async with self._lock:
                # Vérifier à nouveau après l'acquisition du verrou
                if resource not in self._limiters:
                    self._limiters[resource] = RateLimiter(
                        rate=self.default_rate,
                        period=self.default_period
                    )
        
        return self._limiters[resource]
    
    async def acquire(self, resource: str, tokens: int = 1) -> None:
        """Acquiert des jetons pour une ressource spécifique.
        
        Args:
            resource: Identifiant de la ressource
            tokens: Nombre de jetons à acquérir
            
        Raises:
            asyncio.TimeoutError: Si le délai maximum d'attente est dépassé
        """
        limiter = await self.get_limiter(resource)
        await limiter.acquire(tokens)


class AdaptiveRateLimiter(RateLimiter):
    """Limiteur de débit adaptatif basé sur les réponses API.
    
    Cette classe étend RateLimiter pour ajuster dynamiquement les
    paramètres de limitation en fonction des en-têtes de rate limit
    renvoyés par les API.
    """
    
    def __init__(self, 
                 initial_rate: float, 
                 period: float = 1.0,
                 burst: Optional[int] = None,
                 max_delay: Optional[float] = None,
                 safety_factor: float = 0.9):
        """Initialise le limiteur de débit adaptatif.
        
        Args:
            initial_rate: Taux initial de requêtes par période
            period: Durée de la période en secondes
            burst: Nombre maximum de requêtes en rafale
            max_delay: Délai maximum d'attente en secondes
            safety_factor: Facteur de sécurité pour le taux adaptatif (0.0-1.0)
        """
        super().__init__(rate=initial_rate, period=period, burst=burst, max_delay=max_delay)
        self.initial_rate = initial_rate
        self.safety_factor = max(0.1, min(1.0, safety_factor))  # Limiter entre 0.1 et 1.0
        self._request_count = 0  # Nombre total de requêtes effectuées
        self._rate_limit_info: Dict[str, Any] = {}  # Informations sur les limites de débit
    
    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """Met à jour les paramètres de limitation en fonction des en-têtes HTTP.
        
        Cette méthode analyse les en-têtes de rate limit courants et ajuste
        les paramètres du limiteur en conséquence.
        
        Args:
            headers: En-têtes HTTP de la réponse API
        """
        # Rechercher les en-têtes courants de rate limit
        limit_header_keys = [
            # Format: (limite, reste, réinitialisation)
            ('X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'),
            ('RateLimit-Limit', 'RateLimit-Remaining', 'RateLimit-Reset'),
            ('X-Rate-Limit-Limit', 'X-Rate-Limit-Remaining', 'X-Rate-Limit-Reset'),
            ('rate-limit-limit', 'rate-limit-remaining', 'rate-limit-reset'),
            
            # GitHub
            ('X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'),
            
            # Twitter
            ('x-rate-limit-limit', 'x-rate-limit-remaining', 'x-rate-limit-reset'),
        ]
        
        for limit_key, remaining_key, reset_key in limit_header_keys:
            if limit_key.lower() in [k.lower() for k in headers.keys()]:
                # Trouver les clés exactes (insensible à la casse)
                actual_limit_key = next(k for k in headers.keys() if k.lower() == limit_key.lower())
                actual_remaining_key = next(k for k in headers.keys() if k.lower() == remaining_key.lower())
                actual_reset_key = next(k for k in headers.keys() if k.lower() == reset_key.lower())
                
                try:
                    limit = int(headers[actual_limit_key])
                    remaining = int(headers[actual_remaining_key])
                    reset = headers[actual_reset_key]
                    
                    # Convertir reset en datetime si c'est un timestamp
                    if reset.isdigit():
                        reset_value = int(reset)
                        # Certaines API utilisent des secondes, d'autres des millisecondes
                        if reset_value > 10000000000:  # Probablement des millisecondes
                            reset_time = datetime.fromtimestamp(reset_value / 1000)
                        else:
                            reset_time = datetime.fromtimestamp(reset_value)
                    else:
                        # Supposer un format ISO 8601
                        reset_time = datetime.fromisoformat(reset.replace('Z', '+00:00'))
                    
                    # Enregistrer les informations
                    self._rate_limit_info = {
                        'limit': limit,
                        'remaining': remaining,
                        'reset_time': reset_time,
                        'updated_at': datetime.now()
                    }
                    
                    # Calculer le nouveau taux en fonction du temps restant
                    now = datetime.now()
                    if reset_time > now:
                        seconds_until_reset = (reset_time - now).total_seconds()
                        if seconds_until_reset > 0:
                            new_rate = (remaining / seconds_until_reset) * self.period
                            # Appliquer le facteur de sécurité et limiter au taux initial maximum
                            adjusted_rate = min(self.initial_rate, new_rate * self.safety_factor)
                            
                            # Mettre à jour le taux
                            self.rate = max(0.5, adjusted_rate)  # Au moins 0.5 pour éviter les blocages
                            logger.debug(
                                f"Rate limiter ajusté: {self.rate:.2f} req/{self.period}s "
                                f"(restant: {remaining}/{limit}, réinitialisation dans {seconds_until_reset:.2f}s)"
                            )
                    
                    # Sortir de la boucle après avoir trouvé des en-têtes valides
                    break
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erreur lors de l'analyse des en-têtes de rate limit: {str(e)}")
        
        # Vérifier les en-têtes Retry-After (utilisés pour le rate limiting temporaire)
        retry_after_keys = ['Retry-After', 'retry-after', 'X-Retry-After', 'x-retry-after']
        for key in retry_after_keys:
            if key.lower() in [k.lower() for k in headers.keys()]:
                actual_key = next(k for k in headers.keys() if k.lower() == key.lower())
                retry_after = headers[actual_key]
                
                try:
                    # Retry-After peut être un nombre de secondes ou une date HTTP
                    if retry_after.isdigit():
                        seconds = int(retry_after)
                    else:
                        # Format de date HTTP (RFC 7231)
                        from email.utils import parsedate_to_datetime
                        retry_time = parsedate_to_datetime(retry_after)
                        seconds = (retry_time - datetime.now(retry_time.tzinfo)).total_seconds()
                    
                    if seconds > 0:
                        logger.warning(f"Rate limit atteint, attente imposée de {seconds}s")
                        # Force le taux à une valeur très faible temporairement
                        self.rate = 0.1  # Une requête toutes les 10 secondes
                        break
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erreur lors de l'analyse de Retry-After: {str(e)}")


async def rate_limited(limiter: RateLimiter):
    """Décorateur asynchrone pour limiter le débit d'une fonction.
    
    Args:
        limiter: Instance de RateLimiter à utiliser
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator
