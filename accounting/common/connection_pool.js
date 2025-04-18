/**
 * Gestionnaire de pool de connexions pour le module de comptabilité
 * Ce module gère les connexions aux différentes bases de données
 * et fournit un pool de connexions optimisé et résilient.
 */

'use strict';

const { Pool } = require('pg');
const { EventEmitter } = require('events');
const { ConfigManager } = require('./config_manager');

/**
 * Classe de gestion des connexions à la base de données
 */
class ConnectionPool extends EventEmitter {
  /**
   * Crée une nouvelle instance du gestionnaire de connexions
   * @param {Object} options - Options de configuration
   * @param {Object} options.connections - Configuration des connexions
   * @param {Object} options.poolConfig - Configuration globale des pools
   * @param {ConfigManager} options.configManager - Instance du gestionnaire de configuration
   */
  constructor(options = {}) {
    super();
    
    this.connections = options.connections || {};
    this.poolConfig = options.poolConfig || {};
    this.configManager = options.configManager || 
      (ConfigManager.getConfigManager ? ConfigManager.getConfigManager() : null);
    
    // Charger la configuration depuis le gestionnaire si disponible
    if (this.configManager) {
      const dbConfig = this.configManager.getConfig('database', {});
      
      if (dbConfig.connections) {
        this.connections = { ...this.connections, ...dbConfig.connections };
      }
      
      if (dbConfig.poolConfig) {
        this.poolConfig = { ...this.poolConfig, ...dbConfig.poolConfig };
      }
    }
    
    // Configuration par défaut des pools
    this.defaultPoolConfig = {
      max: this.poolConfig.max || 10,
      idleTimeoutMillis: this.poolConfig.idleTimeoutMillis || 30000,
      connectionTimeoutMillis: this.poolConfig.connectionTimeoutMillis || 5000
    };
    
    // Pools de connexions
    this.pools = new Map();
    
    // Compteurs de connexions actives
    this.activeConnections = new Map();
    
    // Initialiser les pools
    this._initializePools();
  }
  
  /**
   * Initialise les pools de connexions configurés
   * @private
   */
  _initializePools() {
    for (const [name, config] of Object.entries(this.connections)) {
      this._createPool(name, config);
    }
  }
  
  /**
   * Crée un pool de connexions pour une base de données
   * @param {string} name - Nom du pool
   * @param {Object} config - Configuration de connexion
   * @returns {Pool} - Instance du pool
   * @private
   */
  _createPool(name, config) {
    if (this.pools.has(name)) {
      return this.pools.get(name);
    }
    
    // Merger la configuration spécifique avec la configuration par défaut
    const poolConfig = {
      ...this.defaultPoolConfig,
      ...(config.pool || {})
    };
    
    // Configuration de connexion PostgreSQL
    const connectionConfig = {
      host: config.host,
      port: config.port || 5432,
      database: config.database,
      user: config.user,
      password: config.password,
      ssl: config.ssl || false,
      application_name: config.applicationName || 'accounting_module'
    };
    
    // Créer le pool
    const pool = new Pool({
      ...connectionConfig,
      ...poolConfig
    });
    
    // Initialiser le compteur de connexions actives
    this.activeConnections.set(name, 0);
    
    // Écouter les événements du pool
    this._setupPoolListeners(name, pool);
    
    // Stocker le pool
    this.pools.set(name, pool);
    
    return pool;
  }
  
  /**
   * Configure les écouteurs d'événements pour un pool
   * @param {string} name - Nom du pool
   * @param {Pool} pool - Instance du pool
   * @private
   */
  _setupPoolListeners(name, pool) {
    // Connexion acquise
    pool.on('acquire', () => {
      const count = (this.activeConnections.get(name) || 0) + 1;
      this.activeConnections.set(name, count);
      
      this.emit('connection:acquire', { name, count });
    });
    
    // Connexion libérée
    pool.on('release', () => {
      const count = Math.max(0, (this.activeConnections.get(name) || 0) - 1);
      this.activeConnections.set(name, count);
      
      this.emit('connection:release', { name, count });
    });
    
    // Erreur de connexion
    pool.on('error', (err) => {
      console.error(`Erreur de pool de connexion ${name}:`, err);
      this.emit('connection:error', { name, error: err });
    });
  }
  
  /**
   * Obtient une connexion à partir d'un pool
   * @param {string} name - Nom du pool
   * @returns {Promise<Object>} - Client de connexion avec méthode release()
   */
  async getConnection(name) {
    // Vérifier si le pool existe
    if (!this.pools.has(name)) {
      // Vérifier si la configuration existe mais le pool n'a pas été créé
      if (this.connections[name]) {
        this._createPool(name, this.connections[name]);
      } else {
        throw new Error(`Pool de connexion non trouvé: ${name}`);
      }
    }
    
    const pool = this.pools.get(name);
    
    try {
      // Acquérir un client
      const client = await pool.connect();
      
      // Wrapper le client pour suivre la libération
      const wrappedClient = this._wrapClientWithTracking(client, name);
      
      return wrappedClient;
    } catch (error) {
      console.error(`Erreur lors de l'acquisition d'une connexion ${name}:`, error);
      this.emit('connection:acquisition-error', { name, error });
      throw error;
    }
  }
  
