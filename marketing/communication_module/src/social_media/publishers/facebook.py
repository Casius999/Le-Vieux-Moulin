"""
Adaptateur pour la publication sur Facebook

Ce module implémente l'adaptateur pour la publication et l'analyse
sur la plateforme Facebook.
"""

import os
import json
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

from .base import SocialMediaPublisher
from ...common import format_date, retry_with_backoff


class FacebookPublisher(SocialMediaPublisher):
    """
    Adaptateur pour la publication sur Facebook.
    
    Utilise l'API Graph de Facebook pour publier du contenu et
    récupérer des données d'analyse.
    """
    
    def _setup_auth(self) -> None:
        """
        Configure l'authentification pour l'API Facebook.
        """
        self.app_id = self.config.get('app_id')
        self.app_secret = self.config.get('app_secret')
        self.page_id = self.config.get('page_id')
        self.access_token = self.config.get('access_token')
        self.api_version = self.config.get('api_version', 'v18.0')
        
        # Valider les paramètres obligatoires
        if not all([self.app_id, self.app_secret, self.page_id, self.access_token]):
            self.logger.warning("Configuration Facebook incomplète - certaines fonctionnalités peuvent ne pas fonctionner")
            
        # Dans une implémentation réelle, initialiser le SDK Facebook
        # Pour l'exemple, on simule simplement l'initialisation
        self.logger.info("SDK Facebook initialisé avec succès")
        
        # Vérifier la validité du token (simulé ici)
        self._validate_token()
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def publish_post(self, content: Dict[str, Any], 
                   targeting: Optional[Dict[str, Any]] = None) -> str:
        """
        Publie du contenu sur Facebook.
        
        Args:
            content: Contenu à publier (texte, médias, etc.)
            targeting: Paramètres de ciblage (optionnel)
            
        Returns:
            Identifiant de la publication Facebook
            
        Raises:
            Exception: En cas d'erreur lors de la publication
        """
        self.logger.info("Publication d'un contenu sur Facebook")
        
        # Valider les paramètres minimaux
        if 'body' not in content:
            raise ValueError("Le contenu doit contenir au moins un corps de texte (body)")
        
        # Préparer les données pour l'API
        post_data = {
            "message": content.get('body'),
            "access_token": self.access_token
        }
        
        # Ajouter un lien si présent
        if 'url' in content:
            post_data["link"] = content.get('url')
        
        # Ajouter les médias si présents
        if 'media_urls' in content and content.get('media_urls'):
            # Dans une implémentation réelle, il faudrait gérer l'upload des médias
            # Pour l'exemple, on simule simplement la présence d'une image
            self.logger.info(f"Ajout de {len(content.get('media_urls'))} média(s) à la publication")
            
            # Si c'est une vidéo, traitement spécifique
            if any(url.endswith(('.mp4', '.mov', '.avi')) for url in content.get('media_urls', [])):
                self.logger.info("Traitement d'une vidéo pour Facebook")
                # Simuler le traitement spécifique pour les vidéos
            
        # Ajouter les paramètres de ciblage si présents
        if targeting:
            # Dans une implémentation réelle, convertir les paramètres de ciblage au format FB
            targeting_spec = self._convert_targeting(targeting)
            post_data["targeting"] = json.dumps(targeting_spec)
            self.logger.info("Ajout de paramètres de ciblage à la publication")
        
        # Dans une implémentation réelle, appeler l'API Facebook
        # Pour l'exemple, simuler une réponse réussie
        try:
            # Simuler un appel API réussi
            self.logger.info(f"POST {self.api_version}/{self.page_id}/feed")
            
            # Générer un ID de publication fictif
            post_id = f"fb_{uuid.uuid4().hex[:10]}"
            
            # Enregistrer localement pour les tests (simulé)
            self._save_post(post_id, content, targeting)
            
            self.logger.info(f"Publication réussie sur Facebook avec ID: {post_id}")
            return post_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la publication sur Facebook: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def schedule_post(self, content: Dict[str, Any], 
                    publish_time: Union[str, datetime.datetime],
                    targeting: Optional[Dict[str, Any]] = None) -> str:
        """
        Programme la publication de contenu sur Facebook.
        
        Args:
            content: Contenu à publier (texte, médias, etc.)
            publish_time: Date et heure de publication
            targeting: Paramètres de ciblage (optionnel)
            
        Returns:
            Identifiant de la publication programmée
            
        Raises:
            Exception: En cas d'erreur lors de la programmation
        """
        self.logger.info(f"Programmation d'une publication sur Facebook pour {publish_time}")
        
        # Convertir la date si nécessaire
        if isinstance(publish_time, str):
            publish_time = datetime.datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
        
        # Vérifier que la date est dans le futur
        now = datetime.datetime.now(datetime.timezone.utc)
        if publish_time <= now:
            raise ValueError("La date de publication doit être dans le futur")
        
        # Convertir la date au format Unix timestamp attendu par Facebook
        publish_timestamp = int(publish_time.timestamp())
        
        # Préparer les données pour l'API, comme pour publish_post
        post_data = {
            "message": content.get('body'),
            "access_token": self.access_token,
            "published": False,
            "scheduled_publish_time": publish_timestamp
        }
        
        # Ajouter les autres éléments comme dans publish_post
        if 'url' in content:
            post_data["link"] = content.get('url')
        
        if targeting:
            targeting_spec = self._convert_targeting(targeting)
            post_data["targeting"] = json.dumps(targeting_spec)
        
        # Dans une implémentation réelle, appeler l'API Facebook
        # Pour l'exemple, simuler une réponse réussie
        try:
            # Simuler un appel API réussi
            self.logger.info(f"POST {self.api_version}/{self.page_id}/feed (scheduled)")
            
            # Générer un ID de publication fictif
            post_id = f"fb_scheduled_{uuid.uuid4().hex[:10]}"
            
            # Enregistrer localement pour les tests (simulé)
            self._save_post(post_id, content, targeting, publish_time)
            
            self.logger.info(f"Publication programmée sur Facebook avec ID: {post_id}")
            return post_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la programmation de la publication sur Facebook: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def delete_post(self, post_id: str) -> bool:
        """
        Supprime une publication Facebook.
        
        Args:
            post_id: Identifiant de la publication à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            Exception: En cas d'erreur lors de la suppression
        """
        self.logger.info(f"Suppression de la publication Facebook {post_id}")
        
        # Dans une implémentation réelle, appeler l'API Facebook
        # Pour l'exemple, simuler une réponse réussie
        try:
            # Simuler un appel API réussi
            self.logger.info(f"DELETE {self.api_version}/{post_id}")
            
            # Supprimer localement pour les tests (simulé)
            self._delete_post_file(post_id)
            
            self.logger.info(f"Publication {post_id} supprimée avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la publication {post_id}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une publication Facebook.
        
        Args:
            post_id: Identifiant de la publication
            
        Returns:
            Détails de la publication
            
        Raises:
            Exception: Si la publication n'existe pas ou autre erreur
        """
        self.logger.info(f"Récupération des détails de la publication {post_id}")
        
        # Dans une implémentation réelle, appeler l'API Facebook
        # Pour l'exemple, simuler une réponse en lisant le fichier local
        try:
            # Récupérer depuis le stockage local simulé
            post_data = self._load_post(post_id)
            
            if not post_data:
                raise ValueError(f"Publication {post_id} non trouvée")
                
            return post_data
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la publication {post_id}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def get_analytics(self, start_date: Optional[Union[str, datetime.datetime]] = None,
                    end_date: Optional[Union[str, datetime.datetime]] = None,
                    post_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Récupère les données d'analyse des publications Facebook.
        
        Args:
            start_date: Date de début pour la période d'analyse
            end_date: Date de fin pour la période d'analyse
            post_ids: Liste des IDs de publications spécifiques à analyser
            
        Returns:
            Données d'analyse
            
        Raises:
            Exception: En cas d'erreur lors de la récupération des analytics
        """
        self.logger.info("Récupération des analytics Facebook")
        
        # Convertir les dates si nécessaire
        if start_date and isinstance(start_date, str):
            start_date = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if end_date and isinstance(end_date, str):
            end_date = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Préparer les paramètres pour l'API
        query_params = {
            "access_token": self.access_token,
            "metric": "page_impressions,page_engaged_users,page_post_engagements",
            "period": "day"
        }
        
        if start_date:
            query_params["since"] = int(start_date.timestamp())
        
        if end_date:
            query_params["until"] = int(end_date.timestamp())
        
        # Dans une implémentation réelle, appeler l'API Facebook Insights
        # Pour l'exemple, simuler des données d'analyse
        try:
            # Simuler un appel API réussi
            self.logger.info(f"GET {self.api_version}/{self.page_id}/insights")
            
            # Générer des données d'analyse fictives
            analytics = {
                "platform": "facebook",
                "period": {
                    "start": format_date(start_date) if start_date else "30 days ago",
                    "end": format_date(end_date) if end_date else "today"
                },
                "page_metrics": {
                    "impressions": 1250,
                    "reach": 980,
                    "engagement": 345
                },
                "posts": {}
            }
            
            # Si des IDs de publications spécifiques sont fournis
            if post_ids:
                for post_id in post_ids:
                    # Dans une implémentation réelle, récupérer les métriques spécifiques
                    # Pour l'exemple, générer des données fictives
                    analytics["posts"][post_id] = {
                        "impressions": 320,
                        "reach": 250,
                        "engagement": 45,
                        "likes": 32,
                        "comments": 8,
                        "shares": 5
                    }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des analytics Facebook: {e}")
            raise
    
    def _validate_token(self) -> None:
        """
        Vérifie la validité du token d'accès.
        
        Dans une implémentation réelle, cela appellerait l'API Facebook
        pour vérifier la validité et les permissions du token.
        """
        self.logger.debug("Vérification du token d'accès Facebook")
        
        # Simuler une vérification réussie
        self.logger.info("Token d'accès Facebook valide")
    
    def _convert_targeting(self, targeting: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertit les paramètres de ciblage génériques au format spécifique à Facebook.
        
        Args:
            targeting: Paramètres de ciblage génériques
            
        Returns:
            Paramètres de ciblage au format Facebook
        """
        fb_targeting = {}
        
        # Convertir les paramètres de localisation
        if 'location' in targeting:
            fb_targeting["geo_locations"] = {
                "cities": [
                    {
                        "name": targeting.get('location'),
                        "distance_unit": "kilometer",
                        "radius": targeting.get('radius', 10)
                    }
                ]
            }
        
        # Convertir les paramètres d'âge
        if 'age_range' in targeting and len(targeting['age_range']) == 2:
            fb_targeting["age_min"] = targeting['age_range'][0]
            fb_targeting["age_max"] = targeting['age_range'][1]
        
        # Convertir les paramètres d'intérêts
        if 'interests' in targeting and targeting['interests']:
            fb_targeting["interests"] = [
                {"name": interest, "id": f"interest_{i}"}
                for i, interest in enumerate(targeting['interests'])
            ]
        
        return fb_targeting
    
    def _save_post(self, post_id: str, content: Dict[str, Any], 
                 targeting: Optional[Dict[str, Any]] = None,
                 publish_time: Optional[datetime.datetime] = None) -> None:
        """
        Sauvegarde les détails d'une publication pour simulation.
        
        Dans une implémentation réelle, cette méthode n'existerait pas.
        Elle est utilisée ici pour simuler la persistance des publications.
        
        Args:
            post_id: Identifiant de la publication
            content: Contenu de la publication
            targeting: Paramètres de ciblage (optionnel)
            publish_time: Date et heure de publication programmée (optionnel)
        """
        # Créer un objet représentant la publication
        post_data = {
            "id": post_id,
            "content": content,
            "created_at": format_date(datetime.datetime.now()),
            "platform": "facebook",
            "page_id": self.page_id
        }
        
        # Ajouter les paramètres de ciblage si présents
        if targeting:
            post_data["targeting"] = targeting
        
        # Ajouter la date de publication programmée si présente
        if publish_time:
            post_data["scheduled_time"] = format_date(publish_time)
            post_data["status"] = "scheduled"
        else:
            post_data["status"] = "published"
        
        # Simuler l'enregistrement dans un fichier
        posts_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(posts_dir, exist_ok=True)
        
        post_file = os.path.join(posts_dir, f"{post_id}.json")
        
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
    
    def _load_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Charge les détails d'une publication depuis le stockage simulé.
        
        Args:
            post_id: Identifiant de la publication
            
        Returns:
            Détails de la publication ou None si non trouvée
        """
        posts_dir = os.path.join(os.path.dirname(__file__), 'data')
        post_file = os.path.join(posts_dir, f"{post_id}.json")
        
        if not os.path.exists(post_file):
            return None
        
        with open(post_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _delete_post_file(self, post_id: str) -> bool:
        """
        Supprime le fichier d'une publication dans le stockage simulé.
        
        Args:
            post_id: Identifiant de la publication
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        posts_dir = os.path.join(os.path.dirname(__file__), 'data')
        post_file = os.path.join(posts_dir, f"{post_id}.json")
        
        if not os.path.exists(post_file):
            return False
        
        os.remove(post_file)
        return True
