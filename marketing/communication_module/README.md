# Module de Communication et d'Automatisation Marketing - Le Vieux Moulin

Ce module gère l'ensemble des communications marketing et leur automatisation pour le restaurant "Le Vieux Moulin". Il synchronise automatiquement toutes les actions de communication, comme la publication sur les réseaux sociaux, l'envoi de notifications, la mise à jour des menus en ligne, et la gestion des campagnes publicitaires.

## Fonctionnalités principales

- **Publication automatisée sur les réseaux sociaux** : Planification et publication automatique de contenu sur Facebook, Instagram, et d'autres plateformes
- **Système de notifications clients** : Envoi automatisé d'emails, SMS, et autres types de notifications
- **Mise à jour des menus en ligne** : Synchronisation automatique des menus sur le site web et les plateformes partenaires
- **Gestion des campagnes publicitaires** : Planification, exécution et suivi des campagnes promotionnelles
- **Intégration multicanal** : Coordination des messages marketing sur tous les canaux de communication
- **Synchronisation avec les données du restaurant** : Intégration transparente avec les autres modules du système (recettes, CRM, comptabilité, IoT)
- **Orchestration centralisée** : Gestion centralisée de toutes les actions de communication via un orchestrateur

## Architecture du module

Le module est conçu selon une architecture modulaire, avec un orchestrateur central qui coordonne toutes les actions de communication :

```
┌────────────────────────────────────────────────────────────┐
│                  Orchestrateur de Communication             │
└────────────┬────────────────┬──────────────┬───────────────┘
             │                │              │
┌────────────▼───┐ ┌──────────▼───────┐ ┌────▼─────────┐ ┌────────────────┐
│ Gestionnaire   │ │ Gestionnaire de  │ │ Gestionnaire │ │ Gestionnaire de │
│ Réseaux Sociaux│ │ Notifications    │ │ de Campagnes │ │ Menus          │
└────────────────┘ └──────────────────┘ └──────────────┘ └────────────────┘
             │                │              │                │
             │                │              │                │
┌────────────▼───┐ ┌──────────▼───────┐ ┌────▼─────────┐ ┌────▼───────────┐
│  API Externes   │ │ Services d'Envoi │ │  Planifieurs │ │  Plateformes   │
│ (Facebook, etc.)│ │ (Email, SMS)     │ │  de Campagnes│ │  Externes      │
└────────────────┘ └──────────────────┘ └──────────────┘ └────────────────┘
             ▲                ▲              ▲                ▲
             │                │              │                │
┌────────────┴────────────────┴──────────────┴────────────────┴───────────┐
│                       Intégrateur Système                                │
└───────────────┬───────────────┬────────────────┬────────────────────────┘
                │               │                │
┌───────────────▼─┐ ┌───────────▼────┐ ┌─────────▼──────┐ ┌────────────────┐
│  Module CRM     │ │ Module Recettes│ │ Module IoT     │ │    Module      │
│ (Données Client)│ │    (ML)        │ │ (Données Stocks)│ │  Comptabilité  │
└─────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
```

## Structure du module

```
communication_module/
├── README.md                     # Documentation générale
├── COMMUNICATION.md              # Documentation technique détaillée
├── src/                          # Code source
│   ├── orchestrator.py           # Orchestrateur central de communication
│   ├── social_media/             # Gestion des réseaux sociaux
│   │   ├── publishers/           # Connecteurs pour chaque plateforme
│   │   ├── content_generator/    # Générateurs de contenu
│   │   └── analytics/            # Analyse des performances
│   ├── notification/             # Système de notifications
│   │   ├── adapters/             # Adaptateurs pour les canaux (email, SMS)
│   │   └── templates/            # Templates de messages
│   ├── menu_updater/             # Mise à jour des menus en ligne
│   ├── campaign_manager/         # Gestion des campagnes
│   │   ├── scheduler/            # Planification des campagnes
│   │   ├── targeting/            # Ciblage des campagnes
│   │   └── performance/          # Suivi des performances
│   ├── integration/              # Intégration avec les autres modules
│   │   └── system_integrator.py  # Intégrateur système
│   ├── common/                   # Composants communs
│   │   ├── auth/                 # Gestion de l'authentification
│   │   ├── utils/                # Utilitaires
│   │   └── data_models/          # Modèles de données
│   ├── api/                      # API REST pour intégration externe
│   │   ├── routes.py             # Définition des routes API
│   │   ├── server.py             # Serveur API
│   │   └── webhooks.py           # Gestionnaire de webhooks
│   └── main.py                   # Point d'entrée principal
├── config/                       # Configuration
│   ├── platforms.json            # Configuration des plateformes
│   ├── templates.json            # Configuration des templates
│   └── settings.json             # Paramètres généraux
├── tests/                        # Tests unitaires et d'intégration
└── examples/                     # Exemples d'utilisation
    ├── social_media_automation.py      # Exemple d'automatisation des réseaux sociaux
    ├── notification_automation.py      # Exemple d'automatisation des notifications
    └── menu_integration.py            # Exemple d'intégration des menus
```

## Installation

### Prérequis

- Python 3.9+
- Accès aux API des plateformes de réseaux sociaux
- Compte SendGrid/Mailjet pour les emails
- Compte Twilio/OVH pour les SMS
- Connexion à la base de données centrale du restaurant

### Installation

```bash
# Création d'un environnement virtuel (Python)
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows

# Installation des dépendances
pip install -r requirements.txt

# Configuration initiale
python src/setup.py
```

## Configuration

