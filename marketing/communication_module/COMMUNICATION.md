# Documentation Technique - Module de Communication et d'Automatisation Marketing

## Architecture du module

Le module de communication et d'automatisation marketing est conçu selon une architecture modulaire et évolutive, permettant d'ajouter facilement de nouveaux canaux de communication et de modifier les stratégies marketing sans impacter l'ensemble du système.

### Architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                   Communication Controller                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌─────────────┬─────────┴──────────┬─────────────┐
        │             │                    │             │
┌───────▼───────┐ ┌───▼───────────┐ ┌──────▼─────┐ ┌────▼───────┐
│ Social Media  │ │ Notification  │ │   Menu     │ │ Campaign   │
│   Manager     │ │   Manager     │ │  Updater   │ │  Manager   │
└───────┬───────┘ └───────┬───────┘ └──────┬─────┘ └────┬───────┘
        │                 │                │            │
        │                 │                │            │
┌───────▼───────┐ ┌───────▼───────┐ ┌──────▼─────┐ ┌────▼───────┐
│  Publishers   │ │Channel Adapters│ │  Platform  │ │  Campaign  │
│   Adapters    │ │(Email, SMS...) │ │ Connectors │ │   Engine   │
└───────────────┘ └───────────────┘ └────────────┘ └────────────┘
```

### Composants principaux

1. **Communication Controller** : 
   - Orchestre l'ensemble des fonctionnalités du module
   - Gère la planification centralisée des tâches de communication
   - Assure la cohérence des messages sur tous les canaux

2. **Social Media Manager** : 
   - Gère les publications sur les différentes plateformes
   - Adapte le contenu au format de chaque réseau social
   - Analyse les performances des publications

3. **Notification Manager** : 
   - Envoie des notifications personnalisées via différents canaux
   - Gère les modèles de messages et leur personnalisation
   - Assure le suivi des envois et des interactions

4. **Menu Updater** : 
   - Synchronise les menus à travers toutes les plateformes
   - Convertit les données du menu au format requis par chaque plateforme
   - Planifie les mises à jour selon des horaires prédéfinis

5. **Campaign Manager** :
   - Crée et gère les campagnes marketing multicanal
   - Analyse les performances des campagnes
   - Optimise les stratégies en fonction des résultats

### Intégration avec les autres modules

Le module de communication s'intègre avec plusieurs autres composants du système :

```
┌─────────────────┐      ┌───────────────────┐      ┌─────────────────┐
│ Module Central  │      │    Module de      │      │  Module CRM     │
│   (Serveur)     ├─────►│  Communication    │◄─────┤ (Données Client)│
└────────┬────────┘      └───────┬───────────┘      └─────────────────┘
         │                       │                          ▲
         │                       │                          │
         ▼                       ▼                          │
┌─────────────────┐      ┌───────────────────┐      ┌───────┴─────────┐
│   Module de     │      │   Module IoT      │      │     Module      │
│ Recettes (ML)   ├─────►│ (Données Stocks)  │      │  Comptabilité   │
└─────────────────┘      └───────────────────┘      └─────────────────┘
```

## Protocoles de communication

### 1. API REST

Le module expose et consomme des API REST pour l'échange de données structurées :

#### Endpoints exposés

- `GET /api/communication/status` - État actuel du module
- `GET /api/communication/campaigns` - Liste des campagnes actives
- `POST /api/communication/publish` - Publication de contenu
- `GET /api/communication/analytics` - Statistiques de performance
- `POST /api/communication/notify` - Envoi de notifications

#### Format des requêtes/réponses

```json
// Exemple de requête pour publication
POST /api/communication/publish
{
  "content": {
    "title": "Promotion du jour",
    "body": "Profitez de notre offre spéciale sur les pizzas !",
    "media_urls": ["https://example.com/images/promo.jpg"],
    "hashtags": ["promotion", "pizza", "vieuxmoulin"]
  },
  "platforms": ["facebook", "instagram"],
  "scheduled_time": "2025-04-20T18:30:00Z",
  "targeting": {
    "location": "Vensac",
    "radius": 20,
    "age_range": [18, 65]
  }
}

