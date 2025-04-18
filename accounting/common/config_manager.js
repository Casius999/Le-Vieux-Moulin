/**
 * Gestionnaire de configuration pour le module de comptabilité
 * Ce module centralise la gestion des configurations et paramètres du système
 * avec support pour les environnements multiples et les surcharges locales.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const _ = require('lodash');

/**
 * Classe de gestion des configurations du module de comptabilité
 */
class ConfigManager {
  /**
   * Crée une nouvelle instance du gestionnaire de configuration
   * @param {Object} options - Options de configuration
   * @param {string} options.configPath - Chemin vers le répertoire de configuration
   * @param {string} options.environment - Environnement d'exécution (development, test, production)
   * @param {Object} options.defaultConfig - Configuration par défaut
   * @param {boolean} options.watchForChanges - Surveiller les changements de configuration
   */
  constructor(options = {}) {
    this.configPath = options.configPath || process.env.CONFIG_PATH || path.join(__dirname, '../config');
    this.environment = options.environment || process.env.NODE_ENV || 'development';
    this.defaultConfig = options.defaultConfig || {};
    this.watchForChanges = options.watchForChanges !== undefined ? options.watchForChanges : true;
    
    this._loadedConfigs = new Map();
    this._watchers = new Map();
    
    // Charger la configuration immédiatement
    this.reload();
  }
  
  /**
   * Recharge toutes les configurations
   * @returns {Object} - La configuration chargée
   */
  reload() {
    this._loadedConfigs.clear();
    
    // Arrêter les watchers existants
    for (const [_, watcher] of this._watchers) {
      watcher.close();
    }
    this._watchers.clear();
    
    // Charger la configuration de base
    this._loadConfig('base');
    
    // Charger la configuration spécifique à l'environnement
    this._loadConfig(this.environment);
    
    // Charger la configuration locale (si existante)
    this._loadConfig('local');
    
    return this.getConfig();
  }
  
  /**
   * Récupère la configuration complète ou une section spécifique
   * @param {string} [section] - Section de configuration à récupérer (optionnel)
   * @param {Object} [defaultValue] - Valeur par défaut si la section n'existe pas
   * @returns {Object} - La configuration demandée
   */
  getConfig(section, defaultValue = {}) {
    // Fusionner toutes les configurations dans l'ordre de priorité
    const mergedConfig = _.merge(
      {},
      this.defaultConfig,
      this._loadedConfigs.get('base') || {},
      this._loadedConfigs.get(this.environment) || {},
      this._loadedConfigs.get('local') || {}
    );
    
    if (section) {
      return _.get(mergedConfig, section, defaultValue);
    }
    
    return mergedConfig;
  }
  
  /**
   * Récupère une valeur spécifique de la configuration
   * @param {string} path - Chemin de la valeur (notation par points)
   * @param {*} defaultValue - Valeur par défaut si le chemin n'existe pas
   * @returns {*} - La valeur demandée
   */
  get(path, defaultValue) {
    return _.get(this.getConfig(), path, defaultValue);
  }
  
  /**
   * Définit une valeur dans la configuration locale
   * @param {string} path - Chemin de la valeur (notation par points)
   * @param {*} value - Valeur à définir
   * @param {boolean} [persist=false] - Persister la modification dans le fichier local
   * @returns {boolean} - Succès de l'opération
   */
  set(path, value, persist = false) {
    // Récupérer la configuration locale
    let localConfig = this._loadedConfigs.get('local') || {};
    
    // Mettre à jour la valeur
    _.set(localConfig, path, value);
    this._loadedConfigs.set('local', localConfig);
    
    // Persister si demandé
    if (persist) {
      try {
        const localConfigPath = path.join(this.configPath, 'local.json');
        fs.writeFileSync(localConfigPath, JSON.stringify(localConfig, null, 2), 'utf8');
        return true;
      } catch (error) {
        console.error('Erreur lors de la persistance de la configuration:', error);
        return false;
      }
    }
    
    return true;
  }
  
  /**
   * Vérifie si une valeur de configuration existe
   * @param {string} path - Chemin de la valeur (notation par points)
   * @returns {boolean} - Existence de la valeur
   */
  has(path) {
    return _.has(this.getConfig(), path);
  }
  
  /**
   * Charge un fichier de configuration
   * @param {string} name - Nom de la configuration (base, development, production, local, etc.)
   * @returns {Object|null} - Configuration chargée ou null en cas d'échec
   * @private
   */
  _loadConfig(name) {
    const configFile = path.join(this.configPath, `${name}.json`);
    
    try {
      // Vérifier si le fichier existe
      if (!fs.existsSync(configFile)) {
        if (name !== 'local') {
          console.warn(`Fichier de configuration ${configFile} non trouvé`);
        }
        return null;
      }
      
      // Lire et parser le fichier
      const configData = fs.readFileSync(configFile, 'utf8');
      const config = JSON.parse(configData);
      
      // Stocker la configuration
      this._loadedConfigs.set(name, config);
      
      // Mettre en place un watcher si demandé
      if (this.watchForChanges && !this._watchers.has(name)) {
        const watcher = fs.watch(configFile, (eventType) => {
          if (eventType === 'change') {
            console.log(`Configuration ${name} modifiée, rechargement...`);
            this._loadConfig(name);
          }
        });
        
        this._watchers.set(name, watcher);
      }
      
      return config;
    } catch (error) {
      console.error(`Erreur lors du chargement de la configuration ${name}:`, error);
      return null;
    }
  }
}

// Singleton pour l'accès global
let instance = null;

/**
 * Initialise l'instance globale du gestionnaire de configuration
 * @param {Object} options - Options de configuration
 * @returns {ConfigManager} - L'instance du gestionnaire
 */
function initializeConfig(options = {}) {
  instance = new ConfigManager(options);
  return instance;
}

/**
 * Récupère l'instance globale du gestionnaire de configuration
 * @returns {ConfigManager} - L'instance du gestionnaire
 * @throws {Error} - Si l'instance n'a pas été initialisée
 */
function getConfigManager() {
  if (!instance) {
    throw new Error('ConfigManager non initialisé. Appelez initializeConfig() d\'abord.');
  }
  return instance;
}

module.exports = {
  ConfigManager,
  initializeConfig,
  getConfigManager
};
