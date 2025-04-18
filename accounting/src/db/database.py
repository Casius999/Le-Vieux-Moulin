"""
Module de gestion de la base de données pour le module de comptabilité.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import settings

# Configuration du logger
logger = structlog.get_logger(__name__)

# Création de l'URL de connexion
DB_URL = (
    f"postgresql+asyncpg://{settings.database.user}:{settings.database.password}@"
    f"{settings.database.host}:{settings.database.port}/{settings.database.database}"
)

# Configuration SSL si activée
connect_args = {}
if settings.database.ssl_enabled and settings.database.ssl_ca_cert:
    connect_args["ssl"] = True
    connect_args["sslmode"] = "verify-full"
    connect_args["sslrootcert"] = settings.database.ssl_ca_cert

# Création du moteur de base de données
engine = create_async_engine(
    DB_URL,
    echo=settings.server.debug,
    future=True,
    pool_size=settings.database.pool_size,
    max_overflow=10,
    connect_args=connect_args
)

# Création du sessionmaker
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Classe de base pour les modèles
Base = declarative_base()

# Contexte de session asynchrone
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Contexte de session pour les opérations sur la base de données.
    
    Yields:
        AsyncSession: Session de base de données
    """
    session = async_session()
    try:
        yield session
    except Exception as e:
        logger.error("Erreur de session de base de données", error=str(e))
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """
    Initialise la base de données au démarrage de l'application.
    Crée les tables si elles n'existent pas.
    """
    logger.info("Initialisation de la base de données")
    
    async with engine.begin() as conn:
        # En mode debug/développement, on peut recréer les tables à chaque démarrage
        if settings.server.debug:
            logger.warning("Mode DEBUG: Recréation des tables")
            await conn.run_sync(Base.metadata.drop_all)
        
        # Création des tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Base de données initialisée avec succès")


# Fonctions utilitaires pour les opérations courantes
async def add_and_commit(session: AsyncSession, obj) -> None:
    """
    Ajoute un objet à la session et commit.
    
    Args:
        session (AsyncSession): Session de base de données
        obj: Objet à ajouter
    """
    session.add(obj)
    await session.commit()
    await session.refresh(obj)


async def add_all_and_commit(session: AsyncSession, objs: list) -> None:
    """
    Ajoute plusieurs objets à la session et commit.
    
    Args:
        session (AsyncSession): Session de base de données
        objs (list): Liste d'objets à ajouter
    """
    session.add_all(objs)
    await session.commit()
    for obj in objs:
        await session.refresh(obj)


async def delete_and_commit(session: AsyncSession, obj) -> None:
    """
    Supprime un objet de la session et commit.
    
    Args:
        session (AsyncSession): Session de base de données
        obj: Objet à supprimer
    """
    await session.delete(obj)
    await session.commit()
