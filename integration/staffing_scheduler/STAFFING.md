# Documentation d'Optimisation des Plannings

## Méthodologie d'Optimisation

Le module d'optimisation des plannings du personnel du restaurant "Le Vieux Moulin" utilise une approche hybride qui combine plusieurs techniques pour générer des plannings efficaces et équilibrés.

### 1. Algorithmes d'Optimisation

Notre système propose deux types d'algorithmes d'optimisation complémentaires :

#### 1.1 Algorithme Génétique Multi-contraintes (Standard)

L'optimiseur standard utilise un **algorithme génétique multi-contraintes** qui optimise simultanément plusieurs objectifs :

- Adéquation entre le nombre d'employés et l'affluence prévue
- Minimisation des coûts de main-d'œuvre
- Respect des contraintes légales et des préférences des employés
- Équité dans la distribution des horaires
- Maintien d'une qualité de service constante

L'algorithme fonctionne en plusieurs phases :

1. **Initialisation** : Génération d'une population initiale de plannings potentiels
2. **Évaluation** : Notation de chaque planning selon les critères d'optimisation
3. **Sélection** : Sélection des meilleurs candidats
4. **Croisement et Mutation** : Création de nouveaux plannings par combinaison et modification
5. **Convergence** : Répétition jusqu'à obtention d'un planning optimal

#### 1.2 Optimiseur ML Avancé (Nouveau)

En complément, le système propose un **optimiseur basé sur le Machine Learning** qui améliore les résultats en s'appuyant sur les données historiques et les performances passées :

- **Apprentissage des motifs de performance** à partir des plannings précédents
- **Analyse des performances individuelles** des employés selon les postes et horaires
- **Amélioration continue** des prédictions grâce à la rétroaction
- **Recommandations personnalisées** pour l'affectation des employés

L'optimiseur ML fonctionne selon ce processus :

1. **Collecte de données historiques** : Analyse des plannings passés et leurs métriques de performance
2. **Extraction de caractéristiques** : Identification des facteurs clés influençant la qualité des plannings
3. **Entraînement du modèle** : Création d'un modèle prédictif des performances
4. **Optimisation guidée** : Utilisation du modèle pour orienter l'algorithme génétique
5. **Analyse post-optimisation** : Fourniture d'insights et recommandations

### 2. Prévisions d'Affluence et Besoins en Personnel

Le système exploite les données du module de prédiction pour estimer les besoins en personnel :

#### Sources de Données
- **Prévisions horaires d'affluence** obtenues via l'API du module de prédiction
- **Historique des réservations** et tendances identifiées
- **Événements spéciaux** (fêtes, promotions, etc.)
- **Saisonnalité** (jour de la semaine, mois, saison)

#### Calcul des Besoins
Pour chaque créneau horaire, le système calcule :

```
NombreEmployésNécessaires = BaselineStaffing + (PrévisionClients * RatioPersonnelParClient) + AjustementÉvénement
```

Où :
- `BaselineStaffing` : Personnel minimum requis pour le fonctionnement de base
- `RatioPersonnelParClient` : Taux adaptatif selon le moment de la journée et le type de service
- `AjustementÉvénement` : Modification selon les événements spéciaux

## Règles et Critères d'Attribution des Horaires

### 1. Contraintes Fermes (doivent être respectées)

- **Légales** :
  - Temps de repos minimum entre deux services (11h)
  - Durée maximum de travail par jour (10h)
  - Durée maximum de travail par semaine (48h)
  - Respect des jours de congé contractuels

- **Compétences** :
  - Chaque poste doit être couvert par au moins un employé qualifié
  - Ratios minimums de personnel expérimenté/junior

- **Disponibilités** :
  - Respect des indisponibilités déclarées par les employés
  - Respect des congés validés

### 2. Contraintes Souples (à optimiser)

- **Préférences des employés** :
  - Prise en compte des souhaits d'horaires (pondération adaptative)
  - Rotation équitable des horaires non-désirés (weekends, soirées)

