"""
Planificateur de tâches pour le module de comptabilité.

Ce module gère la planification et l'exécution de tâches récurrentes:
- Génération automatique de rapports
- Synchronisation des données
- Tâches de maintenance
- etc.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from src.config import settings
from src.db.database import get_session
from src.db.models import ReportSchedule, ReportStatus
from src.reports.report_generator import ReportGenerator, ReportType

# Configuration du logger
logger = structlog.get_logger(__name__)

# Initialisation du planificateur
scheduler = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'scheduler.db')}")
    },
    timezone="Europe/Paris"
)


async def generate_scheduled_report(schedule_id: str):
    """
    Génère un rapport à partir d'une programmation.
    
    Args:
        schedule_id (str): ID de la programmation
    """
    logger.info("Génération d'un rapport programmé", schedule_id=schedule_id)
    
    try:
        async with get_session() as session:
            # Récupérer la programmation
            result = await session.execute(
                select(ReportSchedule).where(ReportSchedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()
            
            if not schedule:
                logger.error("Programmation de rapport non trouvée", schedule_id=schedule_id)
                return
            
            if not schedule.is_active:
                logger.info("Programmation de rapport inactive", schedule_id=schedule_id)
                return
            
            # Déterminer la période du rapport en fonction de la fréquence
            end_date = datetime.now()
            start_date = None
            
            if schedule.frequency == "DAILY":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif schedule.frequency == "WEEKLY":
                # Début de la semaine (lundi)
                start_date = end_date - timedelta(days=end_date.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif schedule.frequency == "MONTHLY":
                # Début du mois
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif schedule.frequency == "QUARTERLY":
                # Début du trimestre
                quarter_month = ((end_date.month - 1) // 3) * 3 + 1
                start_date = end_date.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            elif schedule.frequency == "ANNUAL":
                # Début de l'année
                start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                # Valeur par défaut pour les fréquences personnalisées ou non reconnues
                start_date = end_date - timedelta(days=30)
            
            # Définir le type de rapport
            report_type = ReportType(schedule.report_config.get("report_type", "monthly"))
            
            # Récupérer les paramètres supplémentaires
            report_params = schedule.report_config.get("params", {})
            
            # Générer le rapport
            report_generator = ReportGenerator()
            report = await report_generator.generate_report(
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                format=schedule.report_config.get("format", "PDF"),
                template_id=schedule.report_config.get("template_id"),
                report_params=report_params
            )
            
            if not report:
                logger.error("Échec de la génération du rapport programmé", schedule_id=schedule_id)
                return
            
            # Si le rapport est terminé avec succès et qu'il y a des destinataires, envoyer le rapport
            if report.status == ReportStatus.COMPLETED and schedule.recipients:
                from src.utils.email_sender import send_report_email
                
                await send_report_email(
                    report_id=str(report.id),
                    recipients=schedule.recipients,
                    subject=f"Rapport {report_type.value} - {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
                    body=f"Veuillez trouver en pièce jointe le rapport {report_type.value} pour la période du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}."
                )
            
            # Mettre à jour la date de prochaine exécution
            schedule.next_run = get_next_run_time(schedule)
            await session.commit()
            
            logger.info("Rapport programmé généré avec succès", 
                      schedule_id=schedule_id, 
                      report_id=str(report.id),
                      next_run=schedule.next_run)
            
    except Exception as e:
        logger.error("Erreur lors de la génération du rapport programmé", 
                   schedule_id=schedule_id, 
                   error=str(e))


async def sync_data_task():
    """
    Tâche de synchronisation des données avec les sources externes.
    """
    logger.info("Démarrage de la synchronisation des données")
    
    try:
        # Synchronisation des ventes depuis le POS
        from src.collectors.pos_collector import POSCollector
        
        pos_collector = POSCollector()
        await pos_collector.sync_recent_sales(days_back=1)
        
        # Synchronisation des stocks
        # TODO: Implémenter la synchronisation des stocks
        
        # Synchronisation des commandes fournisseurs
        # TODO: Implémenter la synchronisation des commandes
        
        logger.info("Synchronisation des données terminée avec succès")
    
    except Exception as e:
        logger.error("Erreur lors de la synchronisation des données", error=str(e))


async def maintenance_task():
    """
    Tâche de maintenance du système.
    """
    logger.info("Démarrage des tâches de maintenance")
    
    try:
        # Vérification de l'espace disque
        # Purge des anciens fichiers temporaires
        temp_dir = settings.reporting.temp_directory
        
        if os.path.exists(temp_dir):
            now = datetime.now()
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    # Supprimer les fichiers temporaires de plus de 7 jours
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if now - file_time > timedelta(days=7):
                        os.remove(file_path)
                        logger.debug(f"Fichier temporaire supprimé: {file_path}")
        
        # Vérification et maintenance de la base de données
        # TODO: Implémenter la maintenance de la base de données
        
        logger.info("Tâches de maintenance terminées avec succès")
    
    except Exception as e:
        logger.error("Erreur lors des tâches de maintenance", error=str(e))


def get_next_run_time(schedule: ReportSchedule) -> datetime:
    """
    Calcule la date de prochaine exécution d'une programmation.
    
    Args:
        schedule (ReportSchedule): Programmation
    
    Returns:
        datetime: Date de prochaine exécution
    """
    now = datetime.now()
    
    if schedule.frequency == "DAILY":
        # Prochaine exécution demain, à l'heure configurée (par défaut 01:00)
        hour = 1
        minute = 0
        if schedule.report_config and "time" in schedule.report_config:
            time_parts = schedule.report_config["time"].split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
    
    elif schedule.frequency == "WEEKLY":
        # Prochaine exécution lundi prochain, à l'heure configurée (par défaut 01:00)
        day_of_week = 0  # Lundi
        hour = 1
        minute = 0
        
        if schedule.report_config:
            if "day_of_week" in schedule.report_config:
                day_of_week = schedule.report_config["day_of_week"]
            if "time" in schedule.report_config:
                time_parts = schedule.report_config["time"].split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Calculer le nombre de jours jusqu'au prochain jour de la semaine spécifié
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:  # Si nous sommes déjà ce jour-là ou après, aller à la semaine prochaine
            days_ahead += 7
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    
    elif schedule.frequency == "MONTHLY":
        # Prochaine exécution le 1er du mois prochain, à l'heure configurée (par défaut 01:00)
        day = 1
        hour = 1
        minute = 0
        
        if schedule.report_config:
            if "day" in schedule.report_config:
                day = schedule.report_config["day"]
            if "time" in schedule.report_config:
                time_parts = schedule.report_config["time"].split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Calculer le prochain mois
        if now.month == 12:
            next_month = 1
            next_year = now.year + 1
        else:
            next_month = now.month + 1
            next_year = now.year
        
        # Ajuster le jour si nécessaire (ex: 31 pour février)
        import calendar
        _, last_day = calendar.monthrange(next_year, next_month)
        adjusted_day = min(day, last_day)
        
        next_run = now.replace(year=next_year, month=next_month, day=adjusted_day, 
                              hour=hour, minute=minute, second=0, microsecond=0)
    
    elif schedule.frequency == "QUARTERLY":
        # Prochaine exécution le 1er jour du prochain trimestre, à l'heure configurée (par défaut 01:00)
        hour = 1
        minute = 0
        
        if schedule.report_config and "time" in schedule.report_config:
            time_parts = schedule.report_config["time"].split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Déterminer le mois de début du prochain trimestre
        current_quarter = (now.month - 1) // 3
        next_quarter_month = ((current_quarter + 1) % 4) * 3 + 1
        
        # Calculer l'année pour le prochain trimestre
        next_quarter_year = now.year
        if current_quarter == 3:  # Si nous sommes au 4ème trimestre, le prochain trimestre est dans la nouvelle année
            next_quarter_year += 1
        
        next_run = now.replace(year=next_quarter_year, month=next_quarter_month, day=1, 
                              hour=hour, minute=minute, second=0, microsecond=0)
    
    elif schedule.frequency == "ANNUAL":
        # Prochaine exécution le 1er janvier de l'année prochaine, à l'heure configurée (par défaut 01:00)
        month = 1
        day = 1
        hour = 1
        minute = 0
        
        if schedule.report_config:
            if "month" in schedule.report_config:
                month = schedule.report_config["month"]
            if "day" in schedule.report_config:
                day = schedule.report_config["day"]
            if "time" in schedule.report_config:
                time_parts = schedule.report_config["time"].split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        next_year = now.year + 1
        next_run = now.replace(year=next_year, month=month, day=day, 
                              hour=hour, minute=minute, second=0, microsecond=0)
    
    elif schedule.frequency == "CUSTOM" and schedule.cron_expression:
        # Prochaine exécution selon l'expression cron
        from croniter import croniter
        
        # Utiliser croniter pour calculer la prochaine exécution
        cron = croniter(schedule.cron_expression, now)
        next_run = cron.get_next(datetime)
    
    else:
        # Par défaut: prochaine exécution dans 24 heures
        next_run = now + timedelta(days=1)
    
    return next_run


async def load_scheduled_tasks():
    """
    Charge et planifie toutes les tâches programmées depuis la base de données.
    """
    logger.info("Chargement des tâches programmées")
    
    try:
        async with get_session() as session:
            # Récupérer toutes les programmations de rapports actives
            result = await session.execute(
                select(ReportSchedule).where(ReportSchedule.is_active == True)
            )
            schedules = result.scalars().all()
            
            if not schedules:
                logger.info("Aucune programmation de rapport active trouvée")
                return
            
            # Planifier chaque rapport
            for schedule in schedules:
                # Calculer la prochaine exécution si elle n'est pas définie
                if not schedule.next_run:
                    schedule.next_run = get_next_run_time(schedule)
                    await session.commit()
                
                # Si l'exécution est dans le passé, recalculer la prochaine exécution
                if schedule.next_run < datetime.now():
                    schedule.next_run = get_next_run_time(schedule)
                    await session.commit()
                
                # Planifier le job
                if schedule.frequency == "CUSTOM" and schedule.cron_expression:
                    # Utiliser l'expression cron pour la planification
                    scheduler.add_job(
                        generate_scheduled_report,
                        'cron',
                        args=[str(schedule.id)],
                        id=f"report_{schedule.id}",
                        replace_existing=True,
                        **parse_cron_expression(schedule.cron_expression)
                    )
                else:
                    # Utiliser la date de prochaine exécution
                    scheduler.add_job(
                        generate_scheduled_report,
                        'date',
                        args=[str(schedule.id)],
                        id=f"report_{schedule.id}",
                        run_date=schedule.next_run,
                        replace_existing=True
                    )
                
                logger.info(
                    "Rapport programmé chargé", 
                    schedule_id=str(schedule.id),
                    name=schedule.name,
                    frequency=schedule.frequency,
                    next_run=schedule.next_run
                )
    
    except Exception as e:
        logger.error("Erreur lors du chargement des tâches programmées", error=str(e))


def parse_cron_expression(cron_expression: str) -> Dict:
    """
    Convertit une expression cron en paramètres pour APScheduler.
    
    Args:
        cron_expression (str): Expression cron (format: "minute hour day_of_month month day_of_week")
    
    Returns:
        Dict: Paramètres pour APScheduler
    """
    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError(f"Expression cron invalide: {cron_expression}. Format attendu: 'minute hour day_of_month month day_of_week'")
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day': parts[2],
        'month': parts[3],
        'day_of_week': parts[4]
    }


def setup_scheduler():
    """
    Configure et démarre le planificateur de tâches.
    """
    logger.info("Configuration du planificateur de tâches")
    
    # Ajouter les tâches récurrentes du système
    
    # Synchronisation des données toutes les heures
    scheduler.add_job(
        sync_data_task,
        'interval',
        hours=1,
        id='sync_data',
        replace_existing=True
    )
    
    # Tâche de maintenance tous les jours à 3h du matin
    scheduler.add_job(
        maintenance_task,
        'cron',
        hour=3,
        minute=0,
        id='maintenance',
        replace_existing=True
    )
    
    # Charger les tâches programmées depuis la base de données
    scheduler.add_job(
        load_scheduled_tasks,
        'date',
        run_date=datetime.now() + timedelta(seconds=10),
        id='load_scheduled_tasks',
        replace_existing=True
    )
    
    # Démarrer le planificateur
    scheduler.start()
    logger.info("Planificateur de tâches démarré")
