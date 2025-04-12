# Guide de Contribution - Le Vieux Moulin

## Sommaire

1. [Introduction](#1-introduction)
2. [Structure du Dépôt](#2-structure-du-dépôt)
3. [Nomenclature et Organisation](#3-nomenclature-et-organisation)
   - [3.1 Conventions de Nommage](#31-conventions-de-nommage)
   - [3.2 Structure des Dossiers](#32-structure-des-dossiers)
   - [3.3 Ajout de Nouveaux Modules](#33-ajout-de-nouveaux-modules)
4. [Standards de Code](#4-standards-de-code)
   - [4.1 JavaScript / TypeScript](#41-javascript--typescript)
   - [4.2 Python](#42-python)
   - [4.3 HTML/CSS](#43-htmlcss)
   - [4.4 Commentaires](#44-commentaires)
   - [4.5 Logging](#45-logging)
5. [Documentation](#5-documentation)
   - [5.1 Structure des README.md](#51-structure-des-readmemd)
   - [5.2 Documentation d'API](#52-documentation-dapi)
   - [5.3 Architecture et Diagrammes](#53-architecture-et-diagrammes)
   - [5.4 Exemples et Cas d'Utilisation](#54-exemples-et-cas-dutilisation)
6. [Processus de Contribution](#6-processus-de-contribution)
   - [6.1 Modèle de Branches](#61-modèle-de-branches)
   - [6.2 Commits et Messages](#62-commits-et-messages)
   - [6.3 Pull Requests](#63-pull-requests)
   - [6.4 Résolution de Conflits](#64-résolution-de-conflits)
7. [Processus de Revue](#7-processus-de-revue)
   - [7.1 Revue de Code](#71-revue-de-code)
   - [7.2 Revue de Documentation](#72-revue-de-documentation)
   - [7.3 Tests et Intégration Continue](#73-tests-et-intégration-continue)
8. [Gestion des Doublons et Redondances](#8-gestion-des-doublons-et-redondances)
   - [8.1 Détection du Code Dupliqué](#81-détection-du-code-dupliqué)
   - [8.2 Réutilisation vs Duplication](#82-réutilisation-vs-duplication)
   - [8.3 Refactorisation](#83-refactorisation)
9. [Mise à Jour des Conventions](#9-mise-à-jour-des-conventions)
   - [9.1 Processus de Révision](#91-processus-de-révision)
   - [9.2 Proposition de Modifications](#92-proposition-de-modifications)
10. [Outils Recommandés](#10-outils-recommandés)
11. [Contact et Assistance](#11-contact-et-assistance)

---

## 1. Introduction

Ce document définit les directives et conventions à suivre pour contribuer au projet "Le Vieux Moulin". L'adhésion à ces standards garantit la cohérence, la qualité et la maintenabilité du code et de la documentation.

Le système de gestion intelligente pour le restaurant "Le Vieux Moulin" est un projet complexe et modulaire. Ces conventions visent à faciliter la collaboration entre contributeurs et à maintenir une architecture cohérente, tout en permettant l'évolutivité du système, notamment pour sa duplication vers un second établissement.

**Principes fondamentaux :**
- Modularité : chaque composant doit être indépendant et réutilisable
- Granularité : décomposition en micro-tâches pour une maintenance facilitée
- Documentation exhaustive : tout code doit être documenté de façon claire et complète
- Tests systématiques : tout code ajouté doit être accompagné de tests appropriés
- Éviter la duplication : privilégier la réutilisation à la duplication de code

## 2. Structure du Dépôt

Le dépôt est organisé en modules fonctionnels, chacun ayant un rôle spécifique dans le système global :

| Répertoire | Description |
|------------|-------------|
| `/ARCHITECTURE/` | Diagrammes et documentation d'architecture système |
| `/docs/` | Documentation générale du projet |
| `/iot/` | Code et documentation pour les modules IoT (capteurs, passerelles) |
| `/ml/` | Modèles d'IA/ML pour prédictions et optimisations |
| `/ui/` | Interfaces utilisateur (tablettes, dashboards, commande vocale) |
| `/integration/` | Intégrations avec les systèmes externes (caisse, fournisseurs, etc.) |
| `/marketing/` | Modules de marketing automatisé |
| `/accounting/` | Module de comptabilité avancé |
| `/common/` | Code partagé entre plusieurs modules |
| `/tests/` | Tests globaux d'intégration |

Les fichiers principaux à la racine incluent :
- `README.md` : Vue d'ensemble du projet
- `REQUIREMENTS.md` : Spécifications détaillées
- `CONTRIBUTING.md` (ce document) : Guide de contribution
- `LICENSE` : Informations de licence et droits d'auteur

## 3. Nomenclature et Organisation

### 3.1 Conventions de Nommage

#### Général
- **Éviter absolument** : les espaces, les caractères spéciaux, les accents
- **Éviter** : les abréviations ambiguës ou non standard

#### Dossiers
- Utiliser le **snake_case** (minuscules avec underscores) : `sensor_module`, `data_processing`
- Exceptions pour les dossiers racine qui utilisent le format PascalCase : `ARCHITECTURE`, `REQUIREMENTS.md`

#### Fichiers
- **Code source** : utiliser le **snake_case** pour Python (`weight_sensor.py`) et le **camelCase** pour JavaScript/TypeScript (`userAuthentication.js`)
- **Documentation** : utiliser le **kebab-case** (minuscules avec tirets) : `installation-guide.md`, `api-reference.md`
- **Configurations** : utiliser le **snake_case** : `database_config.json`, `mqtt_settings.yaml`

#### Variables, Fonctions et Classes
- **JavaScript/TypeScript** :
  - Variables et fonctions : **camelCase** (`getUserData`, `totalAmount`)
  - Classes : **PascalCase** (`UserManager`, `DataProcessor`)
  - Constantes : **UPPER_SNAKE_CASE** (`MAX_RETRY_COUNT`, `API_BASE_URL`)

- **Python** :
  - Variables et fonctions : **snake_case** (`get_user_data`, `total_amount`)
  - Classes : **PascalCase** (`UserManager`, `DataProcessor`)
  - Constantes : **UPPER_SNAKE_CASE** (`MAX_RETRY_COUNT`, `API_BASE_URL`)

#### Bases de données
- Tables : **snake_case** au pluriel (`users`, `order_items`)
- Colonnes : **snake_case** (`first_name`, `created_at`)
- Clés étrangères : format `table_singulier_id` (`user_id`, `product_id`)

### 3.2 Structure des Dossiers

Chaque répertoire principal doit suivre une structure organisée :

```
module_name/
├── README.md                # Documentation principale du module
├── index.js/py              # Point d'entrée principal (si applicable)
├── package.json/requirements.txt # Dépendances
├── src/                     # Code source
│   ├── components/          # Composants/classes principaux
│   ├── utils/               # Utilitaires et helpers
│   └── config/              # Fichiers de configuration
├── tests/                   # Tests unitaires et d'intégration
│   ├── unit/                # Tests unitaires
│   └── integration/         # Tests d'intégration
├── docs/                    # Documentation spécifique au module
│   ├── api/                 # Documentation d'API
│   └── examples/            # Exemples d'utilisation
└── scripts/                 # Scripts utilitaires
```

Respectez cette structure générale tout en l'adaptant aux besoins spécifiques de chaque module.

### 3.3 Ajout de Nouveaux Modules

Lors de l'ajout d'un nouveau module au projet, suivez ces étapes :

1. **Vérifiez la nécessité** : Assurez-vous que le module ne duplique pas des fonctionnalités existantes
2. **Consultez l'équipe** : Discutez de l'intégration du nouveau module avec les responsables du projet
3. **Créez une structure conforme** :
   ```
   nouveau_module/
   ├── README.md                # Documentation du module
   ├── src/                     # Code source
   └── tests/                   # Tests
   ```
4. **Intégrez avec l'existant** : Identifiez les dépendances et intégrations avec les autres modules
5. **Documentez** : Créez une documentation complète selon les standards du projet
6. **Créez une Pull Request** : Soumettez votre module pour revue

## 4. Standards de Code

### 4.1 JavaScript / TypeScript

Nous suivons les standards Airbnb pour JavaScript avec quelques adaptations :

- **Indentation** : 2 espaces
- **Longueur maximale** : 100 caractères par ligne
- **Semicolons** : obligatoires
- **Quotes** : utiliser les single quotes `'` pour les chaînes standard
- **Template literals** : préférer les backticks `` ` `` pour les chaînes avec interpolation
- **Déclaration des variables** : préférer `const` à `let`, éviter `var`
- **Arrow functions** : préférer les arrow functions pour les expressions anonymes
- **Destructuring** : utiliser la déstructuration pour les objets et tableaux
- **Modules** : utiliser la syntaxe ES6 pour les imports/exports
- **Async/Await** : privilégier async/await plutôt que les Promises directes

Configuration ESLint recommandée :
```json
{
  "extends": "airbnb-base",
  "rules": {
    "no-console": ["error", { "allow": ["warn", "error"] }],
    "max-len": ["error", { "code": 100 }],
    "import/prefer-default-export": "off"
  }
}
```

Pour TypeScript, nous utilisons les types stricts et évitons le type `any` sauf nécessité absolue.

### 4.2 Python

Nous suivons PEP 8 avec quelques modifications :

- **Indentation** : 4 espaces
- **Longueur maximale** : 88 caractères (compatible avec Black)
- **Docstrings** : format Google, pas NumPy ni reStructuredText
- **Imports** : groupés par standard, tiers, et internes, ordonnés alphabétiquement
- **Type hints** : obligatoires pour toutes les fonctions et méthodes
- **Formatage** : utiliser le formateur Black

Exemple de formatage de fonction avec docstring :
```python
def calculate_ingredient_usage(
    ingredient_id: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, float]:
    """Calcule l'utilisation d'un ingrédient sur une période donnée.
    
    Args:
        ingredient_id: Identifiant unique de l'ingrédient.
        start_date: Date de début de la période d'analyse.
        end_date: Date de fin de la période d'analyse.
        
    Returns:
        Dictionnaire contenant la quantité utilisée et le coût associé.
        
    Raises:
        IngredientNotFoundError: Si l'ingrédient n'existe pas.
        DateRangeError: Si la période est invalide.
    """
    # Implémentation...
```

Configuration flake8 recommandée :
```ini
[flake8]
max-line-length = 88
extend-ignore = E203
```

### 4.3 HTML/CSS

Pour HTML et CSS, nous suivons les conventions suivantes :

- **Indentation** : 2 espaces
- **Noms de classes CSS** : utiliser BEM (Block Element Modifier) ou Tailwind
- **Sélecteurs** : éviter les sélecteurs trop spécifiques
- **Compatibilité** : supporter les 2 dernières versions des navigateurs majeurs
- **Responsive** : conception mobile-first obligatoire

### 4.4 Commentaires

Les commentaires doivent être clairs, concis et surtout utiles :

- **Commentaires de fonction/méthode** : expliquer le but, les paramètres, la valeur de retour et les exceptions
- **Commentaires d'implémentation** : expliquer "pourquoi", pas "comment" (le code explique déjà le "comment")
- **TODO/FIXME** : utiliser les tags standardisés suivis d'une description et d'une référence à un ticket

#### Exemples de bons commentaires

```javascript
// GOOD: Explique pourquoi cette approche est utilisée
// Utilisation de setTimeout pour éviter le rate limiting de l'API
setTimeout(() => {
  fetchDataFromApi();
}, 1000);

// GOOD: Documentation de fonction
/**
 * Calcule le prix optimal basé sur l'historique des ventes et la demande actuelle
 * @param {string} productId - Identifiant du produit
 * @param {number} currentStock - Niveau de stock actuel
 * @returns {number} Prix optimal recommandé
 * @throws {ProductNotFoundError} Si le produit n'existe pas
 */
function calculateOptimalPrice(productId, currentStock) {
  // Implémentation...
}
```

#### Exemples de mauvais commentaires

```javascript
// BAD: Répète ce que le code fait déjà
// Incrémente counter de 1
counter += 1;

// BAD: Commentaire obsolète ou incorrect
// Vérifie si l'utilisateur est admin
if (user.role === 'editor') {
  // ...
}
```

### 4.5 Logging

Utilisez le logging approprié plutôt que `console.log` :

- **Niveaux de log** : ERROR, WARN, INFO, DEBUG, TRACE
- **Format** : timestamp, niveau, module, message, contexte
- **Sensibilité** : jamais de données sensibles dans les logs

## 5. Documentation

### 5.1 Structure des README.md

Chaque module doit avoir un fichier README.md avec la structure suivante :

```markdown
# Nom du Module

Description concise du rôle et des fonctionnalités du module.

## Structure du Module

Description de l'organisation interne du module.

## Installation

Instructions détaillées pour l'installation et la configuration.

## Utilisation

Exemples d'utilisation basiques et avancés.

## API

Description des interfaces publiques.

## Dépendances

Liste des dépendances externes.

## Tests

Instructions pour exécuter les tests.

## Contribution

Instructions spécifiques pour contribuer à ce module.
```

### 5.2 Documentation d'API

Pour les API REST, utilisez la spécification OpenAPI 3.0 :

- Chaque endpoint doit être documenté avec :
  - Description
  - Paramètres d'entrée
  - Format de réponse
  - Codes d'erreur possibles
  - Exemples de requête et réponse

Pour les API internes (modules, classes, fonctions) :

- JavaScript/TypeScript : utiliser JSDoc
- Python : utiliser les docstrings au format Google

### 5.3 Architecture et Diagrammes

Pour les diagrammes d'architecture :

- Utiliser des formats standards : UML, C4, etc.
- Stocker les sources des diagrammes (par exemple, fichiers PlantUML ou draw.io) avec les diagrammes exportés
- Placer les diagrammes dans le dossier `/ARCHITECTURE` ou dans le sous-dossier `docs` du module concerné

### 5.4 Exemples et Cas d'Utilisation

Fournissez des exemples concrets pour chaque fonctionnalité importante :

- Exemples de code complets et fonctionnels
- Cas d'utilisation réels
- Scénarios de test et configurations types

## 6. Processus de Contribution

### 6.1 Modèle de Branches

Nous utilisons un modèle de branches inspiré de GitFlow :

- `main` : branche principale, toujours stable et déployable
- `develop` : branche d'intégration des fonctionnalités
- `feature/*` : branches pour les nouvelles fonctionnalités
- `bugfix/*` : branches pour les corrections de bugs
- `hotfix/*` : branches pour les correctifs urgents
- `release/*` : branches de préparation des releases

Nommage des branches :
- `feature/module-nom-fonctionnalite` (ex: `feature/iot-weight-calibration`)
- `bugfix/module-description-bug` (ex: `bugfix/ui-fix-responsive-layout`)
- `hotfix/description-probleme` (ex: `hotfix/security-oauth-vulnerability`)
- `release/vX.Y.Z` (ex: `release/v1.2.0`)

### 6.2 Commits et Messages

Les messages de commit doivent être clairs et informatifs :

- Format : `type(scope): description concise`
- Types : `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- Scope : module ou composant concerné
- Description : en français, à l'impératif présent, première lettre en minuscule
- Corps du message : expliquer "pourquoi" plutôt que "comment"
- Référence aux tickets : inclure "Fixes #123" ou "Relates to #456"

Exemples :
```
feat(iot): ajouter calibration automatique des cellules de charge

Cette fonctionnalité permet aux cellules de charge de s'auto-calibrer 
quotidiennement basé sur des points de référence connus.

Fixes #45
```

```
fix(ui): corriger l'affichage du tableau de bord sur tablettes

Le layout était cassé sur les appareils avec une résolution entre 768px et 1024px.

Relates to #78
```

### 6.3 Pull Requests

Les Pull Requests (PR) doivent suivre ces règles :

- **Titre** : format similaire aux messages de commit `type(scope): description`
- **Description** : utiliser le template fourni, inclure:
  - Objectif de la PR
  - Changements apportés
  - Captures d'écran (si UI)
  - Tests effectués
  - Références aux tickets concernés
- **Taille** : limiter à un maximum de 500 lignes modifiées par PR
- **Assignation** : assigner au moins 2 reviewers
- **CI** : tous les tests automatisés doivent passer
- **Revue** : approbation de 2 reviewers minimum requise

Template de Pull Request :
```markdown
## Description
Décrivez le but et le contexte de cette PR.

## Changements
- Détaillez les modifications importantes
- Listez les nouveaux fichiers
- Mentionnez les dépendances ajoutées

## Captures d'écran
Si applicable, ajoutez des captures d'écran.

## Tests
- [ ] Tests unitaires ajoutés/modifiés
- [ ] Tests d'intégration effectués
- [ ] Validation manuelle réalisée

## Tickets
Fixes #123
Relates to #456
```

### 6.4 Résolution de Conflits

En cas de conflits lors d'un merge ou rebase :

1. Assurez-vous de comprendre les deux versions du code en conflit
2. Privilégiez la version la plus récente si elle est compatible
3. Consultez les auteurs originaux en cas de doute
4. Testez soigneusement après résolution des conflits
5. Documentez les décisions importantes dans le message de commit

## 7. Processus de Revue

### 7.1 Revue de Code

La revue de code vérifie les points suivants :

1. **Fonctionnalité** : le code fait-il ce qu'il est censé faire ?
2. **Qualité** : respect des standards de code, lisibilité, maintenabilité
3. **Tests** : couverture de tests adéquate, cas limites pris en compte
4. **Performance** : absence de problèmes de performance évidents
5. **Sécurité** : absence de vulnérabilités

Checklist de revue :
- [ ] Le code respecte les standards et conventions du projet
- [ ] Les noms de variables/fonctions sont clairs et significatifs
- [ ] La logique est simple et compréhensible
- [ ] Le code ne contient pas de duplication évitable
- [ ] Les tests couvrent les cas normaux et exceptionnels
- [ ] La documentation est complète et à jour
- [ ] Les logs et messages d'erreur sont appropriés
- [ ] Le code gère correctement les erreurs
- [ ] Les performances sont acceptables
- [ ] Les données sensibles sont correctement protégées

### 7.2 Revue de Documentation

La revue de documentation vérifie :

1. **Exactitude** : la documentation correspond au code
2. **Complétude** : tous les aspects sont documentés
3. **Clarté** : la documentation est compréhensible
4. **Format** : respect des standards de documentation
5. **Exemples** : présence d'exemples pertinents

### 7.3 Tests et Intégration Continue

Notre pipeline CI/CD exécute automatiquement :

1. **Linting** : analyse statique du code
2. **Tests unitaires** : tests de composants isolés
3. **Tests d'intégration** : tests des interactions entre composants
4. **Analyse de couverture** : minimum 80% de couverture requis
5. **Build** : vérification que le projet se compile correctement
6. **Analyse de sécurité** : détection de vulnérabilités connues

Exigences pour les tests :
- Chaque nouvelle fonctionnalité doit avoir des tests unitaires
- Les modifications de code existant doivent maintenir ou améliorer la couverture
- Les tests doivent être indépendants et reproductibles
- Les mocks et stubs doivent être utilisés pour isoler les dépendances

## 8. Gestion des Doublons et Redondances

### 8.1 Détection du Code Dupliqué

Nous utilisons des outils automatisés pour détecter le code dupliqué :

- ESLint avec `no-duplicate-imports` et `import/no-duplicates`
- SonarQube pour l'analyse de duplication de code
- Rapport de couverture pour identifier les tests redondants

### 8.2 Réutilisation vs Duplication

Principes à suivre :

- **DRY (Don't Repeat Yourself)** : factoriser le code commun
- **Modularité** : concevoir des composants réutilisables
- **Dépendances partagées** : utiliser le dossier `/common/` pour le code partagé entre modules
- **Bibliothèques utilitaires** : créer des bibliothèques internes pour les fonctionnalités réutilisables

Quand la duplication peut être acceptable :
- Lorsque la réutilisation crée un couplage excessif
- Pour des optimisations de performance critiques
- Pour des composants qui évoluent de manière divergente

### 8.3 Refactorisation

Principes pour une refactorisation efficace :

1. Identifier les zones de duplication
2. Évaluer l'impact d'une refactorisation
3. Créer des tests couvrant la fonctionnalité actuelle
4. Refactoriser progressivement
5. Vérifier que les tests continuent de passer
6. Documenter les changements architecturaux

## 9. Mise à Jour des Conventions

### 9.1 Processus de Révision

Ce document CONTRIBUTING.md est révisé :

- À chaque version majeure du projet (x.0.0)
- Lors de l'ajout d'un nouveau module majeur
- Sur proposition justifiée d'un membre de l'équipe

### 9.2 Proposition de Modifications

Pour proposer des modifications aux conventions :

1. Créez un ticket dans le système de suivi avec le label "convention"
2. Détaillez la proposition avec justification et exemples
3. Obtenez l'approbation d'au moins 3 membres de l'équipe core
4. Créez une PR modifiant le CONTRIBUTING.md
5. Après approbation et merge, communiquez les changements à toute l'équipe

## 10. Outils Recommandés

Pour assurer l'adhésion aux standards, nous recommandons ces outils :

- **Éditeurs** : VSCode, WebStorm, PyCharm
- **Extensions VSCode** :
  - ESLint
  - Prettier
  - Python (avec support Black)
  - EditorConfig
  - GitLens
  - Markdown All in One
- **Outils en ligne de commande** :
  - ESLint
  - Prettier
  - Black
  - flake8
  - isort
  - commitlint
  - husky (pre-commit hooks)

Configuration EditorConfig recommandée :
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{js,jsx,ts,tsx,json}]
indent_style = space
indent_size = 2

[*.{py}]
indent_style = space
indent_size = 4

[*.{md,markdown}]
trim_trailing_whitespace = false
```

## 11. Contact et Assistance

Pour toute question concernant ces conventions ou le processus de contribution :

- Consultez la documentation existante
- Demandez sur le canal Slack `#dev-contribution`
- Contactez les responsables du projet :
  - Jean Dupont (Architecture) - jean.dupont@example.com
  - Marie Martin (DevOps) - marie.martin@example.com

---

Ce document est maintenu par l'équipe de développement de "Le Vieux Moulin".
Dernière mise à jour : 12 avril 2025
