"""
Générateur de rapports financiers pour le module de comptabilité.

Ce module est responsable de la génération de rapports financiers
en utilisant les données collectées et traitées par le système.
"""

import asyncio
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import structlog
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import get_session
from src.db.models import (EntryType, JournalEntry, Report, ReportFormat,
                          ReportStatus, ReportTemplate, Transaction)
from src.reports.exporters.csv_exporter import CSVExporter
from src.reports.exporters.excel_exporter import ExcelExporter
from src.reports.exporters.pdf_exporter import PDFExporter
from src.utils.date_utils import get_period_bounds

# Configuration du logger
logger = structlog.get_logger(__name__)


class ReportType(str, Enum):
    """Types de rapports financiers disponibles."""
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


class ReportGenerator:
    """
    Générateur de rapports financiers.
    
    Cette classe est responsable de:
    - La collecte des données nécessaires pour les rapports
    - Le traitement et l'analyse des données
    - La génération des rapports dans différents formats
    - L'enregistrement des rapports générés
    """
    
    def __init__(self):
        """Initialise le générateur de rapports."""
        # Répertoire des templates de rapports
        self.template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "templates",
            "reports"
        )
        
        # Initialisation du moteur de templates Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
        
        # Répertoire de sortie pour les rapports générés
        self.output_dir = settings.reporting.report_directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Répertoire temporaire pour la génération
        self.temp_dir = settings.reporting.temp_directory
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialisation des exporteurs
        self.exporters = {
            ReportFormat.PDF: PDFExporter(),
            ReportFormat.EXCEL: ExcelExporter(),
            ReportFormat.CSV: CSVExporter(),
        }
    
    async def generate_report(
        self,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
        format: ReportFormat = ReportFormat.PDF,
        template_id: Optional[str] = None,
        report_params: Optional[Dict] = None
    ) -> Optional[Report]:
        """
        Génère un rapport financier.
        
        Args:
            report_type (ReportType): Type de rapport à générer
            period_start (datetime): Date de début de la période
            period_end (datetime): Date de fin de la période
            format (ReportFormat, optional): Format de sortie. Par défaut à PDF.
            template_id (str, optional): ID du template à utiliser. Si None, utilise le template par défaut.
            report_params (Dict, optional): Paramètres supplémentaires pour la génération.
        
        Returns:
            Optional[Report]: Objet rapport généré, ou None en cas d'échec
        """
        logger.info(
            "Génération de rapport",
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            format=format
        )
        
        # Créer l'enregistrement du rapport en base
        async with get_session() as session:
            # Récupérer le template de rapport
            template = None
            if template_id:
                template = await self._get_template_by_id(session, template_id)
            
            if not template:
                template = await self._get_default_template(session, report_type)
            
            if not template:
                logger.error("Aucun template trouvé pour ce type de rapport", report_type=report_type)
                return None
            
            # Créer l'enregistrement du rapport
            report = Report(
                name=f"Rapport {report_type.value} du {period_start.strftime('%d/%m/%Y')} au {period_end.strftime('%d/%m/%Y')}",
                description=f"Rapport {report_type.value} généré automatiquement",
                report_date=datetime.now(),
                period_start=period_start,
                period_end=period_end,
                status=ReportStatus.GENERATING,
                format=format,
                template_id=template.id,
                metadata={
                    "report_type": report_type.value,
                    "params": report_params or {}
                }
            )
            
            session.add(report)
            await session.commit()
            await session.refresh(report)
            
            try:
                # Collecter les données pour le rapport
                report_data = await self._collect_report_data(session, report_type, period_start, period_end, report_params)
                
                # Générer le contenu du rapport avec le template
                report_content = await self._render_report_template(template, report_data)
                
                # Exporter dans le format demandé
                if format not in self.exporters:
                    logger.error("Format d'export non supporté", format=format)
                    report.status = ReportStatus.FAILED
                    report.metadata["error"] = f"Format d'export non supporté: {format}"
                    await session.commit()
                    return report
                
                # Générer le nom de fichier
                filename = f"{report_type.value}_{period_start.strftime('%Y%m%d')}_{period_end.strftime('%Y%m%d')}"
                
                # Exporter le rapport
                file_path = await self.exporters[format].export(
                    report_content,
                    os.path.join(self.output_dir, f"{filename}.{format.value.lower()}"),
                    report_data
                )
                
                # Mettre à jour le statut du rapport
                report.status = ReportStatus.COMPLETED
                report.file_path = file_path
                await session.commit()
                
                logger.info("Rapport généré avec succès", report_id=str(report.id), file_path=file_path)
                return report
                
            except Exception as e:
                logger.error("Erreur lors de la génération du rapport", error=str(e), report_id=str(report.id))
                report.status = ReportStatus.FAILED
                report.metadata["error"] = str(e)
                await session.commit()
                return report
    
    async def _get_template_by_id(self, session: AsyncSession, template_id: str) -> Optional[ReportTemplate]:
        """
        Récupère un template de rapport par son ID.
        
        Args:
            session (AsyncSession): Session de base de données
            template_id (str): ID du template
        
        Returns:
            Optional[ReportTemplate]: Template de rapport, ou None si non trouvé
        """
        try:
            result = await session.execute(
                select(ReportTemplate).where(ReportTemplate.id == template_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Erreur lors de la récupération du template", error=str(e), template_id=template_id)
            return None
    
    async def _get_default_template(self, session: AsyncSession, report_type: ReportType) -> Optional[ReportTemplate]:
        """
        Récupère le template par défaut pour un type de rapport.
        
        Args:
            session (AsyncSession): Session de base de données
            report_type (ReportType): Type de rapport
        
        Returns:
            Optional[ReportTemplate]: Template de rapport, ou None si non trouvé
        """
        try:
            result = await session.execute(
                select(ReportTemplate)
                .where(ReportTemplate.template_type == report_type.value.upper())
                .where(ReportTemplate.is_active == True)
                .order_by(ReportTemplate.name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Erreur lors de la récupération du template par défaut", 
                       error=str(e), report_type=report_type)
            return None
    
    async def _collect_report_data(
        self, 
        session: AsyncSession,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
        report_params: Optional[Dict] = None
    ) -> Dict:
        """
        Collecte les données nécessaires pour le rapport.
        
        Args:
            session (AsyncSession): Session de base de données
            report_type (ReportType): Type de rapport
            period_start (datetime): Date de début de la période
            period_end (datetime): Date de fin de la période
            report_params (Dict, optional): Paramètres supplémentaires
        
        Returns:
            Dict: Données pour le rapport
        """
        # Données de base communes à tous les rapports
        base_data = {
            "report_type": report_type.value,
            "period_start": period_start,
            "period_end": period_end,
            "generation_date": datetime.now(),
            "restaurant_name": "Le Vieux Moulin",
            "params": report_params or {}
        }
        
        # Collecter les données spécifiques au type de rapport
        if report_type == ReportType.DAILY:
            return await self._collect_daily_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.WEEKLY:
            return await self._collect_weekly_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.MONTHLY:
            return await self._collect_monthly_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.QUARTERLY:
            return await self._collect_quarterly_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.ANNUAL:
            return await self._collect_annual_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.SALES:
            return await self._collect_sales_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.EXPENSES:
            return await self._collect_expenses_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.PROFIT_LOSS:
            return await self._collect_profit_loss_report_data(session, base_data, period_start, period_end)
        elif report_type == ReportType.TAX:
            return await self._collect_tax_report_data(session, base_data, period_start, period_end)
        else:
            # Rapport personnalisé ou non géré spécifiquement
            return base_data
    
    async def _collect_daily_report_data(
        self, 
        session: AsyncSession,
        base_data: Dict,
        period_start: datetime,
        period_end: datetime
    ) -> Dict:
        """
        Collecte les données pour un rapport journalier.
        
        Args:
            session (AsyncSession): Session de base de données
            base_data (Dict): Données de base du rapport
            period_start (datetime): Date de début (début de journée)
            period_end (datetime): Date de fin (fin de journée)
        
        Returns:
            Dict: Données complètes pour le rapport
        """
        # Récupérer les transactions de la journée
        result = await session.execute(
            select(Transaction)
            .where(Transaction.transaction_date >= period_start)
            .where(Transaction.transaction_date <= period_end)
            .order_by(Transaction.transaction_date)
        )
        transactions = result.scalars().all()
        
        # Récupérer les écritures comptables de la journée
        result = await session.execute(
            select(JournalEntry)
            .where(JournalEntry.entry_date >= period_start)
            .where(JournalEntry.entry_date <= period_end)
            .order_by(JournalEntry.entry_date)
        )
        entries = result.scalars().all()
        
        # Calculer les totaux
        total_sales = sum(t.total_amount for t in transactions if t.source_type == "POS")
        total_expenses = sum(t.total_amount for t in transactions if t.source_type in ["SUPPLIERS", "EXPENSES"])
        
        # Calcul des taxes
        tax_by_rate = {}
        for entry in entries:
            if entry.entry_type == EntryType.SALE and not entry.debit:
                # Écritures de TVA collectée
                if entry.account.code.startswith("4457"):
                    tax_rate = entry.metadata.get("tax_rate", "unknown")
                    if tax_rate not in tax_by_rate:
                        tax_by_rate[tax_rate] = 0
                    tax_by_rate[tax_rate] += entry.amount
        
        # Ventilation des ventes par catégorie
        sales_by_category = {}
        for transaction in transactions:
            if transaction.source_type == "POS":
                for item in transaction.metadata.get("items", []):
                    category = item.get("category", "Autre")
                    if category not in sales_by_category:
                        sales_by_category[category] = 0
                    sales_by_category[category] += float(item.get("amount", 0))
        
        # Ventilation des ventes par période de la journée
        sales_by_hour = {}
        for transaction in transactions:
            if transaction.source_type == "POS":
                hour = transaction.transaction_date.hour
                period = "Matin" if hour < 12 else "Après-midi" if hour < 18 else "Soir"
                if period not in sales_by_hour:
                    sales_by_hour[period] = 0
                sales_by_hour[period] += transaction.total_amount
        
        # Méthodes de paiement
        payment_methods = {}
        for transaction in transactions:
            if transaction.source_type == "POS":
                method = transaction.payment_method.value if transaction.payment_method else "AUTRE"
                if method not in payment_methods:
                    payment_methods[method] = 0
                payment_methods[method] += transaction.total_amount
        
        # Compléter les données du rapport
        report_data = {
            **base_data,
            "transactions": transactions,
            "entries": entries,
            "total_sales": total_sales,
            "total_expenses": total_expenses,
            "gross_profit": total_sales - total_expenses,
            "tax_by_rate": tax_by_rate,
            "sales_by_category": sales_by_category,
            "sales_by_hour": sales_by_hour,
            "payment_methods": payment_methods,
            "transactions_count": len([t for t in transactions if t.source_type == "POS"]),
            "average_transaction": total_sales / len([t for t in transactions if t.source_type == "POS"]) if len([t for t in transactions if t.source_type == "POS"]) > 0 else 0
        }
        
        return report_data
    
    # Les autres méthodes de collecte similaires pour les différents types de rapports
    # (weekly, monthly, quarterly, annual, etc.) suivraient le même modèle
    
    async def _render_report_template(self, template: ReportTemplate, data: Dict) -> str:
        """
        Rend le template de rapport avec les données.
        
        Args:
            template (ReportTemplate): Template de rapport
            data (Dict): Données pour le rapport
        
        Returns:
            str: Contenu rendu du rapport (format HTML)
        """
        try:
            # Vérifier que le fichier template existe
            template_path = template.template_file
            if not os.path.exists(os.path.join(self.template_dir, template_path)):
                logger.error("Fichier template non trouvé", template_path=template_path)
                raise FileNotFoundError(f"Template non trouvé: {template_path}")
            
            # Charger et rendre le template
            jinja_template = self.jinja_env.get_template(template_path)
            rendered_content = jinja_template.render(**data)
            
            return rendered_content
        except Exception as e:
            logger.error("Erreur lors du rendu du template", error=str(e), template_id=str(template.id))
            raise
    
    async def get_report_file(self, report_id: str) -> Optional[str]:
        """
        Récupère le chemin du fichier pour un rapport.
        
        Args:
            report_id (str): ID du rapport
        
        Returns:
            Optional[str]: Chemin du fichier, ou None si non trouvé
        """
        async with get_session() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()
            
            if not report or not report.file_path or report.status != ReportStatus.COMPLETED:
                return None
            
            return report.file_path


# Créer une instance du générateur de rapports
report_generator = ReportGenerator()
