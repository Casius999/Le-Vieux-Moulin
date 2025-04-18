"""
Modèles Pydantic pour l'API du module de comptabilité.

Ce module définit les modèles de données utilisés pour la validation et la sérialisation
des requêtes et réponses de l'API.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from src.reports.report_generator import ReportType


# Modèles pour l'authentification
class Token(BaseModel):
    """Modèle de token d'authentification."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Données extraites du token."""
    username: Optional[str] = None
    roles: List[str] = []
    exp: Optional[int] = None


class UserLogin(BaseModel):
    """Modèle pour la connexion utilisateur."""
    username: str
    password: str


class UserInfo(BaseModel):
    """Informations sur l'utilisateur connecté."""
    id: str
    username: str
    email: Optional[str] = None
    roles: List[str]
    is_active: bool


# Modèles pour les rapports
class ReportGenerationRequest(BaseModel):
    """Requête de génération de rapport."""
    report_type: str  # Un des types définis dans ReportType
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    format: str = "PDF"  # PDF, EXCEL, CSV
    template_id: Optional[str] = None
    params: Optional[Dict] = None
    
    @validator('report_type')
    def validate_report_type(cls, v):
        """Valide que le type de rapport est supporté."""
        try:
            ReportType(v)
            return v
        except ValueError:
            valid_types = ", ".join([t.value for t in ReportType])
            raise ValueError(f"Type de rapport invalide. Valeurs supportées: {valid_types}")
    
    @validator('format')
    def validate_format(cls, v):
        """Valide que le format est supporté."""
        supported_formats = ["PDF", "EXCEL", "CSV", "JSON", "HTML"]
        if v.upper() not in supported_formats:
            raise ValueError(f"Format invalide. Formats supportés: {', '.join(supported_formats)}")
        return v.upper()


class ReportResponse(BaseModel):
    """Réponse pour un rapport."""
    id: str
    name: str
    description: Optional[str] = None
    report_date: datetime
    period_start: datetime
    period_end: datetime
    status: str  # PENDING, GENERATING, COMPLETED, FAILED
    format: str  # PDF, EXCEL, CSV
    file_path: Optional[str] = None


class ReportScheduleCreate(BaseModel):
    """Requête de création d'une programmation de rapport."""
    name: str
    description: Optional[str] = None
    report_type: str
    frequency: str  # DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL, CUSTOM
    cron_expression: Optional[str] = None
    recipients: List[str]
    format: str = "PDF"
    is_active: bool = True
    report_params: Optional[Dict] = None


class ReportScheduleResponse(BaseModel):
    """Réponse pour une programmation de rapport."""
    id: str
    name: str
    description: Optional[str] = None
    report_type: str
    frequency: str
    cron_expression: Optional[str] = None
    next_run: Optional[datetime] = None
    is_active: bool
    recipients: List[str]
    format: str
    report_params: Optional[Dict] = None


# Modèles pour les transactions
class TransactionCreate(BaseModel):
    """Requête de création d'une transaction."""
    transaction_date: datetime
    reference: Optional[str] = None
    description: Optional[str] = None
    total_amount: float
    payment_method: Optional[str] = None  # CASH, CARD, TRANSFER, CHECK, ONLINE, OTHER
    source_type: str  # POS, SUPPLIERS, PAYROLL, etc.
    source_id: Optional[str] = None
    metadata: Optional[Dict] = None
    entries: List[Dict]  # Liste des écritures comptables associées


class TransactionUpdate(BaseModel):
    """Requête de mise à jour d'une transaction."""
    transaction_date: Optional[datetime] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    total_amount: Optional[float] = None
    payment_method: Optional[str] = None
    metadata: Optional[Dict] = None


class TransactionResponse(BaseModel):
    """Réponse pour une transaction."""
    id: str
    transaction_date: datetime
    reference: Optional[str] = None
    description: Optional[str] = None
    total_amount: float
    payment_method: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    metadata: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime


class JournalEntryResponse(BaseModel):
    """Réponse pour une écriture comptable."""
    id: str
    entry_date: datetime
    entry_type: str
    description: Optional[str] = None
    amount: float
    debit: bool
    account_code: str
    account_name: str
    transaction_id: str
    validated: bool
    metadata: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime


# Modèles pour les requêtes de données financières
class FinancialDataRequest(BaseModel):
    """Requête pour des données financières."""
    data_type: str  # sales, expenses, margins, cash_flow, etc.
    period_start: datetime
    period_end: datetime
    group_by: Optional[str] = None  # day, week, month, category, etc.
    filters: Optional[Dict] = None


class FinancialDataResponse(BaseModel):
    """Réponse pour des données financières."""
    data_type: str
    period_start: datetime
    period_end: datetime
    group_by: Optional[str] = None
    data: Dict
    aggregates: Optional[Dict] = None
    metadata: Optional[Dict] = None
