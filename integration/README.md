# Module d'Intégration - Le Vieux Moulin

Ce répertoire contient l'ensemble des connecteurs et intégrations avec les systèmes externes pour le restaurant "Le Vieux Moulin". Ces intégrations permettent la communication avec la caisse enregistreuse, les fournisseurs, le système de réservation en ligne et le CRM, créant ainsi un écosystème interconnecté et automatisé.

## Structure du Répertoire

- **/pos/** - Intégration avec la caisse enregistreuse
- **/suppliers/** - Connexion avec les systèmes fournisseurs
- **/reservation/** - Intégration des plateformes de réservation
- **/crm/** - Connecteurs avec le système de gestion de la relation client
- **/common/** - Bibliothèques et utilitaires partagés
- **/scheduling/** - Optimisation des plannings et staffing

## Intégrations Disponibles

### 1. Caisse Enregistreuse (POS)

L'intégration avec la caisse enregistreuse permet la synchronisation bidirectionnelle des données de vente et de stock.

#### Fonctionnalités
- Récupération des transactions en temps réel
- Mise à jour automatique des prix
- Synchronisation des promotions
- Transmission des données vers le module comptable

#### Configuration
```json
// Exemple de configuration POS (pos/config.json)
{
  "pos_type": "LightSpeed",
  "connection": {
    "api_url": "https://api.lightspeed.com/v1/",
    "store_id": "12345",
    "auth_method": "oauth2",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  },
  "sync_settings": {
    "transactions": {
      "enabled": true,
      "interval_minutes": 5
    },
    "menu_items": {
      "enabled": true,
      "interval_minutes": 60
    },
    "promotions": {
      "enabled": true,
      "interval_minutes": 120
    }
  },
  "error_handling": {
    "retry_attempts": 3,
    "notification_email": "tech@levieuxmoulin.fr"
  }
}
```

#### Utilisation de l'API
```javascript
// Exemple d'utilisation du connecteur POS
const { POSConnector } = require('./connectors/lightspeed');

// Initialiser la connexion
const posConnector = new POSConnector(config);

// Récupérer les transactions récentes
async function getRecentTransactions() {
  try {
    const transactions = await posConnector.getTransactions({
      from: '2025-04-01T00:00:00Z',
      to: '2025-04-12T23:59:59Z',
      status: 'completed'
    });
    
    return transactions;
  } catch (error) {
    console.error('Erreur lors de la récupération des transactions:', error);
    return [];
  }
}
```

### 2. Fournisseurs

L'intégration avec les systèmes fournisseurs permet d'automatiser les commandes et le suivi des livraisons.

#### Fournisseurs Supportés
- Metro France (API DirectOrder)
- Transgourmet (API REST)
- Pomona (API B2B)
- Fournisseurs locaux (via interface standardisée)

#### Fonctionnalités
- Commandes automatiques basées sur les prévisions
- Suivi des livraisons et des délais
- Gestion des prix et des promotions
- Notifications en cas de retard ou problème

#### Exemple d'Utilisation
```javascript
// Exemple d'utilisation pour une commande automatique
const { MetroConnector } = require('./connectors/metro');

// Initialiser la connexion
const metroConnector = new MetroConnector(config);

// Placer une commande
async function placeOrder(orderItems) {
  try {
    const orderResponse = await metroConnector.createOrder({
      delivery_date: '2025-04-15',
      items: orderItems,
      priority: 'normal',
      notes: 'Commander des produits frais en priorité'
    });
    
    console.log(`Commande #${orderResponse.order_id} créée avec succès`);
    return orderResponse;
  } catch (error) {
    console.error('Erreur lors de la création de la commande:', error);
    throw error;
  }
}
```

### 3. Réservation en Ligne

L'intégration avec les plateformes de réservation permet de centraliser la gestion des tables et des clients.

#### Plateformes Supportées
- TheFork (LaFourchette)
- Resy
- OpenTable
- Système de réservation propriétaire

#### Fonctionnalités
- Synchronisation en temps réel des réservations
- Gestion centralisée du planning des tables
- Profils clients et préférences
- Statistiques et prévisions d'affluence

#### Webhook et Notifications
```javascript
// Exemple de gestionnaire de webhook pour nouvelle réservation
app.post('/api/webhooks/reservation', async (req, res) => {
  try {
    const { reservation_id, platform, customer, date, party_size, special_requests } = req.body;
    
    // Valider la signature du webhook
    if (!validateWebhookSignature(req)) {
      return res.status(401).json({ error: 'Signature invalide' });
    }
    
    // Traiter la réservation
    await reservationManager.processNewReservation({
      external_id: reservation_id,
      source: platform,
      customer_info: customer,
      datetime: new Date(date),
      guests: party_size,
      requests: special_requests
    });
    
    // Envoyer une confirmation au client si nécessaire
    
    return res.status(200).json({ status: 'success' });
  } catch (error) {
    console.error('Erreur de traitement de réservation:', error);
    return res.status(500).json({ error: 'Erreur de traitement' });
  }
});
```

### 4. CRM (Customer Relationship Management)

L'intégration CRM permet de gérer les relations clients et d'optimiser les actions marketing.

#### Fonctionnalités
- Profils clients unifiés
- Historique des commandes et préférences
- Programmes de fidélité
- Segmentation pour campagnes ciblées

#### Utilisation de l'API
```javascript
// Exemple d'utilisation de l'API CRM
const { CRMClient } = require('./crm/client');

// Initialiser le client
const crmClient = new CRMClient(config);

// Mettre à jour le profil client après une visite
async function updateCustomerAfterVisit(customerId, orderDetails) {
  try {
    // Récupérer le profil existant
    const customerProfile = await crmClient.getCustomer(customerId);
    
    // Mettre à jour les statistiques
    const updatedProfile = {
      ...customerProfile,
      visit_count: customerProfile.visit_count + 1,
      last_visit_date: new Date().toISOString(),
      favorite_items: updateFavorites(customerProfile.favorite_items, orderDetails.items),
      lifetime_value: customerProfile.lifetime_value + orderDetails.total_amount
    };
    
    // Sauvegarder les modifications
    await crmClient.updateCustomer(customerId, updatedProfile);
    
    // Déclencher des actions basées sur le comportement client
    if (updatedProfile.visit_count % 10 === 0) {
      await crmClient.triggerLoyaltyReward(customerId, 'milestone_visit');
    }
    
    return updatedProfile;
  } catch (error) {
    console.error('Erreur lors de la mise à jour du profil client:', error);
    throw error;
  }
}
```

### 5. Optimisation des Plannings (Staffing)

Le module de planification permet d'optimiser les horaires du personnel en fonction des prévisions d'affluence.

#### Fonctionnalités
- Prévision des besoins en personnel
- Génération automatique des plannings
- Gestion des disponibilités et contraintes
- Alertes en cas de sous-effectif prévu

#### Configuration
```javascript
// Exemple de configuration pour l'optimisation des plannings
const staffingConfig = {
  roles: [
    { id: 'chef', min_staff: 1, optimal_ratio: 0.1 },  // 1 chef pour 10 clients
    { id: 'server', min_staff: 1, optimal_ratio: 0.2 }, // 1 serveur pour 5 clients
    { id: 'bartender', min_staff: 1, optimal_ratio: 0.15 } // 1 barman pour ~7 clients
  ],
  constraints: {
    max_hours_per_week: 35,
    max_consecutive_days: 5,
    min_rest_between_shifts: 11 // heures
  },
  forecasting: {
    use_reservation_data: true,
    use_historical_data: true,
    special_events: [
      { date: '2025-07-14', multiplier: 1.5, note: 'Fête nationale' }
    ]
  }
};
```

## Utilisation des Modèles d'Authentification

Les différentes intégrations utilisent des méthodes d'authentification standardisées:

### OAuth 2.0
```javascript
// Exemple d'initialisation OAuth 2.0
const { OAuth2Client } = require('./common/auth/oauth2');

const oauth2Client = new OAuth2Client({
  client_id: process.env.CLIENT_ID,
  client_secret: process.env.CLIENT_SECRET,
  token_url: 'https://api.service.com/oauth/token',
  redirect_uri: 'https://levieuxmoulin.fr/oauth/callback',
  scope: 'read write'
});

// Obtenir un token
async function getAccessToken() {
  const tokenData = await oauth2Client.getToken();
  return tokenData.access_token;
}
```

### API Key
```javascript
// Exemple d'utilisation d'API Key
const apiClient = new ApiClient({
  base_url: 'https://api.supplier.com/v1',
  api_key: process.env.SUPPLIER_API_KEY,
  timeout: 5000
});
```

## Gestion des Erreurs et Résilience

Toutes les intégrations incluent des mécanismes de résilience:
- Retry automatique avec backoff exponentiel
- Circuit Breaker pour éviter la surcharge des services
- Logging détaillé pour le diagnostic
- Alertes en cas de dysfonctionnement prolongé

## Maintenance et Monitoring

Un tableau de bord de monitoring est disponible pour surveiller toutes les intégrations:
- Statut en temps réel de chaque connexion
- Historique des opérations
- Métriques de performance
- Alertes configurables

---

Pour toute question ou assistance concernant les intégrations, consultez la documentation détaillée de chaque connecteur ou contactez l'équipe d'intégration.
