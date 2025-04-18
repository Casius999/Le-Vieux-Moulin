/**
 * Module de collecte de données pour le système de comptabilité
 * Ce module est responsable de la récupération et de l'agrégation des données
 * en provenance des différentes sources du système.
 */

'use strict';

const axios = require('axios');
const moment = require('moment');
const { ApiClient } = require('../../integration/api_connectors/api_client');
const { ConnectionPool } = require('./connection_pool');
const { ConfigManager } = require('./config_manager');
const { SecurityUtils } = require('./security_utils');

/**
 * Classe principale pour la collecte de données financières
 */
class DataCollector {
  /**
   * Crée une nouvelle instance du collecteur de données
   * @param {Object} options - Options de configuration
   * @param {Object} options.apiConfig - Configuration des API externes
   * @param {Object} options.dbConfig - Configuration des connexions aux bases de données
   * @param {Object} options.cachingConfig - Configuration du cache de données
   * @param {Object} options.securityConfig - Configuration de sécurité et authentification
   */
  constructor(options = {}) {
    this.apiConfig = options.apiConfig || {};
    this.dbConfig = options.dbConfig || {};
    this.cachingConfig = options.cachingConfig || { enabled: true, ttl: 300 }; // TTL en secondes
    this.securityConfig = options.securityConfig || {};
    
    // Initialisation des clients API et connexions DB
    this.apiClients = {};
    this.dbConnections = {};
    this.cache = new Map();
    
    this._initializeConnections();
  }
  
  /**
   * Initialise les connexions aux différentes sources de données
   * @private
   */
  _initializeConnections() {
    // Initialisation des clients API
    if (this.apiConfig.endpoints) {
      for (const [name, config] of Object.entries(this.apiConfig.endpoints)) {
        this.apiClients[name] = new ApiClient({
          baseUrl: config.baseUrl,
          auth: config.auth,
          timeout: config.timeout || 30000,
          retries: config.retries || 3,
          headers: config.headers || {}
        });
      }
    }
    
    // Initialisation des connexions à la base de données
    if (this.dbConfig.connections) {
      this.connectionPool = new ConnectionPool(this.dbConfig);
    }
  }
  
  /**
   * Récupère les données de ventes pour une période donnée
   * @param {Object} options - Options de filtrage
   * @param {string|Date} options.startDate - Date de début de la période (incluse)
   * @param {string|Date} options.endDate - Date de fin de la période (incluse)
   * @param {string} options.granularity - Granularité des données (day, week, month)
   * @param {string[]} options.categories - Filtrage par catégories
   * @param {boolean} options.includeDetails - Inclure les détails des transactions
   * @returns {Promise<Object>} - Données de ventes formatées
   */
  async getSalesData(options = {}) {
    const cacheKey = `sales_${JSON.stringify(options)}`;
    
    // Vérifier le cache si activé
    if (this.cachingConfig.enabled) {
      const cached = this._getCachedData(cacheKey);
      if (cached) return cached;
    }
    
    try {
      // Normaliser les dates
      const startDate = options.startDate ? moment(options.startDate).startOf('day') : moment().startOf('day');
      const endDate = options.endDate ? moment(options.endDate).endOf('day') : moment().endOf('day');
      
      // Préparer les paramètres de requête
      const params = {
        startDate: startDate.format('YYYY-MM-DD'),
        endDate: endDate.format('YYYY-MM-DD'),
        granularity: options.granularity || 'day',
        includeDetails: options.includeDetails || false
      };
      
      if (options.categories && Array.isArray(options.categories)) {
        params.categories = options.categories.join(',');
      }
      
      // Récupérer les données depuis l'API ou la BD
      let salesData;
      
      if (this.apiClients.pos) {
        // Depuis l'API de caisse
        salesData = await this.apiClients.pos.get('/sales', { params });
      } else if (this.connectionPool) {
        // Depuis la base de données
        const db = await this.connectionPool.getConnection('sales');
        
        const query = `
          SELECT 
            date_trunc($1, created_at) as period,
            category,
            SUM(total_amount) as total_amount,
            SUM(total_amount_without_tax) as total_amount_without_tax,
            SUM(tax_amount) as tax_amount,
            COUNT(*) as transaction_count
          FROM transactions
          WHERE created_at BETWEEN $2 AND $3
          ${options.categories ? 'AND category = ANY($4)' : ''}
          GROUP BY period, category
          ORDER BY period, category
        `;
        
        const queryParams = [
          params.granularity,
          params.startDate,
          params.endDate
        ];
        
        if (options.categories) {
          queryParams.push(options.categories);
        }
        
        const result = await db.query(query, queryParams);
        salesData = this._transformDatabaseResult(result.rows);
        
        // Ajouter les détails si demandés
        if (options.includeDetails) {
          const detailsQuery = `
            SELECT 
              id, 
              created_at, 
              total_amount, 
              payment_method,
              items
            FROM transactions
            WHERE created_at BETWEEN $1 AND $2
            ${options.categories ? 'AND category = ANY($3)' : ''}
            ORDER BY created_at DESC
          `;
          
          const detailsParams = [
            params.startDate,
            params.endDate
          ];
          
          if (options.categories) {
            detailsParams.push(options.categories);
          }
          
          const detailsResult = await db.query(detailsQuery, detailsParams);
          salesData.details = detailsResult.rows;
        }
        
        db.release();
      } else {
        throw new Error('Aucune source de données configurée pour les ventes');
      }
      
      // Enrichir les données avec des calculs complémentaires
      this._enrichSalesData(salesData, options);
      
      // Mettre en cache
      if (this.cachingConfig.enabled) {
        this._setCachedData(cacheKey, salesData, this.cachingConfig.ttl);
      }
      
      return salesData;
    } catch (error) {
      console.error('Erreur lors de la récupération des données de ventes:', error);
      throw new Error(`Échec de récupération des données de ventes: ${error.message}`);
    }
  }
  
