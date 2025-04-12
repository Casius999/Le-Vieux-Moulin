# Module de Commande Vocale - Le Vieux Moulin

Ce module permet la reconnaissance vocale et la conversion des commandes du personnel en actions concrètes dans l'écosystème du restaurant "Le Vieux Moulin". Conçu pour être utilisé sur des tablettes murales en cuisine ou en salle, il offre une interface mains-libres facilitant les opérations quotidiennes.

## Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture du module](#architecture-du-module)
4. [Installation](#installation)
   - [Prérequis](#prérequis)
   - [Installation des dépendances](#installation-des-dépendances)
   - [Configuration](#configuration)
5. [Utilisation](#utilisation)
   - [Démarrage de l'application](#démarrage-de-lapplication)
   - [Commandes vocales disponibles](#commandes-vocales-disponibles)
   - [Interface utilisateur](#interface-utilisateur)
6. [Intégration avec le système](#intégration-avec-le-système)
   - [Communication avec le serveur central](#communication-avec-le-serveur-central)
   - [Interaction avec le module de gestion des stocks](#interaction-avec-le-module-de-gestion-des-stocks)
7. [Développement](#développement)
   - [Structure du code](#structure-du-code)
   - [Ajouter de nouvelles commandes](#ajouter-de-nouvelles-commandes)
   - [Tests](#tests)
8. [Dépannage](#dépannage)
9. [Support](#support)

## Vue d'ensemble

Le module de commande vocale permet au personnel du restaurant d'interagir avec le système de gestion intelligente sans avoir à utiliser leurs mains, ce qui est particulièrement utile dans un environnement de cuisine. Il utilise des technologies modernes de reconnaissance vocale pour comprendre les commandes, les traiter et les transmettre aux composants appropriés du système.

## Fonctionnalités

- **Reconnaissance vocale multilingue** (français, anglais, espagnol)
- **Traitement du langage naturel** adapté au contexte de la restauration
- **Interface utilisateur intuitive** sur tablette murale
- **Retour visuel et audio** des commandes reconnues
- **Mode hors ligne** avec synchronisation différée
- **Adaptation au bruit ambiant** d'une cuisine professionnelle
- **Personnalisation des commandes** et des actions associées

## Architecture du module

Le module est structuré autour de trois composants principaux :

1. **`speech_recognition.py`** : Gère la reconnaissance vocale et la transformation de la parole en texte
2. **`command_processor.py`** : Analyse le texte reconnu et identifie les commandes à exécuter
3. **`ui_interface.py`** : Gère l'interface utilisateur de la tablette murale

Le script principal **`app.py`** coordonne ces composants et gère la communication avec le reste du système.

## Installation

### Prérequis

- Tablette sous Android 9.0+ ou iPad (iOS 13+)
- Microphone de qualité (intégré ou externe)
- Connexion réseau (WiFi)
- Compte d'accès au système Le Vieux Moulin

### Installation des dépendances

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/ui/voice_command

# Installer les dépendances Python
pip install -r requirements.txt

# Installation pour développement
pip install -e .
```

### Configuration

1. Créez un fichier de configuration basé sur l'exemple :
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Modifiez le fichier de configuration selon votre environnement :
   ```bash
   nano config.yaml
   ```

## Utilisation

### Démarrage de l'application

```bash
# Lancement de l'application avec la configuration par défaut
python app.py

# Lancement avec un fichier de configuration spécifique
python app.py --config custom_config.yaml

# Lancement en mode debug
python app.py --debug
```

### Commandes vocales disponibles

Le système reconnaît plusieurs catégories de commandes vocales :

#### Commandes de stock
- **"Vérifier stock [ingrédient]"** - Affiche le niveau de stock actuel
- **"Commander [ingrédient]"** - Lance une commande auprès du fournisseur
- **"Niveau critique [ingrédient]"** - Signale un niveau bas non détecté par les capteurs

#### Commandes de recette
- **"Recette [plat]"** - Affiche la recette et les ingrédients
- **"Ingrédients [plat]"** - Liste uniquement les ingrédients nécessaires

#### Commandes d'équipement
- **"État [équipement]"** - Vérifie l'état d'un équipement (four, friteuse...)
- **"Maintenance [équipement]"** - Signale un besoin de maintenance

### Interface utilisateur

L'interface utilisateur de la tablette comprend :

- Un bouton d'activation de la reconnaissance vocale
- Une zone d'affichage du texte reconnu
- Une confirmation visuelle des commandes comprises
- Des options de correction manuelle
- Un historique des commandes récentes

## Intégration avec le système

### Communication avec le serveur central

Le module communique avec le serveur central via des API REST et WebSockets :

- **REST API** : Pour les requêtes d'information et les actions non urgentes
- **WebSockets** : Pour les mises à jour en temps réel et les notifications

### Interaction avec le module de gestion des stocks

Le module interroge et met à jour le système de gestion des stocks pour :

- Vérifier les niveaux actuels
- Signaler des problèmes non détectés par les capteurs
- Initier des commandes automatiques

## Développement

### Structure du code

- `app.py` : Point d'entrée principal de l'application
- `config.py` : Gestion de la configuration
- `speech_recognition.py` : Reconnaissance vocale
- `command_processor.py` : Traitement des commandes
- `ui_interface.py` : Interface utilisateur de la tablette
- `api_client.py` : Communication avec le serveur central
- `utils/` : Utilitaires divers
  - `logger.py` : Configuration des journaux
  - `audio_processor.py` : Traitement du signal audio
  - `text_normalizer.py` : Normalisation du texte reconnu
- `tests/` : Tests unitaires et d'intégration

### Ajouter de nouvelles commandes

Pour ajouter une nouvelle catégorie de commandes vocales :

1. Modifiez `commands.yaml` pour ajouter les nouveaux modèles de commandes
2. Créez les gestionnaires correspondants dans `command_handlers/`
3. Enregistrez les nouveaux gestionnaires dans `command_registry.py`
4. Testez les nouvelles commandes avec différentes formulations

### Tests

Les tests sont organisés dans le dossier `tests/` :

```bash
# Exécuter tous les tests
pytest

# Exécuter les tests de reconnaissance vocale uniquement
pytest tests/test_speech_recognition.py

# Exécuter les tests avec couverture
pytest --cov=voice_command tests/
```

## Dépannage

| Problème | Cause possible | Solution |
|----------|----------------|----------|
| Faible taux de reconnaissance | Bruit ambiant excessif | Ajuster la sensibilité du microphone ou utiliser un micro externe |
| Latence élevée | Connexion réseau instable | Vérifier la connexion WiFi ou activer le mode hors ligne |
| Commandes non reconnues | Vocabulaire spécifique manquant | Entraîner le système avec de nouveaux exemples |
| Erreur de connexion au serveur | Problème réseau ou serveur indisponible | Vérifier les paramètres de connexion ou le statut du serveur |

## Support

Pour toute question ou problème :
- Consultez la documentation complète dans le dossier `/docs`
- Créez une issue sur le dépôt GitHub
- Contactez l'équipe technique à support@levieuxmoulin.fr
