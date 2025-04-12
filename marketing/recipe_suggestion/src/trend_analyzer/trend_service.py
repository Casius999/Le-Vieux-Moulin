"""
Service d'analyse des tendances pour Le Vieux Moulin.

Ce module analyse les tendances locales, les préférences clients
et les données de vente pour identifier les tendances actuelles.
"""

import logging
import json
import os
from datetime import datetime, timedelta
import random
import requests

logger = logging.getLogger('recipe_suggestion.trends')

class TrendAnalyzer:
    """Analyseur de tendances clients et locales."""
    
    def __init__(self, config):
        """Initialise l'analyseur avec la configuration spécifiée."""
        self.config = config
        self.data_sources = self._load_data_sources()
        logger.info("Service d'analyse des tendances initialisé")
    
    def _load_data_sources(self):
        """Charge les sources de données pour l'analyse des tendances."""
        try:
            sources_path = os.path.join('config', 'data_sources.json')
            with open(sources_path, 'r') as file:
                sources = json.load(file)
                logger.info(f"Sources de données chargées: {', '.join(sources.keys())}")
                return sources
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors du chargement des sources de données: {e}")
            # Sources de données par défaut
            return {
                "pos_system": {
                    "type": "api",
                    "endpoint": "http://localhost:8000/api/sales/history",
                    "username": "trend_analyzer",
                    "password": "****"
                },
                "social_media": {
                    "type": "api",
                    "platforms": ["instagram", "facebook", "google_reviews"],
                    "endpoint": "http://localhost:8000/api/social/trends"
                },
                "local_events": {
                    "type": "api",
                    "endpoint": "http://localhost:8000/api/local/events"
                },
                "weather": {
                    "type": "api",
                    "endpoint": "http://localhost:8000/api/weather"
                }
            }
    
    def get_current_trends(self):
        """
        Récupère et analyse les tendances actuelles.
        
        Returns:
            Dictionnaire contenant les tendances identifiées
        """
        logger.info("Analyse des tendances actuelles")
        
        # Récupération des données depuis les différentes sources
        sales_data = self._get_sales_data()
        social_data = self._get_social_media_trends()
        local_events = self._get_local_events()
        weather_data = self._get_weather_data()
        
        # Fusion et analyse des données
        trends = self._analyze_trends(sales_data, social_data, local_events, weather_data)
        
        return trends
    
    def _get_sales_data(self):
        """Récupère les données de vente récentes."""
        try:
            source = self.data_sources.get('pos_system', {})
            if source.get('type') != 'api':
                return self._generate_mock_sales_data()
                
            # Dans un environnement réel, appel à l'API du système de point de vente
            # response = requests.get(
            #     source.get('endpoint'),
            #     auth=(source.get('username'), source.get('password')),
            #     params={'days': 30}
            # )
            # return response.json()
            
            # Pour le développement, utilisation de données fictives
            return self._generate_mock_sales_data()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de vente: {e}")
            return self._generate_mock_sales_data()
    
    def _generate_mock_sales_data(self):
        """Génère des données de vente fictives pour le développement."""
        today = datetime.now()
        sales_data = {
            "period": f"{(today - timedelta(days=30)).strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
            "total_sales": random.randint(8000, 12000),
            "total_transactions": random.randint(800, 1200),
            "top_selling_items": [
                {"name": "Pizza Margherita", "count": random.randint(80, 120), "revenue": random.randint(800, 1200)},
                {"name": "Magret de canard", "count": random.randint(60, 100), "revenue": random.randint(1000, 1800)},
                {"name": "Pizza Regina", "count": random.randint(50, 90), "revenue": random.randint(600, 1000)},
                {"name": "Tiramisu", "count": random.randint(40, 70), "revenue": random.randint(300, 500)},
                {"name": "Pizza Calzone", "count": random.randint(30, 60), "revenue": random.randint(400, 700)}
            ],
            "sales_by_category": {
                "pizza": {"count": random.randint(300, 500), "revenue": random.randint(3500, 5500)},
                "plat_principal": {"count": random.randint(200, 350), "revenue": random.randint(3000, 5000)},
                "dessert": {"count": random.randint(150, 250), "revenue": random.randint(1000, 2000)},
                "boisson": {"count": random.randint(400, 600), "revenue": random.randint(1200, 2000)}
            },
            "sales_by_day": {
                "monday": random.randint(50, 100),
                "tuesday": random.randint(40, 80),
                "wednesday": random.randint(60, 110),
                "thursday": random.randint(70, 120),
                "friday": random.randint(100, 180),
                "saturday": random.randint(150, 250),
                "sunday": random.randint(120, 200)
            },
            "customer_preferences": {
                "vegetarian": random.uniform(0.15, 0.25),
                "spicy": random.uniform(0.30, 0.40),
                "local_products": random.uniform(0.40, 0.60),
                "premium": random.uniform(0.20, 0.35)
            },
            "ingredient_popularity": [
                {"name": "mozzarella", "score": random.uniform(0.8, 1.0)},
                {"name": "tomate", "score": random.uniform(0.7, 0.9)},
                {"name": "champignon", "score": random.uniform(0.6, 0.8)},
                {"name": "jambon", "score": random.uniform(0.5, 0.7)},
                {"name": "magret", "score": random.uniform(0.4, 0.6)},
                {"name": "chocolat", "score": random.uniform(0.3, 0.5)}
            ]
        }
        
        return sales_data
    
    def _get_social_media_trends(self):
        """Récupère les tendances des réseaux sociaux."""
        try:
            source = self.data_sources.get('social_media', {})
            if source.get('type') != 'api':
                return self._generate_mock_social_data()
                
            # Dans un environnement réel, appel à l'API d'analyse des réseaux sociaux
            # response = requests.get(
            #     source.get('endpoint'),
            #     params={'platforms': ','.join(source.get('platforms', []))}
            # )
            # return response.json()
            
            # Pour le développement, utilisation de données fictives
            return self._generate_mock_social_data()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tendances sociales: {e}")
            return self._generate_mock_social_data()
    
    def _generate_mock_social_data(self):
        """Génère des données sociales fictives pour le développement."""
        # Tendances possibles sur les réseaux sociaux
        possible_trends = [
            {"term": "pizza artisanale", "category": "dish", "score": random.uniform(0.7, 1.0)},
            {"term": "produits locaux", "category": "concept", "score": random.uniform(0.6, 0.9)},
            {"term": "cuisine méditerranéenne", "category": "cuisine", "score": random.uniform(0.5, 0.8)},
            {"term": "truffe", "category": "ingredient", "score": random.uniform(0.4, 0.7)},
            {"term": "burrata", "category": "ingredient", "score": random.uniform(0.6, 0.9)},
            {"term": "pizza au feu de bois", "category": "cooking_style", "score": random.uniform(0.5, 0.8)},
            {"term": "cuisine fusion", "category": "concept", "score": random.uniform(0.3, 0.6)},
            {"term": "saveurs d'été", "category": "concept", "score": random.uniform(0.4, 0.7)},
            {"term": "desserts italiens", "category": "dish", "score": random.uniform(0.3, 0.6)},
            {"term": "nourriture instagrammable", "category": "concept", "score": random.uniform(0.7, 1.0)}
        ]
        
        # Sélection aléatoire de tendances
        selected_trends = random.sample(possible_trends, min(5, len(possible_trends)))
        
        # Posts populaires fictifs
        popular_posts = [
            {
                "platform": "instagram",
                "post_id": "12345",
                "likes": random.randint(50, 200),
                "description": "Cette pizza aux truffes est incroyable! #foodporn #pizza #truffe",
                "relevant_tags": ["pizza", "truffe", "foodporn"]
            },
            {
                "platform": "facebook",
                "post_id": "67890",
                "likes": random.randint(30, 150),
                "description": "Soirée parfaite avec ces mets délicieux et ce vin local!",
                "relevant_tags": ["vin local", "gastronomie"]
            }
        ]
        
        # Génération du résultat
        social_data = {
            "period": "last 7 days",
            "keywords": selected_trends,
            "popular_posts": popular_posts,
            "sentiment": {
                "positive": random.uniform(0.6, 0.8),
                "neutral": random.uniform(0.1, 0.3),
                "negative": random.uniform(0.0, 0.1)
            },
            "engagement_by_topic": {
                "food": random.uniform(0.6, 0.9),
                "service": random.uniform(0.3, 0.6),
                "ambiance": random.uniform(0.4, 0.7),
                "price": random.uniform(0.2, 0.5)
            }
        }
        
        return social_data
    
    def _get_local_events(self):
        """Récupère les événements locaux actuels et à venir."""
        try:
            source = self.data_sources.get('local_events', {})
            if source.get('type') != 'api':
                return self._generate_mock_events()
                
            # Dans un environnement réel, appel à l'API d'événements locaux
            # response = requests.get(
            #     source.get('endpoint'),
            #     params={'radius': 20, 'days_ahead': 14}
            # )
            # return response.json()
            
            # Pour le développement, utilisation de données fictives
            return self._generate_mock_events()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des événements locaux: {e}")
            return self._generate_mock_events()
    
    def _generate_mock_events(self):
        """Génère des événements locaux fictifs pour le développement."""
        today = datetime.now()
        
        # Événements possibles
        possible_events = [
            {
                "name": "Festival des vins de Médoc",
                "type": "festival",
                "start_date": (today + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=random.randint(8, 10))).strftime('%Y-%m-%d'),
                "expected_attendance": random.randint(500, 2000),
                "distance": random.randint(1, 15),
                "food_related": True,
                "keywords": ["vin", "médoc", "gastronomie"]
            },
            {
                "name": "Marché nocturne de Vensac",
                "type": "market",
                "start_date": (today + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=random.randint(6, 8))).strftime('%Y-%m-%d'),
                "expected_attendance": random.randint(200, 800),
                "distance": random.randint(0, 5),
                "food_related": True,
                "keywords": ["marché", "local", "artisanat", "produits locaux"]
            },
            {
                "name": "Concert en plein air",
                "type": "concert",
                "start_date": (today + timedelta(days=random.randint(3, 10))).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=random.randint(3, 10))).strftime('%Y-%m-%d'),
                "expected_attendance": random.randint(300, 1200),
                "distance": random.randint(5, 20),
                "food_related": False,
                "keywords": ["musique", "concert", "été"]
            },
            {
                "name": "Fête locale de Vensac",
                "type": "local_festival",
                "start_date": (today + timedelta(days=random.randint(5, 15))).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=random.randint(7, 17))).strftime('%Y-%m-%d'),
                "expected_attendance": random.randint(500, 1500),
                "distance": random.randint(0, 2),
                "food_related": True,
                "keywords": ["fête", "local", "tradition", "gastronomie"]
            }
        ]
        
        # Sélection aléatoire d'événements
        selected_events = random.sample(possible_events, min(random.randint(1, 3), len(possible_events)))
        
        # Génération du résultat
        events_data = {
            "current_events": [e for e in selected_events if e["start_date"] <= today.strftime('%Y-%m-%d') <= e["end_date"]],
            "upcoming_events": [e for e in selected_events if e["start_date"] > today.strftime('%Y-%m-%d')],
            "recommended_themes": [
                {
                    "theme": "Vins du Médoc" if any("vin" in e.get("keywords", []) for e in selected_events) else "Cuisine locale",
                    "relevance": random.uniform(0.7, 1.0),
                    "suggested_ingredients": ["vin rouge", "fromage", "canard"] if any("vin" in e.get("keywords", []) for e in selected_events) else ["produits locaux", "légumes de saison"]
                }
            ]
        }
        
        return events_data
    
    def _get_weather_data(self):
        """Récupère les données météo actuelles et prévisions."""
        try:
            source = self.data_sources.get('weather', {})
            if source.get('type') != 'api':
                return self._generate_mock_weather()
                
            # Dans un environnement réel, appel à l'API météo
            # response = requests.get(
            #     source.get('endpoint'),
            #     params={'days': 7}
            # )
            # return response.json()
            
            # Pour le développement, utilisation de données fictives
            return self._generate_mock_weather()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données météo: {e}")
            return self._generate_mock_weather()
    
    def _generate_mock_weather(self):
        """Génère des données météo fictives pour le développement."""
        today = datetime.now()
        
        # Types de météo possibles selon la saison
        current_month = today.month
        
        if current_month in [12, 1, 2]:  # Hiver
            possible_conditions = ["cloudy", "rainy", "cold", "windy"]
            temp_range = (3, 12)
        elif current_month in [3, 4, 5]:  # Printemps
            possible_conditions = ["sunny", "partially_cloudy", "rainy", "mild"]
            temp_range = (10, 20)
        elif current_month in [6, 7, 8]:  # Été
            possible_conditions = ["sunny", "hot", "partially_cloudy", "stormy"]
            temp_range = (20, 32)
        else:  # Automne
            possible_conditions = ["rainy", "windy", "partially_cloudy", "mild"]
            temp_range = (12, 22)
        
        # Prévisions pour les prochains jours
        forecast = []
        for i in range(7):
            day = today + timedelta(days=i)
            forecast.append({
                "date": day.strftime('%Y-%m-%d'),
                "condition": random.choice(possible_conditions),
                "temperature": {
                    "min": random.randint(temp_range[0], temp_range[0] + 5),
                    "max": random.randint(temp_range[1] - 5, temp_range[1])
                },
                "precipitation": random.uniform(0, 100) if "rainy" in possible_conditions else 0
            })
        
        # Génération des recommandations culinaires basées sur la météo
        weather_based_recommendations = []
        
        current_condition = forecast[0]["condition"]
        current_temp = (forecast[0]["temperature"]["min"] + forecast[0]["temperature"]["max"]) / 2
        
        if current_condition in ["rainy", "cold", "windy"] or current_temp < 15:
            weather_based_recommendations.append({
                "type": "warm_comfort_food",
                "reason": "Temps frais ou pluvieux",
                "suggested_categories": ["pizza", "plats mijotés", "soupes"],
                "relevance": random.uniform(0.7, 1.0)
            })
        elif current_condition in ["sunny", "hot"] or current_temp > 25:
            weather_based_recommendations.append({
                "type": "light_refreshing",
                "reason": "Temps chaud et ensoleillé",
                "suggested_categories": ["salades", "plats légers", "desserts frais"],
                "relevance": random.uniform(0.7, 1.0)
            })
        else:
            weather_based_recommendations.append({
                "type": "balanced",
                "reason": "Temps modéré",
                "suggested_categories": ["plats équilibrés", "options diverses"],
                "relevance": random.uniform(0.5, 0.8)
            })
        
        # Génération du résultat
        weather_data = {
            "current": forecast[0],
            "forecast": forecast,
            "dining_recommendations": weather_based_recommendations
        }
        
        return weather_data
    
    def _analyze_trends(self, sales_data, social_data, local_events, weather_data):
        """
        Analyse les données de différentes sources pour identifier les tendances.
        
        Returns:
            Dictionnaire des tendances identifiées
        """
        trends = {
            "timestamp": datetime.now().isoformat(),
            "keywords": [],
            "popular_dishes": [],
            "ingredients_trend": [],
            "consumer_preferences": {},
            "event_related_suggestions": [],
            "weather_suggestions": []
        }
        
        # 1. Analyse des mots-clés populaires (réseaux sociaux)
        if "keywords" in social_data:
            trends["keywords"] = social_data["keywords"]
        
        # 2. Plats populaires (ventes)
        if "top_selling_items" in sales_data:
            for item in sales_data["top_selling_items"]:
                # Extraction des ingrédients des plats populaires
                # Dans un environnement réel, cela serait lié à une base de données de recettes
                ingredients = self._extract_mock_ingredients(item["name"])
                
                trends["popular_dishes"].append({
                    "name": item["name"],
                    "popularity": item["count"] / sales_data.get("total_transactions", 1000),
                    "ingredients": ingredients
                })
        
        # 3. Tendances des ingrédients
        if "ingredient_popularity" in sales_data:
            trends["ingredients_trend"] = sales_data["ingredient_popularity"]
        
        # 4. Préférences consommateurs
        if "customer_preferences" in sales_data:
            trends["consumer_preferences"] = sales_data["customer_preferences"]
        
        # 5. Suggestions liées aux événements
        for event_list in ["current_events", "upcoming_events"]:
            if event_list in local_events:
                for event in local_events[event_list]:
                    if event.get("food_related"):
                        trends["event_related_suggestions"].append({
                            "event_name": event["name"],
                            "theme": event["keywords"][0] if event.get("keywords") else "local",
                            "relevance": 0.8 if event_list == "current_events" else 0.6,
                            "suggested_ingredients": self._get_theme_ingredients(event.get("keywords", []))
                        })
        
        # 6. Suggestions liées à la météo
        if "dining_recommendations" in weather_data:
            trends["weather_suggestions"] = weather_data["dining_recommendations"]
        
        # 7. Indicateurs supplémentaires
        current_month = datetime.now().month
        trends["seasonal"] = current_month in [6, 7, 8]  # Saison estivale (juin-août)
        trends["weekend"] = datetime.now().weekday() >= 5  # Weekend (samedi-dimanche)
        trends["premium_trend"] = sales_data.get("customer_preferences", {}).get("premium", 0) > 0.3
        trends["consider_seasonal"] = True
        
        return trends
    
    def _extract_mock_ingredients(self, dish_name):
        """Extrait les ingrédients fictifs d'un plat basé sur son nom."""
        # Correspondances simplifiées pour la démonstration
        dish_ingredients = {
            "Pizza Margherita": ["sauce tomate", "mozzarella", "basilic"],
            "Magret de canard": ["magret", "miel", "pomme de terre"],
            "Pizza Regina": ["sauce tomate", "mozzarella", "jambon", "champignon"],
            "Tiramisu": ["mascarpone", "café", "cacao", "biscuit"],
            "Pizza Calzone": ["sauce tomate", "mozzarella", "jambon", "champignon", "œuf"]
        }
        
        # Recherche par correspondance exacte ou partielle
        for key, ingredients in dish_ingredients.items():
            if key.lower() == dish_name.lower():
                return ingredients
            elif key.lower() in dish_name.lower():
                return ingredients
        
        # Si aucune correspondance, ingrédients génériques selon le type de plat
        if "pizza" in dish_name.lower():
            return ["sauce tomate", "mozzarella", "ingrédient spécial"]
        elif "dessert" in dish_name.lower() or "gâteau" in dish_name.lower():
            return ["sucre", "farine", "beurre", "œuf"]
        else:
            return ["ingrédient principal", "accompagnement", "sauce"]
    
    def _get_theme_ingredients(self, keywords):
        """Détermine les ingrédients suggérés en fonction d'un thème."""
        theme_ingredients = {
            "vin": ["magret", "fromage", "champignon"],
            "médoc": ["vin rouge", "canard", "cèpes"],
            "gastronomie": ["truffe", "foie gras", "champignon"],
            "marché": ["légumes frais", "fromage local", "herbes fraîches"],
            "local": ["produits du terroir", "spécialités régionales"],
            "artisanat": ["produits artisanaux", "spécialités locales"],
            "tradition": ["recettes traditionnelles", "produits du terroir"]
        }
        
        suggested_ingredients = []
        for keyword in keywords:
            if keyword.lower() in theme_ingredients:
                suggested_ingredients.extend(theme_ingredients[keyword.lower()])
        
        # Éliminer les doublons et limiter le nombre d'ingrédients
        return list(set(suggested_ingredients))[:5]
