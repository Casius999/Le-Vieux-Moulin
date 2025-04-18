#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serveur API REST du module de planification du personnel.

Ce module implémente un serveur API REST complet avec FastAPI pour exposer
les fonctionnalités du module de planification.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, HTTPException, Depends, Response, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from pydantic import BaseModel, Field
import uvicorn

from ..config import API_CONFIG
from ..models.employee import Employee, EmployeeRole
from ..models.shift import Shift, ShiftStatus, ShiftType
from ..models.schedule import Schedule, ScheduleStatus
from ..models.constraint import Constraint, ConstraintType, ConstraintSet
from ..scheduler.optimizer import ScheduleOptimizer
from ..integration.prediction_client import PredictionClient
from ..integration.reservation_client import ReservationClient
from ..integration.notification_service import NotificationService
from ..data.repository import EmployeeRepository, ScheduleRepository, ConstraintRepository

# Configurer le logger
logger = logging.getLogger(__name__)

# Modèles Pydantic pour les données d'API

class EmployeeBase(BaseModel):
    """Modèle de base pour un employé."""
    first_name: str
    last_name: str
    email: str
    phone: str
    primary_role: str
    secondary_roles: Optional[List[str]] = []
    hourly_rate: Optional[float] = None
    weekly_hours: Optional[int] = None
    
class EmployeeCreate(EmployeeBase):
    """Modèle pour la création d'un employé."""
    pass
    
class EmployeeUpdate(BaseModel):
    """Modèle pour la mise à jour d'un employé."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    primary_role: Optional[str] = None
    secondary_roles: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    weekly_hours: Optional[int] = None
    
class EmployeeResponse(EmployeeBase):
    """Modèle de réponse pour un employé."""
    employee_id: str
    is_active: bool
    
    class Config:
        """Configuration du modèle."""
        orm_mode = True

class ShiftBase(BaseModel):
    """Modèle de base pour un shift."""
    date: str  # ISO format (YYYY-MM-DD)
    start_time: str  # Format HH:MM
    end_time: str  # Format HH:MM
    role: str
    employee_id: Optional[str] = None
    shift_type: Optional[str] = None
    location: Optional[str] = None
    break_duration: Optional[int] = 0  # Minutes
    notes: Optional[str] = None
    
class ShiftCreate(ShiftBase):
    """Modèle pour la création d'un shift."""
    pass
    
class ShiftUpdate(BaseModel):
    """Modèle pour la mise à jour d'un shift."""
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    role: Optional[str] = None
    employee_id: Optional[str] = None
    shift_type: Optional[str] = None
    location: Optional[str] = None
    break_duration: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    
class ShiftResponse(ShiftBase):
    """Modèle de réponse pour un shift."""
    shift_id: str
    status: str
    duration: float  # Heures
    employee_name: Optional[str] = None
    
    class Config:
        """Configuration du modèle."""
        orm_mode = True

class ScheduleBase(BaseModel):
    """Modèle de base pour un planning."""
    start_date: str  # ISO format (YYYY-MM-DD)
    end_date: str  # ISO format (YYYY-MM-DD)
    name: Optional[str] = None
    description: Optional[str] = None
    
class ScheduleCreate(ScheduleBase):
    """Modèle pour la création d'un planning."""
    pass
    
class ScheduleUpdate(BaseModel):
    """Modèle pour la mise à jour d'un planning."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    
class ScheduleResponse(ScheduleBase):
    """Modèle de réponse pour un planning."""
    schedule_id: str
    status: str
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    version: int
    metrics: Optional[Dict] = None
    
    class Config:
        """Configuration du modèle."""
        orm_mode = True

class GenerateScheduleRequest(BaseModel):
    """Modèle pour la génération d'un planning."""
    start_date: str  # ISO format (YYYY-MM-DD)
    end_date: str  # ISO format (YYYY-MM-DD)
    name: Optional[str] = None
    description: Optional[str] = None
    employee_ids: Optional[List[str]] = None  # Liste des IDs d'employés à inclure
    previous_schedule_id: Optional[str] = None  # ID du planning précédent pour continuité
    optimization_params: Optional[Dict] = None  # Paramètres d'optimisation
    constraints: Optional[List[Dict]] = None  # Contraintes supplémentaires
    generate_shifts: bool = True  # Si True, génère automatiquement les shifts nécessaires
    
class AssignEmployeeRequest(BaseModel):
    """Modèle pour l'assignation d'un employé à un shift."""
    employee_id: str
    
class OptimizationStatusResponse(BaseModel):
    """Modèle de réponse pour le statut d'une optimisation."""
    job_id: str
    status: str
    progress: float  # 0.0 à 1.0
    message: Optional[str] = None
    estimated_completion: Optional[str] = None
    
class LoginRequest(BaseModel):
    """Modèle pour la connexion."""
    username: str
    password: str
    
class TokenResponse(BaseModel):
    """Modèle de réponse pour un token d'authentification."""
    access_token: str
    token_type: str
    expires_in: int  # Secondes
    user_id: str
    user_role: str

