"""
Collecteur de données pour le système de point de vente (POS).

Ce module est responsable de la récupération des données de vente depuis le
système de caisse du restaurant, leur transformation en un format standardisé
et leur intégration dans le système comptable.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import aiohttp
import structlog
from tenacity import (RetryError, retry, retry_if_exception_type, stop_after_attempt,
                        wait_exponential)

from src.config import settings
from src.db.models import EntryType, JournalEntry, PaymentMethod, Transaction
from src.utils.exceptions import ConnectionError, DataFormatError, RateLimitError

# Configuration du logger
logger = structlog.get_logger(__name__)


class POSCollector:
    """
    Collecteur de données depuis le système de point de vente (POS).
    Supporte actuellement les systèmes Lightspeed et Square.
    """
    
    def __init__(self):
        """Initialise le collecteur POS."""
        # Configuration de l'API du POS
        self.api_config = settings.data_sources.pos
        self.base_url = self.api_config.url
        self.auth_type = self.api_config.auth_type
        self.refresh_interval = self.api_config.refresh_interval_minutes
        
        # Cache pour éviter des requêtes répétées
        self._token_cache = None
        self._token_expiry = None
    
    async def _get_auth_token(self) -> str:
        """
        Récupère un token d'authentification pour l'API POS.
        
        Returns:
            str: Token d'authentification
        
        Raises:
            ConnectionError: En cas d'erreur de connexion à l'API
            AuthenticationError: En cas d'échec d'authentification
        """
        # Vérifier si on a déjà un token valide en cache
        if self._token_cache and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token_cache
        
        # Récupérer un nouveau token via l'API centrale
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.integration.central_server_url}/auth/token",
                    json={"service": "pos"},
                    headers={"X-API-Key": settings.integration.api_key}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ConnectionError(f"Erreur d'authentification POS: {response.status} - {error_text}")
                    
                    data = await response.json()
                    self._token_cache = data["token"]
                    
                    # Calculer l'expiration (5 minutes avant la fin réelle pour éviter les problèmes)
                    expires_in = data.get("expires_in", 3600)  # Par défaut 1h
                    self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
                    
                    return self._token_cache
        except Exception as e:
            logger.error("Erreur lors de la récupération du token POS", error=str(e))
            raise ConnectionError(f"Erreur de connexion au service d'authentification: {str(e)}")
    
    @retry(
        retry=retry_if_exception_type((ConnectionError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _api_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None, 
                          data: Optional[Dict] = None) -> Dict:
        """
        Effectue une requête à l'API POS avec gestion des erreurs et retry.
        
        Args:
            endpoint (str): Point d'API à appeler
            method (str, optional): Méthode HTTP. Par défaut à "GET".
            params (Dict, optional): Paramètres de requête. Par défaut à None.
            data (Dict, optional): Données à envoyer pour POST/PUT. Par défaut à None.
        
        Returns:
            Dict: Données de réponse
        
        Raises:
            ConnectionError: En cas d'erreur de connexion
            RateLimitError: En cas de dépassement de limite d'appels API
            DataFormatError: En cas de format de données invalide
        """
        token = await self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                request_kwargs = {
                    "url": f"{self.base_url}/{endpoint.lstrip('/')}",
                    "headers": headers,
                    "params": params,
                }
                
                if method in ["POST", "PUT", "PATCH"] and data:
                    request_kwargs["json"] = data
                
                async with getattr(session, method.lower())(**request_kwargs) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", "60"))
                        logger.warning("Limite d'API POS atteinte", retry_after=retry_after)
                        raise RateLimitError(f"Limite d'API POS atteinte. Réessayer après {retry_after}s")
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error("Erreur API POS", status=response.status, error=error_text)
                        raise ConnectionError(f"Erreur API POS: {response.status} - {error_text}")
                    
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error("Erreur de connexion à l'API POS", error=str(e))
            raise ConnectionError(f"Erreur de connexion à l'API POS: {str(e)}")
        except ValueError as e:
            logger.error("Erreur de format de données API POS", error=str(e))
            raise DataFormatError(f"Format de données invalide: {str(e)}")
    
    async def get_sales(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Récupère les ventes sur une période donnée.
        
        Args:
            start_date (datetime): Date de début
            end_date (datetime): Date de fin
        
        Returns:
            List[Dict]: Liste des transactions de vente formatées
        """
        logger.info("Récupération des ventes", start_date=start_date, end_date=end_date)
        
        try:
            sales_data = await self._api_request(
                "sales",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "include_items": True,
                    "include_payments": True,
                    "include_tax_details": True
                }
            )
            
            # Transformer les données dans le format standardisé
            transformed_sales = []
            for sale in sales_data.get("sales", []):
                try:
                    # Détecter la méthode de paiement
                    payment_method = PaymentMethod.CARD  # Par défaut
                    if sale.get("payments"):
                        pm_type = sale["payments"][0].get("type", "").upper()
                        if pm_type == "CASH":
                            payment_method = PaymentMethod.CASH
                        elif pm_type in ["CHECK", "CHEQUE"]:
                            payment_method = PaymentMethod.CHECK
                        elif pm_type in ["TRANSFER", "BANK_TRANSFER"]:
                            payment_method = PaymentMethod.TRANSFER
                        elif pm_type in ["ONLINE", "WEB"]:
                            payment_method = PaymentMethod.ONLINE
                    
                    # Créer la transaction formatée
                    transaction = {
                        "transaction_date": datetime.fromisoformat(sale["date"]),
                        "reference": str(sale["id"]),
                        "description": f"Vente {sale.get('reference', '')}",
                        "total_amount": float(sale["total"]),
                        "payment_method": payment_method,
                        "source_type": "POS",
                        "source_id": str(sale["id"]),
                        "metadata": {
                            "items": sale.get("items", []),
                            "payments": sale.get("payments", []),
                            "tax_details": sale.get("tax_details", []),
                            "customer": sale.get("customer"),
                            "employee": sale.get("employee"),
                            "discount": sale.get("discount")
                        },
                        "entries": self._generate_entries_from_sale(sale)
                    }
                    
                    transformed_sales.append(transaction)
                except (KeyError, ValueError) as e:
                    logger.warning("Erreur lors de la transformation d'une vente", 
                                 sale_id=sale.get("id"), error=str(e))
                    continue
            
            logger.info(f"Récupération de {len(transformed_sales)} ventes terminée")
            return transformed_sales
        
        except RetryError as e:
            logger.error("Échec après plusieurs tentatives de récupération des ventes", error=str(e))
            return []
        except Exception as e:
            logger.error("Erreur inattendue lors de la récupération des ventes", error=str(e))
            return []
    
    def _generate_entries_from_sale(self, sale: Dict) -> List[Dict]:
        """
        Génère les écritures comptables à partir d'une vente.
        
        Args:
            sale (Dict): Données de la vente
        
        Returns:
            List[Dict]: Liste des écritures comptables
        """
        entries = []
        sale_date = datetime.fromisoformat(sale["date"])
        total_amount = float(sale["total"])
        
        # 1. Écriture de vente (crédit)
        # Déterminer le compte en fonction du mode de paiement
        revenue_account = "707"  # Ventes de marchandises par défaut
        
        # Vérifier si on peut déterminer des comptes plus précis en fonction des articles
        if "items" in sale:
            # Logique de détermination des comptes selon les articles vendus
            pass
        
        entries.append({
            "entry_date": sale_date,
            "entry_type": EntryType.SALE,
            "description": f"Vente {sale.get('reference', '')}",
            "amount": total_amount,
            "debit": False,  # Crédit
            "account_code": revenue_account,
            "metadata": {
                "sale_id": sale["id"],
                "items": sale.get("items")
            }
        })
        
        # 2. Écriture de TVA (crédit)
        if "tax_details" in sale:
            for tax in sale["tax_details"]:
                tax_amount = float(tax["amount"])
                tax_rate = float(tax["rate"])
                
                # Déterminer le compte de TVA en fonction du taux
                if tax_rate == 20.0:
                    tax_account = "44571"  # TVA collectée 20%
                elif tax_rate == 10.0:
                    tax_account = "445711"  # TVA collectée 10%
                elif tax_rate == 5.5:
                    tax_account = "445712"  # TVA collectée 5.5%
                else:
                    tax_account = "44571"  # Compte par défaut
                
                entries.append({
                    "entry_date": sale_date,
                    "entry_type": EntryType.SALE,
                    "description": f"TVA sur vente {sale.get('reference', '')}",
                    "amount": tax_amount,
                    "debit": False,  # Crédit
                    "account_code": tax_account,
                    "metadata": {
                        "tax_rate": tax_rate,
                        "tax_base": float(tax["base"])
                    }
                })
        
        # 3. Écriture de trésorerie (débit)
        # Déterminer le compte en fonction du mode de paiement
        if "payments" in sale and sale["payments"]:
            payment = sale["payments"][0]
            payment_type = payment.get("type", "").upper()
            
            if payment_type == "CASH":
                cash_account = "53"  # Caisse
            elif payment_type in ["CARD", "CB"]:
                cash_account = "512"  # Banque
            elif payment_type in ["CHECK", "CHEQUE"]:
                cash_account = "5112"  # Chèques à encaisser
            else:
                cash_account = "512"  # Banque par défaut
            
            entries.append({
                "entry_date": sale_date,
                "entry_type": EntryType.SALE,
                "description": f"Encaissement vente {sale.get('reference', '')}",
                "amount": total_amount,
                "debit": True,  # Débit
                "account_code": cash_account,
                "metadata": {
                    "payment_method": payment_type,
                    "payment_id": payment.get("id")
                }
            })
        else:
            # Pas d'information de paiement, on utilise le compte client
            entries.append({
                "entry_date": sale_date,
                "entry_type": EntryType.SALE,
                "description": f"Créance client vente {sale.get('reference', '')}",
                "amount": total_amount,
                "debit": True,  # Débit
                "account_code": "411",  # Clients
                "metadata": {}
            })
        
        return entries
    
    async def sync_recent_sales(self, days_back: int = 1) -> List[Transaction]:
        """
        Synchronise les ventes récentes avec la base de données.
        
        Args:
            days_back (int, optional): Nombre de jours à remonter. Par défaut à 1.
        
        Returns:
            List[Transaction]: Liste des transactions créées ou mises à jour
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Récupérer les ventes
        sales = await self.get_sales(start_date, end_date)
        
        # Traitement pour chaque vente et insertion en base
        # Note: Cette partie nécessiterait une logique complète d'insertion en base
        # avec gestion des transactions existantes (mises à jour vs créations)
        
        return []
