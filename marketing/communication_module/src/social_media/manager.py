"""
Gestionnaire de réseaux sociaux

Ce module fournit la classe principale pour gérer les interactions avec
les différentes plateformes de réseaux sociaux.
"""

import os
import logging
import json
import datetime
import requests
from typing import Dict, List, Any, Optional, Union

from ..common import retry_with_backoff, format_date
from .publishers import get_publisher


class SocialMediaManager:
    """Gère la publication et l'analyse sur les réseaux sociaux"""
    
    def __init__(self, config):
        """
        Initialise le gestionnaire de réseaux sociaux.
        
        Args:
            config: L'objet de configuration global ou spécifique aux réseaux sociaux
        """
        self.logger = logging.getLogger("communication.social_media")
        
        # Récupérer la configuration spécifique aux réseaux sociaux
        if hasattr(config, 'get'):
            platforms_config = config.get('social_media.platforms', {})
            self.default_platforms = config.get('social_media.default_platforms', [])
            self.content_strategy = config.get('social_media.content_strategy', {})
            self.image_service_api_key = config.get('social_media.image_generation.api_key', '')
            self.image_service_endpoint = config.get('social_media.image_generation.endpoint', '')
        else:
            platforms_config = config.get('platforms', {})
            self.default_platforms = config.get('default_platforms', [])
            self.content_strategy = config.get('content_strategy', {})
            self.image_service_api_key = config.get('image_generation', {}).get('api_key', '')
            self.image_service_endpoint = config.get('image_generation', {}).get('endpoint', '')
            
        # Initialiser les publishers pour chaque plateforme configurée
        self.publishers = {}
        for platform_name, platform_config in platforms_config.items():
            if platform_config.get('enabled', False):
                try:
                    self.publishers[platform_name] = get_publisher(platform_name, platform_config)
                    self.logger.info(f"Plateforme {platform_name} initialisée avec succès")
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'initialisation de {platform_name}: {e}")
        
        self.logger.info(f"Gestionnaire de réseaux sociaux initialisé avec {len(self.publishers)} plateformes")
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def publish_content(self, content: Dict[str, Any], 
                      platforms: Optional[List[str]] = None,
                      scheduled_time: Optional[Union[str, datetime.datetime]] = None,
                      targeting: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie du contenu sur une ou plusieurs plateformes.
        
        Args:
            content: Dictionnaire contenant les détails du contenu à publier
            platforms: Liste des plateformes où publier (si None, utilise les plateformes par défaut)
            scheduled_time: Date/heure de publication programmée (si None, publie immédiatement)
            targeting: Paramètres de ciblage pour la publication
            
        Returns:
            Dictionnaire contenant les IDs des publications créées et leur statut
        """
        if platforms is None:
            platforms = self.default_platforms
            
        if scheduled_time and isinstance(scheduled_time, str):
            scheduled_time = datetime.datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
        results = {
            "status": "scheduled" if scheduled_time else "published",
            "publication_ids": {},
            "errors": {}
        }
        
        if scheduled_time:
            results["scheduled_time"] = format_date(scheduled_time)
            
        for platform in platforms:
            if platform not in self.publishers:
                results["errors"][platform] = f"Plateforme {platform} non configurée"
                continue
                
            try:
                # Adapter le contenu à la plateforme
                adapted_content = self._adapt_content(content, platform)
                
                # Publier ou programmer la publication
                if scheduled_time:
                    pub_id = self.publishers[platform].schedule_post(adapted_content, scheduled_time, targeting)
                    self.logger.info(f"Publication programmée sur {platform} pour le {scheduled_time}")
                else:
                    pub_id = self.publishers[platform].publish_post(adapted_content, targeting)
                    self.logger.info(f"Publication effectuée sur {platform}")
                
                results["publication_ids"][platform] = pub_id
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la publication sur {platform}: {e}")
                results["errors"][platform] = str(e)
                
        # Si tout a échoué, mettre à jour le statut
        if not results["publication_ids"] and results["errors"]:
            results["status"] = "failed"
            
        return results
    
    def get_analytics(self, platform: Optional[str] = None, 
                    start_date: Optional[Union[str, datetime.datetime]] = None,
                    end_date: Optional[Union[str, datetime.datetime]] = None,
                    post_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Récupère les données d'analyse des publications.
        
        Args:
            platform: Plateforme spécifique (si None, agrège toutes les plateformes)
            start_date: Date de début pour la période d'analyse
            end_date: Date de fin pour la période d'analyse
            post_ids: Liste des IDs de publications spécifiques à analyser
            
        Returns:
            Dictionnaire contenant les données d'analyse
        """
        if start_date and isinstance(start_date, str):
            start_date = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if end_date and isinstance(end_date, str):
            end_date = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
        analytics = {
            "period": {
                "start": format_date(start_date) if start_date else None,
                "end": format_date(end_date) if end_date else None
            },
            "platforms": {}
        }
        
        # Si une plateforme spécifique est demandée
        if platform:
            if platform in self.publishers:
                try:
                    analytics["platforms"][platform] = self.publishers[platform].get_analytics(
                        start_date=start_date,
                        end_date=end_date,
                        post_ids=post_ids
                    )
                except Exception as e:
                    self.logger.error(f"Erreur lors de la récupération des analytics pour {platform}: {e}")
                    analytics["platforms"][platform] = {"error": str(e)}
            else:
                analytics["error"] = f"Plateforme {platform} non configurée"
        else:
            # Récupérer les analytics pour toutes les plateformes
            for platform_name, publisher in self.publishers.items():
                try:
                    analytics["platforms"][platform_name] = publisher.get_analytics(
                        start_date=start_date,
                        end_date=end_date,
                        post_ids=post_ids
                    )
                except Exception as e:
                    self.logger.error(f"Erreur lors de la récupération des analytics pour {platform_name}: {e}")
                    analytics["platforms"][platform_name] = {"error": str(e)}
        
        # Calculer des métriques agrégées si plusieurs plateformes
        if len(analytics["platforms"]) > 1:
            total_engagement = 0
            total_reach = 0
            total_impressions = 0
            
            for platform_data in analytics["platforms"].values():
                if isinstance(platform_data, dict) and "error" not in platform_data:
                    total_engagement += platform_data.get("engagement", 0)
                    total_reach += platform_data.get("reach", 0)
                    total_impressions += platform_data.get("impressions", 0)
            
            analytics["aggregated"] = {
                "engagement": total_engagement,
                "reach": total_reach,
                "impressions": total_impressions
            }
        
        return analytics
    
    def create_promotional_content(self, promotion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un contenu promotionnel basé sur les données fournies.
        
        Args:
            promotion_data: Données de la promotion (titre, description, date de validité, etc.)
            
        Returns:
            Contenu formaté pour publication
        """
        # Template de base pour une promotion
        content = {
            "title": promotion_data.get("title", "Offre spéciale"),
            "body": f"{promotion_data.get('description', 'Découvrez notre offre spéciale !')} "
                   f"Valable jusqu'au {promotion_data.get('validUntil', 'bientôt')}.",
            "media_urls": [],
            "hashtags": ["vieuxmoulin", "promotion", "restaurant"]
        }
        
        # Ajouter des hashtags spécifiques s'ils sont fournis
        if "hashtags" in promotion_data:
            content["hashtags"].extend(promotion_data["hashtags"])
        
        # Ajouter une image si un prompt est fourni
        if "imagePrompt" in promotion_data:
            self.logger.info(f"Génération d'image à partir du prompt: {promotion_data['imagePrompt']}")
            
            try:
                # Appel à l'API de génération d'images
                image_url = self._generate_image(promotion_data['imagePrompt'])
                if image_url:
                    content["media_urls"].append(image_url)
                    self.logger.info(f"Image générée avec succès: {image_url}")
                else:
                    self.logger.warning("Échec de la génération d'image")
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération d'image: {e}")
            
        return content
    
    def _generate_image(self, prompt: str) -> Optional[str]:
        """
        Génère une image en utilisant le service d'IA configuré.
        
        Args:
            prompt: Description textuelle de l'image à générer
            
        Returns:
            URL de l'image générée ou None en cas d'erreur
        """
        if not self.image_service_endpoint or not self.image_service_api_key:
            self.logger.error("Configuration du service d'image manquante")
            return None
            
        try:
            # Appel à l'API de génération d'images (Stability AI, DALL-E, etc.)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.image_service_api_key}"
            }
            
            payload = {
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "url"
            }
            
            response = requests.post(
                self.image_service_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Format de réponse variable selon l'API utilisée
            # Exemple pour DALL-E
            if "data" in data and data["data"] and "url" in data["data"][0]:
                return data["data"][0]["url"]
            # Exemple pour Stability AI
            elif "artifacts" in data and data["artifacts"] and "base64" in data["artifacts"][0]:
                # Ici il faudrait stocker l'image et retourner son URL
                artifact_id = data["artifacts"][0]["id"]
                # Stocker l'image dans un stockage persistant (S3, GCS, etc.)
                storage_url = self._store_image(data["artifacts"][0]["base64"], artifact_id)
                return storage_url
                
            self.logger.warning(f"Format de réponse inattendu: {data}")
            return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur lors de l'appel à l'API de génération d'images: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la génération d'image: {e}")
            return None
            
    def _store_image(self, base64_content: str, image_id: str) -> str:
        """
        Stocke une image encodée en base64 dans un stockage persistant.
        
        Args:
            base64_content: Contenu de l'image en base64
            image_id: Identifiant unique de l'image
            
        Returns:
            URL publique de l'image stockée
        """
        import base64
        from io import BytesIO
        import boto3
        from botocore.exceptions import ClientError
        
        try:
            # Décodage de l'image
            image_data = base64.b64decode(base64_content)
            
            # Configuration de S3 (devrait être paramétrée via la configuration)
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION', 'eu-west-3')
            )
            
            bucket_name = os.environ.get('S3_BUCKET_NAME', 'vieuxmoulin-marketing-assets')
            file_name = f"generated/img_{image_id}.png"
            
            # Upload vers S3
            s3_client.upload_fileobj(
                BytesIO(image_data),
                bucket_name,
                file_name,
                ExtraArgs={'ContentType': 'image/png'}
            )
            
            # Génération de l'URL publique
            url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
            
            return url
            
        except ClientError as e:
            self.logger.error(f"Erreur S3 lors du stockage de l'image: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur lors du stockage de l'image: {e}")
            raise
    
    def _adapt_content(self, content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Adapte le contenu aux spécificités de la plateforme.
        
        Args:
            content: Contenu original à adapter
            platform: Nom de la plateforme cible
            
        Returns:
            Contenu adapté à la plateforme
        """
        adapted = content.copy()
        
        # Adaptations spécifiques à chaque plateforme
        if platform == "instagram":
            # Instagram a besoin d'une image et accepte jusqu'à 30 hashtags
            if not adapted.get("media_urls"):
                self.logger.warning("Instagram nécessite une image, génération d'une image par défaut")
                # Génération d'une image de secours
                try:
                    default_prompt = f"Image pour {adapted.get('title', 'restaurant Le Vieux Moulin')}"
                    image_url = self._generate_image(default_prompt)
                    if image_url:
                        adapted["media_urls"] = [image_url]
                except Exception as e:
                    self.logger.error(f"Impossible de générer une image de secours: {e}")
            
            # Limiter les hashtags à 30 maximum
            if "hashtags" in adapted and len(adapted["hashtags"]) > 30:
                adapted["hashtags"] = adapted["hashtags"][:30]
                
        elif platform == "twitter":
            # Twitter a une limite de caractères
            max_length = 280
            if len(adapted.get("body", "")) > max_length:
                # Tronquer et ajouter "..."
                adapted["body"] = adapted["body"][:max_length-3] + "..."
                
        elif platform == "facebook":
            # Facebook peut avoir des liens et des formats riches
            # Ici, nous pourrions ajouter des métadonnées OpenGraph par exemple
            if "url" in adapted:
                # Récupérer les métadonnées OpenGraph de l'URL
                try:
                    og_data = self._fetch_opengraph_data(adapted["url"])
                    if og_data:
                        adapted["og_data"] = og_data
                except Exception as e:
                    self.logger.warning(f"Impossible de récupérer les métadonnées OpenGraph: {e}")
        
        return adapted
        
    def _fetch_opengraph_data(self, url: str) -> Optional[Dict[str, str]]:
        """
        Récupère les métadonnées OpenGraph d'une URL.
        
        Args:
            url: URL à analyser
            
        Returns:
            Dictionnaire contenant les métadonnées OpenGraph
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Utilisation de BeautifulSoup pour parser le HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            og_data = {}
            for tag in soup.find_all("meta"):
                if tag.get("property", "").startswith("og:"):
                    og_property = tag.get("property")[3:]  # Enlever 'og:'
                    og_data[og_property] = tag.get("content", "")
                    
            return og_data if og_data else None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Erreur lors de la récupération des métadonnées OpenGraph: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Erreur inattendue lors de l'analyse OpenGraph: {e}")
            return None