1. Modifiez le fichier `config/settings.json` pour les paramètres généraux
2. Configurez les accès aux API des plateformes dans `config/platforms.json`
3. Personnalisez les templates de communication dans `config/templates.json`

## Utilisation

### Démarrage du service

```bash
# Démarrer le service de communication
python src/main.py

# Mode développement avec rechargement automatique
python src/main.py --dev
```

### Exemples d'utilisation

#### Publication sur les réseaux sociaux

```python
from src.orchestrator import get_orchestrator
from src.common import Config

# Initialiser la configuration
config = Config("config/settings.json")

# Obtenir l'orchestrateur
orchestrator = get_orchestrator(config)

# Publier un contenu sur plusieurs plateformes
await orchestrator.publish_to_social_media(
    content={
        "title": "Notre pizza du jour : La Méditerranéenne !",
        "body": "Venez déguster notre pizza spéciale du jour...",
        "media_url": "https://example.com/images/pizza_med.jpg",
        "hashtags": ["pizza", "vieuxmoulin", "vensac"]
    },
    platforms=["facebook", "instagram"],
    scheduled_time="2025-04-15T18:30:00"
)
```

#### Envoi de notifications

```python
from src.orchestrator import get_orchestrator
from src.common import Config

# Initialiser la configuration
config = Config("config/settings.json")

# Obtenir l'orchestrateur
orchestrator = get_orchestrator(config)

# Envoyer une notification
await orchestrator.send_notification(
    template="promotion_annonce",
    recipients=["client1@example.com", "+33612345678"],
    data={
        "promotion_name": "Happy Hour",
        "discount": "20%",
        "valid_until": "2025-04-20"
    },
    channels=["email", "sms"]
)
```

#### Mise à jour de menu

```python
from src.orchestrator import get_orchestrator
from src.common import Config

# Initialiser la configuration
config = Config("config/settings.json")

# Obtenir l'orchestrateur
orchestrator = get_orchestrator(config)

# Mettre à jour le menu
await orchestrator.update_menu(
    menu_data={
        "name": "Menu Printemps 2025",
        "categories": [
            {"name": "Entrées", "items": [...]}
        ]
    },
    platforms=["website", "social_media", "delivery_platforms"]
)
```

### Exemples complets

Pour des exemples plus complets, consultez les fichiers dans le répertoire `examples/` :

- `social_media_automation.py` : Automatisation des publications sur les réseaux sociaux
- `notification_automation.py` : Automatisation des notifications clients
- `menu_integration.py` : Intégration et synchronisation des menus

## API REST

Le module expose une API REST complète pour l'intégration avec d'autres systèmes. Chaque endpoint est documenté et prend en charge les méthodes HTTP standard.

### Endpoints principaux

```
GET /api/communication/status - État actuel du module
GET /api/communication/campaigns - Liste des campagnes actives
POST /api/communication/publish - Publication de contenu
GET /api/communication/analytics - Statistiques de performance
POST /api/communication/notify - Envoi de notifications
```

Pour une documentation complète de l'API, consultez la documentation Swagger disponible à l'adresse `/api/docs` après le démarrage du service.

## Intégration avec les autres modules

### Module de suggestion de recettes

Le module de communication s'intègre avec le module de suggestion de recettes (`/marketing/recipe_suggestion`) pour:
- Diffuser automatiquement les suggestions de recettes sur les réseaux sociaux
- Envoyer des notifications aux clients concernant les plats spéciaux
- Générer des campagnes promotionnelles basées sur les recettes suggérées

### Module CRM

L'intégration avec le CRM permet:
- La segmentation précise des clients pour les campagnes ciblées
- La personnalisation des communications selon l'historique client
- Le suivi de l'efficacité des communications marketing

### Module comptabilité

Le module communique avec le module de comptabilité pour:
- Suivre le ROI des campagnes marketing
- Ajuster les budgets publicitaires en fonction des performances
- Générer des rapports de dépenses marketing

### Module IoT

L'intégration avec le module IoT permet:
- Adapter les promotions en fonction des niveaux de stock
- Ajuster les campagnes selon l'affluence en temps réel
- Cibler les notifications en fonction de la présence des clients

## Sécurité et conformité

- Toutes les communications sont conformes au RGPD
- Les données sensibles sont chiffrées
- Les consentements des clients sont gérés et documentés
- Les tokens d'API sont stockés de manière sécurisée

## Monitoring et performances

Le module inclut un tableau de bord de suivi accessible à `http://localhost:5001/dashboard`

Métriques principales:
- Taux d'engagement des publications
- Taux d'ouverture des emails et SMS
- Conversions générées par les campagnes
- Performance comparative des différents canaux

## Dépannage

### Problèmes courants

- **Échec de publication** : Vérifiez les tokens d'accès aux API
- **Emails non délivrés** : Consultez les logs du service d'envoi d'emails
- **Synchronisation incomplète** : Vérifiez la connectivité avec le serveur central

Les logs détaillés sont disponibles dans `/var/log/communication_module/`

## Contribution

Pour contribuer au développement du module, consultez le fichier `CONTRIBUTING.md` à la racine du projet principal.

## Roadmap

- [ ] Intégration de l'IA générative pour la création de contenu
- [ ] Support des stories Instagram éphémères
- [ ] Analyse de sentiment des commentaires sur les réseaux sociaux
- [ ] Module de gestion de réputation en ligne
- [ ] Intégration avec les plateformes publicitaires (Google Ads, Facebook Ads)

## Licence

© 2025 Le Vieux Moulin - Tous droits réservés
