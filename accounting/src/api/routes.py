"""
Configuration des routes API pour le module de comptabilité.

Ce module définit toutes les routes API exposées par le module de comptabilité.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.models import (ReportGenerationRequest, ReportResponse,
                           TransactionCreate, TransactionResponse,
                           FinancialDataRequest, FinancialDataResponse)
from src.db.database import get_session
from src.db.models import (EntryType, JournalEntry, Report, ReportFormat,
                          ReportStatus, Transaction)
from src.reports.report_generator import ReportGenerator, ReportType
from src.utils.date_utils import get_period_bounds

# Configuration du logger
logger = structlog.get_logger(__name__)

# Création des routers
router_reports = APIRouter(prefix="/reports", tags=["reports"])
router_transactions = APIRouter(prefix="/transactions", tags=["transactions"])
router_data = APIRouter(prefix="/data", tags=["data"])
router_export = APIRouter(prefix="/export", tags=["export"])
router_admin = APIRouter(prefix="/admin", tags=["admin"])


#
# Routes pour les rapports
#

@router_reports.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerationRequest,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Génère un rapport financier selon les paramètres spécifiés.
    """
    logger.info(
        "Demande de génération de rapport", 
        user_id=current_user.id,
        report_type=request.report_type,
        period_start=request.period_start,
        period_end=request.period_end
    )
    
    try:
        # Récupérer les dates de début/fin de période
        if not request.period_end:
            request.period_end = datetime.now()
        
        if not request.period_start:
            # Déterminer la date de début en fonction du type de rapport
            if request.report_type == ReportType.DAILY:
                request.period_start = request.period_end.replace(hour=0, minute=0, second=0, microsecond=0)
            elif request.report_type == ReportType.WEEKLY:
                request.period_start = request.period_end - timedelta(days=7)
            elif request.report_type == ReportType.MONTHLY:
                request.period_start = request.period_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif request.report_type == ReportType.QUARTERLY:
                month = request.period_end.month
                quarter_start_month = ((month - 1) // 3) * 3 + 1
                request.period_start = request.period_end.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            elif request.report_type == ReportType.ANNUAL:
                request.period_start = request.period_end.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                request.period_start = request.period_end - timedelta(days=30)  # Par défaut: 30 jours
        
        # Valider les dates
        if request.period_start > request.period_end:
            raise HTTPException(status_code=400, detail="La date de début doit être antérieure à la date de fin")
        
        # Convertir format si nécessaire
        report_format = ReportFormat(request.format.upper())
        
        # Générer le rapport
        report_generator = ReportGenerator()
        report = await report_generator.generate_report(
            report_type=ReportType(request.report_type),
            period_start=request.period_start,
            period_end=request.period_end,
            format=report_format,
            template_id=request.template_id,
            report_params=request.params
        )
        
        if not report:
            raise HTTPException(status_code=500, detail="Erreur lors de la génération du rapport")
        
        # Retourner la réponse
        return ReportResponse(
            id=str(report.id),
            name=report.name,
            description=report.description,
            report_date=report.report_date,
            period_start=report.period_start,
            period_end=report.period_end,
            status=report.status.value,
            format=report.format.value,
            file_path=report.file_path if report.status == ReportStatus.COMPLETED else None
        )
    
    except ValueError as e:
        logger.error("Erreur de validation", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erreur lors de la génération du rapport", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}")


@router_reports.get("/status/{report_id}", response_model=ReportResponse)
async def get_report_status(
    report_id: str = Path(..., description="ID du rapport"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Vérifie le statut d'un rapport en cours de génération.
    """
    try:
        # Récupérer le rapport
        result = await session.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Rapport non trouvé")
        
        # Retourner la réponse
        return ReportResponse(
            id=str(report.id),
            name=report.name,
            description=report.description,
            report_date=report.report_date,
            period_start=report.period_start,
            period_end=report.period_end,
            status=report.status.value,
            format=report.format.value,
            file_path=report.file_path if report.status == ReportStatus.COMPLETED else None
        )
    
    except Exception as e:
        logger.error("Erreur lors de la récupération du statut du rapport", error=str(e), report_id=report_id)
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router_reports.get("/download/{report_id}")
async def download_report(
    report_id: str = Path(..., description="ID du rapport"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Télécharge un rapport généré.
    """
    try:
        # Récupérer le rapport
        result = await session.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Rapport non trouvé")
        
        if report.status != ReportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail=f"Le rapport n'est pas prêt au téléchargement (statut: {report.status.value})")
        
        if not report.file_path or not os.path.exists(report.file_path):
            raise HTTPException(status_code=404, detail="Fichier de rapport non trouvé")
        
        # Déterminer le type de média en fonction du format
        media_type = "application/pdf"
        if report.format == ReportFormat.EXCEL:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif report.format == ReportFormat.CSV:
            media_type = "text/csv"
        
        # Générer un nom de fichier pour le téléchargement
        filename = os.path.basename(report.file_path)
        
        # Retourner le fichier
        return FileResponse(
            path=report.file_path,
            media_type=media_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors du téléchargement du rapport", error=str(e), report_id=report_id)
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router_reports.get("/list", response_model=List[ReportResponse])
async def list_reports(
    limit: int = Query(20, description="Nombre maximum de rapports à retourner"),
    offset: int = Query(0, description="Décalage pour la pagination"),
    report_type: Optional[str] = Query(None, description="Filtrer par type de rapport"),
    from_date: Optional[datetime] = Query(None, description="Filtrer par date de début"),
    to_date: Optional[datetime] = Query(None, description="Filtrer par date de fin"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Liste les rapports générés avec filtrage et pagination.
    """
    try:
        # Construire la requête
        query = select(Report).order_by(Report.report_date.desc())
        
        # Appliquer les filtres
        if report_type:
            query = query.filter(Report.metadata["report_type"].astext == report_type)
        
        if from_date:
            query = query.filter(Report.report_date >= from_date)
        
        if to_date:
            query = query.filter(Report.report_date <= to_date)
        
        if status:
            query = query.filter(Report.status == status)
        
        # Appliquer la pagination
        query = query.offset(offset).limit(limit)
        
        # Exécuter la requête
        result = await session.execute(query)
        reports = result.scalars().all()
        
        # Convertir en réponse
        return [
            ReportResponse(
                id=str(report.id),
                name=report.name,
                description=report.description,
                report_date=report.report_date,
                period_start=report.period_start,
                period_end=report.period_end,
                status=report.status.value,
                format=report.format.value,
                file_path=report.file_path if report.status == ReportStatus.COMPLETED else None
            )
            for report in reports
        ]
    
    except Exception as e:
        logger.error("Erreur lors de la récupération de la liste des rapports", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


#
# Routes pour les transactions
#

@router_transactions.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Crée une nouvelle transaction financière.
    """
    # Implémentation pour créer une transaction
    pass


@router_transactions.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str = Path(..., description="ID de la transaction"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Récupère les détails d'une transaction spécifique.
    """
    # Implémentation pour récupérer une transaction
    pass


@router_transactions.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    limit: int = Query(20, description="Nombre maximum de transactions à retourner"),
    offset: int = Query(0, description="Décalage pour la pagination"),
    from_date: Optional[datetime] = Query(None, description="Filtrer par date de début"),
    to_date: Optional[datetime] = Query(None, description="Filtrer par date de fin"),
    source_type: Optional[str] = Query(None, description="Filtrer par type de source"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Liste les transactions avec filtrage et pagination.
    """
    # Implémentation pour lister les transactions
    pass


#
# Routes pour les données financières
#

@router_data.post("/query", response_model=FinancialDataResponse)
async def query_financial_data(
    request: FinancialDataRequest,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Interroge les données financières selon divers critères.
    """
    # Implémentation pour interroger les données financières
    pass


#
# Routes pour l'exportation
#

@router_export.post("/accountant")
async def export_for_accountant(
    from_date: datetime = Form(..., description="Date de début"),
    to_date: datetime = Form(..., description="Date de fin"),
    include_details: bool = Form(True, description="Inclure les détails"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Exporte les données pour le comptable.
    """
    # Implémentation pour l'export comptable
    pass


#
# Routes pour l'administration
#

@router_admin.post("/purge-reports")
async def purge_old_reports(
    older_than_days: int = Query(30, description="Supprimer les rapports plus anciens que ce nombre de jours"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Purge les anciens rapports pour libérer de l'espace disque.
    """
    # Implémentation pour la purge des rapports
    pass


# Configuration de toutes les routes
def setup_routes(app: FastAPI):
    """
    Configure les routes API pour l'application.
    
    Args:
        app (FastAPI): Application FastAPI
    """
    # Ajouter les routers à l'application
    app.include_router(router_reports)
    app.include_router(router_transactions)
    app.include_router(router_data)
    app.include_router(router_export)
    app.include_router(router_admin)
    
    @app.get("/health")
    async def health_check():
        """Vérifie l'état de santé de l'API."""
        return {"status": "ok", "version": "1.0.0"}
    
    @app.get("/")
    async def root():
        """Page d'accueil de l'API."""
        return {"message": "Module de Comptabilité Avancé - Le Vieux Moulin", "docs": "/docs"}
