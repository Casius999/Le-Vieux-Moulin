#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Normalisation de texte pour le module de commande vocale.

Ce module fournit des fonctions pour normaliser le texte reconnu par la
reconnaissance vocale afin d'améliorer l'identification des commandes.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import re
import unicodedata
import logging
import string
from typing import List, Optional, Tuple


# Dictionnaire des mots à normaliser spécifiquement au domaine
DOMAIN_REPLACEMENTS = {
    # Ingrédients
    "farine": ["farines", "farin", "la farine"],
    "sucre": ["du sucre", "le sucre"],
    "sel": ["du sel", "le sel"],
    "huile": ["huiles", "de l'huile", "d'huile"],
    "tomate": ["tomates", "des tomates"],
    "fromage": ["du fromage", "fromages"],
    "mozzarella": ["mozzarella", "de la mozzarella"],
    
    # Équipements
    "four": ["le four", "du four"],
    "friteuse": ["la friteuse", "de la friteuse"],
    "réfrigérateur": ["frigo", "réfrigérateur", "le frigo"],
    "congélateur": ["le congélateur", "du congélateur"],
    
    # Actions
    "vérifier": ["vérifier", "vérifie", "contrôler", "contrôle"],
    "commander": ["commander", "commande", "acheter", "achète"],
    "niveau": ["niveau", "quantité", "stock"],
    "recette": ["recette", "préparation", "la recette"],
    
    # Autres normalisations spécifiques
    "pizza": ["pizzas", "la pizza", "les pizzas"],
    "maintenance": ["maintenance", "entretien", "réparation"]
}


def normalize_text(text: str) -> str:
    """Normalise un texte pour la reconnaissance de commandes.

    Cette fonction effectue plusieurs opérations:
    - Conversion en minuscules
    - Suppression des accents
    - Suppression de la ponctuation
    - Normalisation des espaces multiples
    - Normalisation des termes spécifiques au domaine

    Args:
        text (str): Texte à normaliser.

    Returns:
        str: Texte normalisé.
    """
    logger = logging.getLogger("voice_command.text_normalizer")
    
    # Texte original pour le log
    original = text
    
    # Conversion en minuscules
    text = text.lower()
    
    # Normalisation Unicode
    text = unicodedata.normalize('NFKD', text)
    
    # Suppression des accents (conserver uniquement les caractères ASCII)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Suppression de la ponctuation tout en gardant les espaces
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Normalisation des espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Appliquer les normalisations spécifiques au domaine
    text = normalize_domain_terms(text)
    
    logger.debug(f"Normalisation: '{original}' -> '{text}'")
    return text


def normalize_domain_terms(text: str) -> str:
    """Applique des normalisations spécifiques au domaine de la restauration.

    Args:
        text (str): Texte à normaliser.

    Returns:
        str: Texte avec termes normalisés.
    """
    normalized = text
    
    # Construire un dictionnaire inversé pour les remplacements
    inverse_dict = {}
    for standard, variants in DOMAIN_REPLACEMENTS.items():
        for variant in variants:
            inverse_dict[variant] = standard
    
    # Découper le texte en mots
    words = normalized.split()
    for i, word in enumerate(words):
        # Vérifier si le mot (ou une séquence de mots) est dans le dictionnaire inversé
        if word in inverse_dict:
            words[i] = inverse_dict[word]
    
    # Reconstruire le texte avec les mots normalisés
    normalized = ' '.join(words)
    
    # Rechercher et remplacer les expressions composées de plusieurs mots
    for variant, standard in sorted(inverse_dict.items(), key=lambda x: len(x[0]), reverse=True):
        if ' ' in variant and variant in normalized:
            normalized = normalized.replace(variant, standard)
    
    return normalized