// Exemple de réponse
{
  "status": "scheduled",
  "publication_ids": {
    "facebook": "fb_12345",
    "instagram": "ig_67890"
  },
  "scheduled_time": "2025-04-20T18:30:00Z"
}
```

### 2. Webhooks

Le module implémente des webhooks pour les notifications en temps réel :

- **Callbacks de publication** : Notification lors de la publication réussie/échouée
- **Événements d'engagement** : Notification lors d'interactions client (commentaires, likes)
- **Alertes de performance** : Notification lorsqu'une campagne atteint des seuils de performance

Format des payloads de webhook :

```json
{
  "event_type": "publication_success",
  "timestamp": "2025-04-12T15:30:45Z",
  "data": {
    "platform": "facebook",
    "post_id": "fb_12345",
    "engagement_metrics": {
      "likes": 0,
      "shares": 0,
      "comments": 0
    }
  }
}
```

### 3. Message Queue

Pour la communication asynchrone, le module utilise un système de file d'attente de messages :

- **Publication** : Les tâches de publication sont mises en file d'attente pour traitement
- **Notifications** : Les envois de notifications sont traités de manière asynchrone
- **Analytics** : Les données d'analyse sont traitées par lots

La file d'attente utilise RabbitMQ ou Apache Kafka, avec des canaux dédiés pour chaque type d'opération.

## Sécurité et authentification

### Gestion des tokens

Le module implémente une gestion sécurisée des tokens d'authentification pour les API externes :

- Stockage chiffré des tokens dans une base de données sécurisée
- Rotation automatique des tokens selon leurs dates d'expiration
- Monitoring des tentatives d'utilisation non autorisées

### Authentification OAuth

Pour les plateformes sociales, le module utilise OAuth 2.0 :

1. Initialisation du flux d'authentification via l'interface d'administration
2. Redirection vers la plateforme pour authentification
3. Capture et stockage sécurisé du token d'accès
4. Refresh automatique des tokens avant expiration

### Sécurisation HTTPS

Toutes les communications API sont sécurisées par HTTPS avec TLS 1.3, utilisant des certificats validés et régulièrement renouvelés.

## Structure des données

### Modèle de données principal

```
Campaign
  ├── id: UUID
  ├── name: String
  ├── description: String
  ├── start_date: DateTime
  ├── end_date: DateTime
  ├── status: Enum (draft, scheduled, active, completed, canceled)
  ├── target_audience: JSON
  ├── budget: Decimal
  ├── success_metrics: JSON
  └── channels: Array<Channel>

Channel
  ├── type: Enum (social_media, email, sms, web)
  ├── config: JSON
  ├── content_template: String
  ├── schedule: JSON
  └── analytics: ChannelAnalytics

Content
  ├── id: UUID
  ├── title: String
  ├── body: String
  ├── media: Array<Media>
  ├── metadata: JSON
  └── variations: Array<ContentVariation>

Notification
  ├── id: UUID
  ├── template_id: String
  ├── recipient: String
  ├── channel: Enum (email, sms, push)
  ├── data: JSON
  ├── status: Enum (pending, sent, delivered, failed)
  └── sent_at: DateTime