  /**
   * Récupère les données de dépenses pour une période donnée
   * @param {Object} options - Options de filtrage
   * @param {string|Date} options.startDate - Date de début de la période (incluse)
   * @param {string|Date} options.endDate - Date de fin de la période (incluse)
   * @param {string} options.granularity - Granularité des données (day, week, month)
   * @param {string[]} options.categories - Filtrage par catégories de dépenses
   * @param {boolean} options.includeDetails - Inclure les détails des transactions
   * @returns {Promise<Object>} - Données de dépenses formatées
   */
  async getExpensesData(options = {}) {
    const cacheKey = `expenses_${JSON.stringify(options)}`;
    
    // Vérifier le cache si activé
    if (this.cachingConfig.enabled) {
      const cached = this._getCachedData(cacheKey);
      if (cached) return cached;
    }
    
    try {
      // Normaliser les dates
      const startDate = options.startDate ? moment(options.startDate).startOf('day') : moment().subtract(30, 'days').startOf('day');
      const endDate = options.endDate ? moment(options.endDate).endOf('day') : moment().endOf('day');
      
      // Préparer les paramètres de requête
      const params = {
        startDate: startDate.format('YYYY-MM-DD'),
        endDate: endDate.format('YYYY-MM-DD'),
        granularity: options.granularity || 'day',
        includeDetails: options.includeDetails || false
      };
      
      if (options.categories && Array.isArray(options.categories)) {
        params.categories = options.categories.join(',');
      }
      
      // Récupérer les données depuis l'API ou la BD
      let expensesData;
      
      if (this.apiClients.expenses) {
        // Depuis l'API de gestion des dépenses
        expensesData = await this.apiClients.expenses.get('/expenses', { params });
      } else if (this.connectionPool) {
        // Depuis la base de données
        const db = await this.connectionPool.getConnection('expenses');
        
        const query = `
          SELECT 
            date_trunc($1, invoice_date) as period,
            category,
            SUM(total_amount) as total_amount,
            SUM(total_amount_without_tax) as total_amount_without_tax,
            SUM(tax_amount) as tax_amount,
            COUNT(*) as invoice_count
          FROM expenses
          WHERE invoice_date BETWEEN $2 AND $3
          ${options.categories ? 'AND category = ANY($4)' : ''}
          GROUP BY period, category
          ORDER BY period, category
        `;
        
        const queryParams = [
          params.granularity,
          params.startDate,
          params.endDate
        ];
        
        if (options.categories) {
          queryParams.push(options.categories);
        }
        
        const result = await db.query(query, queryParams);
        expensesData = this._transformDatabaseResult(result.rows);
        
        // Ajouter les détails si demandés
        if (options.includeDetails) {
          const detailsQuery = `
            SELECT 
              id, 
              invoice_date, 
              invoice_number,
              supplier,
              total_amount, 
              payment_method,
              payment_status,
              due_date,
              items
            FROM expenses
            WHERE invoice_date BETWEEN $1 AND $2
            ${options.categories ? 'AND category = ANY($3)' : ''}
            ORDER BY invoice_date DESC
          `;
          
          const detailsParams = [
            params.startDate,
            params.endDate
          ];
          
          if (options.categories) {
            detailsParams.push(options.categories);
          }
          
          const detailsResult = await db.query(detailsQuery, detailsParams);
          expensesData.details = detailsResult.rows;
        }
        
        db.release();
      } else {
        throw new Error('Aucune source de données configurée pour les dépenses');
      }
      
      // Mettre en cache
      if (this.cachingConfig.enabled) {
        this._setCachedData(cacheKey, expensesData, this.cachingConfig.ttl);
      }
      
      return expensesData;
    } catch (error) {
      console.error('Erreur lors de la récupération des données de dépenses:', error);
      throw new Error(`Échec de récupération des données de dépenses: ${error.message}`);
    }
  }
  
