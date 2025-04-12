# Module Marketing - Le Vieux Moulin

Ce répertoire contient l'ensemble des composants du module marketing automatisé pour le restaurant "Le Vieux Moulin". Ce module gère les campagnes publicitaires, la communication sur les réseaux sociaux, les notifications automatisées et génère des suggestions de recettes basées sur les tendances et les stocks disponibles.

## Structure du Répertoire

- **/social_media/** - Gestion des réseaux sociaux et publications automatisées
- **/campaign_manager/** - Planification et exécution des campagnes publicitaires
- **/notification/** - Système de notifications clients (email, SMS)
- **/recipe_suggestion/** - **Module fonctionnel** - Suggestion de recettes et promotions fournisseurs
- **/analytics/** - Analyse et reporting des performances marketing
- **/content_generator/** - Outils de génération de contenu assisté par IA

## Fonctionnalités Principales

### 1. Gestion des Réseaux Sociaux

Le module de gestion des réseaux sociaux permet de planifier, créer et publier automatiquement du contenu sur différentes plateformes.

#### Plateformes Supportées
- Facebook
- Instagram
- TikTok
- Google Business Profile

#### Fonctionnalités
- Planification de publications
- Génération automatique de visuels
- Gestion des commentaires et messages
- Analyses de performance

#### Configuration
```javascript
// Exemple de configuration des réseaux sociaux (social_media/config.js)
module.exports = {
  platforms: {
    facebook: {
      enabled: true,
      page_id: 'vieuxmoulinrestaurant',
      auto_comment_response: true,
      post_frequency: {
        min_hours_between_posts: 8,
        optimal_posting_times: ['12:00', '18:30']
      }
    },
    instagram: {
      enabled: true,
      account_id: 'levieuxmoulin_restaurant',
      content_types: ['image', 'carousel', 'reels'],
      hashtags: {
        always_include: ['restaurant', 'vieuxmoulin', 'vensac', 'gironde'],
        food_related: ['gastronomie', 'pizza', 'cuisine', 'foodlover']
      }
    },
    google_business: {
      enabled: true,
      location_id: '12345',
      auto_update_photos: true,
      auto_update_events: true
    }
  },
  content_strategy: {
    ratio: {
      promotional: 0.3,
      informative: 0.4,
      engagement: 0.3
    },
    recycle_content_after_days: 90
  }
};
```

#### Utilisation
```javascript
// Exemple d'utilisation pour programmation de post
const { SocialMediaManager } = require('./social_media/manager');

// Initialiser le gestionnaire
const socialManager = new SocialMediaManager(config);

// Planifier une publication
async function schedulePromoPost(specialOffer) {
  try {
    const postContent = await socialManager.createPromotionalContent({
      title: specialOffer.title,
      description: specialOffer.description,
      validUntil: specialOffer.endDate,
      imagePrompt: `Photo de ${specialOffer.title}, ambiance restaurant`
    });
    
    // Programmer sur plusieurs plateformes
    const scheduledPosts = await socialManager.schedulePost({
      content: postContent,
      platforms: ['facebook', 'instagram'],
      scheduledTime: specialOffer.publishDate,
      targeting: {
        location: 'Vensac',
        radius: 20, // km
        interests: ['cuisine', 'restaurant', 'sortir']
      }
    });
    
    return scheduledPosts;
  } catch (error) {
    console.error('Erreur lors de la planification du post:', error);
    throw error;
  }
}
```

### 2. Gestionnaire de Campagnes

Le gestionnaire de campagnes permet de créer, exécuter et analyser des campagnes marketing sur plusieurs canaux.

#### Types de Campagnes
- Promotions spéciales
- Événements
- Lancement de nouveaux plats
- Programmes de fidélité

#### Fonctionnalités
- Définition de segments clients
- Automatisation multi-canal
- Tests A/B
- Suivi des conversions

#### Structure des Campagnes
```javascript
// Exemple de structure de campagne
const summerCampaign = {
  id: 'summer2025',
  name: 'Menu d\'été 2025',
  start_date: '2025-06-01',
  end_date: '2025-08-31',
  budget: 1200.00,
  currency: 'EUR',
  segments: ['locals', 'tourists', 'families'],
  channels: [
    {
      type: 'email',
      template_id: 'summer_menu_announcement',
      schedule: 'weekly',
      day_of_week: 'thursday',
      time: '10:00'
    },
    {
      type: 'social_media',
      platforms: ['facebook', 'instagram'],
      frequency: 'twice_weekly',
      budget_allocation: 0.4 // 40% du budget
    },
    {
      type: 'sms',
      template_id: 'flash_promo',
      trigger: 'weather',
      condition: 'temperature > 30'
    }
  ],
  success_metrics: {
    reservations: {
      target: 150,
      attribution_window: 48 // heures
    },
    revenue: {
      target: 15000,
      minimum: 10000
    }
  }
};
```

### 3. Système de Notifications

Le module de notification permet d'envoyer des communications ciblées aux clients par email, SMS ou notifications push.

#### Types de Notifications
- Confirmations de réservation
- Promotions personnalisées
- Événements spéciaux
- Rappels de fidélité

#### Canaux de Communication
- Email (via SendGrid/Mailjet)
- SMS (via Twilio/OVH)
- Push App Mobile
- Messenger/WhatsApp

#### Templates et Personnalisation
```javascript
// Exemple de template de notification avec personnalisation
const birthdayOfferTemplate = {
  name: 'birthday_special',
  subject: 'Un cadeau d\'anniversaire vous attend au Vieux Moulin !',
  body: `
    Cher(e) {{customer.first_name}},
    
    Toute l'équipe du Vieux Moulin vous souhaite un très joyeux anniversaire !
    
    Pour célébrer cette occasion spéciale, nous serions ravis de vous offrir {{offer.description}} lors de votre prochaine visite.
    
    Cette offre est valable jusqu'au {{offer.valid_until | date('dd/MM/yyyy')}}.
    
    Réservez dès maintenant en cliquant sur ce lien : {{reservation_link}}
    
    À très bientôt !
    L'équipe du Vieux Moulin
  `,
  sms_version: 'Joyeux anniversaire {{customer.first_name}} ! Pour fêter ça, {{offer.description}} vous attend au Vieux Moulin jusqu'au {{offer.valid_until | date('dd/MM')}}. Réservez : {{short_link}}',
  trigger: {
    event: 'customer_birthday',
    days_offset: -2 // 2 jours avant
  },
  tracking: {
    utm_source: 'crm',
    utm_medium: 'email',
    utm_campaign: 'birthday'
  }
};
```

### 4. Suggestion de Recettes

Ce module utilise l'intelligence artificielle pour générer des suggestions de plats spéciaux en fonction des stocks disponibles, des tendances culinaires et des préférences clients.

#### ✅ Statut: Fonctionnel

Le module de suggestion de recettes est désormais complètement opérationnel et prêt à l'emploi. Il permet d'analyser les promotions fournisseurs et de générer automatiquement des suggestions de recettes optimisées.

#### Fonctionnalités Principales
- Analyse des promotions fournisseurs en temps réel
- Détection des tendances locales et préférences clients
- Génération de suggestions de recettes (pizza du jour, plat spécial)
- Création et publication automatique de promotions associées
- Intégration avec les systèmes de vente et de stock

#### Intégration avec les autres composants
- Utilise les données du module IA/ML pour améliorer les suggestions
- Alimente le module de réseaux sociaux pour les publications
- Fournit des données au système de menu et d'affichage

#### Utilisation Python
```python
# Exemple d'utilisation du module de suggestion de recettes
from recipe_suggestion.src.main import RecipeSuggestionService

# Initialiser le service
service = RecipeSuggestionService()

# Générer des suggestions quotidiennes
suggestions = service.generate_daily_suggestions()

# Afficher les suggestions
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion['name']} ({suggestion['category']})")
    print(f"   Prix: {suggestion['price']}€")
    print(f"   Ingrédients principaux: {', '.join(suggestion['main_ingredients'])}")
    print(f"   Promotion: {suggestion['promotion']['description']}\n")
```

Pour plus de détails, consultez la [documentation du module](./recipe_suggestion/README.md).

### 5. Analytique Marketing

Le module d'analytique permet de suivre et d'analyser les performances de toutes les actions marketing.

#### Métriques Suivies
- Engagement sur réseaux sociaux
- Taux de conversion des campagnes
- Efficacité des promotions
- ROI marketing

#### Tableaux de Bord et Rapports
- Dashboard temps réel
- Rapports hebdomadaires automatisés
- Comparaison avec historique
- Prévisions futures

## Intégration avec les Autres Modules

### CRM
Le module marketing s'intègre étroitement au CRM pour:
- Ciblage précis des communications
- Personnalisation basée sur l'historique client
- Analyse du cycle de vie client

### IoT & Stocks
L'intégration avec le système de gestion des stocks permet:
- Création de promotions sur les ingrédients en surabondance
- Suggestions de plats basées sur les stocks disponibles
- Alertes pour planifier des actions marketing spécifiques

### IA/ML
Les modèles d'IA/ML sont utilisés pour:
- Prédiction des performances des campagnes
- Optimisation du contenu et des visuels
- Personnalisation des offres
- Génération de recettes innovantes

## Configuration pour Multi-Établissements

Le module marketing est conçu pour gérer plusieurs établissements:
- Stratégies marketing distinctes ou coordonnées
- Partage de contenu adaptable
- Analyses comparatives de performance
- Campagnes locales ou globales

## Développement et Extension

Pour ajouter un nouveau canal marketing:
1. Créez un dossier dédié dans le répertoire approprié
2. Implémentez l'interface standard de canal
3. Créez les templates spécifiques
4. Ajoutez les tests unitaires et d'intégration
5. Mettez à jour la documentation

## Tests et Validation

Tous les composants du module marketing incluent:
- Tests unitaires pour les fonctions individuelles
- Tests d'intégration pour les workflows
- Tests A/B automatisés pour optimisation
- Simulations de campagnes pour validation

---

Pour toute question ou assistance concernant le module marketing, consultez la documentation détaillée ou contactez l'équipe marketing.
