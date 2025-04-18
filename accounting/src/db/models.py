"""
Modèles de données pour le module de comptabilité.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import (Boolean, Column, DateTime, Enum as SQLAEnum, Float,
                        ForeignKey, Integer, JSON, String, Text)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from src.db.database import Base


# Énumérations
class EntryType(str, Enum):
    """Types d'écritures comptables"""
    SALE = "SALE"                        # Vente
    PURCHASE = "PURCHASE"                # Achat fournisseur
    EXPENSE = "EXPENSE"                  # Dépense
    SALARY = "SALARY"                    # Salaire
    INVENTORY_ADJUSTMENT = "INVENTORY_ADJUSTMENT"  # Ajustement d'inventaire
    BANK_TRANSFER = "BANK_TRANSFER"      # Virement bancaire
    TAX_PAYMENT = "TAX_PAYMENT"          # Paiement de taxes
    DEPOSIT = "DEPOSIT"                  # Dépôt/Acompte
    REFUND = "REFUND"                    # Remboursement
    MANUAL_ENTRY = "MANUAL_ENTRY"        # Écriture manuelle
    BOOKING_DEPOSIT = "BOOKING_DEPOSIT"  # Acompte réservation


class ReportFrequency(str, Enum):
    """Fréquences de génération des rapports"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"
    CUSTOM = "CUSTOM"


class ReportFormat(str, Enum):
    """Formats de rapports disponibles"""
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    JSON = "JSON"
    HTML = "HTML"


class ReportStatus(str, Enum):
    """Statuts des rapports"""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPORTED = "EXPORTED"


class PaymentMethod(str, Enum):
    """Méthodes de paiement"""
    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    CHECK = "CHECK"
    ONLINE = "ONLINE"
    OTHER = "OTHER"


# Modèles de base
class BaseModel(Base):
    """Modèle de base avec ID et horodatage"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Modèles de données
class Account(BaseModel):
    """Compte du plan comptable"""
    __tablename__ = "accounts"
    
    code = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    account_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relations
    entries = relationship("JournalEntry", back_populates="account")
    
    def __repr__(self):
        return f"<Account {self.code}: {self.name}>"


class JournalEntry(BaseModel):
    """Écriture comptable"""
    __tablename__ = "journal_entries"
    
    entry_date = Column(DateTime, nullable=False, index=True)
    entry_type = Column(SQLAEnum(EntryType), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    debit = Column(Boolean, default=True, nullable=False)  # True=débit, False=crédit
    validated = Column(Boolean, default=False, nullable=False)
    
    # Références
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    
    # Métadonnées
    metadata = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    
    # Relations
    account = relationship("Account", back_populates="entries")
    transaction = relationship("Transaction", back_populates="entries")
    
    def __repr__(self):
        entry_type = "débit" if self.debit else "crédit"
        return f"<JournalEntry {self.entry_date}: {self.amount}€ {entry_type} - {self.description}>"


class Transaction(BaseModel):
    """Transaction financière"""
    __tablename__ = "transactions"
    
    transaction_date = Column(DateTime, nullable=False, index=True)
    reference = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(SQLAEnum(PaymentMethod), nullable=True)
    
    # Source de la transaction
    source_type = Column(String(50), nullable=False)  # POS, SUPPLIERS, PAYROLL, etc.
    source_id = Column(String(100), nullable=True)  # ID dans le système source
    
    # Métadonnées
    metadata = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    
    # Relations
    entries = relationship("JournalEntry", back_populates="transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_date}: {self.total_amount}€ - {self.source_type}>"


class TaxRate(BaseModel):
    """Taux de TVA"""
    __tablename__ = "tax_rates"
    
    code = Column(String(10), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    rate = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<TaxRate {self.code}: {self.rate}%>"


class ReportTemplate(BaseModel):
    """Modèle de rapport"""
    __tablename__ = "report_templates"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False)  # DAILY, MONTHLY, etc.
    template_file = Column(String(255), nullable=False)  # Chemin vers le fichier template
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Configuration
    config = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    
    # Relations
    reports = relationship("Report", back_populates="template")
    
    def __repr__(self):
        return f"<ReportTemplate {self.name}>"


class Report(BaseModel):
    """Rapport financier généré"""
    __tablename__ = "reports"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_date = Column(DateTime, nullable=False)  # Date de référence du rapport
    
    # Période couverte
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Statut et format
    status = Column(SQLAEnum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    format = Column(SQLAEnum(ReportFormat), default=ReportFormat.PDF, nullable=False)
    
    # Fichier généré
    file_path = Column(String(255), nullable=True)
    
    # Métadonnées
    metadata = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    
    # Références
    template_id = Column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=False)
    
    # Relations
    template = relationship("ReportTemplate", back_populates="reports")
    schedule = relationship("ReportSchedule", back_populates="reports")
    
    def __repr__(self):
        return f"<Report {self.name} - {self.report_date}: {self.status.value}>"


class ReportSchedule(BaseModel):
    """Programmation de génération automatique de rapports"""
    __tablename__ = "report_schedules"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Configuration de planification
    frequency = Column(SQLAEnum(ReportFrequency), nullable=False)
    cron_expression = Column(String(100), nullable=True)  # Expression cron pour programmation personnalisée
    next_run = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Configuration des rapports
    report_config = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    
    # Destinataires
    recipients = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    
    # Relations
    reports = relationship("Report", back_populates="schedule")
    
    def __repr__(self):
        return f"<ReportSchedule {self.name}: {self.frequency.value}>"


class FinancialPeriod(BaseModel):
    """Période comptable/fiscale"""
    __tablename__ = "financial_periods"
    
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    
    # Type de période
    period_type = Column(String(50), nullable=False)  # MONTH, QUARTER, YEAR
    
    def __repr__(self):
        return f"<FinancialPeriod {self.name}: {self.start_date} - {self.end_date}>"


class AuditLog(BaseModel):
    """Journal d'audit pour la traçabilité des actions comptables"""
    __tablename__ = "audit_logs"
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String(50), nullable=True)
    user_name = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VALIDATE, EXPORT
    resource_type = Column(String(50), nullable=False)  # JOURNAL_ENTRY, TRANSACTION, REPORT
    resource_id = Column(String(50), nullable=True)
    details = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=True)
    ip_address = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<AuditLog {self.timestamp}: {self.action} on {self.resource_type}>"
