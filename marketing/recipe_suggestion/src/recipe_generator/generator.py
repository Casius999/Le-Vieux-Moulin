"""
Module de génération de recettes pour Le Vieux Moulin.

Ce module contient l'algorithme principal de génération de suggestions de recettes
basées sur les promotions fournisseurs et les tendances clients.
"""

import logging
import random
from datetime import datetime
import os
import json
import math

logger = logging.getLogger('recipe_suggestion.generator')

class RecipeGenerator:
    """Générateur de recettes basé sur les promotions et tendances."""
    
    def __init__(self, config):
        """Initialise le générateur avec la configuration spécifiée."""
        self.config = config
        self.base_recipes = self._load_base_recipes()
        self.ingredient_combinations = self._load_ingredient_combinations()
        self.previous_suggestions = self._load_previous_suggestions()
        logger.info("Générateur de recettes initialisé")
    
    def _load_base_recipes(self):
        """Charge la base de recettes depuis le fichier JSON."""
        try:
            recipes_path = os.path.join('config', 'recipes_base.json')
            with open(recipes_path, 'r') as file:
                recipes = json.load(file)
                logger.info(f"Base de {len(recipes)} recettes chargée")
                return recipes
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Erreur lors du chargement des recettes: {e}")
            # Base de recettes minimale en cas d'erreur
            return {
                "pizza": [
                    {
                        "name": "Margherita",
                        "ingredients": ["sauce tomate", "mozzarella", "basilic"],
                        "base_price": 10.0,
                        "category": "classique"
                    },
                    {
                        "name": "Regina",
                        "ingredients": ["sauce tomate", "mozzarella", "jambon", "champignons"],
                        "base_price": 12.0,
                        "category": "classique"
                    }
                ],
                "plat_principal": [
                    {
                        "name": "Magret de canard",
                        "ingredients": ["magret de canard", "miel", "vinaigre balsamique"],
                        "base_price": 18.0,
                        "category": "traditionnel"
                    }
                ]
            }
    
    def _load_ingredient_combinations(self):
        """Charge les combinaisons d'ingrédients connues et leurs affinités."""
        try:
            combinations_path = os.path.join('config', 'ingredient_combinations.json')
            with open(combinations_path, 'r') as file:
                combinations = json.load(file)
                logger.info(f"Combinaisons d'ingrédients chargées")
                return combinations
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors du chargement des combinaisons: {e}")
            # Combinaisons de base en cas d'erreur
            return {
                "affinities": {
                    "tomate": ["mozzarella", "basilic", "ail"],
                    "mozzarella": ["tomate", "basilic", "huile d'olive"],
                    "magret": ["miel", "orange", "poivre"],
                    "chocolat": ["framboise", "menthe", "café"]
                },
                "popular_combinations": [
                    ["mozzarella", "tomate", "basilic"],
                    ["magret", "miel", "romarin"],
                    ["saumon", "aneth", "citron"]
                ]
            }
    
    def _load_previous_suggestions(self):
        """Charge l'historique des suggestions récentes."""
        try:
            history_dir = os.path.join('data', 'suggestions')
            files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
            
            if not files:
                return []
            
            # Trie par date (du plus récent au plus ancien)
            files.sort(reverse=True)
            latest_file = os.path.join(history_dir, files[0])
            
            with open(latest_file, 'r') as file:
                history = json.load(file)
                logger.info(f"Historique des suggestions chargé depuis {latest_file}")
                return history
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.warning(f"Pas d'historique de suggestions disponible: {e}")
            return []
    
    def generate_suggestions(self, promotions, trends, count=3):
        """
        Génère des suggestions de recettes basées sur les promotions et tendances.
        
        Args:
            promotions: Liste des promotions fournisseurs actuelles
            trends: Dictionnaire des tendances clients actuelles
            count: Nombre de suggestions à générer
            
        Returns:
            Liste des suggestions de recettes
        """
        logger.info(f"Génération de {count} suggestions de recettes")
        
        # 1. Identifie les ingrédients en promotion intéressants
        promo_ingredients = self._score_promotional_ingredients(promotions)
        logger.debug(f"Top ingrédients en promotion: {list(promo_ingredients.keys())[:5]}")
        
        # 2. Croise avec les tendances actuelles
        trending_ingredients = self._extract_trending_ingredients(trends)
        logger.debug(f"Ingrédients tendance: {trending_ingredients[:5]}")
        
        # 3. Identifie les opportunités (ingrédients à la fois en promo et tendance)
        opportunities = self._identify_opportunities(promo_ingredients, trending_ingredients)
        logger.info(f"Identifié {len(opportunities)} opportunités")
        
        # 4. Génère les suggestions selon différentes méthodes
        suggestions = []
        
        # 4.1 D'abord par adaptation de recettes existantes
        adapted_recipes = self._adapt_existing_recipes(opportunities, count // 2 + 1)
        suggestions.extend(adapted_recipes)
        
        # 4.2 Ensuite par création de nouvelles combinaisons
        remaining = count - len(suggestions)
        if remaining > 0:
            new_recipes = self._create_new_combinations(opportunities, promo_ingredients, remaining)
            suggestions.extend(new_recipes)
        
        # 5. Diversification des suggestions
        suggestions = self._ensure_diversity(suggestions)
        
        # 6. Finalisation des suggestions (noms, descriptions, prix)
        final_suggestions = self._finalize_suggestions(suggestions, promotions, trends)
        
        return final_suggestions
    
    def _score_promotional_ingredients(self, promotions):
        """
        Évalue et score les ingrédients en promotion.
        
        Returns:
            Dictionnaire {ingredient: score} trié par score décroissant
        """
        ingredient_scores = {}
        
        for promo in promotions:
            ingredient = promo.get('ingredient')
            if not ingredient:
                continue
                
            # Calcul du score basé sur plusieurs facteurs
            discount_pct = promo.get('discount_percentage', 0)
            quantity = promo.get('available_quantity', 100)
            expiry_days = promo.get('days_until_expiry', 30)
            
            # Formule de scoring combinant réduction, quantité et fraîcheur
            base_score = discount_pct * 0.7  # La réduction est le facteur principal
            quantity_factor = min(1.0, quantity / 100)  # Normalisé à 1 max
            freshness_factor = math.exp(-max(0, 30 - expiry_days) / 10)  # Décroissance exponentielle
            
            score = base_score * quantity_factor * freshness_factor
            
            # Bonus pour les ingrédients de saison
            if self._is_seasonal_ingredient(ingredient):
                score *= 1.2
            
            ingredient_scores[ingredient] = score
        
        # Tri par score décroissant
        return dict(sorted(ingredient_scores.items(), key=lambda x: x[1], reverse=True))
    
    def _is_seasonal_ingredient(self, ingredient):
        """Détermine si un ingrédient est de saison."""
        # Exemple simplifié - à remplacer par une vraie base de données saisonnière
        current_month = datetime.now().month
        spring = [3, 4, 5]
        summer = [6, 7, 8]
        fall = [9, 10, 11]
        winter = [12, 1, 2]
        
        spring_ingredients = ["asperge", "fraise", "petits pois"]
        summer_ingredients = ["tomate", "aubergine", "courgette", "poivron"]
        fall_ingredients = ["champignon", "potiron", "raisin"]
        winter_ingredients = ["chou", "endive", "poireau"]
        
        if current_month in spring and ingredient.lower() in spring_ingredients:
            return True
        if current_month in summer and ingredient.lower() in summer_ingredients:
            return True
        if current_month in fall and ingredient.lower() in fall_ingredients:
            return True
        if current_month in winter and ingredient.lower() in winter_ingredients:
            return True
        
        return False
    
    def _extract_trending_ingredients(self, trends):
        """Extrait les ingrédients tendance des données de tendances."""
        trending_ingredients = []
        
        # Extraction depuis les mots-clés tendance
        if 'keywords' in trends:
            for keyword in trends['keywords']:
                if keyword.get('category') == 'ingredient':
                    trending_ingredients.append(keyword['term'])
        
        # Extraction depuis les plats populaires
        if 'popular_dishes' in trends:
            for dish in trends['popular_dishes']:
                if 'ingredients' in dish:
                    trending_ingredients.extend(dish['ingredients'])
        
        # Ajout d'ingrédients saisonniers si pertinent
        if trends.get('consider_seasonal', True):
            # Ajout d'ingrédients de saison
            seasonal = self._get_current_seasonal_ingredients()
            trending_ingredients.extend(seasonal)
        
        # Élimination des doublons et normalisation
        return list(set([i.lower() for i in trending_ingredients]))
    
    def _get_current_seasonal_ingredients(self):
        """Retourne une liste d'ingrédients actuellement de saison."""
        # Implémentation simplifiée - à améliorer avec une vraie base de données
        current_month = datetime.now().month
        
        seasonal_map = {
            1: ["endive", "orange", "chou", "poireau"],  # Janvier
            2: ["endive", "orange", "chou", "poireau"],  # Février
            3: ["asperge", "épinard", "radis"],          # Mars
            4: ["asperge", "fraise", "petits pois"],     # Avril
            5: ["fraise", "cerise", "petits pois"],      # Mai
            6: ["cerise", "tomate", "courgette"],        # Juin
            7: ["tomate", "aubergine", "poivron"],       # Juillet
            8: ["tomate", "aubergine", "poivron"],       # Août
            9: ["raisin", "figue", "champignon"],        # Septembre
            10: ["champignon", "potiron", "raisin"],     # Octobre
            11: ["champignon", "potiron", "clémentine"], # Novembre
            12: ["chou", "clémentine", "huître"]         # Décembre
        }
        
        return seasonal_map.get(current_month, [])
    
    def _identify_opportunities(self, promo_ingredients, trending_ingredients):
        """
        Identifie les opportunités commerciales en croisant promotions et tendances.
        
        Returns:
            Liste de dictionnaires {ingredient, promo_score, trend_score, combined_score}
        """
        opportunities = []
        
        for ingredient, promo_score in promo_ingredients.items():
            # Calcul d'un score de tendance
            trend_score = 0
            if ingredient.lower() in map(str.lower, trending_ingredients):
                trend_score = 1.0
            else:
                # Vérifie des termes partiels ou similaires
                for trend in trending_ingredients:
                    if trend.lower() in ingredient.lower() or ingredient.lower() in trend.lower():
                        trend_score = 0.7
                        break
            
            # Score combiné (promotion + tendance)
            combined_score = promo_score * (1 + trend_score)
            
            opportunities.append({
                'ingredient': ingredient,
                'promo_score': promo_score,
                'trend_score': trend_score,
                'combined_score': combined_score
            })
        
        # Tri par score combiné décroissant
        return sorted(opportunities, key=lambda x: x['combined_score'], reverse=True)
    
    def _adapt_existing_recipes(self, opportunities, count):
        """
        Adapte des recettes existantes en fonction des opportunités identifiées.
        
        Returns:
            Liste de recettes adaptées
        """
        adapted_recipes = []
        
        # Pour chaque catégorie de recette
        for category, recipes in self.base_recipes.items():
            if len(adapted_recipes) >= count:
                break
                
            # Pour chaque recette de base
            for base_recipe in recipes:
                if len(adapted_recipes) >= count:
                    break
                    
                # Vérifie si la recette peut être adaptée avec les ingrédients en opportunité
                recipe_ingredients = base_recipe['ingredients']
                potential_adaptations = []
                
                for opp in opportunities[:10]:  # Considère les 10 meilleures opportunités
                    ingredient = opp['ingredient']
                    
                    # Vérifie si l'ingrédient peut être intégré à la recette
                    for base_ingredient in recipe_ingredients:
                        if self._are_ingredients_compatible(ingredient, base_ingredient):
                            potential_adaptations.append({
                                'original': base_ingredient,
                                'replacement': ingredient,
                                'score': opp['combined_score']
                            })
                
                # Si des adaptations sont possibles, crée une recette adaptée
                if potential_adaptations:
                    # Sélectionne la meilleure adaptation
                    best_adaptation = max(potential_adaptations, key=lambda x: x['score'])
                    
                    # Crée la recette adaptée
                    adapted_recipe = base_recipe.copy()
                    adapted_ingredients = recipe_ingredients.copy()
                    
                    # Remplace l'ingrédient
                    adapted_ingredients = [best_adaptation['replacement'] 
                                          if i == best_adaptation['original'] 
                                          else i for i in adapted_ingredients]
                    
                    # Ajoute éventuellement un ingrédient complémentaire
                    complementary = self._find_complementary_ingredient(best_adaptation['replacement'])
                    if complementary and complementary not in adapted_ingredients:
                        adapted_ingredients.append(complementary)
                    
                    # Met à jour la recette adaptée
                    adapted_recipe['ingredients'] = adapted_ingredients
                    adapted_recipe['based_on'] = adapted_recipe['name']
                    adapted_recipe['name'] = self._generate_recipe_name(adapted_recipe, best_adaptation)
                    
                    adapted_recipes.append(adapted_recipe)
        
        return adapted_recipes
    
    def _are_ingredients_compatible(self, ingredient1, ingredient2):
        """Détermine si deux ingrédients sont compatibles ou substituables."""
        # Vérification dans la base d'affinités
        if ingredient1 in self.ingredient_combinations['affinities']:
            if ingredient2 in self.ingredient_combinations['affinities'][ingredient1]:
                return True
        
        # Vérification des catégories d'ingrédients (implémentation simplifiée)
        ingredient_categories = {
            'fromages': ['mozzarella', 'parmesan', 'chèvre', 'bleu', 'comté'],
            'viandes': ['jambon', 'poulet', 'bœuf', 'magret', 'chorizo'],
            'légumes': ['tomate', 'poivron', 'courgette', 'aubergine', 'champignon']
        }
        
        # Vérifie si les ingrédients appartiennent à la même catégorie
        for category, ingredients in ingredient_categories.items():
            if (ingredient1.lower() in map(str.lower, ingredients) and 
                ingredient2.lower() in map(str.lower, ingredients)):
                return True
        
        return False
    
    def _find_complementary_ingredient(self, ingredient):
        """Trouve un ingrédient complémentaire pour un ingrédient donné."""
        if ingredient in self.ingredient_combinations['affinities']:
            complementary_options = self.ingredient_combinations['affinities'][ingredient]
            if complementary_options:
                return random.choice(complementary_options)
        return None
    
    def _generate_recipe_name(self, recipe, adaptation):
        """Génère un nom attractif pour une recette adaptée."""
        base_name = recipe.get('based_on', recipe['name'])
        new_ingredient = adaptation['replacement']
        
        # Formats possibles pour les noms
        name_formats = [
            f"{base_name} {new_ingredient}",
            f"{base_name} à la {new_ingredient}",
            f"{base_name} façon {new_ingredient}",
            f"{new_ingredient} {base_name}"
        ]
        
        return random.choice(name_formats)
    
    def _create_new_combinations(self, opportunities, promo_ingredients, count):
        """
        Crée de nouvelles combinaisons d'ingrédients basées sur les opportunités.
        
        Returns:
            Liste de nouvelles recettes
        """
        # Implémentation simplifiée - à développer selon les besoins
        new_recipes = []
        
        # Catégories de recettes possibles
        categories = list(self.base_recipes.keys())
        
        for _ in range(count):
            # Sélectionne une catégorie
            category = random.choice(categories)
            
            # Sélectionne 2-3 ingrédients en opportunité
            selected_opportunities = opportunities[:min(10, len(opportunities))]
            main_ingredients = random.sample([o['ingredient'] for o in selected_opportunities], 
                                           min(3, len(selected_opportunities)))
            
            # Ajoute des ingrédients complémentaires
            complementary = []
            for ingredient in main_ingredients:
                comp = self._find_complementary_ingredient(ingredient)
                if comp and comp not in main_ingredients and comp not in complementary:
                    complementary.append(comp)
            
            # Combine tous les ingrédients
            all_ingredients = main_ingredients + complementary[:2]
            
            # Crée la nouvelle recette
            new_recipe = {
                'name': self._generate_new_recipe_name(all_ingredients, category),
                'ingredients': all_ingredients,
                'category': category,
                'is_new_creation': True
            }
            
            new_recipes.append(new_recipe)
        
        return new_recipes
    
    def _generate_new_recipe_name(self, ingredients, category):
        """Génère un nom pour une nouvelle recette."""
        # Sélectionne 1-2 ingrédients principaux pour le nom
        name_ingredients = ingredients[:min(2, len(ingredients))]
        
        if category == "pizza":
            return f"Pizza {' et '.join(name_ingredients)}"
        elif category == "plat_principal":
            return f"{name_ingredients[0]} aux {' et '.join(name_ingredients[1:])}" if len(name_ingredients) > 1 else f"{name_ingredients[0]} spécial"
        else:
            return f"{category.capitalize()} {' et '.join(name_ingredients)}"
    
    def _ensure_diversity(self, suggestions):
        """Assure la diversité dans les suggestions (évite les doublons récents)."""
        # Vérifie si des suggestions sont similaires à celles récemment proposées
        filtered_suggestions = []
        
        for suggestion in suggestions:
            # Vérifie si une suggestion similaire a été faite récemment
            is_duplicate = False
            for prev in self.previous_suggestions:
                if self._are_suggestions_similar(suggestion, prev):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_suggestions.append(suggestion)
        
        # Si trop de suggestions ont été filtrées, réintègre quelques-unes
        while len(filtered_suggestions) < len(suggestions) // 2:
            remaining = [s for s in suggestions if s not in filtered_suggestions]
            if not remaining:
                break
            filtered_suggestions.append(random.choice(remaining))
        
        return filtered_suggestions
    
    def _are_suggestions_similar(self, sugg1, sugg2):
        """Détermine si deux suggestions sont similaires."""
        # Vérifie si les noms sont similaires
        if sugg1.get('name') == sugg2.get('name'):
            return True
        
        # Vérifie si les ingrédients sont similaires
        ingredients1 = set(sugg1.get('ingredients', []))
        ingredients2 = set(sugg2.get('ingredients', []))
        
        # Si plus de 70% des ingrédients sont communs, considère comme similaire
        if ingredients1 and ingredients2:
            common = ingredients1.intersection(ingredients2)
            if len(common) / max(len(ingredients1), len(ingredients2)) > 0.7:
                return True
        
        return False
    
    def _finalize_suggestions(self, suggestions, promotions, trends):
        """Finalise les suggestions avec prix, descriptions et métadonnées."""
        final_suggestions = []
        
        for sugg in suggestions:
            # Calcul du prix en fonction des ingrédients et promotions
            base_price = sugg.get('base_price', 12.0)  # Prix par défaut
            
            # Ajustement en fonction des ingrédients
            price_factor = 1.0
            for ingredient in sugg.get('ingredients', []):
                # Vérifie si l'ingrédient est en promotion
                for promo in promotions:
                    if promo.get('ingredient', '').lower() == ingredient.lower():
                        discount = promo.get('discount_percentage', 0) / 100
                        price_factor -= discount * 0.3  # Répercute 30% de la remise
            
            # Ajustement selon les tendances
            if trends.get('premium_trend', False):
                price_factor *= 1.1  # +10% pour les tendances premium
            
            final_price = round(base_price * max(0.8, price_factor), 2)
            
            # Génération de la description
            description = self._generate_description(sugg, promotions, trends)
            
            # Création de l'objet suggestion final
            final_suggestion = {
                'name': sugg['name'],
                'category': sugg.get('category', 'spécial'),
                'main_ingredients': sugg.get('ingredients', []),
                'price': final_price,
                'description': description,
                'creation_date': datetime.now().isoformat(),
                'is_new_creation': sugg.get('is_new_creation', False),
                'based_on': sugg.get('based_on', None)
            }
            
            final_suggestions.append(final_suggestion)
        
        return final_suggestions
    
    def _generate_description(self, suggestion, promotions, trends):
        """Génère une description marketing pour la suggestion."""
        ingredients = suggestion.get('ingredients', [])
        category = suggestion.get('category', '')
        is_new = suggestion.get('is_new_creation', False)
        
        # Éléments de base pour la description
        parts = []
        
        # Introduction selon le type
        if is_new:
            parts.append(random.choice([
                "Notre nouvelle création exclusive",
                "Une création originale de notre chef",
                "Notre dernière innovation culinaire",
                "Une recette inédite spécialement conçue pour vous"
            ]))
        else:
            parts.append(random.choice([
                "Notre délicieuse spécialité",
                "Un classique revisité",
                "Une recette traditionnelle avec une touche moderne",
                "Un de nos plats les plus appréciés"
            ]))
        
        # Description des ingrédients
        if ingredients:
            main_ingredients = ingredients[:3]
            
            # Vérifie si certains ingrédients sont en promotion
            promo_ingredients = []
            for ingredient in main_ingredients:
                for promo in promotions:
                    if promo.get('ingredient', '').lower() == ingredient.lower():
                        promo_ingredients.append(ingredient)
            
            # Formulation différente selon les promotions
            if promo_ingredients:
                parts.append(f"préparée avec des {', '.join(promo_ingredients)} frais et de saison")
            else:
                parts.append(f"à base de {', '.join(main_ingredients)}")
        
        # Ajout d'éléments tendance si pertinent
        if trends.get('keywords', []):
            trend_terms = [k['term'] for k in trends.get('keywords', [])[:2]]
            if trend_terms:
                parts.append(random.choice([
                    f"dans l'air du temps avec sa touche de {trend_terms[0]}",
                    f"parfaitement dans la tendance {trend_terms[0]}",
                    f"idéale pour les amateurs de {trend_terms[0]}"
                ]))
        
        # Conclusion
        parts.append(random.choice([
            "Un délice à ne pas manquer!",
            "À découvrir absolument!",
            "Un choix parfait pour aujourd'hui!",
            "Laissez-vous tenter!"
        ]))
        
        return " ".join(parts)