  /**
   * Enveloppe un client pour suivre sa libération
   * @param {Object} client - Client de connexion
   * @param {string} poolName - Nom du pool
   * @returns {Object} - Client enveloppé
   * @private
   */
  _wrapClientWithTracking(client, poolName) {
    const originalRelease = client.release;
    
    // Remplacer la méthode release
    client.release = (err) => {
      // Appeler la méthode originale
      originalRelease.call(client, err);
      
      // Émettre un événement personnalisé
      this.emit('client:released', { poolName });
    };
    
    return client;
  }
  
  /**
   * Exécute une requête sur un pool spécifique
   * @param {string} poolName - Nom du pool
   * @param {string} query - Requête SQL
   * @param {Array} params - Paramètres de la requête
   * @returns {Promise<Object>} - Résultat de la requête
   */
  async query(poolName, query, params = []) {
    // Vérifier si le pool existe
    if (!this.pools.has(poolName)) {
      // Vérifier si la configuration existe mais le pool n'a pas été créé
      if (this.connections[poolName]) {
        this._createPool(poolName, this.connections[poolName]);
      } else {
        throw new Error(`Pool de connexion non trouvé: ${poolName}`);
      }
    }
    
    const pool = this.pools.get(poolName);
    
    try {
      return await pool.query(query, params);
    } catch (error) {
      console.error(`Erreur lors de l'exécution de la requête sur ${poolName}:`, error);
      this.emit('query:error', { poolName, query, params, error });
      throw error;
    }
  }
  
  /**
   * Ferme tous les pools de connexion
   * @returns {Promise<void>} - Promesse résolue lorsque tous les pools sont fermés
   */
  async close() {
    const closePromises = [];
    
    for (const [name, pool] of this.pools.entries()) {
      console.log(`Fermeture du pool de connexion ${name}...`);
      
      closePromises.push(
        pool.end()
          .then(() => {
            console.log(`Pool de connexion ${name} fermé avec succès`);
            this.emit('pool:closed', { name });
          })
          .catch(err => {
            console.error(`Erreur lors de la fermeture du pool ${name}:`, err);
            this.emit('pool:close-error', { name, error: err });
          })
      );
    }
    
    // Attendre que tous les pools soient fermés
    await Promise.all(closePromises);
    
    // Vider les maps
    this.pools.clear();
    this.activeConnections.clear();
    
    this.emit('all-pools:closed');
  }
  
  /**
   * Obtient les statistiques d'utilisation des pools
   * @returns {Object} - Statistiques par pool
   */
  getStats() {
    const stats = {};
    
    for (const [name, pool] of this.pools.entries()) {
      stats[name] = {
        total: pool.totalCount,
        idle: pool.idleCount,
        active: this.activeConnections.get(name) || 0,
        waiting: pool.waitingCount,
        max: pool.options.max
      };
    }
    
    return stats;
  }
  
  /**
   * Obtient la liste des pools disponibles
   * @returns {string[]} - Noms des pools
   */
  getAvailablePools() {
    return Array.from(this.pools.keys());
  }
  
  /**
   * Vérifie l'état d'un pool
   * @param {string} name - Nom du pool
   * @returns {Promise<Object>} - État du pool
   */
  async checkPoolHealth(name) {
    if (!this.pools.has(name)) {
      throw new Error(`Pool de connexion non trouvé: ${name}`);
    }
    
    const pool = this.pools.get(name);
    
    try {
      // Acquérir une connexion de test
      const client = await pool.connect();
      
      // Exécuter une requête simple
      const result = await client.query('SELECT NOW() as now');
      
      // Libérer le client
      client.release();
      
      return {
        status: 'healthy',
        timestamp: result.rows[0].now,
        stats: {
          total: pool.totalCount,
          idle: pool.idleCount,
          active: this.activeConnections.get(name) || 0,
          waiting: pool.waitingCount,
          max: pool.options.max
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date(),
        stats: {
          total: pool.totalCount,
          idle: pool.idleCount,
          active: this.activeConnections.get(name) || 0,
          waiting: pool.waitingCount,
          max: pool.options.max
        }
      };
    }
  }
}

// Singleton pour l'accès global
let instance = null;

/**
 * Initialise l'instance globale du gestionnaire de connexions
 * @param {Object} options - Options de configuration
 * @returns {ConnectionPool} - L'instance du gestionnaire
 */
function initializeConnectionPool(options = {}) {
  instance = new ConnectionPool(options);
  return instance;
}

/**
 * Récupère l'instance globale du gestionnaire de connexions
 * @returns {ConnectionPool} - L'instance du gestionnaire
 * @throws {Error} - Si l'instance n'a pas été initialisée
 */
function getConnectionPool() {
  if (!instance) {
    throw new Error('ConnectionPool non initialisé. Appelez initializeConnectionPool() d\'abord.');
  }
  return instance;
}

module.exports = {
  ConnectionPool,
  initializeConnectionPool,
  getConnectionPool
};
