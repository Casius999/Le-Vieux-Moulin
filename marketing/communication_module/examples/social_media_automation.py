#!/usr/bin/env python3
"""
Exemple d'automatisation des réseaux sociaux pour Le Vieux Moulin.

Ce script montre comment utiliser le module de communication pour automatiser
la création et la publication de contenu sur les réseaux sociaux.
"""

import os
import sys
import asyncio
import datetime
import logging
from typing import Dict, List, Any

# Ajout du répertoire parent au PYTHONPATH pour l'importation des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.common import Config, setup_logger
from src.orchestrator import get_orchestrator
from src.social_media import SocialMediaManager


async def publish_menu_of_the_day():
    """
    Publie le menu du jour sur les réseaux sociaux.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("social_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Création du contenu du menu du jour
    today = datetime.datetime.now().strftime("%A %d %B %Y")
    
    menu_content = {
        "title": f"Menu du jour - {today}",
        "body": "Aujourd'hui au Vieux Moulin, notre chef vous propose :\n\n" +
                "🥗 Entrée : Salade de chèvre chaud aux noix et miel\n" +
                "🍖 Plat : Magret de canard aux figues et pommes sarladaises\n" +
                "🍮 Dessert : Tarte fine aux pommes et caramel au beurre salé\n\n" +
                "Réservez votre table dès maintenant !",
        "media_url": "https://example.com/images/menu_jour.jpg",
        "hashtags": ["menudujour", "gastronomie", "vieuxmoulin", "vensac"]
    }
    
    # Publication sur les réseaux sociaux
    await orchestrator.publish_to_social_media(
        content=menu_content,
        platforms=["facebook", "instagram"],
        scheduled_time=get_optimal_posting_time()
    )
    
    logger.info(f"Menu du jour programmé pour publication sur Facebook et Instagram")


async def publish_weekly_promotion():
    """
    Publie la promotion hebdomadaire sur les réseaux sociaux.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("social_example", "INFO")
    
    # Obtention directe du gestionnaire des réseaux sociaux
    social_media = SocialMediaManager(config)
    
    # Création du contenu pour la promotion hebdomadaire
    promo_content = {
        "title": "Offre spéciale du week-end !",
        "body": "Ce week-end au Vieux Moulin, profitez de notre formule spéciale :\n\n" +
                "👉 Menu complet (entrée + plat + dessert) à 29€ au lieu de 39€\n" +
                "👉 Une coupe de champagne offerte pour toute réservation en ligne\n\n" +
                "Offre valable uniquement ce week-end, sur réservation.",
        "media_url": "https://example.com/images/weekend_promo.jpg",
        "hashtags": ["promotion", "weekend", "vieuxmoulin", "bonplan"]
    }
    
    # Publication sur plusieurs plateformes avec timing optimisé
    await social_media.publish_content_async(
        content=promo_content,
        platforms=["facebook", "instagram", "twitter"],
        scheduled_time=get_optimal_posting_time(target_hour=18)  # Publier à 18h
    )
    
    logger.info(f"Promotion hebdomadaire programmée pour publication sur plusieurs plateformes")


async def schedule_monthly_content_calendar():
    """
    Planifie un calendrier mensuel de contenus pour les réseaux sociaux.
    """
    # Initialisation de la configuration et des loggers
    config = Config("../config/settings.json")
    logger = setup_logger("social_example", "INFO")
    
    # Obtention de l'orchestrateur
    orchestrator = get_orchestrator(config)
    
    # Génération d'un calendrier de contenu pour le mois
    today = datetime.datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Définition des thèmes hebdomadaires
    weekly_themes = [
        "Spécialités régionales",
        "Rencontre avec nos producteurs",
        "Cocktails et accords mets-vins",
        "Secrets de cuisine du chef"
    ]
    
    # Créer le calendrier de contenu
    calendar = []
    
    # Commencer au début du mois prochain
    next_month_start = datetime.datetime(current_year, current_month, 1) + datetime.timedelta(days=32)
    next_month_start = datetime.datetime(next_month_start.year, next_month_start.month, 1)
    
    # Générer des publications pour chaque semaine du mois
    for week in range(4):
        theme = weekly_themes[week]
        
        # Définir les jours de publication (lundi, mercredi, vendredi)
        for weekday in [0, 2, 4]:  # 0=Lundi, 2=Mercredi, 4=Vendredi
            # Calculer la date de publication
            current_date = next_month_start + datetime.timedelta(days=7*week + weekday)
            
            # Créer le contenu en fonction du thème
            content = create_themed_content(theme, current_date)
            
            # Ajouter au calendrier
            calendar.append({
                "date": current_date.isoformat(),
                "content": content,
                "platforms": ["facebook", "instagram"]
            })
    
    # Programmer chaque publication
    for entry in calendar:
        await orchestrator.publish_to_social_media(
            content=entry["content"],
            platforms=entry["platforms"],
            scheduled_time=entry["date"]
        )
    
    logger.info(f"Calendrier de contenu programmé pour le mois prochain: {len(calendar)} publications")