```

### Format d'échange

Les données sont échangées entre les composants au format JSON, avec validation par schéma.

## Gestion des erreurs et fiabilité

### Types d'erreurs gérées

1. **Erreurs d'API externe** : Échecs de communication avec les plateformes sociales
   - Mécanisme de retry avec backoff exponentiel
   - Rapports détaillés des échecs
   
2. **Erreurs de validation** : Contenus non conformes aux restrictions des plateformes
   - Validation préalable avec feedback
   - Alternatives suggérées automatiquement
   
3. **Erreurs de planification** : Conflits ou dépassements de quotas
   - Résolution automatique des conflits selon les priorités
   - Replanification intelligente

### Surveillance et récupération

Le module implémente une surveillance continue avec :

- **Heartbeat** : Vérification périodique de la connectivité avec les services externes
- **Circuit Breaker** : Protection contre les défaillances en cascade
- **Self-healing** : Tentatives de réparation automatique des connexions rompues

## Performances et mise à l'échelle

### Métriques de performance

- **Temps de traitement** : <500ms pour les opérations standard
- **Débit** : Jusqu'à 100 publications/minute, 1000 notifications/minute
- **Latence** : <2s pour les publications sur les réseaux sociaux

### Stratégies de mise à l'échelle

1. **Scaling horizontal** : Déploiement de plusieurs instances pour la haute disponibilité
2. **Partitionnement** : Division des tâches par canal ou par campagne
3. **Caching** : Mise en cache des contenus et des réponses API fréquentes

## Procédures de configuration

### Configuration des accès aux réseaux sociaux

1. Créez un compte développeur sur chaque plateforme
2. Générez les clés API et les secrets
3. Dans le fichier `config/platforms.json` :

```json
{
  "facebook": {
    "app_id": "YOUR_FB_APP_ID",
    "app_secret": "YOUR_FB_APP_SECRET",
    "page_id": "YOUR_FB_PAGE_ID",
    "access_token": "YOUR_FB_ACCESS_TOKEN",
    "api_version": "v18.0"
  },
  "instagram": {
    "business_account_id": "YOUR_IG_ACCOUNT_ID",
    "access_token": "YOUR_IG_ACCESS_TOKEN"
  },
  "twitter": {
    "api_key": "YOUR_TWITTER_API_KEY",
    "api_secret": "YOUR_TWITTER_API_SECRET",
    "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
    "access_token_secret": "YOUR_TWITTER_ACCESS_TOKEN_SECRET"
  }
}
```

### Configuration des notifications

1. Configurez les services d'envoi d'emails (SendGrid, Mailjet, etc.)
2. Configurez les services d'envoi de SMS (Twilio, OVH, etc.)
3. Dans le fichier `config/notifications.json` :

```json
{
  "email": {
    "provider": "sendgrid",
    "api_key": "YOUR_SENDGRID_API_KEY",
    "from_email": "restaurant@levieuxmoulin.fr",
    "from_name": "Le Vieux Moulin"
  },
  "sms": {
    "provider": "twilio",
    "account_sid": "YOUR_TWILIO_SID",
    "auth_token": "YOUR_TWILIO_AUTH_TOKEN",
    "from_number": "+33XXXXXXXXX"
  }
}
```

### Configuration des templates de messages

Les templates utilisent le moteur Handlebars pour la personnalisation :

```json
{
  "promotional_email": {
    "subject": "{{promo_title}} - Offre spéciale Le Vieux Moulin",
    "body_html": "<h1>{{promo_title}}</h1><p>Cher(e) {{customer.first_name}},</p><p>{{promo_description}}</p><p>Cette offre est valable jusqu'au {{valid_until}}.</p><p><a href='{{booking_link}}'>Réservez maintenant</a></p>"
  },
  "menu_update": {
    "subject": "Nouveau menu au Vieux Moulin",
    "body_html": "<h1>Notre nouveau menu est arrivé !</h1><p>Découvrez nos nouvelles créations et venez les déguster au Vieux Moulin.</p>{{#each menu_items}}<p><strong>{{this.name}}</strong> - {{this.price}}€<br>{{this.description}}</p>{{/each}}"
  }
}
```

## Tests et validation

Le module inclut plusieurs suites de tests :

1. **Tests unitaires** : Pour chaque composant individuel
2. **Tests d'intégration** : Pour la communication entre les composants
3. **Tests de bout en bout** : Simulations complètes de workflows
4. **Tests de charge** : Validation des performances sous charge

Les mocks des API externes sont utilisés pour les tests locaux et CI/CD.

## Déploiement et opérations

Le module est conçu pour un déploiement dans des conteneurs Docker, avec :

- Configuration par variables d'environnement
- Health checks pour l'orchestration
- Volumes persistants pour les données importantes

Exemple de docker-compose.yml :

```yaml
version: '3.8'
services:
  communication-api:
    image: vieuxmoulin/communication-api:latest
    ports:
      - "3000:3000"
    environment:
      - DB_CONNECTION_STRING=postgresql://user:password@db:5432/communication
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=info
    depends_on:
      - db
      - redis
  
  communication-worker:
    image: vieuxmoulin/communication-worker:latest
    environment:
      - DB_CONNECTION_STRING=postgresql://user:password@db:5432/communication
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=info
    depends_on:
      - db
      - redis
      - rabbitmq
  
  db:
    image: postgres:14
    volumes:
      - communication-data:/var/lib/postgresql/data
  
  redis:
    image: redis:6
    volumes:
      - communication-cache:/data
  
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "15672:15672"
    volumes:
      - communication-queue:/var/lib/rabbitmq

volumes:
  communication-data:
  communication-cache:
  communication-queue:
```

## Évolution et maintenance

Le module est conçu pour une extension facile :

- **Nouveaux canaux** : Ajout de connecteurs pour de nouvelles plateformes
- **Nouvelles fonctionnalités** : Extension des capacités sans modification du core
- **Mises à jour API** : Adaptation aux changements dans les API externes

Le versionnement suit la convention Semantic Versioning (SemVer) pour indiquer clairement les changements incompatibles.