"""
Modèles Pydantic pour l'API du module de comptabilité.

Ce module contient les modèles de requêtes et réponses utilisés par l'API REST.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from src.db.models import EntryType, PaymentMethod, ReportFormat


class ReportType(str, Enum):
    """Types de rapports financiers."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"
    SALES = "sales"
    EXPENSES = "expenses"
    INVENTORY = "inventory"
    PROFIT_LOSS = "profit_loss"
    BALANCE = "balance"
    CASHFLOW = "cashflow"
    TAX = "tax"


class ReportGenerationRequest(BaseModel):
    """Requête de génération de rapport."""
    report_type: ReportType
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    format: str = "PDF"
    template_id: Optional[str] = None
    params: Optional[Dict] = None

    @validator("format")
    def validate_format(cls, v):
        """Valide le format de rapport."""
        formats = [f.value for f in ReportFormat]
        if v.upper() not in formats:
            raise ValueError(f"Format non supporté. Valeurs acceptées: {', '.join(formats)}")
        return v


class ReportResponse(BaseModel):
    """Réponse contenant les détails d'un rapport."""
    id: str
    name: str
    description: Optional[str] = None
    report_date: datetime
    period_start: datetime
    period_end: datetime
    status: str
    format: str
    file_path: Optional[str] = None

    class Config:
        orm_mode = True


class JournalEntryCreate(BaseModel):
    """Requête de création d'une écriture comptable."""
    entry_date: datetime
    entry_type: EntryType
    description: Optional[str] = None
    amount: float
    debit: bool = True
    account_code: str
    metadata: Optional[Dict] = None


class JournalEntryResponse(BaseModel):
    """Réponse contenant les détails d'une écriture comptable."""
    id: str
    entry_date: datetime
    entry_type: str
    description: Optional[str] = None
    amount: float
    debit: bool
    account: Dict
    metadata: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TransactionCreate(BaseModel):
    """Requête de création d'une transaction."""
    transaction_date: datetime
    reference: Optional[str] = None
    description: Optional[str] = None
    total_amount: float
    payment_method: Optional[PaymentMethod] = None
    source_type: str
    source_id: Optional[str] = None
    metadata: Optional[Dict] = None
    entries: List[JournalEntryCreate]


class TransactionResponse(BaseModel):
    """Réponse contenant les détails d'une transaction."""
    id: str
    transaction_date: datetime
    reference: Optional[str] = None
    description: Optional[str] = None
    total_amount: float
    payment_method: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    metadata: Optional[Dict] = None
    entries: List[JournalEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FinancialDataType(str, Enum):
    """Types de données financières pour les requêtes."""
    SALES = "sales"
    EXPENSES = "expenses"
    INVENTORY = "inventory"
    PROFIT_LOSS = "profit_loss"
    BALANCE = "balance"
    CASHFLOW = "cashflow"
    TAX = "tax"
    CUSTOM = "custom"


class FinancialDataRequest(BaseModel):
    """Requête d'interrogation des données financières."""
    data_type: FinancialDataType
    period_start: datetime
    period_end: datetime
    group_by: Optional[str] = None  # day, week, month, quarter, year, category, etc.
    filters: Optional[Dict] = None


class FinancialDataResponse(BaseModel):
    """Réponse contenant les données financières."""
    data_type: str
    period_start: datetime
    period_end: datetime
    generation_date: datetime
    data: Dict
    metadata: Optional[Dict] = None


class UserResponse(BaseModel):
    """Réponse contenant les détails d'un utilisateur."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class ErrorResponse(BaseModel):
    """Réponse d'erreur standard."""
    detail: str
    status_code: int = 400
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