def create_themed_content(theme: str, date: datetime.datetime) -> Dict[str, Any]:
    """
    Crée un contenu thématique pour les réseaux sociaux.
    
    Args:
        theme: Thème de la publication
        date: Date de la publication
        
    Returns:
        Contenu formaté pour la publication
    """
    # Formater la date
    formatted_date = date.strftime("%d/%m/%Y")
    
    # Créer un contenu adapté au thème
    if theme == "Spécialités régionales":
        return {
            "title": f"Spécialités régionales - {formatted_date}",
            "body": "Découvrez aujourd'hui l'une de nos spécialités locales : le grenier médocain.\n\n" +
                    "Cette charcuterie typique du Médoc est élaborée selon une recette traditionnelle, " +
                    "transmise de génération en génération. À déguster en entrée avec un bon verre de vin rouge local.",
            "media_url": "https://example.com/images/grenier_medocain.jpg",
            "hashtags": ["gastronomie", "médoc", "spécialitérégionale", "vieuxmoulin"]
        }
    elif theme == "Rencontre avec nos producteurs":
        return {
            "title": f"Nos producteurs - {formatted_date}",
            "body": "Rencontrez Jean-Pierre, ostréiculteur à Arcachon depuis 30 ans.\n\n" +
                    "Ses huîtres d'exception, sélectionnées avec soin, sont servies dans notre restaurant. " +
                    "Une fraîcheur incomparable qui fait la renommée de notre plateau de fruits de mer.",
            "media_url": "https://example.com/images/ostreiculteur.jpg",
            "hashtags": ["producteurlocal", "circuit-court", "huitres", "vieuxmoulin"]
        }
    elif theme == "Cocktails et accords mets-vins":
        return {
            "title": f"Accord mets-vins - {formatted_date}",
            "body": "Notre sommelier vous suggère : un Saint-Estèphe 2018 pour accompagner notre côte de bœuf.\n\n" +
                    "Ce vin puissant aux tanins fondus s'accorde parfaitement avec la saveur corsée de notre viande " +
                    "de race Bazadaise, pour une explosion de saveurs en bouche.",
            "media_url": "https://example.com/images/accord_vin.jpg",
            "hashtags": ["vin", "accord", "gastronomie", "vieuxmoulin"]
        }
    else:  # Secrets de cuisine du chef
        return {
            "title": f"Les secrets du chef - {formatted_date}",
            "body": "L'astuce du chef pour une sauce béarnaise parfaite ?\n\n" +
                    "Incorporer le beurre clarifié très progressivement, sans cesser de fouetter, et à température stable. " +
                    "Un secret simple mais essentiel pour une onctuosité incomparable.",
            "media_url": "https://example.com/images/sauce_bearnaise.jpg",
            "hashtags": ["astucedechef", "cuisine", "gastronomie", "vieuxmoulin"]
        }


def get_optimal_posting_time(target_hour: int = None) -> str:
    """
    Détermine l'heure optimale pour une publication.
    
    Args:
        target_hour: Heure cible spécifique (optionnelle)
        
    Returns:
        Horodatage ISO 8601 pour la publication
    """
    now = datetime.datetime.now()
    
    if target_hour is not None:
        # Utiliser l'heure cible spécifiée
        target_hour = target_hour
    else:
        # Déterminer l'heure optimale selon le jour de la semaine
        weekday = now.weekday()
        
        if weekday < 5:  # Lundi-Vendredi
            target_hour = 12  # Midi pour la pause déjeuner en semaine
        else:  # Weekend
            target_hour = 11  # 11h le weekend
    
    # Si l'heure actuelle est après l'heure cible, planifier pour le lendemain
    if now.hour >= target_hour:
        target_date = now.date() + datetime.timedelta(days=1)
    else:
        target_date = now.date()
    
    target_time = datetime.datetime.combine(
        target_date,
        datetime.time(hour=target_hour, minute=0)
    )
    
    return target_time.isoformat()


async def main():
    """
    Fonction principale exécutant les exemples.
    """
    # Configuration du logger
    logger = setup_logger("social_example", "INFO")
    logger.info("Démarrage des exemples d'automatisation des réseaux sociaux...")
    
    # Exécution des exemples
    await publish_menu_of_the_day()
    await publish_weekly_promotion()
    await schedule_monthly_content_calendar()
    
    logger.info("Exemples terminés avec succès")


if __name__ == "__main__":
    # Exécution du code asynchrone
    asyncio.run(main())