  /**
   * Récupère les données de bénéfices et marges pour une période donnée
   * @param {Object} options - Options de filtrage
   * @param {string|Date} options.startDate - Date de début de la période (incluse)
   * @param {string|Date} options.endDate - Date de fin de la période (incluse)
   * @param {string} options.granularity - Granularité des données (day, week, month)
   * @param {boolean} options.includeComparison - Inclure des comparaisons avec périodes précédentes
   * @returns {Promise<Object>} - Données de profits formatées
   */
  async getProfitData(options = {}) {
    const cacheKey = `profit_${JSON.stringify(options)}`;
    
    // Vérifier le cache si activé
    if (this.cachingConfig.enabled) {
      const cached = this._getCachedData(cacheKey);
      if (cached) return cached;
    }
    
    try {
      // Récupérer les données de ventes et dépenses pour la période
      const salesData = await this.getSalesData({
        startDate: options.startDate,
        endDate: options.endDate,
        granularity: options.granularity
      });
      
      const expensesData = await this.getExpensesData({
        startDate: options.startDate,
        endDate: options.endDate,
        granularity: options.granularity
      });
      
      // Calculer les profits par période
      const profitData = this._calculateProfitData(salesData, expensesData, options);
      
      // Inclure des comparaisons si demandé
      if (options.includeComparison) {
        await this._addProfitComparisons(profitData, options);
      }
      
      // Mettre en cache
      if (this.cachingConfig.enabled) {
        this._setCachedData(cacheKey, profitData, this.cachingConfig.ttl);
      }
      
      return profitData;
    } catch (error) {
      console.error('Erreur lors de la récupération des données de profit:', error);
      throw new Error(`Échec de récupération des données de profit: ${error.message}`);
    }
  }
  
  /**
   * Récupère les données d'inventaire et valorisation des stocks
   * @param {Object} options - Options de filtrage
   * @param {boolean} options.currentOnly - Récupérer uniquement l'état actuel (vs. historique)
   * @param {string} options.valuationMethod - Méthode de valorisation (weighted_average, fifo, lifo)
   * @param {string[]} options.categories - Filtrage par catégories de produits
   * @returns {Promise<Object>} - Données d'inventaire formatées
   */
  async getInventoryData(options = {}) {
    const cacheKey = `inventory_${JSON.stringify(options)}`;
    
    // Vérifier le cache si activé
    if (this.cachingConfig.enabled) {
      const cached = this._getCachedData(cacheKey);
      if (cached) return cached;
    }
    
    try {
      let inventoryData;
      
      // Paramètres de requête
      const params = {
        currentOnly: options.currentOnly !== undefined ? options.currentOnly : true,
        valuationMethod: options.valuationMethod || 'weighted_average'
      };
      
      if (options.categories && Array.isArray(options.categories)) {
        params.categories = options.categories.join(',');
      }
      
      // Récupérer depuis l'API IoT ou la BD
      if (this.apiClients.inventory) {
        inventoryData = await this.apiClients.inventory.get('/inventory/valuation', { params });
      } else if (this.connectionPool) {
        const db = await this.connectionPool.getConnection('inventory');
        
        let query;
        const queryParams = [];
        
        if (params.currentOnly) {
          // Uniquement l'état actuel
          query = `
            SELECT 
              i.product_id,
              p.name as product_name,
              p.category,
              i.quantity,
              i.unit,
              i.unit_cost,
              i.last_updated,
              (i.quantity * i.unit_cost) as total_value
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            ${options.categories ? 'WHERE p.category = ANY($1)' : ''}
            ORDER BY p.category, p.name
          `;
          
          if (options.categories) {
            queryParams.push(options.categories);
          }
        } else {
          // Historique de valorisation
          query = `
            SELECT 
              date_trunc('day', timestamp) as date,
              SUM(total_value) as total_value
            FROM inventory_history
            WHERE timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY date
            ORDER BY date
          `;
        }
        
        const result = await db.query(query, queryParams);
        
        if (params.currentOnly) {
          // Transformation des données d'inventaire actuel
          inventoryData = {
            timestamp: new Date(),
            totalValue: result.rows.reduce((sum, item) => sum + parseFloat(item.total_value), 0),
            items: result.rows.map(item => ({
              productId: item.product_id,
              name: item.product_name,
              category: item.category,
              quantity: parseFloat(item.quantity),
              unit: item.unit,
              unitCost: parseFloat(item.unit_cost),
              totalValue: parseFloat(item.total_value),
              lastUpdated: item.last_updated
            }))
          };
          
          // Regrouper par catégorie
          inventoryData.categories = Object.entries(
            inventoryData.items.reduce((acc, item) => {
              if (!acc[item.category]) {
                acc[item.category] = {
                  category: item.category,
                  totalValue: 0,
                  itemCount: 0
                };
              }
              
              acc[item.category].totalValue += item.totalValue;
              acc[item.category].itemCount += 1;
              
              return acc;
            }, {})
          ).map(([_, value]) => value);
          
        } else {
          // Transformation des données historiques
          inventoryData = {
            valuationMethod: params.valuationMethod,
            history: result.rows.map(item => ({
              date: item.date,
              totalValue: parseFloat(item.total_value)
            }))
          };
        }
        
        db.release();
      } else {
        throw new Error('Aucune source de données configurée pour l\'inventaire');
      }
      
      // Mettre en cache
      if (this.cachingConfig.enabled) {
        this._setCachedData(cacheKey, inventoryData, 
          // TTL plus court pour l'inventaire (5 minutes)
          params.currentOnly ? 300 : this.cachingConfig.ttl
        );
      }
      
      return inventoryData;
    } catch (error) {
      console.error('Erreur lors de la récupération des données d\'inventaire:', error);
      throw new Error(`Échec de récupération des données d'inventaire: ${error.message}`);
    }
  }
  
