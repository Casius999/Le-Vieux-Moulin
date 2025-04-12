"""
Module de gestion de la configuration

Ce module fournit la classe Config qui permet de charger et d'accéder
aux paramètres de configuration.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union


class Config:
    """
    Classe de gestion de la configuration
    
    Permet de charger des configurations à partir de fichiers JSON et d'y accéder
    via une syntaxe à point (dot notation).
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise un objet de configuration.
        
        Args:
            config_path: Chemin vers le fichier de configuration principal (JSON)
        """
        self.logger = logging.getLogger("communication.config")
        self._config = {}
        
        if config_path:
            self.load(config_path)
    
    def load(self, config_path: str) -> None:
        """
        Charge la configuration à partir d'un fichier JSON.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            json.JSONDecodeError: Si le fichier n'est pas un JSON valide
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self._config = json.load(file)
            self.logger.info(f"Configuration chargée depuis {config_path}")
        except FileNotFoundError:
            self.logger.error(f"Fichier de configuration introuvable: {config_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur de décodage JSON dans {config_path}: {e}")
            raise
    
    def merge(self, config_path: str) -> None:
        """
        Fusionne une configuration supplémentaire avec la configuration existante.
        
        Args:
            config_path: Chemin vers le fichier de configuration à fusionner
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                additional_config = json.load(file)
                
            # Fusion récursive des dictionnaires
            self._merge_dicts(self._config, additional_config)
            self.logger.info(f"Configuration fusionnée depuis {config_path}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la fusion de la configuration depuis {config_path}: {e}")
            raise
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration en utilisant une syntaxe à point.
        
        Args:
            key_path: Chemin d'accès à la valeur (par exemple 'database.host')
            default: Valeur par défaut si le chemin n'existe pas
            
        Returns:
            La valeur associée au chemin ou la valeur par défaut
        """
        parts = key_path.split('.')
        value = self._config
        
        try:
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Définit une valeur de configuration en utilisant une syntaxe à point.
        
        Args:
            key_path: Chemin d'accès à la valeur (par exemple 'database.host')
            value: Valeur à définir
        """
        parts = key_path.split('.')
        current = self._config
        
        # Naviguer dans la structure jusqu'à l'avant-dernier élément
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Définir la valeur sur le dernier élément
        current[parts[-1]] = value
    
    def save(self, config_path: str) -> None:
        """
        Sauvegarde la configuration actuelle dans un fichier JSON.
        
        Args:
            config_path: Chemin où sauvegarder le fichier
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as file:
                json.dump(self._config, file, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration sauvegardée dans {config_path}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de la configuration dans {config_path}: {e}")
            raise
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Retourne la configuration complète sous forme de dictionnaire.
        
        Returns:
            La configuration complète
        """
        return self._config.copy()
    
    def _merge_dicts(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Fusionne récursivement deux dictionnaires.
        
        Args:
            target: Dictionnaire cible (modifié in-place)
            source: Dictionnaire source à fusionner dans la cible
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Fusion récursive des sous-dictionnaires
                self._merge_dicts(target[key], value)
            else:
                # Remplacement ou ajout de la valeur
                target[key] = value
