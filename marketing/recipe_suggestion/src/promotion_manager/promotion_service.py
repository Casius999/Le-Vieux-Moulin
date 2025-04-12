"""
Module de gestion des promotions pour Le Vieux Moulin.

Ce module gère la création, la personnalisation et la publication
des promotions basées sur les suggestions de recettes.
"""

import logging
import json
import os
import random
from datetime import datetime, timedelta
import hashlib
import re

logger = logging.getLogger('recipe_suggestion.promotion_manager')

class PromotionManager:
    """Gestionnaire de promotions basées sur les recettes suggérées."""
    
    def __init__(self, config):
        """Initialise le gestionnaire avec la configuration spécifiée."""
        self.config = config
        self.promotion_templates = self._load_templates()
        self.promotion_history = self._load_history()
        logger.info("Gestionnaire de promotions initialisé")
    
    def _load_templates(self):
        """Charge les templates de promotion depuis le fichier JSON."""
        try:
            templates_path = os.path.join('config', 'promotion_templates.json')
            with open(templates_path, 'r') as file:
                templates = json.load(file)
                logger.info(f"Templates de promotion chargés: {len(templates)}")
                return templates
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors du chargement des templates: {e}")
            # Templates par défaut
            return {
                "standard": {
                    "title": "L'offre du jour: {recipe_name}",
                    "description": "Découvrez notre {recipe_name}, préparé avec des ingrédients frais et à prix spécial aujourd'hui!",
                    "discount_type": "percentage",
                    "discount_value": 10,
                    "duration_hours": 24,
                    "channels": ["in_store", "social_media", "website"]
                },
                "flash_sale": {
                    "title": "FLASH DEAL - {recipe_name}",
                    "description": "Pour quelques heures seulement! Notre {recipe_name} à prix réduit. Ne manquez pas cette offre!",
                    "discount_type": "percentage",
                    "discount_value": 15,
                    "duration_hours": 4,
                    "channels": ["social_media", "website", "email"]
                },
                "weekend_special": {
                    "title": "Spécial Weekend: {recipe_name}",
                    "description": "Célébrez le weekend avec notre délicieux {recipe_name}, une création exclusive de notre chef!",
                    "discount_type": "fixed",
                    "discount_value": 3,
                    "duration_hours": 48,
                    "channels": ["in_store", "social_media", "website"]
                },
                "ingredient_spotlight": {
                    "title": "À l'honneur: {main_ingredient}",
                    "description": "Notre {recipe_name} met en valeur {main_ingredient} de saison. Une expérience gustative à ne pas manquer!",
                    "discount_type": "percentage",
                    "discount_value": 0,
                    "duration_hours": 72,
                    "channels": ["in_store", "website"]
                }
            }
    
    def _load_history(self):
        """Charge l'historique des promotions précédentes."""
        try:
            history_path = os.path.join('data', 'promotion_history.json')
            
            if not os.path.exists(history_path):
                # Crée le répertoire data s'il n'existe pas
                os.makedirs(os.path.dirname(history_path), exist_ok=True)
                return []
                
            with open(history_path, 'r') as file:
                history = json.load(file)
                logger.info(f"Historique des promotions chargé: {len(history)} entrées")
                return history
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Pas d'historique de promotions disponible: {e}")
            return []
    
    def _save_history(self):
        """Sauvegarde l'historique des promotions."""
        try:
            history_path = os.path.join('data', 'promotion_history.json')
            
            # Crée le répertoire data s'il n'existe pas
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            
            with open(history_path, 'w') as file:
                json.dump(self.promotion_history, file, indent=2)
                logger.info(f"Historique des promotions sauvegardé: {len(self.promotion_history)} entrées")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'historique des promotions: {e}")
    
    def create_promotion(self, recipe_suggestion):
        """
        Crée une promotion basée sur une suggestion de recette.
        
        Args:
            recipe_suggestion: Suggestion de recette pour laquelle créer une promotion
            
        Returns:
            Dictionnaire contenant les détails de la promotion
        """
        logger.info(f"Création d'une promotion pour: {recipe_suggestion.get('name')}")
        
        # 1. Sélection du template de promotion approprié
        template = self._select_template(recipe_suggestion)
        
        # 2. Génération des détails de la promotion
        promotion = self._generate_promotion_details(recipe_suggestion, template)
        
        # 3. Enregistrement dans l'historique
        self.promotion_history.append(promotion)
        self._save_history()
        
        # 4. Publication de la promotion sur les canaux configurés
        self._publish_promotion(promotion)
        
        return promotion
    
    def _select_template(self, recipe_suggestion):
        """
        Sélectionne le template de promotion le plus approprié pour la recette.
        
        Args:
            recipe_suggestion: Suggestion de recette
            
        Returns:
            Template de promotion sélectionné
        """
        # Facteurs à considérer pour la sélection du template
        is_weekend = datetime.now().weekday() >= 5  # 5 = Samedi, 6 = Dimanche
        has_promotional_ingredient = any(
            ingredient.lower() in str(recipe_suggestion.get('description', '')).lower()
            for ingredient in ['promotion', 'saison', 'spécial']
        )
        is_new_creation = recipe_suggestion.get('is_new_creation', False)
        price = recipe_suggestion.get('price', 0)
        
        # Logique de sélection
        if is_weekend:
            template_name = 'weekend_special'
        elif has_promotional_ingredient:
            template_name = 'ingredient_spotlight'
        elif is_new_creation:
            template_name = 'flash_sale'
        else:
            template_name = 'standard'
        
        # Ajuste le type de discount en fonction du prix
        template = self.promotion_templates.get(template_name, self.promotion_templates['standard']).copy()
        
        if price > 15:
            # Pour les plats plus chers, on préfère un pourcentage
            template['discount_type'] = 'percentage'
            template['discount_value'] = min(20, template['discount_value'])  # Max 20%
        elif price < 8:
            # Pour les plats moins chers, on préfère un montant fixe
            template['discount_type'] = 'fixed'
            template['discount_value'] = min(2, template['discount_value'])  # Max 2€
        
        logger.debug(f"Template sélectionné: {template_name}")
        return template
    
    def _generate_promotion_details(self, recipe_suggestion, template):
        """
        Génère les détails complets d'une promotion.
        
        Args:
            recipe_suggestion: Suggestion de recette
            template: Template de promotion à utiliser
            
        Returns:
            Dictionnaire contenant les détails de la promotion
        """
        recipe_name = recipe_suggestion.get('name', '')
        main_ingredients = recipe_suggestion.get('main_ingredients', [])
        main_ingredient = main_ingredients[0] if main_ingredients else "ingrédient"
        
        # Génération du titre et de la description
        title_template = template.get('title', '{recipe_name}')
        description_template = template.get('description', '')
        
        title = self._format_template_string(title_template, {
            'recipe_name': recipe_name,
            'main_ingredient': main_ingredient
        })
        
        description = self._format_template_string(description_template, {
            'recipe_name': recipe_name,
            'main_ingredient': main_ingredient
        })
        
        # Calcul du prix promotionnel
        original_price = recipe_suggestion.get('price', 10.0)
        discount_type = template.get('discount_type', 'percentage')
        discount_value = template.get('discount_value', 10)
        
        if discount_type == 'percentage':
            discounted_price = round(original_price * (1 - discount_value / 100), 2)
            discount_description = f"{discount_value}% de réduction"
        else:  # fixed
            discounted_price = round(max(0, original_price - discount_value), 2)
            discount_description = f"{discount_value}€ de réduction"
        
        # Calcul des dates de début et fin
        start_date = datetime.now()
        duration_hours = template.get('duration_hours', 24)
        end_date = start_date + timedelta(hours=duration_hours)
        
        # Génération d'un identifiant unique
        promotion_id = hashlib.md5(f"{recipe_name}_{start_date.isoformat()}".encode()).hexdigest()[:10]
        
        # Assemblage de la promotion complète
        promotion = {
            'promotion_id': promotion_id,
            'recipe_id': recipe_suggestion.get('recipe_id', None),
            'recipe_name': recipe_name,
            'title': title,
            'description': description,
            'main_ingredient': main_ingredient,
            'original_price': original_price,
            'discounted_price': discounted_price,
            'discount_type': discount_type,
            'discount_value': discount_value,
            'discount_description': discount_description,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_hours': duration_hours,
            'channels': template.get('channels', []),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Promotion générée: {title} ({promotion_id})")
        return promotion
    
    def _format_template_string(self, template_str, replacements):
        """
        Formate une chaîne de template avec les remplacements spécifiés.
        
        Args:
            template_str: Chaîne contenant des placeholders {key}
            replacements: Dictionnaire de remplacements
            
        Returns:
            Chaîne formatée
        """
        result = template_str
        
        # Remplacement simple des clés entre accolades
        for key, value in replacements.items():
            placeholder = '{' + key + '}'
            result = result.replace(placeholder, str(value))
        
        # Capitalisation de la première lettre après certains caractères
        def capitalize_match(match):
            return match.group(0).upper()
            
        result = re.sub(r'(^|[.!?]\s+)([a-z])', capitalize_match, result)
        
        return result
    
    def _publish_promotion(self, promotion):
        """
        Publie la promotion sur les canaux configurés.
        
        Args:
            promotion: Promotion à publier
        """
        channels = promotion.get('channels', [])
        logger.info(f"Publication de la promotion {promotion['promotion_id']} sur {len(channels)} canaux")
        
        for channel in channels:
            try:
                if channel == 'in_store':
                    self._publish_to_in_store(promotion)
                elif channel == 'social_media':
                    self._publish_to_social_media(promotion)
                elif channel == 'website':
                    self._publish_to_website(promotion)
                elif channel == 'email':
                    self._publish_to_email(promotion)
                else:
                    logger.warning(f"Canal de publication inconnu: {channel}")
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur {channel}: {e}")
    
    def _publish_to_in_store(self, promotion):
        """
        Publie la promotion en magasin (affichage, menu, etc.).
        
        Args:
            promotion: Promotion à publier
        """
        # Dans un environnement réel, cela pourrait envoyer la promotion
        # au système d'affichage numérique, générer des fiches à imprimer, etc.
        logger.info(f"Promotion publiée en magasin: {promotion['title']}")
        
        # Exemple d'intégration avec un système d'affichage
        # display_api_url = self.config.get('display_api_url')
        # if display_api_url:
        #     response = requests.post(
        #         display_api_url,
        #         json={
        #             'type': 'promotion',
        #             'content': promotion
        #         }
        #     )
        #     if response.status_code != 200:
        #         logger.warning(f"Erreur lors de la publication sur l'affichage: {response.text}")
    
    def _publish_to_social_media(self, promotion):
        """
        Publie la promotion sur les réseaux sociaux.
        
        Args:
            promotion: Promotion à publier
        """
        # Dans un environnement réel, cela pourrait poster la promotion
        # sur Facebook, Instagram, etc.
        logger.info(f"Promotion publiée sur les réseaux sociaux: {promotion['title']}")
        
        # Création du message pour les réseaux sociaux
        message = f"🍽️ {promotion['title']} 🍽️\n\n"
        message += f"{promotion['description']}\n\n"
        message += f"Prix spécial: {promotion['discounted_price']}€ ({promotion['discount_description']})\n"
        message += f"Valable jusqu'au {self._format_date(promotion['end_date'])}"
        
        # Exemple d'intégration avec des API de réseaux sociaux
        # social_config = self.config.get('social_media', {})
        # 
        # # Facebook
        # if 'facebook' in social_config:
        #     import facebook
        #     graph = facebook.GraphAPI(social_config['facebook']['access_token'])
        #     graph.put_object(
        #         parent_object='me',
        #         connection_name='feed',
        #         message=message
        #     )
        # 
        # # Twitter/X
        # if 'twitter' in social_config:
        #     import tweepy
        #     auth = tweepy.OAuth1UserHandler(
        #         social_config['twitter']['consumer_key'],
        #         social_config['twitter']['consumer_secret'],
        #         social_config['twitter']['access_token'],
        #         social_config['twitter']['access_token_secret']
        #     )
        #     api = tweepy.API(auth)
        #     api.update_status(message[:280])  # Limite de caractères Twitter
    
    def _publish_to_website(self, promotion):
        """
        Publie la promotion sur le site web du restaurant.
        
        Args:
            promotion: Promotion à publier
        """
        # Dans un environnement réel, cela pourrait mettre à jour la page des promotions
        # sur le site web, ajouter une bannière, etc.
        logger.info(f"Promotion publiée sur le site web: {promotion['title']}")
        
        # Exemple d'intégration avec une API de site web
        # website_api_url = self.config.get('website_api_url')
        # if website_api_url:
        #     response = requests.post(
        #         f"{website_api_url}/promotions",
        #         json=promotion,
        #         headers={
        #             'Authorization': f"Bearer {self.config.get('website_api_key')}"
        #         }
        #     )
        #     if response.status_code != 200:
        #         logger.warning(f"Erreur lors de la publication sur le site web: {response.text}")
    
    def _publish_to_email(self, promotion):
        """
        Envoie la promotion par email aux clients abonnés.
        
        Args:
            promotion: Promotion à publier
        """
        # Dans un environnement réel, cela pourrait envoyer un email
        # aux clients abonnés à la newsletter
        logger.info(f"Promotion envoyée par email: {promotion['title']}")
        
        # Création du contenu de l'email
        subject = f"🍽️ {promotion['title']} - Offre spéciale Le Vieux Moulin"
        
        body = f"<h2>{promotion['title']}</h2>"
        body += f"<p>{promotion['description']}</p>"
        body += f"<p><strong>Prix spécial: {promotion['discounted_price']}€</strong> "
        body += f"<span style='color:#e74c3c'>({promotion['discount_description']})</span></p>"
        body += f"<p>Valable jusqu'au {self._format_date(promotion['end_date'])}</p>"
        body += "<p>À bientôt au Vieux Moulin!</p>"
        
        # Exemple d'intégration avec un service d'emails
        # email_config = self.config.get('email_service', {})
        # 
        # if email_config:
        #     import smtplib
        #     from email.mime.multipart import MIMEMultipart
        #     from email.mime.text import MIMEText
        #     
        #     msg = MIMEMultipart()
        #     msg['From'] = email_config.get('from_email')
        #     msg['Subject'] = subject
        #     msg.attach(MIMEText(body, 'html'))
        #     
        #     # Récupération des abonnés à la newsletter
        #     subscribers = self._get_email_subscribers()
        #     
        #     # Envoi des emails
        #     server = smtplib.SMTP(email_config.get('smtp_server'), email_config.get('smtp_port'))
        #     server.starttls()
        #     server.login(email_config.get('username'), email_config.get('password'))
        #     
        #     for subscriber in subscribers:
        #         msg['To'] = subscriber
        #         server.send_message(msg)
        #     
        #     server.quit()
    
    def _get_email_subscribers(self):
        """
        Récupère la liste des abonnés à la newsletter.
        
        Returns:
            Liste d'adresses email
        """
        # Dans un environnement réel, cela pourrait interroger une base de données
        # ou un service CRM pour obtenir la liste des abonnés
        return ['client1@example.com', 'client2@example.com']
    
    def _format_date(self, iso_date_str):
        """
        Formate une date ISO en format lisible.
        
        Args:
            iso_date_str: Date au format ISO
            
        Returns:
            Date formatée
        """
        try:
            date = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
            return date.strftime('%d/%m/%Y à %H:%M')
        except (ValueError, TypeError) as e:
            logger.warning(f"Erreur dans le formatage de la date: {e}")
            return iso_date_str
    
    def get_active_promotions(self):
        """
        Récupère toutes les promotions actuellement actives.
        
        Returns:
            Liste des promotions actives
        """
        now = datetime.now().isoformat()
        
        active_promotions = [
            promo for promo in self.promotion_history
            if promo.get('status') == 'active' and promo.get('end_date') > now
        ]
        
        logger.info(f"Promotions actives: {len(active_promotions)}")
        return active_promotions
    
    def cancel_promotion(self, promotion_id):
        """
        Annule une promotion spécifique.
        
        Args:
            promotion_id: ID de la promotion à annuler
            
        Returns:
            Succès de l'opération
        """
        for i, promo in enumerate(self.promotion_history):
            if promo.get('promotion_id') == promotion_id:
                self.promotion_history[i]['status'] = 'cancelled'
                self.promotion_history[i]['cancelled_at'] = datetime.now().isoformat()
                self._save_history()
                logger.info(f"Promotion {promotion_id} annulée")
                
                # Notifier les canaux de la promotion annulée
                self._notify_promotion_cancelled(self.promotion_history[i])
                
                return True
        
        logger.warning(f"Promotion {promotion_id} non trouvée pour annulation")
        return False
    
    def _notify_promotion_cancelled(self, promotion):
        """
        Notifie les canaux concernés qu'une promotion a été annulée.
        
        Args:
            promotion: Promotion annulée
        """
        channels = promotion.get('channels', [])
        
        for channel in channels:
            try:
                if channel == 'website':
                    # Supprimer la promotion du site web
                    pass
                elif channel == 'social_media':
                    # Publier une mise à jour sur les réseaux sociaux
                    pass
                elif channel == 'in_store':
                    # Mettre à jour l'affichage en magasin
                    pass
            except Exception as e:
                logger.error(f"Erreur lors de la notification d'annulation sur {channel}: {e}")
