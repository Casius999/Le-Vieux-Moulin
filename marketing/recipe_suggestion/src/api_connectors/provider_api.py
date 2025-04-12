"""
Module de connexion aux API des fournisseurs pour Le Vieux Moulin.

Ce module gère les connexions aux différentes API des fournisseurs
pour récupérer les informations sur les promotions et les produits disponibles.
"""

import logging
import json
import os
import requests
from datetime import datetime, timedelta
import random
import hashlib

logger = logging.getLogger('recipe_suggestion.provider_api')

class ProviderAPI:
    """Gestionnaire de connexion aux API des fournisseurs."""
    
    def __init__(self, config):
        """Initialise le gestionnaire avec la configuration spécifiée."""
        self.config = config
        self.providers = self._load_providers()
        self.cache = {}
        self.cache_timeout = config.get('provider_cache_timeout', 3600)  # 1 heure par défaut
        logger.info(f"Gestionnaire d'API fournisseurs initialisé avec {len(self.providers)} fournisseurs")
    
    def _load_providers(self):
        """Charge la configuration des fournisseurs depuis le fichier JSON."""
        try:
            providers_path = os.path.join('config', 'providers.json')
            with open(providers_path, 'r') as file:
                providers = json.load(file)
                logger.info(f"Configuration de {len(providers)} fournisseurs chargée")
                return providers
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors du chargement des fournisseurs: {e}")
            # Configuration par défaut
            return {
                "metro": {
                    "name": "Metro",
                    "api_type": "rest",
                    "base_url": "https://api.metro.fr/v2",
                    "promotions_endpoint": "/promotions",
                    "products_endpoint": "/products",
                    "auth": {
                        "type": "oauth2",
                        "client_id": "client_id_here",
                        "client_secret": "client_secret_here",
                        "token_url": "https://api.metro.fr/v2/oauth/token"
                    }
                },
                "transgourmet": {
                    "name": "Transgourmet",
                    "api_type": "rest",
                    "base_url": "https://api.transgourmet.fr/api",
                    "promotions_endpoint": "/promotions/current",
                    "products_endpoint": "/products/catalog",
                    "auth": {
                        "type": "api_key",
                        "key_name": "x-api-key",
                        "key_value": "api_key_here"
                    }
                },
                "pomona": {
                    "name": "Pomona",
                    "api_type": "soap",
                    "wsdl_url": "https://api.pomona.fr/services/PromotionService?wsdl",
                    "auth": {
                        "type": "basic",
                        "username": "username_here",
                        "password": "password_here"
                    }
                }
            }
    
    def get_current_promotions(self, providers=None, force_refresh=False):
        """
        Récupère les promotions actuelles de tous les fournisseurs ou fournisseurs spécifiés.
        
        Args:
            providers: Liste des fournisseurs à interroger (None = tous)
            force_refresh: Force une actualisation des données sans utiliser le cache
            
        Returns:
            Liste des promotions actuelles
        """
        providers_to_query = providers or list(self.providers.keys())
        logger.info(f"Récupération des promotions pour {len(providers_to_query)} fournisseurs")
        
        all_promotions = []
        
        for provider_id in providers_to_query:
            if provider_id not in self.providers:
                logger.warning(f"Fournisseur inconnu: {provider_id}")
                continue
                
            # Vérification du cache si force_refresh est False
            cache_key = f"promotions_{provider_id}"
            if not force_refresh and cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if (datetime.now() - cache_entry['timestamp']).total_seconds() < self.cache_timeout:
                    logger.info(f"Utilisation du cache pour {provider_id}")
                    all_promotions.extend(cache_entry['data'])
                    continue
            
            # Si pas de cache valide, requête l'API
            provider_promotions = self._get_provider_promotions(provider_id)
            
            # Mise en cache des résultats
            self.cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': provider_promotions
            }
            
            all_promotions.extend(provider_promotions)
        
        return all_promotions
    
    def _get_provider_promotions(self, provider_id):
        """
        Récupère les promotions d'un fournisseur spécifique.
        
        Args:
            provider_id: Identifiant du fournisseur
            
        Returns:
            Liste des promotions du fournisseur
        """
        provider = self.providers[provider_id]
        logger.info(f"Récupération des promotions du fournisseur: {provider['name']}")
        
        try:
            # En environnement réel, appel à l'API du fournisseur
            # Si API REST
            if provider.get('api_type') == 'rest':
                # url = f"{provider['base_url']}{provider['promotions_endpoint']}"
                # headers = self._get_auth_headers(provider_id)
                # response = requests.get(url, headers=headers)
                # return self._parse_rest_promotions(response.json(), provider_id)
                
                # Pour le développement, génération de données fictives
                return self._generate_mock_promotions(provider_id)
                
            # Si API SOAP
            elif provider.get('api_type') == 'soap':
                # En environnement réel, appel à l'API SOAP
                # from zeep import Client
                # client = Client(provider['wsdl_url'])
                # auth = self._get_soap_auth(provider_id)
                # response = client.service.GetCurrentPromotions(**auth)
                # return self._parse_soap_promotions(response, provider_id)
                
                # Pour le développement, génération de données fictives
                return self._generate_mock_promotions(provider_id)
                
            else:
                logger.warning(f"Type d'API non supporté pour {provider_id}: {provider.get('api_type')}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des promotions pour {provider_id}: {e}")
            # En cas d'erreur, utilisation de données fictives pour le développement
            return self._generate_mock_promotions(provider_id)
    
    def _get_auth_headers(self, provider_id):
        """
        Génère les en-têtes d'authentification pour un fournisseur.
        
        Args:
            provider_id: Identifiant du fournisseur
            
        Returns:
            Dictionnaire des en-têtes d'authentification
        """
        provider = self.providers[provider_id]
        auth = provider.get('auth', {})
        auth_type = auth.get('type')
        
        headers = {}
        
        if auth_type == 'api_key':
            headers[auth.get('key_name')] = auth.get('key_value')
            
        elif auth_type == 'oauth2':
            # En environnement réel, obtention du token OAuth2
            # token_response = requests.post(
            #     auth.get('token_url'),
            #     data={
            #         'grant_type': 'client_credentials',
            #         'client_id': auth.get('client_id'),
            #         'client_secret': auth.get('client_secret')
            #     }
            # )
            # token = token_response.json().get('access_token')
            # headers['Authorization'] = f"Bearer {token}"
            
            # Pour le développement, token fictif
            token = f"dev_token_{provider_id}_{datetime.now().strftime('%Y%m%d')}"
            headers['Authorization'] = f"Bearer {token}"
            
        elif auth_type == 'basic':
            # En environnement réel, Basic Auth
            # import base64
            # credentials = f"{auth.get('username')}:{auth.get('password')}"
            # encoded = base64.b64encode(credentials.encode()).decode()
            # headers['Authorization'] = f"Basic {encoded}"
            
            # Pour le développement, pas besoin d'encodage réel
            headers['Authorization'] = f"Basic dev_basic_auth_{provider_id}"
        
        return headers
    
    def _get_soap_auth(self, provider_id):
        """
        Prépare les paramètres d'authentification pour une API SOAP.
        
        Args:
            provider_id: Identifiant du fournisseur
            
        Returns:
            Dictionnaire des paramètres d'authentification
        """
        provider = self.providers[provider_id]
        auth = provider.get('auth', {})
        
        # Pour une API SOAP, on retourne généralement les identifiants
        # qui seront utilisés dans l'appel de méthode
        return {
            'username': auth.get('username'),
            'password': auth.get('password')
        }
    
    def _parse_rest_promotions(self, data, provider_id):
        """
        Parse les données de promotions d'une API REST.
        
        Args:
            data: Données de la réponse
            provider_id: Identifiant du fournisseur
            
        Returns:
            Liste formatée des promotions
        """
        promotions = []
        provider = self.providers[provider_id]
        
        # Le parsing dépend du format de réponse de chaque fournisseur
        # Voici un exemple générique à adapter
        for item in data.get('items', []):
            promotion = {
                'provider_id': provider_id,
                'provider_name': provider['name'],
                'promotion_id': item.get('id'),
                'ingredient': item.get('product_name', ''),
                'description': item.get('description', ''),
                'discount_percentage': item.get('discount_percentage', 0),
                'discount_amount': item.get('discount_amount', 0),
                'original_price': item.get('original_price', 0),
                'discounted_price': item.get('discounted_price', 0),
                'start_date': item.get('start_date'),
                'end_date': item.get('end_date'),
                'category': item.get('category'),
                'available_quantity': item.get('available_quantity', 0),
                'unit': item.get('unit', 'kg'),
                'days_until_expiry': self._calculate_days_until_expiry(item.get('end_date'))
            }
            promotions.append(promotion)
        
        return promotions
    
    def _parse_soap_promotions(self, response, provider_id):
        """
        Parse les données de promotions d'une API SOAP.
        
        Args:
            response: Données de la réponse
            provider_id: Identifiant du fournisseur
            
        Returns:
            Liste formatée des promotions
        """
        promotions = []
        provider = self.providers[provider_id]
        
        # Le parsing dépend du format de réponse de chaque fournisseur
        # Voici un exemple générique à adapter
        for item in response:
            promotion = {
                'provider_id': provider_id,
                'provider_name': provider['name'],
                'promotion_id': item.PromotionId,
                'ingredient': item.ProductName,
                'description': item.Description,
                'discount_percentage': item.DiscountPercentage,
                'discount_amount': item.DiscountAmount,
                'original_price': item.OriginalPrice,
                'discounted_price': item.DiscountedPrice,
                'start_date': item.StartDate,
                'end_date': item.EndDate,
                'category': item.Category,
                'available_quantity': item.AvailableQuantity,
                'unit': item.Unit,
                'days_until_expiry': self._calculate_days_until_expiry(item.EndDate)
            }
            promotions.append(promotion)
        
        return promotions
    
    def _calculate_days_until_expiry(self, end_date_str):
        """
        Calcule le nombre de jours jusqu'à l'expiration d'une promotion.
        
        Args:
            end_date_str: Date de fin de la promotion
            
        Returns:
            Nombre de jours jusqu'à l'expiration (0 si expiré)
        """
        if not end_date_str:
            return 0
            
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            days = (end_date - datetime.now(end_date.tzinfo)).days
            return max(0, days)
        except (ValueError, TypeError) as e:
            logger.warning(f"Erreur dans le calcul de la date d'expiration: {e}")
            return 0
    
    def _generate_mock_promotions(self, provider_id):
        """
        Génère des promotions fictives pour un fournisseur.
        
        Args:
            provider_id: Identifiant du fournisseur
            
        Returns:
            Liste de promotions fictives
        """
        provider = self.providers[provider_id]
        
        # Nombre de promotions à générer
        if provider_id == "metro":
            num_promotions = random.randint(10, 20)
        elif provider_id == "transgourmet":
            num_promotions = random.randint(8, 15)
        else:
            num_promotions = random.randint(5, 12)
        
        promotions = []
        
        # Ingrédients possibles par catégorie
        ingredients = {
            "viandes": ["bœuf haché", "magret de canard", "poulet fermier", "bavette d'aloyau", "veau", "porc", "agneau"],
            "poissons": ["saumon", "thon", "cabillaud", "dorade", "bar", "crevettes"],
            "légumes": ["tomate", "poivron", "aubergine", "courgette", "champignon", "artichaut", "asperge"],
            "fruits": ["fraise", "framboise", "pomme", "poire", "orange", "citron", "abricot"],
            "fromages": ["mozzarella", "parmesan", "chèvre", "bleu", "comté", "emmental", "burrata"],
            "épicerie": ["huile d'olive", "vinaigre balsamique", "pâtes", "riz", "farine", "sucre"],
            "charcuterie": ["jambon blanc", "jambon cru", "chorizo", "saucisson", "coppa", "pancetta"]
        }
        
        # Génération des promotions
        today = datetime.now()
        for i in range(num_promotions):
            # Catégorie aléatoire
            category = random.choice(list(ingredients.keys()))
            # Ingrédient aléatoire dans la catégorie
            ingredient = random.choice(ingredients[category])
            
            # Prix original
            original_price = round(random.uniform(5, 30), 2)
            
            # Pourcentage de réduction
            discount_percentage = random.choice([10, 15, 20, 25, 30, 40, 50])
            
            # Prix après réduction
            discounted_price = round(original_price * (1 - discount_percentage / 100), 2)
            
            # Dates de début et fin de la promotion
            start_date = (today - timedelta(days=random.randint(0, 5))).isoformat()
            end_date = (today + timedelta(days=random.randint(1, 15))).isoformat()
            
            # Création d'un ID unique basé sur le fournisseur et l'ingrédient
            promotion_id = hashlib.md5(f"{provider_id}_{ingredient}_{i}".encode()).hexdigest()[:10]
            
            promotion = {
                'provider_id': provider_id,
                'provider_name': provider['name'],
                'promotion_id': promotion_id,
                'ingredient': ingredient,
                'description': f"Promotion sur {ingredient} - {discount_percentage}% de réduction",
                'discount_percentage': discount_percentage,
                'discount_amount': round(original_price - discounted_price, 2),
                'original_price': original_price,
                'discounted_price': discounted_price,
                'start_date': start_date,
                'end_date': end_date,
                'category': category,
                'available_quantity': random.randint(10, 200),
                'unit': random.choice(['kg', 'pièce', 'paquet', 'barquette', 'litre']),
                'days_until_expiry': random.randint(1, 15)
            }
            
            promotions.append(promotion)
        
        return promotions
    
    def get_product_details(self, product_id, provider_id):
        """
        Récupère les détails d'un produit spécifique.
        
        Args:
            product_id: Identifiant du produit
            provider_id: Identifiant du fournisseur
            
        Returns:
            Détails du produit
        """
        # Cette méthode suivrait une logique similaire à get_current_promotions
        # mais pour les détails d'un produit spécifique
        logger.info(f"Récupération des détails du produit {product_id} du fournisseur {provider_id}")
        
        # En environnement réel, appel à l'API du fournisseur
        # Pour le développement, génération de données fictives
        return self._generate_mock_product_details(product_id, provider_id)
    
    def _generate_mock_product_details(self, product_id, provider_id):
        """
        Génère des détails de produit fictifs.
        
        Args:
            product_id: Identifiant du produit
            provider_id: Identifiant du fournisseur
            
        Returns:
            Détails fictifs du produit
        """
        provider = self.providers.get(provider_id, {"name": "Fournisseur inconnu"})
        
        # Création d'un produit fictif basé sur l'ID
        return {
            'product_id': product_id,
            'provider_id': provider_id,
            'provider_name': provider['name'],
            'name': f"Produit {product_id}",
            'description': f"Description détaillée du produit {product_id}",
            'category': "Catégorie test",
            'price': round(random.uniform(5, 50), 2),
            'unit': random.choice(['kg', 'pièce', 'paquet']),
            'available': True,
            'stock_level': random.randint(10, 100),
            'allergens': ["gluten", "lactose"] if random.random() > 0.5 else [],
            'nutritional_info': {
                'calories': random.randint(100, 500),
                'proteins': round(random.uniform(0, 30), 1),
                'carbs': round(random.uniform(0, 50), 1),
                'fats': round(random.uniform(0, 40), 1)
            }
        }