- **Continuité de service** :
  - Éviter les changements fréquents d'équipe
  - Maintenir des équipes cohérentes

- **Équité** :
  - Distribution équilibrée des heures entre employés de même statut
  - Alternance équitable des horaires valorisés et contraignants

### 3. Système de Pondération

Chaque contrainte est associée à un **coefficient de pondération** qui peut être ajusté par les gestionnaires selon les priorités actuelles du restaurant.

## Logique de Croisement Prévisions/Affectations

### Processus d'Intégration des Données

1. **Collecte et prétraitement** :
   - Récupération des prévisions d'affluence via l'API du module de prédiction
   - Extraction des réservations confirmées depuis la base de données
   - Collecte des données RH (disponibilités, congés, compétences)

2. **Modélisation de la charge de travail** :
   - Conversion des prévisions d'affluence en besoins de personnel par poste
   - Ajustement selon la complexité des services prévus

3. **Génération et optimisation des plannings** :
   - Exécution de l'algorithme avec les contraintes actuelles
   - Ajustements fins pour maximiser l'efficacité

4. **Validation et publication** :
   - Contrôle automatique de validité du planning
   - Soumission aux managers pour validation finale

### Mécanismes d'Adaptation

Le système intègre plusieurs mécanismes d'adaptation :

- **Détection d'anomalies** : Identification des écarts significatifs entre prévisions et réalité
- **Ajustement dynamique** : Modification des coefficients selon les performances passées
- **Apprentissage continu** : Amélioration progressive des prévisions de besoins en personnel

## Utilisation de l'Apprentissage Automatique

### 1. Extraction de Caractéristiques

Le système extrait et analyse plusieurs caractéristiques des plannings pour l'apprentissage :

- **Structure des équipes** :
  - Ratio de couverture par rôle (chefs, serveurs, etc.)
  - Équilibre entre personnel expérimenté et junior
  - Distribution des compétences spécifiques

- **Distribution temporelle** :
  - Répartition des effectifs par jour et heure
  - Concentration du personnel aux heures de pointe
  - Couverture des périodes creuses

- **Métriques de performance** :
  - Taux de couverture des besoins
  - Respect des préférences des employés
  - Coût relatif du planning
  - Indicateurs de satisfaction client associés

### 2. Analyse Prédictive des Performances

Le modèle ML utilise ces caractéristiques pour :

- **Prédire la performance attendue** d'un planning proposé
- **Identifier les facteurs clés** qui contribuent à un planning réussi
- **Détecter les configurations sous-optimales** avant leur mise en œuvre
- **Suggérer des améliorations spécifiques** pour optimiser les plannings

### 3. Optimisation Intelligente

L'optimiseur ML améliore le processus standard en :

- **Initialisant intelligemment** la population avec des configurations prometteuses
- **Orientant la recherche** vers les caractéristiques historiquement performantes
- **Équilibrant exploitation et exploration** pour découvrir de nouvelles configurations optimales
- **Ajustant dynamiquement les coefficients de pondération** selon les tendances observées

### 4. Insights et Recommandations

Le système fournit des analyses avancées aux gestionnaires :

- **Visualisation de l'importance des caractéristiques** pour comprendre les facteurs de succès
- **Profils de performance individuels** pour chaque employé
- **Recommandations d'affectation personnalisées** basées sur les performances historiques
- **Suggestions d'amélioration continue** du système de planification

## Interface pour les Managers

Les managers disposent d'une interface complète pour interagir avec le système de planification :

### Fonctionnalités d'Édition

- **Visualisation multi-vues** : Consultation par jour, semaine, mois, employé
- **Édition manuelle** : Possibilité de modifier manuellement les plannings générés
- **Simulation d'impact** : Visualisation des conséquences d'un changement avant validation
- **Historique des modifications** : Suivi complet des changements avec horodatage

### Processus de Validation

1. Génération automatique du planning selon la périodicité configurée
2. Notification au manager pour révision
3. Possibilité d'ajustements manuels
4. Validation définitive et publication aux employés
5. Notifications automatiques aux employés concernés