  /**
   * Récupère les données de transactions bancaires pour réconciliation
   * @param {Object} options - Options de filtrage
   * @param {string|Date} options.startDate - Date de début de la période
   * @param {string|Date} options.endDate - Date de fin de la période
   * @param {string} options.accountId - Identifiant du compte bancaire
   * @returns {Promise<Object>} - Données de transactions bancaires
   */
  async getBankTransactionData(options = {}) {
    // Implémentation similaire aux méthodes précédentes
    // ...
    
    // Exemple simplifié
    return {
      accountId: options.accountId,
      period: {
        start: options.startDate,
        end: options.endDate
      },
      transactions: [],
      summary: {
        openingBalance: 0,
        closingBalance: 0,
        totalDeposits: 0,
        totalWithdrawals: 0
      }
    };
  }
  
  /**
   * Récupère un élément en cache
   * @param {string} key - Clé de cache
   * @returns {Object|null} - Données en cache ou null si absentes ou expirées
   * @private
   */
  _getCachedData(key) {
    if (!this.cache.has(key)) return null;
    
    const cached = this.cache.get(key);
    
    // Vérifier si les données sont expirées
    if (cached.expiresAt < Date.now()) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  /**
   * Met en cache des données
   * @param {string} key - Clé de cache
   * @param {Object} data - Données à mettre en cache
   * @param {number} ttl - Durée de vie en secondes
   * @private
   */
  _setCachedData(key, data, ttl = this.cachingConfig.ttl) {
    this.cache.set(key, {
      data,
      expiresAt: Date.now() + (ttl * 1000)
    });
  }
  
  /**
   * Transforme les résultats de requête BD en format standardisé
   * @param {Array} rows - Lignes de résultats BD
   * @returns {Object} - Données formatées
   * @private
   */
  _transformDatabaseResult(rows) {
    // Implémentation spécifique de transformation
    // ...
    
    return {
      // Structure de données formatée
    };
  }
  
  /**
   * Enrichit les données de ventes avec des calculs et statistiques
   * @param {Object} salesData - Données de ventes brutes
   * @param {Object} options - Options de configuration
   * @private
   */
  _enrichSalesData(salesData, options) {
    // Implémentation de l'enrichissement
    // ...
  }
  
  /**
   * Calcule les données de profit à partir des ventes et dépenses
   * @param {Object} salesData - Données de ventes
   * @param {Object} expensesData - Données de dépenses
   * @param {Object} options - Options de configuration
   * @returns {Object} - Données de profit calculées
   * @private
   */
  _calculateProfitData(salesData, expensesData, options) {
    // Implémentation du calcul
    // ...
    
    return {
      // Structure de données de profit
    };
  }
  
  /**
   * Ajoute des comparaisons aux données de profit
   * @param {Object} profitData - Données de profit
   * @param {Object} options - Options de configuration
   * @returns {Promise<void>}
   * @private
   */
  async _addProfitComparisons(profitData, options) {
    // Implémentation de l'ajout de comparaisons
    // ...
  }
}

module.exports = { DataCollector };
