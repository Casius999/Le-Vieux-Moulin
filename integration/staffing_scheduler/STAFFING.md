# Documentation d'Optimisation des Plannings

## Méthodologie d'Optimisation

Le module d'optimisation des plannings du personnel du restaurant "Le Vieux Moulin" utilise une approche hybride qui combine plusieurs techniques pour générer des plannings efficaces et équilibrés.

### 1. Algorithme Principal

Notre système utilise un **algorithme génétique multi-contraintes** qui optimise simultanément plusieurs objectifs :

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
   - Exécution de l'algorithme génétique avec les contraintes actuelles
   - Ajustements fins pour maximiser l'efficacité

4. **Validation et publication** :
   - Contrôle automatique de validité du planning
   - Soumission aux managers pour validation finale

### Mécanismes d'Adaptation

Le système intègre plusieurs mécanismes d'adaptation :

- **Détection d'anomalies** : Identification des écarts significatifs entre prévisions et réalité
- **Ajustement dynamique** : Modification des coefficients selon les performances passées
- **Apprentissage continu** : Amélioration progressive des prévisions de besoins en personnel

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