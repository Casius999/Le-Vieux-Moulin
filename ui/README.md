# Interface Utilisateur - Le Vieux Moulin

Ce répertoire contient l'ensemble des composants d'interface utilisateur du système de gestion intelligente pour le restaurant "Le Vieux Moulin". L'interface comprend les tablettes murales, le module de commande vocale et les tableaux de bord pour le suivi des stocks, des commandes et des campagnes marketing.

## Structure du Répertoire

- **/tablet_app/** - Application pour tablettes murales (React Native)
- **/voice_command/** - Module de reconnaissance et traitement vocal
- **/dashboard/** - Tableaux de bord et visualisations en temps réel
- **/admin_panel/** - Interface d'administration du système
- **/common/** - Composants UI partagés et thèmes
- **/mobile/** - Application mobile pour gestionnaires (iOS/Android)

## Technologies Utilisées

### Frontend
- **React/React Native** - Pour les applications tablette et mobile
- **Redux** - Gestion d'état
- **Material-UI** - Composants UI
- **D3.js/Chart.js** - Visualisations et graphiques
- **Socket.io** - Communications en temps réel
- **Electron** - Pour les versions desktop (administration)

### Backend UI
- **Node.js/Express** - Serveur d'application UI
- **WebSockets** - Communications temps réel
- **TensorFlow.js** - Reconnaissance vocale côté client
- **JWT** - Authentification sécurisée

## Interface Tablette Murale

L'interface tablette est conçue pour être utilisée dans l'environnement de cuisine ou en salle. Elle est optimisée pour:
- Écrans tactiles résistants aux éclaboussures
- Utilisation avec des mains humides ou gantées
- Visibilité dans différentes conditions d'éclairage

### Installation de l'Application Tablette

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/ui/tablet_app

# Installer les dépendances
npm install

# Configuration
cp .env.example .env
# Éditer le fichier .env avec les paramètres spécifiques

# Lancer l'application en mode développement
npm start

# Construire l'application pour déploiement
npm run build
```

### Configuration de la Tablette

1. Installez l'application sur la tablette
2. Accédez au menu de configuration (⚙️ > Configuration)
3. Entrez les paramètres de connexion au serveur
4. Sélectionnez la zone d'utilisation (cuisine, bar, salle)
5. Configurez les permissions utilisateur si nécessaire

## Module de Commande Vocale

Le module de commande vocale permet au personnel d'interagir avec le système sans utiliser les mains, particulièrement utile pendant la préparation des plats.

### Fonctionnalités Vocales

- Reconnaissance de commandes spécifiques au domaine de la restauration
- Support multilingue (français, anglais, espagnol)
- Adaptation au bruit ambiant
- Mode d'apprentissage pour améliorer la reconnaissance

### Configuration Vocale

```javascript
// Exemple de configuration vocale (voice_command/config.js)
module.exports = {
  recognition: {
    language: 'fr-FR',  // Langue principale
    fallbackLanguages: ['en-US', 'es-ES'],
    noiseThreshold: 0.2,
    confidenceThreshold: 0.75
  },
  commands: {
    inventory: ['stock', 'inventaire', 'niveau'],
    order: ['commande', 'commander', 'besoin'],
    recipe: ['recette', 'ingrédients', 'préparation'],
    // Autres catégories de commandes...
  },
  feedback: {
    audio: true,  // Retour audio
    visual: true  // Confirmation visuelle
  }
};
```

## Tableaux de Bord (Dashboards)

Les tableaux de bord fournissent des visualisations en temps réel des données critiques pour le restaurant.

### Types de Dashboards

1. **Dashboard Cuisine**
   - Niveaux de stock en temps réel
   - Alertes pour ingrédients bas
   - État des équipements (température four, friteuse, etc.)

2. **Dashboard Gestion**
   - Synthèse des ventes
   - Prévisions de consommation
   - Performance financière

3. **Dashboard Marketing**
   - Campagnes en cours
   - Analyse de l'engagement
   - Suggestions promotionnelles

### Personnalisation des Dashboards

Chaque dashboard est personnalisable via l'interface d'administration:
1. Accédez à l'interface admin (`/admin_panel`)
2. Naviguez vers "Configuration des tableaux de bord"
3. Sélectionnez les widgets à afficher
4. Configurez la mise en page
5. Définissez les seuils d'alerte et les indicateurs clés

## Responsive Design

L'ensemble des interfaces est conçu selon une approche "mobile-first" et s'adapte à différentes tailles d'écran:
- Tablettes murales (10-12 pouces)
- Smartphones pour personnel mobile
- Écrans de bureau pour administration
- Grands écrans pour dashboards publics

## Authentification et Sécurité

- Authentification à deux facteurs pour les accès administrateur
- Détection de présence pour verrouillage automatique
- Niveaux d'autorisation basés sur les rôles:
  - Cuisiniers
  - Serveurs
  - Managers
  - Administrateurs
  - Comptables (accès limité)

## Mode Hors Ligne

Toutes les interfaces incluent un mode hors ligne qui permet de:
- Consulter les dernières données synchronisées
- Continuer à saisir des commandes
- Mettre en file d'attente les actions pour synchronisation ultérieure

## Internationalisation

L'interface supporte plusieurs langues via le système i18n:
```javascript
// Exemple d'utilisation de l'internationalisation
import { useTranslation } from 'react-i18next';

function InventoryWidget() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h2>{t('inventory.title')}</h2>
      <p>{t('inventory.stock_level')}: {level}</p>
      {/* Autres éléments traduits */}
    </div>
  );
}
```

## Tests

Le code UI inclut des tests unitaires et d'intégration:
```bash
# Exécuter les tests unitaires
npm test

# Exécuter les tests d'interface
npm run test:e2e

# Vérifier la couverture des tests
npm run test:coverage
```

## Support Multi-Établissements

L'interface est conçue pour prendre en charge plusieurs établissements:
- Sélecteur d'établissement pour les utilisateurs avec accès multiple
- Thèmes et configurations personnalisables par établissement
- Possibilité de comparer les performances entre établissements

---

Pour toute question ou assistance concernant l'interface utilisateur, consultez la documentation complète ou contactez l'équipe de développement frontend.
