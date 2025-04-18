# Guide des Tests et de l'Intégration Continue - Le Vieux Moulin

## Sommaire

1. [Introduction](#1-introduction)
2. [Structure des Tests](#2-structure-des-tests)
3. [Types de Tests](#3-types-de-tests)
   - [3.1 Tests Unitaires](#31-tests-unitaires)
   - [3.2 Tests d'Intégration](#32-tests-dintégration)
   - [3.3 Tests de Système (Cross-Module)](#33-tests-de-système-cross-module)
4. [Écriture des Tests](#4-écriture-des-tests)
   - [4.1 Bonnes Pratiques](#41-bonnes-pratiques)
   - [4.2 Utilisation des Mocks](#42-utilisation-des-mocks)
   - [4.3 Assertions et Vérifications](#43-assertions-et-vérifications)
5. [Exécution des Tests](#5-exécution-des-tests)
   - [5.1 En Local](#51-en-local)
   - [5.2 Via GitHub Actions](#52-via-github-actions)
   - [5.3 Interprétation des Rapports](#53-interprétation-des-rapports)
6. [Pipeline CI/CD](#6-pipeline-cicd)
   - [6.1 Configuration GitHub Actions](#61-configuration-github-actions)
   - [6.2 Étapes du Pipeline](#62-étapes-du-pipeline)
   - [6.3 Déploiement Automatique](#63-déploiement-automatique)
7. [Gestion des Échecs de Tests](#7-gestion-des-échecs-de-tests)
   - [7.1 Analyse des Échecs](#71-analyse-des-échecs)
   - [7.2 Correction et Validation](#72-correction-et-validation)
8. [Ajout de Nouveaux Tests](#8-ajout-de-nouveaux-tests)
   - [8.1 Création de Nouveaux Fichiers de Test](#81-création-de-nouveaux-fichiers-de-test)
   - [8.2 Intégration dans le Pipeline](#82-intégration-dans-le-pipeline)
9. [Maintenance des Tests](#9-maintenance-des-tests)
   - [9.1 Révision Périodique](#91-révision-périodique)
   - [9.2 Tests Obsolètes](#92-tests-obsolètes)
10. [Ressources](#10-ressources)
    - [10.1 Outils](#101-outils)
    - [10.2 Documentation](#102-documentation)
    - [10.3 Contact](#103-contact)

---

## 1. Introduction

Ce document décrit les procédures de test et d'intégration continue pour le projet "Le Vieux Moulin". Un système de tests robuste et une intégration continue efficace sont essentiels pour maintenir la qualité et la fiabilité de notre système de gestion intelligente pour le restaurant.

Les tests et l'intégration continue assurent que :
- Les nouvelles fonctionnalités n'introduisent pas de régressions
- Le code reste maintenable et de haute qualité
- Les bugs sont détectés rapidement
- Le déploiement vers les environnements de production est fiable

**Principes fondamentaux :**
- Chaque module doit avoir des tests unitaires
- Les interactions entre modules doivent être couvertes par des tests d'intégration
- Tout nouveau code doit être accompagné de tests appropriés
- Aucun code ne doit être fusionné dans les branches principales sans passer les tests automatisés

## 2. Structure des Tests

Le dossier `/tests` à la racine du projet est organisé par modules, reflétant la structure du code source :

```
/tests
├── __init__.py                  # Nécessaire pour l'import des modules de test
├── iot/                         # Tests pour le module IoT
│   ├── __init__.py
│   ├── test_weight_sensor.py
│   ├── test_temperature_sensor.py
│   └── ...
├── integration/                 # Tests pour le module d'intégration API
│   ├── __init__.py
│   ├── test_api_connector.py
│   └── ...
├── ml/                          # Tests pour le module ML
│   ├── __init__.py
│   ├── test_prediction_model.py
│   └── ...
├── ui/                          # Tests pour l'interface utilisateur
│   ├── __init__.py
│   ├── test_dashboard.py
│   └── ...
├── marketing/                   # Tests pour le module marketing
│   ├── __init__.py
│   ├── test_recipe_suggestion.py
│   └── ...
├── accounting/                  # Tests pour le module comptabilité
│   ├── __init__.py
│   ├── test_financial_report.py
│   └── ...
└── integration_all/             # Tests d'intégration cross-module
    ├── __init__.py
    ├── test_stock_order_integration.py
    └── ...
```

## 3. Types de Tests

### 3.1 Tests Unitaires

Les tests unitaires vérifient le comportement d'un composant isolé, indépendamment des autres parties du système.

**Caractéristiques :**
- Testent une seule fonction, classe ou méthode
- Utilisent des mocks pour simuler les dépendances
- Sont rapides à exécuter
- Sont déterministes (résultats prévisibles)

**Exemple :** 
```python
def test_weight_reading():
    """Vérifie que la lecture du poids fonctionne correctement."""
    sensor = WeightSensor(pin=5, max_weight=5000, test=True)
    weight = sensor.read()
    
    assert isinstance(weight, (int, float))
    assert 0 <= weight <= 5000
```

### 3.2 Tests d'Intégration

Les tests d'intégration vérifient les interactions entre différents composants d'un même module.

**Caractéristiques :**
- Testent la collaboration entre plusieurs classes ou fonctions
- Peuvent utiliser des mocks pour les dépendances externes
- Vérifient les flux de données entre composants

**Exemple :**
```python
def test_supplier_api_authentication_and_order():
    """Vérifie le flux d'authentification et de commande."""
    connector = SupplierConnector(
        api_url="https://api.example.com",
        client_id="test_client",
        client_secret="test_secret",
        test_mode=True
    )
    
    # Test du flux complet
    token = connector.authenticate()
    assert token is not None
    
    products = connector.get_products(category="baking")
    assert len(products) > 0
    
    order_result = connector.place_order([
        {"product_id": products[0]["id"], "quantity": 10}
    ])
    assert order_result["status"] == "confirmed"
```

### 3.3 Tests de Système (Cross-Module)

Les tests de système vérifient les interactions entre différents modules pour valider le comportement global du système.

**Caractéristiques :**
- Testent des fonctionnalités de bout en bout
- Vérifient l'intégration entre plusieurs modules
- Peuvent simuler des scénarios d'utilisation réels

**Exemple :**
```python
def test_low_stock_triggers_automatic_order():
    """Vérifie que la détection de stock bas déclenche une commande automatique."""
    # Initialisation des différents composants
    weight_sensor = MockWeightSensor(current_weight=200, threshold=1000)
    supplier_api = MockSupplierConnector()
    stock_manager = StockManager(
        sensors={"farine": weight_sensor},
        supplier_connector=supplier_api
    )
    
    # Exécution du flux complet
    result = stock_manager.process_inventory_and_order()
    
    # Vérifications
    assert "orders" in result
    assert len(result["orders"]) > 0
    assert result["orders"][0]["status"] == "confirmed"
```

## 4. Écriture des Tests

### 4.1 Bonnes Pratiques

- **Nommage :** Utilisez des noms descriptifs qui expliquent ce qui est testé
- **Structure AAA :** Arrange (préparation), Act (action), Assert (vérification)
- **Indépendance :** Chaque test doit être isolé et indépendant des autres
- **Idempotence :** Le test doit donner le même résultat à chaque exécution
- **Focus :** Testez une seule chose par test
- **Documentation :** Ajoutez des docstrings expliquant l'objectif du test

### 4.2 Utilisation des Mocks

Les mocks permettent de simuler le comportement des dépendances pour isoler le composant testé.

```python
@patch('requests.post')
def test_authentication(self, mock_post):
    """Vérifie que l'authentification fonctionne correctement."""
    # Configuration du mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_token", "expires_in": 3600}
    mock_post.return_value = mock_response
    
    # Test de l'authentification
    token = self.connector.authenticate()
    assert token == "test_token"
```

### 4.3 Assertions et Vérifications

Utilisez les assertions de manière précise pour vérifier le comportement attendu :

```python
def test_predict_optimal_quantity():
    """Vérifie que la prédiction de quantité optimale fonctionne."""
    # Préparation
    predictor = StockPredictor(historical_data=test_data)
    
    # Action
    result = predictor.predict_optimal_quantity("farine")
    
    # Vérifications
    assert isinstance(result, float)
    assert result > 0
    assert 5 <= result <= 50  # Vérification de plage raisonnable
```

## 5. Exécution des Tests

### 5.1 En Local

Pour exécuter les tests en local, utilisez pytest :

```bash
# Installation des dépendances de test
pip install pytest pytest-cov

# Exécution de tous les tests
pytest

# Exécution des tests d'un module spécifique
pytest tests/iot/

# Exécution d'un test spécifique
pytest tests/iot/test_weight_sensor.py::TestWeightSensor::test_weight_reading

# Exécution avec rapport de couverture
pytest --cov=.
```

### 5.2 Via GitHub Actions

Les tests sont automatiquement exécutés lors des push et des pull requests via GitHub Actions :

1. Accédez à l'onglet "Actions" du dépôt GitHub
2. Sélectionnez le workflow "CI/CD Pipeline Le Vieux Moulin"
3. Consultez les résultats de l'exécution la plus récente

### 5.3 Interprétation des Rapports

Les rapports de test incluent :

- **Résultats des tests :** Succès, échecs, erreurs
- **Couverture de code :** Pourcentage du code couvert par les tests
- **Durée :** Temps d'exécution de chaque test
- **Logs :** Messages d'erreur détaillés en cas d'échec

## 6. Pipeline CI/CD

### 6.1 Configuration GitHub Actions

Le pipeline CI/CD est configuré dans le fichier `.github/workflows/ci.yml`. Il définit :

- Les événements déclencheurs (push, pull request)
- Les étapes d'exécution
- Les environnements de déploiement

### 6.2 Étapes du Pipeline

1. **Lint :** Vérification du style de code
2. **Tests Unitaires :** Par module (IoT, ML, UI, etc.)
3. **Tests d'Intégration :** Tests des interactions entre composants
4. **Build :** Compilation et empaquetage du code
5. **Deploy :** Déploiement vers les environnements appropriés

### 6.3 Déploiement Automatique

Le déploiement est automatisé selon les règles suivantes :

- Les push sur `main` déclenchent un déploiement en production
- Les push sur `develop` déclenchent un déploiement en staging
- Les push sur les branches `release/*` déclenchent un déploiement en préproduction

## 7. Gestion des Échecs de Tests

### 7.1 Analyse des Échecs

En cas d'échec de tests dans le pipeline CI/CD :

1. Examinez les logs d'erreur dans l'interface GitHub Actions
2. Identifiez les tests qui ont échoué et pourquoi
3. Reproduisez le problème en local si possible

### 7.2 Correction et Validation

1. Corrigez le code ou le test selon la cause du problème
2. Exécutez les tests localement pour vérifier la correction
3. Poussez les modifications et vérifiez que le pipeline passe
4. Documentez la correction dans le message de commit

## 8. Ajout de Nouveaux Tests

### 8.1 Création de Nouveaux Fichiers de Test

Pour ajouter de nouveaux tests :

1. Identifiez le module concerné
2. Créez un fichier de test dans le dossier correspondant (`/tests/module_name/`)
3. Nommez le fichier avec le préfixe `test_` (ex: `test_new_feature.py`)
4. Structurez vos tests selon les bonnes pratiques

**Structure recommandée :**
```python
"""
Tests pour [fonctionnalité].

Description détaillée des tests.
"""

import unittest
# imports nécessaires

class TestFeature(unittest.TestCase):
    """Tests pour la fonctionnalité X."""

    def setUp(self):
        """Initialisation avant chaque test."""
        # Préparation commune

    def test_specific_behavior(self):
        """Vérifie un comportement spécifique."""
        # Arrange
        # Act
        # Assert

    def tearDown(self):
        """Nettoyage après chaque test."""
        # Nettoyage nécessaire
```

### 8.2 Intégration dans le Pipeline

Les nouveaux tests sont automatiquement intégrés dans le pipeline CI/CD :

- Si le nouveau test concerne un module existant, aucune configuration supplémentaire n'est nécessaire
- Si vous créez un nouveau type de test ou module, vous devrez peut-être ajuster le fichier `.github/workflows/ci.yml`

## 9. Maintenance des Tests

### 9.1 Révision Périodique

Les tests doivent être révisés régulièrement pour :

- Assurer qu'ils restent pertinents
- Maintenir une couverture adéquate
- Améliorer la performance des tests
- Mettre à jour les mocks selon l'évolution des API

### 9.2 Tests Obsolètes

Lorsqu'un test devient obsolète :

1. Évaluez si le test peut être mis à jour pour rester pertinent
2. Si non, documentez pourquoi le test est supprimé
3. Créez un nouveau test pour couvrir la fonctionnalité actuelle si nécessaire
4. Mettez à jour la documentation des tests

## 10. Ressources

### 10.1 Outils

- [Pytest](https://docs.pytest.org/) - Framework de test principal
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Rapports de couverture
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html) - Bibliothèque de mock Python
- [GitHub Actions](https://docs.github.com/en/actions) - Documentation CI/CD

### 10.2 Documentation

- [Conventions de codage](./CONTRIBUTING.md) - Standards de code du projet
- [Spécifications](./REQUIREMENTS.md) - Spécifications détaillées du projet

### 10.3 Contact

Pour toute question concernant les tests ou l'intégration continue :

- Créez une issue sur le dépôt GitHub
- Contactez l'équipe technique à support@levieuxmoulin.fr

---

**Version :** 1.0.0  
**Dernière mise à jour :** 18 avril 2025  
**Auteurs :** Équipe développement Le Vieux Moulin
