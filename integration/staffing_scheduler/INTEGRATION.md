# Intégration du Module de Planification du Personnel

Ce document décrit comment le module d'optimisation des plannings s'intègre avec les autres composants du système de gestion du restaurant "Le Vieux Moulin".

## Architecture d'Intégration

Le module de planification du personnel est conçu comme un service indépendant qui interagit avec plusieurs autres modules via des API REST et des échanges de données standardisés.

### Schéma d'Intégration Globale

```
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │      │                   │
│  Module Prévision ├──────►  Planification    │◄─────┤  Système de       │
│  (ML)             │      │  du Personnel     │      │  Réservations     │
│                   │      │                   │      │                   │
└───────┬───────────┘      └─────────┬─────────┘      └───────────────────┘
        │                            │                          ▲
        │                            │                          │
        │                            ▼                          │
        │               ┌───────────────────────┐               │
        │               │                       │               │
        └───────────────►  Base de Données      ├───────────────┘
                        │  Centrale            │
                        │                       │
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │                       │
                        │  Interface            │
                        │  Gestionnaire         │
                        │                       │
                        └───────────────────────┘
```

## Interfaces d'Intégration

### 1. Module de Prédiction (ML)

Le module de planification récupère les prévisions d'affluence via l'API REST du module de prédiction.

#### Endpoints Utilisés

- **GET** `/api/finance/forecast`
  - Récupère les prévisions financières pour estimer l'activité
  - Paramètres: métriques, horizon temporel
  
- **POST** `/api/stock/forecast`
  - Analyse les prévisions de consommation pour estimer l'activité par service
  - Peut être corrélé avec les besoins en personnel

#### Format d'Échange

```json
{
  "date": "2025-04-21",
  "hourly_predictions": {
    "11:00": {"customers": 25, "confidence_interval": [20, 30]},
    "12:00": {"customers": 45, "confidence_interval": [38, 52]},
    "13:00": {"customers": 60, "confidence_interval": [52, 68]},
    // ...autres heures
  },
  "special_events": [
    {"type": "holiday", "impact_factor": 1.5}
  ]
}
```

### 2. Système de Réservations

Le module récupère les réservations confirmées pour affiner les prévisions d'affluence.

#### Endpoints Utilisés

- **GET** `/api/reservations/upcoming`
  - Récupère les réservations pour une période donnée
  - Paramètres: date de début, date de fin
  
- **GET** `/api/reservations/groups`
  - Récupère spécifiquement les réservations de groupe qui nécessitent un personnel dédié

#### Format d'Échange

```json
{
  "date": "2025-04-21",
  "reservations": [
    {
      "time": "19:30",
      "guests": 4,
      "table_id": "T15",
      "special_requests": null
    },
    {
      "time": "20:00",
      "guests": 8,
      "table_id": "T10",
      "special_requests": "Anniversaire"
    }
    // ...autres réservations
  ],
  "total_reserved": 45,
  "estimated_walk_ins": 15
}
```

### 3. Module de Comptabilité

Les données de planification sont transmises au module de comptabilité pour le suivi des coûts de personnel.

#### Endpoints Utilisés

- **POST** `/api/accounting/labor-costs`
  - Transmet les heures planifiées pour estimation des coûts
  - Reçoit les contraintes budgétaires pour ajuster les plannings

#### Format d'Échange

```json
{
  "week_start": "2025-04-21",
  "week_end": "2025-04-27",
  "staff_hours": [
    {
      "employee_id": "EMP123",
      "role": "serveur",
      "hours": 35,
      "estimated_cost": 525.00
    },
    // ...autres employés
  ],
  "total_hours": 320,
  "total_cost": 4800.00,
  "budget_limit": 5000.00
}
```

### 4. Base de Données Centrale

Le module interagit avec la base de données centrale pour stocker et récupérer les données relatives aux employés et aux plannings.

#### Tables Principales

- `employees` - Informations sur les employés
- `schedules` - Plannings générés
- `availability` - Disponibilités des employés
- `skills` - Compétences des employés
- `shift_templates` - Modèles de shifts prédéfinis
- `schedule_constraints` - Contraintes personnalisées

#### Exemple de Requête

```sql
-- Récupérer les employés disponibles pour un créneau spécifique
SELECT e.employee_id, e.name, e.role, e.hourly_rate
FROM employees e
JOIN availability a ON e.employee_id = a.employee_id
WHERE e.role = 'serveur'
AND a.day_of_week = 1 -- Lundi
AND a.start_time <= '18:00' AND a.end_time >= '23:00'
AND e.employee_id NOT IN (
    SELECT employee_id FROM scheduled_shifts 
    WHERE shift_date = '2025-04-21'
    AND ((start_time <= '18:00' AND end_time > '18:00') 
       OR (start_time < '23:00' AND end_time >= '23:00')
       OR (start_time >= '18:00' AND end_time <= '23:00'))
);
```

