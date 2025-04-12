#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de recommandation de recettes pour le restaurant Le Vieux Moulin.

Ce module implémente un système hybride de recommandation qui combine:
- Un système de filtrage collaboratif
- Une approche basée sur le contenu
- Un module contextuel prenant en compte les contraintes (stocks disponibles, saison, etc.)

Il est utilisé pour générer des suggestions de plats du jour, de pizzas spéciales, etc.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf
from tensorflow.keras.models import load_model

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecipeRecommender:
    """
    Système de recommandation hybride pour la suggestion de recettes.
    
    Cette classe implémente un système qui combine plusieurs approches:
    - Filtrage collaboratif: basé sur les préférences clients et les ventes historiques
    - Approche basée sur le contenu: analyse des attributs des recettes (ingrédients, type)
    - Modèle contextuel: intègre les contraintes actuelles (stocks, saison, promotions)
    """
    
    def __init__(
        self,
        model_path: str = None,
        recipe_db_path: str = None,
        sales_history_path: str = None,
        embedding_dim: int = 64
    ):
        """
        Initialise le système de recommandation.
        
        Args:
            model_path: Chemin vers le modèle de recommandation entraîné
            recipe_db_path: Chemin vers la base de données des recettes
            sales_history_path: Chemin vers l'historique des ventes
            embedding_dim: Dimension des embeddings pour le filtrage collaboratif
        """
        self.model_path = model_path
        self.recipe_db_path = recipe_db_path
        self.sales_history_path = sales_history_path
        self.embedding_dim = embedding_dim
        
        # Attributs qui seront chargés à partir des fichiers
        self.model = None  # Modèle d'IA pour la recommandation
        self.recipes_df = None  # DataFrame avec les recettes
        self.recipe_embeddings = None  # Embeddings des recettes
        self.ingredient_weights = None  # Importance des ingrédients
        self.seasonal_adjustments = None  # Ajustements saisonniers
        
        # Chargement des données si les chemins sont spécifiés
        if recipe_db_path and os.path.exists(recipe_db_path):
            self._load_recipe_database()
        
        if model_path and os.path.exists(model_path):
            self._load_model()
    
    def _load_recipe_database(self) -> None:
        """
        Charge la base de données des recettes.
        """
        try:
            logger.info(f"Chargement de la base de recettes depuis {self.recipe_db_path}")
            
            # Dans un système réel, cela pourrait être une base de données SQL
            # Pour cet exemple, nous utilisons un fichier CSV
            if self.recipe_db_path.endswith('.csv'):
                self.recipes_df = pd.read_csv(self.recipe_db_path)
            elif self.recipe_db_path.endswith('.json'):
                with open(self.recipe_db_path, 'r', encoding='utf-8') as f:
                    recipes_data = json.load(f)
                self.recipes_df = pd.DataFrame(recipes_data)
            else:
                raise ValueError(f"Format de fichier non pris en charge: {self.recipe_db_path}")
            
            logger.info(f"Base de recettes chargée: {len(self.recipes_df)} recettes disponibles")
            
            # Chargement des embeddings pré-calculés si disponibles
            embeddings_path = os.path.join(
                os.path.dirname(self.recipe_db_path),
                "recipe_embeddings.npy"
            )
            if os.path.exists(embeddings_path):
                self.recipe_embeddings = np.load(embeddings_path)
                logger.info(f"Embeddings de recettes chargés: {self.recipe_embeddings.shape}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la base de recettes: {str(e)}")
            raise
    
    def _load_model(self) -> None:
        """
        Charge le modèle de recommandation.
        """
        try:
            logger.info(f"Chargement du modèle depuis {self.model_path}")
            self.model = load_model(self.model_path)
            
            # Chargement des poids des ingrédients si disponibles
            weights_path = os.path.join(
                os.path.dirname(self.model_path),
                "ingredient_weights.json"
            )
            if os.path.exists(weights_path):
                with open(weights_path, 'r', encoding='utf-8') as f:
                    self.ingredient_weights = json.load(f)
                logger.info(f"Poids des ingrédients chargés: {len(self.ingredient_weights)} ingrédients")
            
            # Chargement des ajustements saisonniers si disponibles
            seasonal_path = os.path.join(
                os.path.dirname(self.model_path),
                "seasonal_adjustments.json"
            )
            if os.path.exists(seasonal_path):
                with open(seasonal_path, 'r', encoding='utf-8') as f:
                    self.seasonal_adjustments = json.load(f)
                logger.info("Ajustements saisonniers chargés")
            
            logger.info("Modèle et métadonnées chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            raise
    
    def _get_similar_recipes(
        self,
        recipe_id: Optional[int] = None,
        ingredients: Optional[List[str]] = None,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Trouve des recettes similaires basées sur un ID de recette ou une liste d'ingrédients.
        
        Args:
            recipe_id: ID de la recette de référence
            ingredients: Liste d'ingrédients pour trouver des recettes similaires
            top_n: Nombre de recettes similaires à retourner
            
        Returns:
            Liste des recettes similaires avec leurs scores
        """
        if self.recipes_df is None:
            raise ValueError("Base de recettes non chargée.")
        
        if recipe_id is not None:
            # Recherche basée sur une recette de référence
            if recipe_id not in self.recipes_df['id'].values:
                raise ValueError(f"ID de recette non trouvé: {recipe_id}")
            
            reference_idx = self.recipes_df[self.recipes_df['id'] == recipe_id].index[0]
            
            if self.recipe_embeddings is not None:
                # Utilisation des embeddings pré-calculés si disponibles
                reference_embedding = self.recipe_embeddings[reference_idx].reshape(1, -1)
                similarities = cosine_similarity(reference_embedding, self.recipe_embeddings)[0]
            else:
                # Approche simplifiée basée sur les ingrédients communs
                reference_ingredients = set(self.recipes_df.loc[reference_idx, 'ingredients'].split(','))
                
                similarities = []
                for idx, row in self.recipes_df.iterrows():
                    recipe_ingredients = set(row['ingredients'].split(','))
                    jaccard_sim = len(reference_ingredients.intersection(recipe_ingredients)) / len(reference_ingredients.union(recipe_ingredients))
                    similarities.append(jaccard_sim)
                
                similarities = np.array(similarities)
        
        elif ingredients is not None:
            # Recherche basée sur une liste d'ingrédients
            ingredient_set = set(ingredients)
            
            similarities = []
            for idx, row in self.recipes_df.iterrows():
                recipe_ingredients = set(row['ingredients'].split(','))
                # Nombre d'ingrédients en commun / nombre total d'ingrédients dans la recette
                similarity = len(ingredient_set.intersection(recipe_ingredients)) / len(recipe_ingredients)
                similarities.append(similarity)
            
            similarities = np.array(similarities)
        
        else:
            raise ValueError("Vous devez spécifier soit recipe_id soit ingredients.")
        
        # Obtenir les indices des recettes les plus similaires (excluant la référence)
        if recipe_id is not None:
            similarities[reference_idx] = -1  # Exclure la recette de référence
        
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Construire la liste des recettes similaires
        similar_recipes = []
        for idx in top_indices:
            recipe = self.recipes_df.iloc[idx].to_dict()
            recipe['similarity_score'] = float(similarities[idx])
            similar_recipes.append(recipe)
        
        return similar_recipes
    
    def _adjust_scores_by_context(
        self,
        recipes: List[Dict],
        available_ingredients: Optional[Dict[str, float]] = None,
        current_date: Optional[datetime] = None,
        promotions: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Ajuste les scores des recettes en fonction du contexte actuel.
        
        Args:
            recipes: Liste des recettes avec leurs scores initiaux
            available_ingredients: Dictionnaire des ingrédients disponibles et leurs quantités
            current_date: Date actuelle pour les ajustements saisonniers
            promotions: Dictionnaire des ingrédients en promotion et leurs remises
            
        Returns:
            Liste des recettes avec scores ajustés
        """
        if not recipes:
            return []
        
        # Date par défaut = aujourd'hui
        if current_date is None:
            current_date = datetime.now()
        
        # Mois et saison actuels
        current_month = current_date.month
        seasons = {
            (12, 1, 2): 'winter',
            (3, 4, 5): 'spring',
            (6, 7, 8): 'summer',
            (9, 10, 11): 'autumn'
        }
        current_season = next(season for months, season in seasons.items() if current_month in months)
        
        for recipe in recipes:
            adjustment_factor = 1.0
            recipe_ingredients = recipe['ingredients'].split(',')
            
            # 1. Ajustement basé sur les ingrédients disponibles
            if available_ingredients:
                availability_score = 0
                total_ingredients = len(recipe_ingredients)
                
                for ingredient in recipe_ingredients:
                    ingredient = ingredient.strip()
                    if ingredient in available_ingredients:
                        # Plus la quantité disponible est grande, meilleur est le score
                        availability_score += min(1.0, available_ingredients[ingredient] / 100.0)
                    else:
                        # Pénalité pour les ingrédients non disponibles
                        availability_score -= 0.5
                
                # Normaliser entre 0.5 et 1.5
                norm_availability = 0.5 + (availability_score / total_ingredients)
                adjustment_factor *= max(0.5, min(1.5, norm_availability))
            
            # 2. Ajustement saisonnier
            if self.seasonal_adjustments:
                season_factor = self.seasonal_adjustments.get(current_season, {}).get(recipe['id'], 1.0)
                adjustment_factor *= season_factor
            
            # 3. Ajustement basé sur les promotions
            if promotions:
                promotion_score = 0
                for ingredient in recipe_ingredients:
                    ingredient = ingredient.strip()
                    if ingredient in promotions:
                        promotion_score += promotions[ingredient]
                
                # Bonus pour les recettes avec des ingrédients en promotion
                promotion_factor = 1.0 + (promotion_score / 10.0)  # Max +50% si tous les ingrédients sont en grosse promo
                adjustment_factor *= promotion_factor
            
            # Appliquer l'ajustement final au score initial
            initial_score = recipe.get('similarity_score', 0.5)
            recipe['adjusted_score'] = initial_score * adjustment_factor
            
            # Ajouter des informations contextuelles pour l'explication
            recipe['context_info'] = {
                'season': current_season,
                'availability_factor': norm_availability if available_ingredients else 1.0,
                'promotion_factor': promotion_factor if promotions else 1.0
            }
        
        # Trier les recettes par score ajusté
        sorted_recipes = sorted(recipes, key=lambda x: x['adjusted_score'], reverse=True)
        
        return sorted_recipes
    
    def generate_suggestions(
        self,
        count: int = 3,
        recipe_type: Optional[str] = None,
        available_ingredients: Optional[Dict[str, float]] = None,
        promotions: Optional[Dict[str, float]] = None,
        current_date: Optional[datetime] = None,
        exclude_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Génère des suggestions de recettes basées sur le contexte actuel.
        
        Args:
            count: Nombre de suggestions à générer
            recipe_type: Type de recette (pizza, plat, dessert, etc.)
            available_ingredients: Dictionnaire des ingrédients disponibles et leurs quantités
            promotions: Dictionnaire des ingrédients en promotion et leurs remises
            current_date: Date actuelle pour les ajustements saisonniers
            exclude_ids: Liste des IDs de recettes à exclure
            
        Returns:
            Liste des recettes suggérées avec scores et explications
        """
        if self.recipes_df is None:
            raise ValueError("Base de recettes non chargée.")
        
        # Filtrer par type de recette si spécifié
        if recipe_type:
            filtered_df = self.recipes_df[self.recipes_df['type'] == recipe_type].copy()
            if filtered_df.empty:
                logger.warning(f"Aucune recette trouvée pour le type: {recipe_type}")
                filtered_df = self.recipes_df.copy()
        else:
            filtered_df = self.recipes_df.copy()
        
        # Exclure les IDs spécifiés
        if exclude_ids:
            filtered_df = filtered_df[~filtered_df['id'].isin(exclude_ids)]
        
        # Si pas assez de recettes, retourner toutes celles disponibles
        if len(filtered_df) <= count:
            logger.warning(f"Seulement {len(filtered_df)} recettes disponibles après filtrage")
            candidates = filtered_df.to_dict('records')
            for recipe in candidates:
                recipe['similarity_score'] = 1.0
        else:
            # Calculer les scores initiaux
            # Dans un système réel, cela utiliserait le modèle d'IA chargé
            
            if self.model:
                # Utilisation du modèle chargé pour obtenir des suggestions
                # Code simplifié - dans un système réel, cela dépendrait de l'architecture du modèle
                candidates = filtered_df.head(count * 3).to_dict('records')
                for recipe in candidates:
                    recipe['similarity_score'] = 0.5 + (0.5 * np.random.random())
            else:
                # Approche simplifiée sans modèle: prendre les recettes les plus populaires
                if 'popularity' in filtered_df.columns:
                    top_candidates = filtered_df.nlargest(count * 3, 'popularity')
                else:
                    # Si pas de colonne de popularité, prendre des recettes aléatoires
                    top_candidates = filtered_df.sample(min(count * 3, len(filtered_df)))
                
                candidates = top_candidates.to_dict('records')
                for recipe in candidates:
                    recipe['similarity_score'] = 0.5 + (0.5 * np.random.random())
        
        # Ajuster les scores en fonction du contexte
        adjusted_candidates = self._adjust_scores_by_context(
            candidates,
            available_ingredients,
            current_date,
            promotions
        )
        
        # Prendre les N meilleures suggestions
        suggestions = adjusted_candidates[:count]
        
        # Ajouter des explications pour chaque suggestion
        for suggestion in suggestions:
            explanation = self._generate_explanation(suggestion, available_ingredients, promotions)
            suggestion['explanation'] = explanation
        
        return suggestions
    
    def _generate_explanation(
        self,
        recipe: Dict,
        available_ingredients: Optional[Dict[str, float]] = None,
        promotions: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Génère une explication humainement lisible pour une suggestion de recette.
        
        Args:
            recipe: Dictionnaire contenant les informations de la recette
            available_ingredients: Dictionnaire des ingrédients disponibles
            promotions: Dictionnaire des ingrédients en promotion
            
        Returns:
            Explication textuelle
        """
        explanation = f"Suggestion: {recipe['name']} - "
        
        # Facteurs contextuels
        context = recipe.get('context_info', {})
        season = context.get('season', '')
        
        # Liste des raisons
        reasons = []
        
        # Raison saisonnière
        if season:
            seasons_fr = {
                'winter': "d'hiver",
                'spring': "de printemps",
                'summer': "d'été",
                'autumn': "d'automne"
            }
            season_fr = seasons_fr.get(season, '')
            if season_fr:
                reasons.append(f"parfait pour la saison {season_fr}")
        
        # Raison liée aux ingrédients disponibles
        availability_factor = context.get('availability_factor', 1.0)
        if availability_factor > 1.2:
            reasons.append("tous les ingrédients sont en stock")
        elif availability_factor < 0.8:
            reasons.append("nécessite de commander quelques ingrédients")
        
        # Raison liée aux promotions
        promotion_factor = context.get('promotion_factor', 1.0)
        if promotion_factor > 1.1:
            # Identifier quels ingrédients sont en promotion
            promo_ingredients = []
            if promotions:
                recipe_ingredients = recipe['ingredients'].split(',')
                for ingredient in recipe_ingredients:
                    ingredient = ingredient.strip()
                    if ingredient in promotions and promotions[ingredient] > 0.05:
                        promo_ingredients.append(ingredient)
            
            if promo_ingredients:
                promo_text = ", ".join(promo_ingredients[:2])
                if len(promo_ingredients) > 2:
                    promo_text += f" et {len(promo_ingredients)-2} autres"
                reasons.append(f"profite des promotions actuelles sur {promo_text}")
        
        # Popularité
        if 'popularity' in recipe and recipe['popularity'] > 4.5:
            reasons.append("très populaire auprès de nos clients")
        
        # Assembler l'explication
        if reasons:
            explanation += "Cette recette est " + ", ".join(reasons) + "."
        else:
            explanation += "Une option équilibrée pour votre menu."
        
        return explanation


# Fonction d'utilisation pour les tests
def example_usage():
    """
    Exemple d'utilisation du système de recommandation de recettes.
    """
    # Données fictives pour l'exemple
    mock_recipes = [
        {
            'id': 1,
            'name': 'Pizza Margherita',
            'type': 'pizza',
            'ingredients': 'farine,tomate,mozzarella,basilic,huile_olive',
            'popularity': 4.8,
            'preparation_time': 20,
            'cooking_time': 10
        },
        {
            'id': 2,
            'name': 'Pizza Quatre Fromages',
            'type': 'pizza',
            'ingredients': 'farine,tomate,mozzarella,gorgonzola,parmesan,fromage_chevre',
            'popularity': 4.6,
            'preparation_time': 20,
            'cooking_time': 12
        },
        {
            'id': 3,
            'name': 'Pizza Végétarienne',
            'type': 'pizza',
            'ingredients': 'farine,tomate,mozzarella,poivron,champignon,olive,huile_olive',
            'popularity': 4.3,
            'preparation_time': 25,
            'cooking_time': 12
        },
        {
            'id': 4,
            'name': 'Salade Caesar',
            'type': 'entree',
            'ingredients': 'laitue,poulet,parmesan,croûton,sauce_caesar',
            'popularity': 4.5,
            'preparation_time': 15,
            'cooking_time': 0
        },
        {
            'id': 5,
            'name': 'Tiramisu',
            'type': 'dessert',
            'ingredients': 'cafe,mascarpone,biscuit,cacao,sucre',
            'popularity': 4.7,
            'preparation_time': 30,
            'cooking_time': 0
        }
    ]
    
    # Créer un DataFrame à partir des données fictives
    recipes_df = pd.DataFrame(mock_recipes)
    
    # Ingrédients disponibles dans l'inventaire
    available_ingredients = {
        'farine': 10.0,  # kg
        'tomate': 15.0,  # kg
        'mozzarella': 8.0,  # kg
        'basilic': 0.5,  # kg
        'huile_olive': 3.0,  # L
        'poivron': 5.0,  # kg
        'champignon': 3.0,  # kg
        'parmesan': 2.0,  # kg
        'laitue': 4.0,  # kg
        'poulet': 7.0,  # kg
        'sauce_caesar': 1.0,  # L
        'croûton': 0.5,  # kg
    }
    
    # Ingrédients en promotion
    promotions = {
        'mozzarella': 0.15,  # 15% de réduction
        'poivron': 0.20,  # 20% de réduction
        'champignon': 0.10,  # 10% de réduction
    }
    
    # Initialiser le recommandeur sans charger de fichiers
    recommender = RecipeRecommender()
    
    # Injecter manuellement les données pour l'exemple
    recommender.recipes_df = recipes_df
    
    # Générer des suggestions pour une pizza
    try:
        print("Génération de suggestions pour des pizzas:")
        pizza_suggestions = recommender.generate_suggestions(
            count=2,
            recipe_type='pizza',
            available_ingredients=available_ingredients,
            promotions=promotions,
            current_date=datetime(2025, 4, 1)  # Printemps
        )
        
        # Afficher les suggestions
        for i, suggestion in enumerate(pizza_suggestions, 1):
            print(f"\n{i}. {suggestion['name']} (Score: {suggestion['adjusted_score']:.2f})")
            print(f"   Ingrédients: {suggestion['ingredients']}")
            print(f"   {suggestion['explanation']}")
    
    except Exception as e:
        print(f"Erreur lors de la génération des suggestions: {str(e)}")


if __name__ == "__main__":
    # Exécuter l'exemple d'utilisation si ce script est exécuté directement
    example_usage()
