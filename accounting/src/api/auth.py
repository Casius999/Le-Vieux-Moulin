"""
Module d'authentification pour l'API du module de comptabilité.

Gère l'authentification, l'autorisation et la sécurité des routes API.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field, validator

from src.config import settings

# Configuration du logger
logger = structlog.get_logger(__name__)

# Configuration de l'authentification OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    """Modèle d'utilisateur du système."""
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str  # admin, accountant, manager, viewer
    is_active: bool = True
    last_login: Optional[datetime] = None
    permissions: List[str] = []


class Token(BaseModel):
    """Modèle de token d'authentification."""
    access_token: str
    token_type: str
    expires_at: datetime
    user: Dict


class TokenData(BaseModel):
    """Données contenues dans un token JWT."""
    sub: str
    exp: int
    role: str
    permissions: List[str] = []


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Authentifie l'utilisateur à partir du token JWT.
    
    Args:
        token (str): Token d'authentification
    
    Returns:
        User: Utilisateur authentifié
    
    Raises:
        HTTPException: En cas d'échec d'authentification
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants d'authentification invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Vérifier et décoder le token
        payload = jwt.decode(
            token, 
            settings.security.secret_key, 
            algorithms=[settings.security.algorithm]
        )
        
        # Extraire les données du token
        token_data = TokenData(
            sub=payload.get("sub"),
            exp=payload.get("exp"),
            role=payload.get("role", "viewer"),
            permissions=payload.get("permissions", [])
        )
        
        # Vérifier si le token est expiré
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            logger.warning("Token expiré", username=token_data.sub)
            raise credentials_exception
        
        # Créer l'objet utilisateur
        user = User(
            id=token_data.sub,
            username=token_data.sub,
            email=f"{token_data.sub}@levieuxmoulin.fr",  # Placeholder, à remplacer par l'email réel
            role=token_data.role,
            permissions=token_data.permissions,
            is_active=True
        )
        
        return user
        
    except jwt.PyJWTError as e:
        logger.warning("Erreur de décodage du token", error=str(e))
        raise credentials_exception


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token d'accès JWT.
    
    Args:
        data (Dict): Données à encoder dans le token
        expires_delta (timedelta, optional): Durée de validité du token
    
    Returns:
        str: Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    # Encoder le token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.security.secret_key, 
        algorithm=settings.security.algorithm
    )
    
    return encoded_jwt


def check_permission(user: User, required_permission: str) -> bool:
    """
    Vérifie si l'utilisateur a la permission requise.
    
    Args:
        user (User): Utilisateur à vérifier
        required_permission (str): Permission requise
    
    Returns:
        bool: True si l'utilisateur a la permission, False sinon
    """
    # Les administrateurs ont toutes les permissions
    if user.role == "admin":
        return True
    
    # Vérifier si la permission est dans la liste des permissions de l'utilisateur
    return required_permission in user.permissions
