"""
Module d'authentification pour l'API du module de comptabilité.

Ce module gère l'authentification et l'autorisation des utilisateurs
pour l'accès aux fonctionnalités de l'API.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import TokenData, UserInfo
from src.config import settings
from src.db.database import get_session

# Configuration du logger
logger = structlog.get_logger(__name__)

# Configuration de l'authentification
SECRET_KEY = settings.security.secret_key
ALGORITHM = settings.security.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.token_expire_minutes

# Point de terminaison pour l'authentification OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Contexte de hachage pour les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si le mot de passe en clair correspond au hash stocké.
    
    Args:
        plain_password (str): Mot de passe en clair
        hashed_password (str): Hash du mot de passe stocké
    
    Returns:
        bool: True si le mot de passe correspond, False sinon
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Génère un hash sécurisé pour un mot de passe.
    
    Args:
        password (str): Mot de passe en clair
    
    Returns:
        str: Hash du mot de passe
    """
    return pwd_context.hash(password)


async def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authentifie un utilisateur avec son nom d'utilisateur et son mot de passe.
    
    Args:
        username (str): Nom d'utilisateur
        password (str): Mot de passe en clair
    
    Returns:
        Optional[Dict]: Informations sur l'utilisateur si l'authentification réussit, None sinon
    """
    # Dans un environnement de production, ces informations proviendraient d'une base de données
    # Pour cet exemple, nous utilisons des utilisateurs codés en dur
    users = {
        "admin": {
            "id": "1",
            "username": "admin",
            "email": "admin@levieuxmoulin.fr",
            "hashed_password": get_password_hash("admin_password"),
            "roles": ["admin", "accountant"],
            "is_active": True
        },
        "comptable": {
            "id": "2",
            "username": "comptable",
            "email": "comptable@levieuxmoulin.fr",
            "hashed_password": get_password_hash("comptable_password"),
            "roles": ["accountant"],
            "is_active": True
        },
        "manager": {
            "id": "3",
            "username": "manager",
            "email": "manager@levieuxmoulin.fr",
            "hashed_password": get_password_hash("manager_password"),
            "roles": ["manager"],
            "is_active": True
        }
    }
    
    # Vérifier si l'utilisateur existe
    if username not in users:
        return None
    
    user = users[username]
    
    # Vérifier si l'utilisateur est actif
    if not user["is_active"]:
        return None
    
    # Vérifier le mot de passe
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT avec les données spécifiées.
    
    Args:
        data (Dict): Données à encoder dans le token
        expires_delta (timedelta, optional): Durée de validité du token. Par défaut à None.
    
    Returns:
        str: Token JWT encodé
    """
    to_encode = data.copy()
    
    # Définir l'expiration du token
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encoder le token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    """
    Récupère l'utilisateur courant à partir du token JWT.
    
    Args:
        token (str, optional): Token JWT. Par défaut à Depends(oauth2_scheme).
    
    Returns:
        UserInfo: Informations sur l'utilisateur connecté
    
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Décoder le token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        # Extraire les données du token
        token_data = TokenData(
            username=username,
            roles=payload.get("roles", []),
            exp=payload.get("exp")
        )
    except JWTError:
        logger.warning("Token JWT invalide")
        raise credentials_exception
    
    # Dans un environnement de production, ces informations proviendraient d'une base de données
    # Pour cet exemple, nous utilisons des utilisateurs codés en dur
    users = {
        "admin": {
            "id": "1",
            "username": "admin",
            "email": "admin@levieuxmoulin.fr",
            "roles": ["admin", "accountant"],
            "is_active": True
        },
        "comptable": {
            "id": "2",
            "username": "comptable",
            "email": "comptable@levieuxmoulin.fr",
            "roles": ["accountant"],
            "is_active": True
        },
        "manager": {
            "id": "3",
            "username": "manager",
            "email": "manager@levieuxmoulin.fr",
            "roles": ["manager"],
            "is_active": True
        }
    }
    
    # Vérifier si l'utilisateur existe
    if token_data.username not in users:
        logger.warning("Utilisateur non trouvé", username=token_data.username)
        raise credentials_exception
    
    user = users[token_data.username]
    
    # Vérifier si l'utilisateur est actif
    if not user["is_active"]:
        logger.warning("Utilisateur inactif", username=token_data.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inactif")
    
    return UserInfo(**user)


def get_admin_user(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    Vérifie que l'utilisateur actuel a le rôle 'admin'.
    
    Args:
        current_user (UserInfo, optional): Utilisateur actuel. Par défaut à Depends(get_current_user).
    
    Returns:
        UserInfo: Utilisateur actuel si c'est un administrateur
    
    Raises:
        HTTPException: Si l'utilisateur n'a pas le rôle 'admin'
    """
    if "admin" not in current_user.roles:
        logger.warning(
            "Accès interdit - Rôle admin requis", 
            username=current_user.username, 
            roles=current_user.roles
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'accéder à cette ressource. Rôle 'admin' requis."
        )
    
    return current_user


def get_accountant_user(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    Vérifie que l'utilisateur actuel a le rôle 'accountant'.
    
    Args:
        current_user (UserInfo, optional): Utilisateur actuel. Par défaut à Depends(get_current_user).
    
    Returns:
        UserInfo: Utilisateur actuel si c'est un comptable
    
    Raises:
        HTTPException: Si l'utilisateur n'a pas le rôle 'accountant'
    """
    if "accountant" not in current_user.roles and "admin" not in current_user.roles:
        logger.warning(
            "Accès interdit - Rôle accountant requis", 
            username=current_user.username, 
            roles=current_user.roles
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'accéder à cette ressource. Rôle 'accountant' requis."
        )
    
    return current_user


def get_manager_user(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    Vérifie que l'utilisateur actuel a le rôle 'manager'.
    
    Args:
        current_user (UserInfo, optional): Utilisateur actuel. Par défaut à Depends(get_current_user).
    
    Returns:
        UserInfo: Utilisateur actuel si c'est un manager
    
    Raises:
        HTTPException: Si l'utilisateur n'a pas le rôle 'manager'
    """
    if "manager" not in current_user.roles and "admin" not in current_user.roles:
        logger.warning(
            "Accès interdit - Rôle manager requis", 
            username=current_user.username, 
            roles=current_user.roles
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'accéder à cette ressource. Rôle 'manager' requis."
        )
    
    return current_user


def check_permission(required_role: str, current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    Vérifie que l'utilisateur actuel a le rôle requis.
    
    Args:
        required_role (str): Rôle requis
        current_user (UserInfo, optional): Utilisateur actuel. Par défaut à Depends(get_current_user).
    
    Returns:
        UserInfo: Utilisateur actuel si il a le rôle requis
    
    Raises:
        HTTPException: Si l'utilisateur n'a pas le rôle requis
    """
    if required_role not in current_user.roles and "admin" not in current_user.roles:
        logger.warning(
            f"Accès interdit - Rôle {required_role} requis", 
            username=current_user.username, 
            roles=current_user.roles
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Vous n'avez pas la permission d'accéder à cette ressource. Rôle '{required_role}' requis."
        )
    
    return current_user
