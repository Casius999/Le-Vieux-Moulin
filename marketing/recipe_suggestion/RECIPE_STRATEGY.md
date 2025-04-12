# Stratégie de Génération de Recettes - Le Vieux Moulin

Ce document détaille la stratégie et l'algorithme utilisés par le module de suggestion de recettes dynamiques du restaurant "Le Vieux Moulin". Il explique la logique derrière l'algorithme, les données d'entrée nécessaires, et les critères de décision pour générer des suggestions pertinentes.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Données d'entrée](#données-dentrée)
3. [Algorithme de génération](#algorithme-de-génération)
4. [Critères de décision](#critères-de-décision)
5. [Processus de validation](#processus-de-validation)
6. [Adaptation et apprentissage](#adaptation-et-apprentissage)
7. [Exemples concrets](#exemples-concrets)

## Vue d'ensemble

Le système de génération de recettes dynamiques vise à créer des suggestions innovantes et rentables en croisant trois sources principales d'information :
- Les promotions actuelles des fournisseurs
- Les préférences et tendances clients
- L'inventaire et les capacités opérationnelles du restaurant

L'objectif est de maximiser simultanément :
- L'attractivité commerciale des suggestions
- La rentabilité économique
- L'utilisation efficace des ingrédients à forte disponibilité ou en promotion
- La variation et l'innovation dans les offres

## Données d'entrée

### 1. Données fournisseurs

**Sources :**
- API des fournisseurs principaux (Metro, Transgourmet, Pomona)
- Flux EDI (Échange de Données Informatisé)
- Saisie manuelle des promotions ponctuelles

**Informations collectées :**
- Prix normal et prix promotionnel des ingrédients
- Durée de validité des promotions
- Quantités disponibles et délais de livraison
- Qualité et spécificités des produits (labels, origines, etc.)

### 2. Données clients et tendances

**Sources :**
- Historique des ventes du restaurant (POS)
- Commentaires et évaluations clients
- Tendances locales (événements, météo, saison)
- Tendances culinaires identifiées sur les réseaux sociaux

**Informations collectées :**
- Popularité des plats existants
- Combinaisons d'ingrédients appréciées
- Sensibilité au prix
- Préférences démographiques
- Saisonnalité des préférences

### 3. Données internes du restaurant

**Sources :**
- Système d'inventaire
- Planning de production
- Compétences et disponibilité du personnel
- Capacité des équipements

**Informations collectées :**
- Niveaux de stock actuels
- Ingrédients à écouler prioritairement
- Contraintes de production
- Rentabilité historique par plat/ingrédient

## Algorithme de génération

L'algorithme fonctionne en plusieurs phases séquentielles :

### Phase 1 : Collecte et prétraitement des données

1. **Récupération des promotions** : Agrégation des offres de tous les fournisseurs
2. **Normalisation des données** : Conversion en format standard (unités, catégories, etc.)
3. **Filtrage préliminaire** : Élimination des promotions non pertinentes (allergènes interdits, etc.)

### Phase 2 : Analyse des opportunités

1. **Scoring des ingrédients** selon plusieurs critères :
   - Économie potentielle (différence prix normal/promotion)
   - Quantité disponible ou à écouler
   - Facilité d'utilisation
   - Compatibilité avec les autres ingrédients courants

2. **Identification des combinaisons avantageuses** :
   - Groupes d'ingrédients promotionnels complémentaires
   - Combinaisons avec forte marge potentielle
   - Combinaisons alignées aux tendances actuelles

### Phase 3 : Génération de recettes

1. **Consultation de la base de connaissances** :
   - Base de recettes existantes du restaurant
   - Recettes classiques de la gastronomie
   - Innovations précédentes à succès

2. **Approche hybride de génération** :
   - Adaptation de recettes existantes avec les ingrédients cibles
   - Création de nouvelles combinaisons selon des règles culinaires
   - Application de techniques d'apprentissage automatique (si connecté au module ML)

3. **Optimisation multicritères** :
   - Équilibre entre coût, attractivité, et faisabilité opérationnelle
   - Diversité de l'offre dans le temps
   - Respect des contraintes nutritionnelles et allergènes

### Phase 4 : Raffinement et présentation

1. **Ajustement des quantités et proportions**
2. **Calcul précis des coûts et de la rentabilité**
3. **Formulation d'un nom commercial attractif**
4. **Création d'une description marketing**
5. **Génération de visuels ou templates pour la promotion**

## Critères de décision

Les suggestions sont évaluées et priorisées selon les critères suivants :

### Critères économiques (40%)

- **Marge brute** : Différence entre prix de vente et coût des ingrédients
- **Économie d'approvisionnement** : Réduction du coût par l'usage de promotions
- **Optimisation des stocks** : Utilisation d'ingrédients à écouler
- **Rendement de production** : Temps de préparation et complexité

### Critères commerciaux (30%)

- **Attractivité estimée** : Basée sur l'historique de ventes de plats similaires
- **Unicité de l'offre** : Différenciation par rapport aux offres standards
- **Valeur perçue** : Rapport qualité-prix apparent pour le client
- **Alignement saisonnier** : Pertinence par rapport à la saison actuelle

### Critères opérationnels (20%)

- **Facilité de préparation** : Complexité technique et temps requis
- **Disponibilité des équipements** nécessaires
- **Compétences requises** vs. compétences disponibles en cuisine
- **Durabilité de l'offre** : Possibilité de maintenir la recette pendant la durée prévue

### Critères stratégiques (10%)

- **Alignement avec l'identité du restaurant**
- **Contribution à la variation de l'offre**
- **Potentiel médiatique** (instagrammabilité, etc.)
- **Cohérence avec les objectifs marketing actuels**

## Processus de validation

Chaque suggestion générée passe par un processus de validation en plusieurs étapes :

1. **Validation technique** : Vérification de la faisabilité culinaire et de la cohérence des ingrédients

2. **Validation économique** : Confirmation de la rentabilité et des avantages économiques

3. **Validation opérationnelle** (optionnelle) : Approbation par le chef ou le responsable de cuisine

4. **Validation marketing** (pour les suggestions majeures) : Alignement avec la stratégie marketing

## Adaptation et apprentissage

Le système s'améliore continuellement grâce à :

1. **Analyse des performances** : Suivi des ventes et de la popularité des suggestions précédentes

2. **Rétroaction manuelle** : Retours des équipes de cuisine et de service

3. **Ajustement des poids** : Modification des pondérations des critères selon les performances observées

4. **Enrichissement de la base de connaissances** : Ajout des nouvelles recettes réussies à la base

## Exemples concrets

### Exemple 1 : Pizza du jour basée sur une promotion de fromage

**Données d'entrée :**
- Promotion : -30% sur la mozzarella di bufala chez Metro (valable 5 jours)
- Tendance détectée : Intérêt croissant pour les produits locaux
- Données internes : Stock élevé de tomates cerises et de roquette à écouler

**Processus de génération :**
1. L'algorithme identifie la combinaison avantageuse : mozzarella di bufala + tomates cerises + roquette
2. Consultation de la base de recettes pour des pizzas similaires
3. Génération d'une variante : "Pizza Bufala Primavera" avec base blanche, mozzarella di bufala, tomates cerises, roquette et huile d'olive au basilic
4. Calcul de rentabilité : marge de 72% malgré la promotion
5. Suggestion marketing : "Pizza du jour avec mozzarella di bufala AOP et produits de notre région"

### Exemple 2 : Plat spécial basé sur un événement local

**Données d'entrée :**
- Événement local : Festival des vins de Médoc ce week-end
- Promotion : -20% sur le magret de canard chez Transgourmet
- Tendance : Photos de plats à base de canard populaires sur Instagram local
- Données internes : Vin rouge local déjà en stock

**Processus de génération :**
1. L'algorithme identifie l'opportunité de créer un plat en accord avec l'événement local
2. Création d'une recette spéciale : "Magret de canard au vin rouge du Médoc"
3. Suggestion d'un menu accord mets-vins spécial festival
4. Calcul du prix optimal pour maximiser l'attractivité et la marge
5. Génération d'une description mettant en avant le caractère local et événementiel

---

Ce document est régulièrement mis à jour pour refléter les évolutions et améliorations apportées à l'algorithme de suggestion de recettes.

**Dernière mise à jour :** Avril 2025