### Indicateurs de Performance

Le système fournit des indicateurs clés pour évaluer l'efficacité des plannings :

- **Taux de couverture** : Adéquation entre besoins prévus et personnel affecté
- **Coût horaire moyen** : Suivi des coûts de main-d'œuvre
- **Satisfaction du personnel** : Basée sur le respect des préférences
- **Stabilité des plannings** : Fréquence des modifications après publication

### Analyses Avancées et Visualisations

L'interface propose également des analyses avancées pour aider à la décision :

- **Tableaux de bord analytiques** présentant l'évolution des métriques sur le temps
- **Cartographie thermique** des besoins vs. affectations par jour/heure
- **Graphiques d'équité** montrant la distribution des horaires et charges de travail
- **Prédictions de performance** pour différentes configurations de planning

## Cas d'Usage Spécifiques

### Gestion des Événements Spéciaux

Pour les événements spéciaux (réservations de groupe, soirées thématiques) :
1. Le système identifie l'événement dans les réservations
2. Les besoins spécifiques en personnel sont calculés
3. Un planning dédié peut être généré en complément du planning régulier

### Gestion des Absences Non-Planifiées

En cas d'absence imprévue :
1. Le système identifie les employés pouvant remplacer (compétences, disponibilités)
2. Propose une liste de remplaçants potentiels avec impact minimal sur le planning existant
3. Facilite le contact et la modification du planning

### Périodes de Haute Activité

Pour les périodes de forte affluence (fêtes, saison touristique) :
1. Détection anticipée grâce aux prévisions long-terme
2. Planification précoce et optimisée des ressources
3. Possibilité d'intégrer du personnel temporaire avec une analyse coût-bénéfice automatisée

### Optimisation Continue

Le système s'améliore en continu grâce à un processus d'auto-ajustement :

1. **Collecte des données de performance réelle** après chaque cycle de planning
2. **Analyse des écarts** entre prévisions et résultats
3. **Ajustement automatique des paramètres** du modèle prédictif
4. **Suggestions d'amélioration** du système présentées aux managers

## Intégration et Exportation

### Exportation des Plannings

Les plannings générés peuvent être exportés dans plusieurs formats :

- **PDF** : Pour impression et affichage
- **CSV/Excel** : Pour analyse et traitement externes
- **iCal/ICS** : Pour intégration aux calendriers personnels
- **JSON/API** : Pour intégration avec d'autres systèmes

### Intégration avec d'Autres Modules

Le module s'intègre nativement avec les autres composants du système :

- **Module de prédiction** : Pour obtenir les prévisions d'affluence
- **Système de réservation** : Pour ajuster en fonction des réservations confirmées
- **Module comptabilité** : Pour le suivi des coûts de personnel
- **Système de pointage** : Pour la comparaison planning vs. heures réelles

### Persistance et Sauvegarde

Les modèles ML entraînés et les configurations optimales peuvent être :

- **Exportés** pour utilisation sur d'autres déploiements
- **Sauvegardés** pour référence et analyse comparative
- **Restaurés** en cas de besoin ou pour effectuer des tests

## Considérations Techniques

### Performances et Scalabilité

Le système est conçu pour :

- Générer rapidement des plannings pour des équipes de 5 à 100 personnes
- Traiter des horizons de planification de 1 jour à 6 mois
- Optimiser jusqu'à 5000 shifts par cycle de planification
- Exécuter le traitement ML en arrière-plan sans impact sur les opérations courantes

### Confidentialité et Sécurité

Toutes les données utilisées sont :

- Anonymisées pour les analyses comparatives
- Stockées de manière sécurisée conformément aux règles RGPD
- Accessibles uniquement aux personnes autorisées selon leur niveau d'habilitation

### Maintenance et Évolution

Le système est conçu avec une architecture modulaire permettant :

- L'ajout de nouveaux algorithmes d'optimisation
- L'intégration de nouvelles sources de données
- L'extension des capacités prédictives
- La personnalisation selon l'évolution des besoins du restaurant