## API Exposée par le Module de Planification

Le module de planification expose sa propre API REST pour permettre aux autres composants d'interagir avec lui.

### Endpoints Principaux

#### 1. Génération de Planning

- **POST** `/api/schedules/generate`
  - Corps: Période, contraintes spécifiques
  - Génère un nouveau planning pour la période spécifiée

#### 2. Consultation des Plannings

- **GET** `/api/schedules`
  - Paramètres: Date de début, date de fin
  - Récupère les plannings existants

#### 3. Modification de Planning

- **PUT** `/api/schedules/{schedule_id}`
  - Corps: Modifications à appliquer
  - Met à jour un planning existant

#### 4. Validation de Planning

- **POST** `/api/schedules/{schedule_id}/validate`
  - Corps: Identifiant du validateur, commentaires
  - Marque un planning comme validé

## Formats de Données Échangées

### 1. Format de Planning Complet

```json
{
  "schedule_id": "SCH-2025-16",
  "period": {
    "start_date": "2025-04-21",
    "end_date": "2025-04-27"
  },
  "generated_at": "2025-04-15T14:30:22Z",
  "generated_by": "system",
  "last_modified_at": "2025-04-16T09:15:30Z",
  "last_modified_by": "manager@vieuxmoulin.fr",
  "status": "draft",
  "shifts": [
    {
      "shift_id": "SHF-123456",
      "employee_id": "EMP123",
      "employee_name": "Jean Dupont",
      "role": "serveur",
      "date": "2025-04-21",
      "start_time": "17:00",
      "end_time": "23:30",
      "break_duration": 30,
      "location": "salle_principale"
    },
    // ...autres shifts
  ],
  "metrics": {
    "total_hours": 320,
    "total_cost": 4800.00,
    "coverage_rate": 0.95,
    "preference_satisfaction": 0.82
  }
}
```

### 2. Format de Contraintes

```json
{
  "constraint_id": "CON-987",
  "type": "unavailability",
  "employee_id": "EMP123",
  "start_date": "2025-04-23",
  "end_date": "2025-04-23",
  "start_time": "18:00",
  "end_time": "22:00",
  "priority": "high",
  "reason": "Formation externe",
  "created_at": "2025-04-10T11:23:45Z",
  "created_by": "employee",
  "status": "approved"
}
```

## Protocoles de Communication

1. **REST API** - Communication synchrone avec JSON
2. **WebSockets** - Notifications en temps réel des changements de planning
3. **Webhooks** - Notifications asynchrones vers d'autres systèmes
4. **Message Queue** - Communication asynchrone pour les tâches de longue durée

## Sécurité et Authentification

- Toutes les API sont protégées par authentification OAuth2
- Utilisation de JWT (JSON Web Tokens) pour l'autorisation
- Chiffrement TLS pour toutes les communications
- Gestion fine des permissions via RBAC (Role-Based Access Control)

## Gestion des Erreurs

Structure standardisée pour les erreurs:

```json
{
  "error": {
    "code": "STAFF_UNAVAILABLE",
    "message": "Impossible de générer un planning complet avec les contraintes actuelles",
    "details": [
      "Le poste 'Chef de Rang' n'a pas de personnel disponible le 2025-04-23 entre 19:00 et 23:00",
      "3 serveurs supplémentaires nécessaires pour le 2025-04-24"
    ],
    "timestamp": "2025-04-15T14:32:10Z",
    "request_id": "REQ-123456"
  },
  "suggestions": [
    "Considérer l'embauche de personnel temporaire",
    "Modifier les contraintes de disponibilité",
    "Réduire le personnel minimum requis"
  ]
}
```

## Cas d'Intégration Spécifiques

### 1. Événements Spéciaux

Pour un événement spécial (ex: soirée à thème), l'intégration suit ce processus:

1. Le module de réservation signale l'événement spécial
2. Le module de prédiction ajuste ses prévisions en conséquence
3. Le module de planification génère un planning spécifique avec personnel dédié
4. Le module comptable reçoit une catégorisation spécifique pour ces coûts

### 2. Intégration avec le Système de Temps de Travail

Les heures planifiées sont comparées aux heures réellement travaillées:

1. Le système de pointage envoie les données réelles
2. Le module de planification analyse les écarts
3. Ces données alimentent le système d'amélioration continue
4. Le module comptable reçoit les heures réelles pour la paie

## Tests d'Intégration

Des tests d'intégration automatisés vérifient la compatibilité entre les différents modules:

1. Tests de bout en bout simulant des scénarios complets
2. Tests de performance sous charge
3. Tests de résistance aux erreurs et de récupération
4. Validation des formats de données échangées