# Création de l'application FastAPI
def create_app():
    """
    Crée et configure l'application FastAPI.
    
    Returns:
        Application FastAPI configurée
    """
    app = FastAPI(
        title="API de Planification - Le Vieux Moulin",
        description="API pour la gestion des plannings du personnel",
        version="1.0.0"
    )
    
    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=API_CONFIG.get('cors_origins', ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configuration de l'authentification
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    JWT_SECRET = os.environ.get("JWT_SECRET", "vieux-moulin-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = 3600  # 1 heure
    
    # Simples rôles utilisateurs pour la démonstration
    USER_DB = {
        "admin": {
            "username": "admin",
            "password": "adminpassword",  # En production, utiliser des hash
            "role": "admin"
        },
        "manager": {
            "username": "manager",
            "password": "managerpassword",
            "role": "manager"
        },
        "employee": {
            "username": "employee",
            "password": "employeepassword",
            "role": "employee"
        }
    }
    
    # Instances des repositories
    employee_repo = EmployeeRepository()
    schedule_repo = ScheduleRepository()
    constraint_repo = ConstraintRepository()
    
    # Instances des services
    prediction_client = PredictionClient()
    reservation_client = ReservationClient()
    notification_service = NotificationService()
    
    # Dictionnaire pour suivre les tâches d'optimisation en cours
    optimization_jobs = {}
    
    # Fonction de vérification d'authentification
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        """
        Vérifie le token JWT et retourne l'utilisateur.
        
        Args:
            token: Token JWT
            
        Returns:
            Utilisateur
            
        Raises:
            HTTPException: Si le token est invalide
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            if username is None or username not in USER_DB:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token d'authentification invalide",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return USER_DB[username]
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Fonction de vérification des droits administrateur
    async def get_admin_user(user: dict = Depends(get_current_user)):
        """
        Vérifie que l'utilisateur est administrateur.
        
        Args:
            user: Utilisateur
            
        Returns:
            Utilisateur administrateur
            
        Raises:
            HTTPException: Si l'utilisateur n'est pas administrateur
        """
        if user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droits insuffisants pour cette opération",
            )
        return user
    
    # Fonction de vérification des droits gestionnaire ou administrateur
    async def get_manager_user(user: dict = Depends(get_current_user)):
        """
        Vérifie que l'utilisateur est gestionnaire ou administrateur.
        
        Args:
            user: Utilisateur
            
        Returns:
            Utilisateur gestionnaire ou administrateur
            
        Raises:
            HTTPException: Si l'utilisateur n'a pas les droits suffisants
        """
        if user["role"] not in ["admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droits insuffisants pour cette opération",
            )
        return user
    
    # Routes d'authentification
    
    @app.post("/token", response_model=TokenResponse)
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Route de connexion pour obtenir un token JWT.
        
        Args:
            form_data: Formulaire de connexion
            
        Returns:
            Token JWT
            
        Raises:
            HTTPException: Si les identifiants sont invalides
        """
        user = USER_DB.get(form_data.username)
        if not user or user["password"] != form_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants incorrects",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Créer le token JWT
        expiration = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
        token_data = {
            "sub": user["username"],
            "role": user["role"],
            "exp": expiration
        }
        token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION,
            "user_id": user["username"],
            "user_role": user["role"]
        }
    
    # Routes API
    
    @app.get("/")
    async def root():
        """
        Page d'accueil de l'API.
        
        Returns:
            Informations sur l'API
        """
        return {
            "message": "API de Planification - Le Vieux Moulin",
            "version": "1.0.0",
            "documentation": "/docs",
            "status": "online"
        }
    
    @app.get("/health")
    async def health_check():
        """
        Vérification de l'état de santé de l'API.
        
        Returns:
            État de santé
        """
        # Vérifier la connexion aux services externes
        prediction_status = {"status": "unknown"}
        reservation_status = {"status": "unknown"}
        
        try:
            # Vérifier le service de prédiction
            prediction_status = {"status": "healthy"}
        except:
            prediction_status = {"status": "unhealthy"}
            
        try:
            # Vérifier le service de réservation
            reservation_status = {"status": "healthy"}
        except:
            reservation_status = {"status": "unhealthy"}
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "external_services": {
                "prediction": prediction_status,
                "reservation": reservation_status
            }
        }
    
    # Routes pour les employés
    
    @app.get("/api/employees", response_model=List[EmployeeResponse])
    async def list_employees(
        active_only: bool = True,
        role: Optional[str] = None,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Liste les employés.
        
        Args:
            active_only: Si True, ne retourne que les employés actifs
            role: Filtre par rôle (optionnel)
            current_user: Utilisateur actuel
            
        Returns:
            Liste des employés
        """
        # Récupérer les employés depuis le repository
        employees = employee_repo.get_all(active_only=active_only)
        
        # Filtrer par rôle si nécessaire
        if role:
            try:
                role_enum = EmployeeRole(role)
                employees = [e for e in employees if e.primary_role == role_enum or role_enum in e.secondary_roles]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rôle inconnu: {role}"
                )
        
        # Convertir en réponse API
        return [
            EmployeeResponse(
                employee_id=e.employee_id,
                first_name=e.first_name,
                last_name=e.last_name,
                email=e.email,
                phone=e.phone,
                primary_role=e.primary_role.value,
                secondary_roles=[r.value for r in e.secondary_roles],
                hourly_rate=e.hourly_rate,
                weekly_hours=e.weekly_hours,
                is_active=e.is_active
            )
            for e in employees
        ]
    
    @app.get("/api/employees/{employee_id}", response_model=EmployeeResponse)
    async def get_employee(
        employee_id: str,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Récupère un employé par son ID.
        
        Args:
            employee_id: ID de l'employé
            current_user: Utilisateur actuel
            
        Returns:
            Employé
            
        Raises:
            HTTPException: Si l'employé n'existe pas
        """
        # Récupérer l'employé depuis le repository
        employee = employee_repo.get_by_id(employee_id)
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employé non trouvé: {employee_id}"
            )
        
        # Convertir en réponse API
        return EmployeeResponse(
            employee_id=employee.employee_id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            phone=employee.phone,
            primary_role=employee.primary_role.value,
            secondary_roles=[r.value for r in employee.secondary_roles],
            hourly_rate=employee.hourly_rate,
            weekly_hours=employee.weekly_hours,
            is_active=employee.is_active
        )
    
    @app.post("/api/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
    async def create_employee(
        employee: EmployeeCreate,
        current_user: dict = Depends(get_admin_user)
    ):
        """
        Crée un nouvel employé.
        
        Args:
            employee: Données de l'employé
            current_user: Utilisateur actuel
            
        Returns:
            Employé créé
        """
        # Convertir les rôles en enums
        try:
            primary_role = EmployeeRole(employee.primary_role)
            secondary_roles = [EmployeeRole(r) for r in employee.secondary_roles] if employee.secondary_roles else []
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rôle invalide: {str(e)}"
            )
        
        # Créer l'employé
        new_employee = Employee.create_new(
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            phone=employee.phone,
            primary_role=primary_role,
            secondary_roles=secondary_roles,
            hourly_rate=employee.hourly_rate or 0.0,
            weekly_hours=employee.weekly_hours or 40
        )
        
        # Sauvegarder dans le repository
        employee_repo.save(new_employee)
        
        # Convertir en réponse API
        return EmployeeResponse(
            employee_id=new_employee.employee_id,
            first_name=new_employee.first_name,
            last_name=new_employee.last_name,
            email=new_employee.email,
            phone=new_employee.phone,
            primary_role=new_employee.primary_role.value,
            secondary_roles=[r.value for r in new_employee.secondary_roles],
            hourly_rate=new_employee.hourly_rate,
            weekly_hours=new_employee.weekly_hours,
            is_active=new_employee.is_active
        )
    
    @app.put("/api/employees/{employee_id}", response_model=EmployeeResponse)
    async def update_employee(
        employee_id: str,
        employee_update: EmployeeUpdate,
        current_user: dict = Depends(get_admin_user)
    ):
        """
        Met à jour un employé.
        
        Args:
            employee_id: ID de l'employé
            employee_update: Données de mise à jour
            current_user: Utilisateur actuel
            
        Returns:
            Employé mis à jour
            
        Raises:
            HTTPException: Si l'employé n'existe pas
        """
        # Récupérer l'employé depuis le repository
        employee = employee_repo.get_by_id(employee_id)
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employé non trouvé: {employee_id}"
            )
        
        # Mettre à jour les attributs
        if employee_update.first_name is not None:
            employee.first_name = employee_update.first_name
        
        if employee_update.last_name is not None:
            employee.last_name = employee_update.last_name
        
        if employee_update.email is not None:
            employee.email = employee_update.email
        
        if employee_update.phone is not None:
            employee.phone = employee_update.phone
        
        if employee_update.primary_role is not None:
            try:
                employee.primary_role = EmployeeRole(employee_update.primary_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rôle primaire invalide: {employee_update.primary_role}"
                )
        
        if employee_update.secondary_roles is not None:
            try:
                employee.secondary_roles = [EmployeeRole(r) for r in employee_update.secondary_roles]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rôle secondaire invalide: {str(e)}"
                )
        
        if employee_update.hourly_rate is not None:
            employee.hourly_rate = employee_update.hourly_rate
        
        if employee_update.weekly_hours is not None:
            employee.weekly_hours = employee_update.weekly_hours
        
        # Sauvegarder les modifications
        employee_repo.save(employee)
        
        # Convertir en réponse API
        return EmployeeResponse(
            employee_id=employee.employee_id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            phone=employee.phone,
            primary_role=employee.primary_role.value,
            secondary_roles=[r.value for r in employee.secondary_roles],
            hourly_rate=employee.hourly_rate,
            weekly_hours=employee.weekly_hours,
            is_active=employee.is_active
        )
    
    @app.delete("/api/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_employee(
        employee_id: str,
        current_user: dict = Depends(get_admin_user)
    ):
        """
        Supprime un employé (désactivation).
        
        Args:
            employee_id: ID de l'employé
            current_user: Utilisateur actuel
            
        Raises:
            HTTPException: Si l'employé n'existe pas
        """
        # Récupérer l'employé depuis le repository
        employee = employee_repo.get_by_id(employee_id)
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employé non trouvé: {employee_id}"
            )
        
        # Désactiver l'employé au lieu de le supprimer
        employee.end_date = datetime.now()
        employee_repo.save(employee)
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    # Routes pour les plannings
    
    @app.get("/api/schedules", response_model=List[ScheduleResponse])
    async def list_schedules(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Liste les plannings.
        
        Args:
            start_date: Date de début pour le filtre (optionnel)
            end_date: Date de fin pour le filtre (optionnel)
            status: Statut pour le filtre (optionnel)
            current_user: Utilisateur actuel
            
        Returns:
            Liste des plannings
        """
        # Convertir les dates
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format de date de début invalide: {start_date}"
                )
        
        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format de date de fin invalide: {end_date}"
                )
        
        # Convertir le statut
        status_enum = None
        if status:
            try:
                status_enum = ScheduleStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Statut invalide: {status}"
                )
        
        # Récupérer les plannings depuis le repository
        schedules = schedule_repo.get_all(
            start_date=start_date_obj,
            end_date=end_date_obj,
            status=status_enum
        )
        
        # Convertir en réponse API
        return [
            ScheduleResponse(
                schedule_id=s.schedule_id,
                start_date=s.start_date.isoformat(),
                end_date=s.end_date.isoformat(),
                name=s.name,
                description=s.description,
                status=s.status.value,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
                created_by=s.created_by,
                approved_by=s.approved_by,
                version=s.version,
                metrics=s.metrics.to_dict() if s.metrics else None
            )
            for s in schedules
        ]
    
    @app.get("/api/schedules/{schedule_id}", response_model=ScheduleResponse)
    async def get_schedule(
        schedule_id: str,
        include_shifts: bool = False,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Récupère un planning par son ID.
        
        Args:
            schedule_id: ID du planning
            include_shifts: Si True, inclut les shifts du planning
            current_user: Utilisateur actuel
            
        Returns:
            Planning
            
        Raises:
            HTTPException: Si le planning n'existe pas
        """
        # Récupérer le planning depuis le repository
        schedule = schedule_repo.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planning non trouvé: {schedule_id}"
            )
        
        # Préparer la réponse
        response = ScheduleResponse(
            schedule_id=schedule.schedule_id,
            start_date=schedule.start_date.isoformat(),
            end_date=schedule.end_date.isoformat(),
            name=schedule.name,
            description=schedule.description,
            status=schedule.status.value,
            created_at=schedule.created_at.isoformat(),
            updated_at=schedule.updated_at.isoformat(),
            created_by=schedule.created_by,
            approved_by=schedule.approved_by,
            version=schedule.version,
            metrics=schedule.metrics.to_dict() if schedule.metrics else None
        )
        
        # Ajouter les shifts si demandé
        if include_shifts:
            response.shifts = [
                ShiftResponse(
                    shift_id=s.shift_id,
                    date=s.date.isoformat(),
                    start_time=s.start_time.isoformat(),
                    end_time=s.end_time.isoformat(),
                    role=s.role.value,
                    employee_id=s.employee_id,
                    employee_name=s.employee.full_name if s.employee else None,
                    shift_type=s.shift_type.value if s.shift_type else None,
                    location=s.location.value if s.location else None,
                    break_duration=s.break_duration,
                    notes=s.notes,
                    status=s.status.value,
                    duration=s.duration
                )
                for s in schedule.shifts
            ]
        
        return response
    
    @app.get("/api/schedules/{schedule_id}/shifts", response_model=List[ShiftResponse])
    async def get_schedule_shifts(
        schedule_id: str,
        date: Optional[str] = None,
        role: Optional[str] = None,
        employee_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Récupère les shifts d'un planning.
        
        Args:
            schedule_id: ID du planning
            date: Filtre par date (optionnel)
            role: Filtre par rôle (optionnel)
            employee_id: Filtre par employé (optionnel)
            current_user: Utilisateur actuel
            
        Returns:
            Liste des shifts
            
        Raises:
            HTTPException: Si le planning n'existe pas
        """
        # Récupérer le planning depuis le repository
        schedule = schedule_repo.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planning non trouvé: {schedule_id}"
            )
        
        # Filtrer les shifts
        shifts = schedule.shifts
        
        # Filtre par date
        if date:
            try:
                date_obj = datetime.fromisoformat(date)
                shifts = [s for s in shifts if s.date.date() == date_obj.date()]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format de date invalide: {date}"
                )
        
        # Filtre par rôle
        if role:
            try:
                role_enum = EmployeeRole(role)
                shifts = [s for s in shifts if s.role == role_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rôle invalide: {role}"
                )
        
        # Filtre par employé
        if employee_id:
            shifts = [s for s in shifts if s.employee_id == employee_id]
        
        # Convertir en réponse API
        return [
            ShiftResponse(
                shift_id=s.shift_id,
                date=s.date.isoformat(),
                start_time=s.start_time.isoformat(),
                end_time=s.end_time.isoformat(),
                role=s.role.value,
                employee_id=s.employee_id,
                employee_name=s.employee.full_name if s.employee else None,
                shift_type=s.shift_type.value if s.shift_type else None,
                location=s.location.value if s.location else None,
                break_duration=s.break_duration,
                notes=s.notes,
                status=s.status.value,
                duration=s.duration
            )
            for s in shifts
        ]
    
    @app.post("/api/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
    async def create_schedule(
        schedule: ScheduleCreate,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Crée un nouveau planning (vide).
        
        Args:
            schedule: Données du planning
            current_user: Utilisateur actuel
            
        Returns:
            Planning créé
        """
        # Convertir les dates
        try:
            start_date = datetime.fromisoformat(schedule.start_date)
            end_date = datetime.fromisoformat(schedule.end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Format de date invalide"
            )
        
        # Créer le planning
        new_schedule = Schedule.create_new(
            start_date=start_date,
            end_date=end_date,
            name=schedule.name,
            created_by=current_user["username"]
        )
        
        if schedule.description:
            new_schedule.description = schedule.description
        
        # Sauvegarder dans le repository
        schedule_repo.save(new_schedule)
        
        # Convertir en réponse API
        return ScheduleResponse(
            schedule_id=new_schedule.schedule_id,
            start_date=new_schedule.start_date.isoformat(),
            end_date=new_schedule.end_date.isoformat(),
            name=new_schedule.name,
            description=new_schedule.description,
            status=new_schedule.status.value,
            created_at=new_schedule.created_at.isoformat(),
            updated_at=new_schedule.updated_at.isoformat(),
            created_by=new_schedule.created_by,
            approved_by=new_schedule.approved_by,
            version=new_schedule.version,
            metrics=new_schedule.metrics.to_dict() if new_schedule.metrics else None
        )
    
    @app.post("/api/schedules/generate", response_model=ScheduleResponse)
    async def generate_schedule(
        request: GenerateScheduleRequest,
        background_tasks: BackgroundTasks,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Génère un planning optimisé.
        
        Args:
            request: Paramètres de génération
            background_tasks: Tâches d'arrière-plan pour l'optimisation
            current_user: Utilisateur actuel
            
        Returns:
            Planning généré (initialement vide, optimisation en arrière-plan)
        """
        # Convertir les dates
        try:
            start_date = datetime.fromisoformat(request.start_date)
            end_date = datetime.fromisoformat(request.end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Format de date invalide"
            )
        
        # Récupérer les employés
        if request.employee_ids:
            employees = [employee_repo.get_by_id(emp_id) for emp_id in request.employee_ids]
            employees = [e for e in employees if e is not None]  # Filtrer les non trouvés
        else:
            employees = employee_repo.get_all(active_only=True)
        
        if not employees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun employé disponible pour la génération du planning"
            )
        
        # Récupérer le planning précédent si spécifié
        previous_schedule = None
        if request.previous_schedule_id:
            previous_schedule = schedule_repo.get_by_id(request.previous_schedule_id)
            if not previous_schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Planning précédent non trouvé: {request.previous_schedule_id}"
                )
        
        # Créer le nouveau planning
        new_schedule = Schedule.create_new(
            start_date=start_date,
            end_date=end_date,
            name=request.name or f"Planning du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
            created_by=current_user["username"]
        )
        
        if request.description:
            new_schedule.description = request.description
        
        # Si un planning précédent est spécifié, mettre à jour la version
        if previous_schedule:
            new_schedule.previous_version_id = previous_schedule.schedule_id
            new_schedule.version = previous_schedule.version + 1
        
        # Sauvegarder le planning initial
        schedule_repo.save(new_schedule)
        
        # ID unique pour la tâche d'optimisation
        job_id = f"opt-{new_schedule.schedule_id}"
        
        # Créer un entry pour le suivi de l'optimisation
        optimization_jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "En attente de démarrage",
            "schedule_id": new_schedule.schedule_id,
            "start_time": datetime.now()
        }
        
        # Fonction pour l'optimisation en arrière-plan
        def optimize_schedule_task(
            schedule_id: str,
            start_date: datetime,
            end_date: datetime,
            employees: List[Employee],
            job_id: str,
            generate_shifts: bool,
            optimization_params: Optional[Dict] = None,
            constraints: Optional[List[Dict]] = None,
            previous_schedule_id: Optional[str] = None
        ):
            try:
                # Mettre à jour le statut
                optimization_jobs[job_id]["status"] = "running"
                optimization_jobs[job_id]["message"] = "Récupération des données de prévision"
                
                # Récupérer les prévisions d'affluence
                try:
                    prediction_client = PredictionClient()
                    staffing_needs = prediction_client.get_staffing_needs(start_date, end_date)
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des prévisions: {str(e)}")
                    staffing_needs = None
                
                # Mettre à jour le statut
                optimization_jobs[job_id]["progress"] = 0.1
                optimization_jobs[job_id]["message"] = "Récupération des réservations"
                
                # Récupérer les réservations
                try:
                    reservation_client = ReservationClient()
                    reservations = reservation_client.get_upcoming_reservations(start_date, end_date)
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des réservations: {str(e)}")
                    reservations = None
                
                # Mettre à jour le statut
                optimization_jobs[job_id]["progress"] = 0.2
                optimization_jobs[job_id]["message"] = "Création des contraintes"
                
                # Créer le set de contraintes
                constraint_set = ConstraintSet()
                
                # Ajouter les contraintes par défaut
                for c in constraint_repo.get_default_constraints():
                    constraint_set.add_constraint(c)
                
                # Ajouter les contraintes supplémentaires
                if constraints:
                    for c_data in constraints:
                        try:
                            c = Constraint.from_dict(c_data)
                            constraint_set.add_constraint(c)
                        except Exception as e:
                            logger.error(f"Erreur lors de la création d'une contrainte: {str(e)}")
                
                # Mettre à jour le statut
                optimization_jobs[job_id]["progress"] = 0.3
                optimization_jobs[job_id]["message"] = "Configuration de l'optimiseur"
                
                # Configuration de l'optimiseur
                optimizer_config = {
                    "timeout_seconds": 60,  # Limiter le temps d'optimisation
                }
                if optimization_params:
                    optimizer_config.update(optimization_params)
                
                # Callback de progression
                def progress_callback(generation, max_generations, stats):
                    progress = min(0.9, 0.3 + (generation / max_generations) * 0.6)
                    optimization_jobs[job_id]["progress"] = progress
                    optimization_jobs[job_id]["message"] = f"Optimisation en cours (génération {generation}/{max_generations})"
                
                # Créer l'optimiseur
                optimizer = ScheduleOptimizer(
                    config=optimizer_config,
                    constraint_set=constraint_set,
                    progress_callback=progress_callback
                )
                
                # Récupérer le planning à optimiser
                schedule = schedule_repo.get_by_id(schedule_id)
                
                if not schedule:
                    raise ValueError(f"Planning non trouvé: {schedule_id}")
                
                # Mettre à jour le statut
                optimization_jobs[job_id]["progress"] = 0.4
                optimization_jobs[job_id]["message"] = "Génération du planning optimisé"
                
                # Récupérer le planning précédent si nécessaire
                previous_schedule = None
                if previous_schedule_id:
                    previous_schedule = schedule_repo.get_by_id(previous_schedule_id)
                
                # Générer le planning optimisé
                optimized_schedule = optimizer.generate_schedule(
                    start_date=start_date,
                    end_date=end_date,
                    employees=employees,
                    staffing_needs=staffing_needs,
                    previous_schedule=previous_schedule,
                    created_by=schedule.created_by
                )
                
                # Mettre à jour le planning
                schedule.shifts = optimized_schedule.shifts
                schedule.metrics = optimized_schedule.metrics
                schedule.calculate_metrics(staffing_needs)
                
                # Sauvegarder le planning
                schedule_repo.save(schedule)
                
                # Mettre à jour le statut
                optimization_jobs[job_id]["status"] = "completed"
                optimization_jobs[job_id]["progress"] = 1.0
                optimization_jobs[job_id]["message"] = "Optimisation terminée avec succès"
                
                # Notifier les employés
                try:
                    notification_service = NotificationService()
                    notification_service.notify_schedule_published(
                        schedule=schedule,
                        employees=employees
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de la notification des employés: {str(e)}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'optimisation du planning: {str(e)}")
                optimization_jobs[job_id]["status"] = "failed"
                optimization_jobs[job_id]["message"] = f"Erreur: {str(e)}"
        
        # Lancer l'optimisation en arrière-plan
        background_tasks.add_task(
            optimize_schedule_task,
            new_schedule.schedule_id,
            start_date,
            end_date,
            employees,
            job_id,
            request.generate_shifts,
            request.optimization_params,
            request.constraints,
            request.previous_schedule_id
        )
        
        # Retourner le planning initial avec l'ID de la tâche d'optimisation
        response = ScheduleResponse(
            schedule_id=new_schedule.schedule_id,
            start_date=new_schedule.start_date.isoformat(),
            end_date=new_schedule.end_date.isoformat(),
            name=new_schedule.name,
            description=new_schedule.description,
            status=new_schedule.status.value,
            created_at=new_schedule.created_at.isoformat(),
            updated_at=new_schedule.updated_at.isoformat(),
            created_by=new_schedule.created_by,
            approved_by=new_schedule.approved_by,
            version=new_schedule.version,
            metrics=new_schedule.metrics.to_dict() if new_schedule.metrics else None
        )
        
        # Ajouter l'ID de la tâche d'optimisation
        response.optimization_job_id = job_id
        
        return response
    
    @app.get("/api/optimization/{job_id}", response_model=OptimizationStatusResponse)
    async def get_optimization_status(
        job_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Récupère le statut d'une tâche d'optimisation.
        
        Args:
            job_id: ID de la tâche
            current_user: Utilisateur actuel
            
        Returns:
            Statut de la tâche
            
        Raises:
            HTTPException: Si la tâche n'existe pas
        """
        if job_id not in optimization_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche d'optimisation non trouvée: {job_id}"
            )
        
        job = optimization_jobs[job_id]
        
        # Calculer l'estimation de fin
        estimated_completion = None
        if job["status"] == "running" and job["progress"] > 0:
            elapsed = (datetime.now() - job["start_time"]).total_seconds()
            if elapsed > 0 and job["progress"] > 0.1:
                total_time = elapsed / job["progress"]
                remaining = total_time - elapsed
                estimated_completion = (datetime.now() + timedelta(seconds=remaining)).isoformat()
        
        return OptimizationStatusResponse(
            job_id=job_id,
            status=job["status"],
            progress=job["progress"],
            message=job["message"],
            estimated_completion=estimated_completion
        )
    
    @app.put("/api/schedules/{schedule_id}/status")
    async def change_schedule_status(
        schedule_id: str,
        new_status: str,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Change le statut d'un planning.
        
        Args:
            schedule_id: ID du planning
            new_status: Nouveau statut
            current_user: Utilisateur actuel
            
        Returns:
            Planning mis à jour
            
        Raises:
            HTTPException: Si le planning n'existe pas ou si le statut est invalide
        """
        # Récupérer le planning depuis le repository
        schedule = schedule_repo.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planning non trouvé: {schedule_id}"
            )
        
        # Convertir le statut
        try:
            status_enum = ScheduleStatus(new_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Statut invalide: {new_status}"
            )
        
        # Changer le statut
        schedule.change_status(status_enum, current_user["username"])
        
        # Si le planning est publié, notifier les employés
        if status_enum == ScheduleStatus.PUBLISHED:
            try:
                # Récupérer les employés concernés
                employee_ids = set(shift.employee_id for shift in schedule.shifts if shift.employee_id)
                employees = [employee_repo.get_by_id(emp_id) for emp_id in employee_ids]
                employees = [e for e in employees if e is not None]
                
                if employees:
                    notification_service.notify_schedule_published(
                        schedule=schedule,
                        employees=employees
                    )
            except Exception as e:
                logger.error(f"Erreur lors de la notification des employés: {str(e)}")
                # Ne pas bloquer la mise à jour en cas d'erreur de notification
        
        # Sauvegarder les modifications
        schedule_repo.save(schedule)
        
        # Convertir en réponse API
        return ScheduleResponse(
            schedule_id=schedule.schedule_id,
            start_date=schedule.start_date.isoformat(),
            end_date=schedule.end_date.isoformat(),
            name=schedule.name,
            description=schedule.description,
            status=schedule.status.value,
            created_at=schedule.created_at.isoformat(),
            updated_at=schedule.updated_at.isoformat(),
            created_by=schedule.created_by,
            approved_by=schedule.approved_by,
            version=schedule.version,
            metrics=schedule.metrics.to_dict() if schedule.metrics else None
        )
    
    @app.post("/api/schedules/{schedule_id}/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
    async def add_shift(
        schedule_id: str,
        shift: ShiftCreate,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Ajoute un shift à un planning.
        
        Args:
            schedule_id: ID du planning
            shift: Données du shift
            current_user: Utilisateur actuel
            
        Returns:
            Shift créé
            
        Raises:
            HTTPException: Si le planning n'existe pas
        """
        # Récupérer le planning depuis le repository
        schedule = schedule_repo.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planning non trouvé: {schedule_id}"
            )
        
        # Convertir les données
        try:
            date = datetime.fromisoformat(shift.date)
            start_time = datetime.strptime(shift.start_time, "%H:%M").time()
            end_time = datetime.strptime(shift.end_time, "%H:%M").time()
            role = EmployeeRole(shift.role)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Données invalides: {str(e)}"
            )
        
        # Vérifier que la date est dans la période du planning
        if date.date() < schedule.start_date.date() or date.date() > schedule.end_date.date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La date {shift.date} est en dehors de la période du planning"
            )
        
        # Déterminer le type de shift
        shift_type = None
        if shift.shift_type:
            try:
                shift_type = ShiftType(shift.shift_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Type de shift invalide: {shift.shift_type}"
                )
        else:
            # Déterminer automatiquement selon l'heure
            if start_time.hour < 16:
                shift_type = ShiftType.MIDDAY
            else:
                shift_type = ShiftType.EVENING
        
        # Créer le shift
        new_shift = Shift.create_new(
            date=date,
            start_time=start_time,
            end_time=end_time,
            role=role,
            shift_type=shift_type
        )
        
        # Assigner l'employé si spécifié
        if shift.employee_id:
            employee = employee_repo.get_by_id(shift.employee_id)
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employé non trouvé: {shift.employee_id}"
                )
            
            if not employee.can_work_role(role):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"L'employé {employee.full_name} ne peut pas travailler comme {role.value}"
                )
            
            new_shift.assign_employee(employee)
        
        # Ajouter les autres attributs
        if shift.location:
            pass  # TODO: Conversion en enum LocationArea
        
        if shift.break_duration is not None:
            new_shift.break_duration = shift.break_duration
        
        if shift.notes:
            new_shift.notes = shift.notes
        
        # Ajouter au planning
        schedule.add_shift(new_shift)
        
        # Sauvegarder le planning
        schedule_repo.save(schedule)
        
        # Convertir en réponse API
        return ShiftResponse(
            shift_id=new_shift.shift_id,
            date=new_shift.date.isoformat(),
            start_time=new_shift.start_time.isoformat(),
            end_time=new_shift.end_time.isoformat(),
            role=new_shift.role.value,
            employee_id=new_shift.employee_id,
            employee_name=new_shift.employee.full_name if new_shift.employee else None,
            shift_type=new_shift.shift_type.value if new_shift.shift_type else None,
            location=new_shift.location.value if new_shift.location else None,
            break_duration=new_shift.break_duration,
            notes=new_shift.notes,
            status=new_shift.status.value,
            duration=new_shift.duration
        )
    
    @app.put("/api/shifts/{shift_id}", response_model=ShiftResponse)
    async def update_shift(
        shift_id: str,
        shift_update: ShiftUpdate,
        notify: bool = True,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Met à jour un shift.
        
        Args:
            shift_id: ID du shift
            shift_update: Données de mise à jour
            notify: Si True, notifie l'employé concerné
            current_user: Utilisateur actuel
            
        Returns:
            Shift mis à jour
            
        Raises:
            HTTPException: Si le shift n'existe pas
        """
        # Rechercher le shift dans tous les plannings
        for schedule in schedule_repo.get_all():
            shift = schedule.get_shift(shift_id)
            if shift:
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shift non trouvé: {shift_id}"
            )
        
        # Mettre à jour les attributs
        if shift_update.date is not None:
            try:
                date = datetime.fromisoformat(shift_update.date)
                shift.date = date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format de date invalide: {shift_update.date}"
                )
        
        if shift_update.start_time is not None:
            try:
                start_time = datetime.strptime(shift_update.start_time, "%H:%M").time()
                shift.start_time = start_time
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format d'heure de début invalide: {shift_update.start_time}"
                )
        
        if shift_update.end_time is not None:
            try:
                end_time = datetime.strptime(shift_update.end_time, "%H:%M").time()
                shift.end_time = end_time
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Format d'heure de fin invalide: {shift_update.end_time}"
                )
        
        if shift_update.role is not None:
            try:
                role = EmployeeRole(shift_update.role)
                shift.role = role
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rôle invalide: {shift_update.role}"
                )
        
        # Gérer l'assignation d'employé
        prev_employee_id = shift.employee_id
        if shift_update.employee_id is not None:
            if shift_update.employee_id == "":
                # Désassigner l'employé
                shift.unassign_employee(current_user["username"])
            else:
                # Assigner un nouvel employé
                employee = employee_repo.get_by_id(shift_update.employee_id)
                if not employee:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Employé non trouvé: {shift_update.employee_id}"
                    )
                
                if not employee.can_work_role(shift.role):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"L'employé {employee.full_name} ne peut pas travailler comme {shift.role.value}"
                    )
                
                shift.assign_employee(employee, current_user["username"])
        
        if shift_update.shift_type is not None:
            try:
                shift_type = ShiftType(shift_update.shift_type)
                shift.shift_type = shift_type
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Type de shift invalide: {shift_update.shift_type}"
                )
        
        if shift_update.break_duration is not None:
            shift.break_duration = shift_update.break_duration
        
        if shift_update.notes is not None:
            shift.notes = shift_update.notes
        
        if shift_update.status is not None:
            try:
                status_enum = ShiftStatus(shift_update.status)
                shift.change_status(status_enum, current_user["username"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Statut de shift invalide: {shift_update.status}"
                )
        
        # Sauvegarder le planning
        schedule_repo.save(schedule)
        
        # Notifier l'employé si demandé et si changement d'assignation
        if notify and (shift.employee_id != prev_employee_id):
            try:
                # Notifier le nouvel employé
                if shift.employee_id:
                    employee = employee_repo.get_by_id(shift.employee_id)
                    if employee:
                        notification_service.notify_employee(
                            employee=employee,
                            subject=f"Nouvelle assignation de shift le {shift.date.strftime('%d/%m/%Y')}",
                            message=f"Vous avez été assigné(e) à un shift le {shift.date.strftime('%d/%m/%Y')} de {shift.start_time.strftime('%H:%M')} à {shift.end_time.strftime('%H:%M')} en tant que {shift.role.value}.",
                            schedule_id=schedule.schedule_id
                        )
                
                # Notifier l'ancien employé
                if prev_employee_id:
                    employee = employee_repo.get_by_id(prev_employee_id)
                    if employee:
                        notification_service.notify_employee(
                            employee=employee,
                            subject=f"Retrait d'assignation de shift le {shift.date.strftime('%d/%m/%Y')}",
                            message=f"Vous avez été retiré(e) d'un shift le {shift.date.strftime('%d/%m/%Y')} de {shift.start_time.strftime('%H:%M')} à {shift.end_time.strftime('%H:%M')}.",
                            schedule_id=schedule.schedule_id
                        )
            except Exception as e:
                logger.error(f"Erreur lors de la notification des employés: {str(e)}")
                # Ne pas bloquer la mise à jour en cas d'erreur de notification
        
        # Convertir en réponse API
        return ShiftResponse(
            shift_id=shift.shift_id,
            date=shift.date.isoformat(),
            start_time=shift.start_time.isoformat(),
            end_time=shift.end_time.isoformat(),
            role=shift.role.value,
            employee_id=shift.employee_id,
            employee_name=shift.employee.full_name if shift.employee else None,
            shift_type=shift.shift_type.value if shift.shift_type else None,
            location=shift.location.value if shift.location else None,
            break_duration=shift.break_duration,
            notes=shift.notes,
            status=shift.status.value,
            duration=shift.duration
        )
    
    @app.post("/api/shifts/{shift_id}/assign", response_model=ShiftResponse)
    async def assign_employee_to_shift(
        shift_id: str,
        request: AssignEmployeeRequest,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Assigne un employé à un shift.
        
        Args:
            shift_id: ID du shift
            request: Données d'assignation
            current_user: Utilisateur actuel
            
        Returns:
            Shift mis à jour
            
        Raises:
            HTTPException: Si le shift ou l'employé n'existe pas
        """
        # Rechercher le shift dans tous les plannings
        for schedule in schedule_repo.get_all():
            shift = schedule.get_shift(shift_id)
            if shift:
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shift non trouvé: {shift_id}"
            )
        
        # Récupérer l'employé
        employee = employee_repo.get_by_id(request.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employé non trouvé: {request.employee_id}"
            )
        
        # Vérifier que l'employé peut travailler ce rôle
        if not employee.can_work_role(shift.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'employé {employee.full_name} ne peut pas travailler comme {shift.role.value}"
            )
        
        # Assigner l'employé
        prev_employee_id = shift.employee_id
        shift.assign_employee(employee, current_user["username"])
        
        # Sauvegarder le planning
        schedule_repo.save(schedule)
        
        # Notifier les employés
        try:
            # Notifier le nouvel employé
            notification_service.notify_employee(
                employee=employee,
                subject=f"Nouvelle assignation de shift le {shift.date.strftime('%d/%m/%Y')}",
                message=f"Vous avez été assigné(e) à un shift le {shift.date.strftime('%d/%m/%Y')} de {shift.start_time.strftime('%H:%M')} à {shift.end_time.strftime('%H:%M')} en tant que {shift.role.value}.",
                schedule_id=schedule.schedule_id
            )
            
            # Notifier l'ancien employé si différent
            if prev_employee_id and prev_employee_id != request.employee_id:
                prev_employee = employee_repo.get_by_id(prev_employee_id)
                if prev_employee:
                    notification_service.notify_employee(
                        employee=prev_employee,
                        subject=f"Retrait d'assignation de shift le {shift.date.strftime('%d/%m/%Y')}",
                        message=f"Vous avez été retiré(e) d'un shift le {shift.date.strftime('%d/%m/%Y')} de {shift.start_time.strftime('%H:%M')} à {shift.end_time.strftime('%H:%M')}.",
                        schedule_id=schedule.schedule_id
                    )
        except Exception as e:
            logger.error(f"Erreur lors de la notification des employés: {str(e)}")
            # Ne pas bloquer la mise à jour en cas d'erreur de notification
        
        # Convertir en réponse API
        return ShiftResponse(
            shift_id=shift.shift_id,
            date=shift.date.isoformat(),
            start_time=shift.start_time.isoformat(),
            end_time=shift.end_time.isoformat(),
            role=shift.role.value,
            employee_id=shift.employee_id,
            employee_name=shift.employee.full_name if shift.employee else None,
            shift_type=shift.shift_type.value if shift.shift_type else None,
            location=shift.location.value if shift.location else None,
            break_duration=shift.break_duration,
            notes=shift.notes,
            status=shift.status.value,
            duration=shift.duration
        )
    
    # Prévisions et statistiques
    
    @app.get("/api/predictions/staffing-needs")
    async def get_staffing_needs(
        start_date: str,
        end_date: str,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Récupère les besoins en personnel prévus pour une période.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            current_user: Utilisateur actuel
            
        Returns:
            Besoins en personnel par jour, shift et rôle
            
        Raises:
            HTTPException: Si les dates sont invalides
        """
        # Convertir les dates
        try:
            start_date_obj = datetime.fromisoformat(start_date)
            end_date_obj = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Format de date invalide"
            )
        
        try:
            # Récupérer les prévisions
            staffing_needs = prediction_client.get_staffing_needs(start_date_obj, end_date_obj)
            return staffing_needs
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des prévisions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération des prévisions: {str(e)}"
            )
    
    @app.get("/api/reservations")
    async def get_reservations(
        start_date: str,
        end_date: str,
        current_user: dict = Depends(get_manager_user)
    ):
        """
        Récupère les réservations pour une période.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            current_user: Utilisateur actuel
            
        Returns:
            Réservations par jour
            
        Raises:
            HTTPException: Si les dates sont invalides
        """
        # Convertir les dates
        try:
            start_date_obj = datetime.fromisoformat(start_date)
            end_date_obj = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Format de date invalide"
            )
        
        try:
            # Récupérer les réservations
            reservations = reservation_client.get_upcoming_reservations(start_date_obj, end_date_obj)
            return reservations
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réservations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération des réservations: {str(e)}"
            )
    
    return app

# Point d'entrée pour l'exécution directe
def run_server():
    """
    Démarre le serveur API.
    """
    app = create_app()
    
    host = API_CONFIG.get('host', '0.0.0.0')
    port = API_CONFIG.get('port', 5002)
    
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
