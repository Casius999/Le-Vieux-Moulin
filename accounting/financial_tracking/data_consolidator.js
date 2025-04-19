/**
 * Module de consolidation des données financières
 * Collecte, agrège et normalise les données financières provenant de diverses sources
 * pour les rendre exploitables par le module de comptabilité
 */

'use strict';

const moment = require('moment');
const { EventEmitter } = require('events');
const axios = require('axios');
const _ = require('lodash');

/**
 * Classe responsable de la consolidation des données financières
 * @extends EventEmitter
 */
class DataConsolidator extends EventEmitter {
  /**
   * Crée une nouvelle instance du consolidateur de données
   * @param {Object} options - Options de configuration
   * @param {Object} options.configManager - Instance du gestionnaire de configuration
   * @param {Object} options.logger - Instance du logger
   * @param {Object} options.dbPool - Pool de connexion à la base de données
   * @param {Object} options.systemIntegrator - Instance de l'intégrateur système
   */
  constructor(options = {}) {
    super();
    
    this.configManager = options.configManager;
    this.logger = options.logger || console;
    this.dbPool = options.dbPool;
    this.systemIntegrator = options.systemIntegrator;
    
    // Cache pour les résultats de requêtes fréquentes
    this.cache = {
      transactions: new Map(),
      expenses: new Map(),
      inventory: new Map()
    };
    
    // Temps d'expiration du cache en millisecondes
    this.cacheExpiration = options.cacheExpiration || 5 * 60 * 1000; // 5 minutes par défaut
    
    // Intervalle de nettoyage du cache
    this.cacheCleaner = setInterval(() => this._cleanCache(), 15 * 60 * 1000); // 15 minutes
    
    this.logger.info('DataConsolidator initialisé');
  }
  
  /**
   * Nettoie les entrées expirées du cache
   * @private
   */
  _cleanCache() {
    const now = Date.now();
    
    // Pour chaque type de données en cache
    for (const [cacheType, cacheMap] of Object.entries(this.cache)) {
      // Parcourir les entrées et supprimer celles qui sont expirées
      for (const [key, entry] of cacheMap.entries()) {
        if (now > entry.expiration) {
          cacheMap.delete(key);
          this.logger.debug(`Cache nettoyé: ${cacheType} - ${key}`);
        }
      }
    }
  }
  
  /**
   * Génère une clé de cache pour une requête
   * @param {string} type - Type de données
   * @param {Object} params - Paramètres de la requête
   * @returns {string} Clé de cache
   * @private
   */
  _generateCacheKey(type, params) {
    return `${type}_${JSON.stringify(params)}`;
  }
  
  /**
   * Vérifie si une entrée est présente dans le cache et non expirée
   * @param {string} type - Type de données
   * @param {string} key - Clé de cache
   * @returns {boolean} True si l'entrée est valide dans le cache
   * @private
   */
  _isCacheValid(type, key) {
    if (!this.cache[type].has(key)) {
      return false;
    }
    
    const entry = this.cache[type].get(key);
    return Date.now() <= entry.expiration;
  }
  
  /**
   * Récupère une entrée du cache
   * @param {string} type - Type de données
   * @param {string} key - Clé de cache
   * @returns {*} Données en cache ou null si non trouvées ou expirées
   * @private
   */
  _getFromCache(type, key) {
    if (this._isCacheValid(type, key)) {
      return this.cache[type].get(key).data;
    }
    
    return null;
  }
  
  /**
   * Stocke une entrée dans le cache
   * @param {string} type - Type de données
   * @param {string} key - Clé de cache
   * @param {*} data - Données à mettre en cache
   * @private
   */
  _storeInCache(type, key, data) {
    this.cache[type].set(key, {
      data,
      expiration: Date.now() + this.cacheExpiration
    });
  }
  
  /**
   * Récupère les transactions financières pour une période donnée
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {string} [params.category] - Catégorie de produit (optionnel)
   * @param {boolean} [params.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Array>} Liste des transactions
   */
  async getTransactions(params = {}) {
    try {
      // Normaliser les dates
      const startDate = params.startDate instanceof Date 
        ? params.startDate 
        : new Date(params.startDate);
      
      const endDate = params.endDate instanceof Date 
        ? params.endDate 
        : new Date(params.endDate);
      
      // Vérifier la validité des dates
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        throw new Error('Dates invalides fournies pour la requête de transactions');
      }
      
      // Paramètres de filtrage
      const queryParams = {
        startDate: moment(startDate).format('YYYY-MM-DD'),
        endDate: moment(endDate).format('YYYY-MM-DD')
      };
      
      if (params.category) {
        queryParams.category = params.category;
      }
      
      // Vérifier le cache si activé
      const useCache = params.useCache !== false;
      const cacheKey = this._generateCacheKey('transactions', queryParams);
      
      if (useCache) {
        const cachedData = this._getFromCache('transactions', cacheKey);
        if (cachedData) {
          this.logger.debug(`Utilisation du cache pour transactions: ${cacheKey}`);
          return cachedData;
        }
      }
      
      // Récupérer les données depuis la base de données
      const transactions = await this._fetchTransactionsFromDb(queryParams);
      
      // Enrichir les transactions avec des données supplémentaires
      const enrichedTransactions = await this._enrichTransactions(transactions);
      
      // Mettre en cache si activé
      if (useCache) {
        this._storeInCache('transactions', cacheKey, enrichedTransactions);
      }
      
      return enrichedTransactions;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des transactions:', error);
      throw error;
    }
  }
  
  /**
   * Récupère les transactions depuis la base de données
   * @param {Object} params - Paramètres de la requête
   * @returns {Promise<Array>} Liste des transactions
   * @private
   */
  async _fetchTransactionsFromDb(params) {
    // Si un pool de connexion est disponible, utiliser la base de données
    if (this.dbPool) {
      const { startDate, endDate, category } = params;
      
      let query = `
        SELECT 
          t.id, t.date, t.total, t.tax_total AS taxTotal,
          t.payment_method AS paymentMethod, t.covers,
          JSON_AGG(
            JSON_BUILD_OBJECT(
              'id', ti.id,
              'name', ti.name,
              'quantity', ti.quantity,
              'price', ti.price,
              'total', ti.total,
              'tax_rate', ti.tax_rate,
              'category', tc.name
            )
          ) AS items
        FROM 
          transactions t
        LEFT JOIN 
          transaction_items ti ON t.id = ti.transaction_id
        LEFT JOIN 
          transaction_categories tc ON ti.category_id = tc.id
        WHERE 
          t.date BETWEEN $1 AND $2
      `;
      
      const queryParams = [startDate, endDate];
      
      // Ajouter le filtre par catégorie si nécessaire
      if (category) {
        query += " AND tc.name = $3";
        queryParams.push(category);
      }
      
      query += `
        GROUP BY 
          t.id
        ORDER BY 
          t.date
      `;
      
      const client = await this.dbPool.connect();
      
      try {
        const result = await client.query(query, queryParams);
        return result.rows;
      } finally {
        client.release();
      }
    }
    
    // Sinon, utiliser l'intégrateur système pour récupérer les données
    if (this.systemIntegrator) {
      return this.systemIntegrator.fetchTransactions(params);
    }
    
    // Si aucune source n'est disponible, retourner un tableau vide
    this.logger.warn('Aucune source de données disponible pour les transactions');
    return [];
  }
  
  /**
   * Enrichit les transactions avec des données supplémentaires
   * @param {Array} transactions - Liste des transactions
   * @returns {Promise<Array>} Transactions enrichies
   * @private
   */
  async _enrichTransactions(transactions) {
    try {
      // Récupérer les méthodes de paiement pour chaque transaction
      const transactionIds = transactions.map(tx => tx.id);
      const payments = await this._fetchPaymentsByTransactionIds(transactionIds);
      
      // Associer les paiements aux transactions
      return transactions.map(transaction => {
        const txPayments = payments.filter(p => p.transactionId === transaction.id);
        
        return {
          ...transaction,
          payments: txPayments
        };
      });
    } catch (error) {
      this.logger.error('Erreur lors de l\'enrichissement des transactions:', error);
      return transactions; // Retourner les transactions non enrichies en cas d'erreur
    }
  }
  
  /**
   * Récupère les paiements pour une liste de transactions
   * @param {string[]} transactionIds - IDs des transactions
   * @returns {Promise<Array>} Liste des paiements
   * @private
   */
  async _fetchPaymentsByTransactionIds(transactionIds) {
    if (!transactionIds || transactionIds.length === 0) {
      return [];
    }
    
    // Si un pool de connexion est disponible, utiliser la base de données
    if (this.dbPool) {
      const client = await this.dbPool.connect();
      
      try {
        const query = `
          SELECT 
            id, transaction_id AS "transactionId", method, amount, type, 
            created_at AS "createdAt"
          FROM 
            payments
          WHERE 
            transaction_id = ANY($1)
        `;
        
        const result = await client.query(query, [transactionIds]);
        return result.rows;
      } finally {
        client.release();
      }
    }
    
    // Sinon, utiliser l'intégrateur système
    if (this.systemIntegrator) {
      return this.systemIntegrator.fetchPaymentsByTransactions(transactionIds);
    }
    
    // Si aucune source n'est disponible, retourner un tableau vide
    return [];
  }
  
  /**
   * Récupère les dépenses pour une période donnée
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {string} [params.category] - Catégorie de dépense (optionnel)
   * @param {boolean} [params.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Array>} Liste des dépenses
   */
  async getExpenses(params = {}) {
    try {
      // Normaliser les dates
      const startDate = params.startDate instanceof Date 
        ? params.startDate 
        : new Date(params.startDate);
      
      const endDate = params.endDate instanceof Date 
        ? params.endDate 
        : new Date(params.endDate);
      
      // Vérifier la validité des dates
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        throw new Error('Dates invalides fournies pour la requête de dépenses');
      }
      
      // Paramètres de filtrage
      const queryParams = {
        startDate: moment(startDate).format('YYYY-MM-DD'),
        endDate: moment(endDate).format('YYYY-MM-DD')
      };
      
      if (params.category) {
        queryParams.category = params.category;
      }
      
      // Vérifier le cache si activé
      const useCache = params.useCache !== false;
      const cacheKey = this._generateCacheKey('expenses', queryParams);
      
      if (useCache) {
        const cachedData = this._getFromCache('expenses', cacheKey);
        if (cachedData) {
          this.logger.debug(`Utilisation du cache pour dépenses: ${cacheKey}`);
          return cachedData;
        }
      }
      
      // Récupérer les données depuis la base de données
      const expenses = await this._fetchExpensesFromDb(queryParams);
      
      // Mettre en cache si activé
      if (useCache) {
        this._storeInCache('expenses', cacheKey, expenses);
      }
      
      return expenses;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des dépenses:', error);
      throw error;
    }
  }
  
  /**
   * Récupère les dépenses depuis la base de données
   * @param {Object} params - Paramètres de la requête
   * @returns {Promise<Array>} Liste des dépenses
   * @private
   */
  async _fetchExpensesFromDb(params) {
    // Si un pool de connexion est disponible, utiliser la base de données
    if (this.dbPool) {
      const { startDate, endDate, category } = params;
      
      let query = `
        SELECT 
          e.id, e.date, e.amount, e.description, 
          e.reference_number AS "referenceNumber",
          e.payment_method AS "paymentMethod",
          ec.name AS category
        FROM 
          expenses e
        LEFT JOIN 
          expense_categories ec ON e.category_id = ec.id
        WHERE 
          e.date BETWEEN $1 AND $2
      `;
      
      const queryParams = [startDate, endDate];
      
      // Ajouter le filtre par catégorie si nécessaire
      if (category) {
        query += " AND ec.name = $3";
        queryParams.push(category);
      }
      
      query += `
        ORDER BY 
          e.date
      `;
      
      const client = await this.dbPool.connect();
      
      try {
        const result = await client.query(query, queryParams);
        return result.rows;
      } finally {
        client.release();
      }
    }
    
    // Sinon, utiliser l'intégrateur système
    if (this.systemIntegrator) {
      return this.systemIntegrator.fetchExpenses(params);
    }
    
    // Si aucune source n'est disponible, retourner un tableau vide
    this.logger.warn('Aucune source de données disponible pour les dépenses');
    return [];
  }
  
  /**
   * Récupère les mouvements de stock pour une période donnée
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {string} [params.productId] - ID du produit (optionnel)
   * @param {string} [params.type] - Type de mouvement (PURCHASE, CONSUMPTION, ADJUSTMENT, etc.)
   * @param {boolean} [params.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Array>} Liste des mouvements de stock
   */
  async getInventoryMovements(params = {}) {
    try {
      // Normaliser les dates
      const startDate = params.startDate instanceof Date 
        ? params.startDate 
        : new Date(params.startDate);
      
      const endDate = params.endDate instanceof Date 
        ? params.endDate 
        : new Date(params.endDate);
      
      // Vérifier la validité des dates
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        throw new Error('Dates invalides fournies pour la requête de mouvements de stock');
      }
      
      // Paramètres de filtrage
      const queryParams = {
        startDate: moment(startDate).format('YYYY-MM-DD'),
        endDate: moment(endDate).format('YYYY-MM-DD')
      };
      
      if (params.productId) {
        queryParams.productId = params.productId;
      }
      
      if (params.type) {
        queryParams.type = params.type;
      }
      
      // Vérifier le cache si activé
      const useCache = params.useCache !== false;
      const cacheKey = this._generateCacheKey('inventory', queryParams);
      
      if (useCache) {
        const cachedData = this._getFromCache('inventory', cacheKey);
        if (cachedData) {
          this.logger.debug(`Utilisation du cache pour mouvements de stock: ${cacheKey}`);
          return cachedData;
        }
      }
      
      // Récupérer les données depuis la base de données ou l'intégrateur
      const movements = await this._fetchInventoryMovementsFromSource(queryParams);
      
      // Mettre en cache si activé
      if (useCache) {
        this._storeInCache('inventory', cacheKey, movements);
      }
      
      return movements;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des mouvements de stock:', error);
      throw error;
    }
  }
  
  /**
   * Récupère les mouvements de stock depuis la source de données appropriée
   * @param {Object} params - Paramètres de la requête
   * @returns {Promise<Array>} Liste des mouvements de stock
   * @private
   */
  async _fetchInventoryMovementsFromSource(params) {
    // Si un pool de connexion est disponible, utiliser la base de données
    if (this.dbPool) {
      const { startDate, endDate, productId, type } = params;
      
      let query = `
        SELECT 
          im.id, im.date, im.type, 
          im.product_id AS "productId",
          p.name AS "productName",
          im.quantity, im.unit_cost AS "unitCost",
          im.quantity * im.unit_cost AS cost,
          im.reference_id AS "referenceId",
          im.reference_type AS "referenceType",
          im.notes
        FROM 
          inventory_movements im
        JOIN 
          products p ON im.product_id = p.id
        WHERE 
          im.date BETWEEN $1 AND $2
      `;
      
      const queryParams = [startDate, endDate];
      let paramIndex = 3;
      
      // Ajouter le filtre par produit si nécessaire
      if (productId) {
        query += ` AND im.product_id = $${paramIndex}`;
        queryParams.push(productId);
        paramIndex++;
      }
      
      // Ajouter le filtre par type si nécessaire
      if (type) {
        query += ` AND im.type = $${paramIndex}`;
        queryParams.push(type);
      }
      
      query += `
        ORDER BY 
          im.date
      `;
      
      const client = await this.dbPool.connect();
      
      try {
        const result = await client.query(query, queryParams);
        return result.rows;
      } finally {
        client.release();
      }
    }
    
    // Sinon, utiliser l'intégrateur système
    if (this.systemIntegrator) {
      return this.systemIntegrator.fetchInventoryMovements(params);
    }
    
    // Si aucune source n'est disponible, retourner un tableau vide
    this.logger.warn('Aucune source de données disponible pour les mouvements de stock');
    return [];
  }
  
  /**
   * Récupère le résumé de stock pour une période donnée
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {boolean} [params.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résumé du stock
   */
  async getInventorySummary(params = {}) {
    try {
      // Récupérer les mouvements de stock pour la période
      const movements = await this.getInventoryMovements(params);
      
      // Calculer les valeurs d'ouverture et de clôture
      const startDate = params.startDate instanceof Date 
        ? params.startDate 
        : new Date(params.startDate);
      
      const openingInventoryValue = await this._calculateInventoryValueAtDate(startDate);
      
      // Agréger les mouvements par type
      const aggregatedMovements = _.groupBy(movements, 'type');
      
      // Calculer les totaux par type
      const movementSummary = {};
      
      for (const [type, typeMovements] of Object.entries(aggregatedMovements)) {
        movementSummary[type] = {
          count: typeMovements.length,
          totalQuantity: _.sumBy(typeMovements, 'quantity'),
          totalCost: _.sumBy(typeMovements, 'cost')
        };
      }
      
      // Calculer la valeur totale de consommation
      const consumption = movementSummary.CONSUMPTION || { totalCost: 0 };
      const purchases = movementSummary.PURCHASE || { totalCost: 0 };
      const adjustments = movementSummary.ADJUSTMENT || { totalCost: 0 };
      
      // Calculer la valeur de clôture
      const closingInventoryValue = openingInventoryValue + 
        purchases.totalCost - 
        consumption.totalCost + 
        adjustments.totalCost;
      
      // Calculer la valeur moyenne du stock sur la période
      const averageInventoryValue = (openingInventoryValue + closingInventoryValue) / 2;
      
      return {
        period: {
          startDate: moment(startDate).format('YYYY-MM-DD'),
          endDate: moment(params.endDate).format('YYYY-MM-DD')
        },
        openingInventoryValue,
        closingInventoryValue,
        averageInventoryValue,
        movements: movementSummary,
        totalConsumption: consumption.totalCost,
        totalPurchases: purchases.totalCost,
        totalAdjustments: adjustments.totalCost
      };
    } catch (error) {
      this.logger.error('Erreur lors de la récupération du résumé de stock:', error);
      throw error;
    }
  }
  
  /**
   * Calcule la valeur de stock à une date donnée
   * @param {Date} date - Date de référence
   * @returns {Promise<number>} Valeur du stock
   * @private
   */
  async _calculateInventoryValueAtDate(date) {
    try {
      // Si un pool de connexion est disponible, utiliser la base de données
      if (this.dbPool) {
        const client = await this.dbPool.connect();
        
        try {
          // Requête pour calculer la valeur du stock à une date donnée
          const query = `
            SELECT 
              COALESCE(SUM(
                CASE 
                  WHEN im.type = 'PURCHASE' THEN im.quantity * im.unit_cost
                  WHEN im.type = 'CONSUMPTION' THEN -1 * im.quantity * im.unit_cost
                  WHEN im.type = 'ADJUSTMENT' THEN im.quantity * im.unit_cost
                  ELSE 0
                END
              ), 0) AS stock_value
            FROM 
              inventory_movements im
            WHERE 
              im.date <= $1
          `;
          
          const result = await client.query(query, [moment(date).format('YYYY-MM-DD')]);
          return parseFloat(result.rows[0].stock_value);
        } finally {
          client.release();
        }
      }
      
      // Sinon, utiliser l'intégrateur système
      if (this.systemIntegrator) {
        return this.systemIntegrator.getInventoryValueAtDate(date);
      }
      
      // Si aucune source n'est disponible, retourner 0
      this.logger.warn('Aucune source de données disponible pour la valeur de stock');
      return 0;
    } catch (error) {
      this.logger.error('Erreur lors du calcul de la valeur de stock:', error);
      return 0;
    }
  }
  
  /**
   * Récupère les coûts de main d'œuvre pour une période donnée
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {boolean} [params.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résumé des coûts de main d'œuvre
   */
  async getLaborCosts(params = {}) {
    try {
      // Si un pool de connexion est disponible, utiliser la base de données
      if (this.dbPool) {
        const { startDate, endDate } = params;
        
        const client = await this.dbPool.connect();
        
        try {
          // Requête pour récupérer les heures travaillées
          const hoursQuery = `
            SELECT 
              s.staff_id, 
              p.name, 
              p.hourly_rate AS "hourlyRate",
              SUM(EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 3600) AS hours_worked,
              SUM(EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 3600 * p.hourly_rate) AS labor_cost
            FROM 
              shifts s
            JOIN 
              personnel p ON s.staff_id = p.id
            WHERE 
              s.date BETWEEN $1 AND $2
            GROUP BY 
              s.staff_id, p.name, p.hourly_rate
            ORDER BY 
              p.name
          `;
          
          const hoursResult = await client.query(hoursQuery, [
            moment(startDate).format('YYYY-MM-DD'),
            moment(endDate).format('YYYY-MM-DD')
          ]);
          
          // Requête pour récupérer les coûts fixes (salaires mensuels, etc.)
          const fixedCostsQuery = `
            SELECT 
              SUM(amount) AS fixed_costs
            FROM 
              payroll_fixed_costs
            WHERE 
              period_start <= $2 AND period_end >= $1
          `;
          
          const fixedCostsResult = await client.query(fixedCostsQuery, [
            moment(startDate).format('YYYY-MM-DD'),
            moment(endDate).format('YYYY-MM-DD')
          ]);
          
          // Calculer le coût total
          const hourlyLaborCost = hoursResult.rows.reduce((sum, row) => sum + parseFloat(row.labor_cost), 0);
          const fixedLaborCost = parseFloat(fixedCostsResult.rows[0]?.fixed_costs || 0);
          const totalCost = hourlyLaborCost + fixedLaborCost;
          
          return {
            period: {
              startDate: moment(startDate).format('YYYY-MM-DD'),
              endDate: moment(endDate).format('YYYY-MM-DD')
            },
            hourlyStaff: hoursResult.rows,
            totalHourlyLaborCost: hourlyLaborCost,
            fixedLaborCost,
            totalCost
          };
        } finally {
          client.release();
        }
      }
      
      // Sinon, utiliser l'intégrateur système
      if (this.systemIntegrator) {
        return this.systemIntegrator.getLaborCosts(params);
      }
      
      // Si aucune source n'est disponible, retourner un objet vide
      this.logger.warn('Aucune source de données disponible pour les coûts de main d\'œuvre');
      return {
        period: {
          startDate: moment(params.startDate).format('YYYY-MM-DD'),
          endDate: moment(params.endDate).format('YYYY-MM-DD')
        },
        hourlyStaff: [],
        totalHourlyLaborCost: 0,
        fixedLaborCost: 0,
        totalCost: 0
      };
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des coûts de main d\'œuvre:', error);
      throw error;
    }
  }
  
  /**
   * Récupère le planning du personnel pour une période donnée
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {string} [params.staffId] - ID du membre du personnel (optionnel)
   * @returns {Promise<Array>} Planning du personnel
   */
  async getStaffSchedule(params = {}) {
    try {
      // Si un pool de connexion est disponible, utiliser la base de données
      if (this.dbPool) {
        const { startDate, endDate, staffId } = params;
        
        let query = `
          SELECT 
            s.id, s.date, s.start_time AS "startTime", s.end_time AS "endTime",
            s.staff_id AS "staffId", p.name AS "staffName",
            p.hourly_rate AS "hourlyRate",
            EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 3600 AS hours,
            (EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 3600) * p.hourly_rate AS cost,
            s.role, s.notes
          FROM 
            shifts s
          JOIN 
            personnel p ON s.staff_id = p.id
          WHERE 
            s.date BETWEEN $1 AND $2
        `;
        
        const queryParams = [
          moment(startDate).format('YYYY-MM-DD'),
          moment(endDate).format('YYYY-MM-DD')
        ];
        
        // Ajouter le filtre par membre du personnel si nécessaire
        if (staffId) {
          query += " AND s.staff_id = $3";
          queryParams.push(staffId);
        }
        
        query += `
          ORDER BY 
            s.date, s.start_time
        `;
        
        const client = await this.dbPool.connect();
        
        try {
          const result = await client.query(query, queryParams);
          return result.rows;
        } finally {
          client.release();
        }
      }
      
      // Sinon, utiliser l'intégrateur système
      if (this.systemIntegrator) {
        return this.systemIntegrator.getStaffSchedule(params);
      }
      
      // Si aucune source n'est disponible, retourner un tableau vide
      this.logger.warn('Aucune source de données disponible pour le planning du personnel');
      return [];
    } catch (error) {
      this.logger.error('Erreur lors de la récupération du planning du personnel:', error);
      throw error;
    }
  }
  
  /**
   * Récupère les données consolidées pour un rapport financier complet
   * @param {Object} params - Paramètres de la requête
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {boolean} [params.includeInventory=true] - Inclure les données d'inventaire
   * @param {boolean} [params.includeLaborCosts=true] - Inclure les coûts de main d'œuvre
   * @returns {Promise<Object>} Données consolidées
   */
  async getConsolidatedFinancialData(params = {}) {
    try {
      const { 
        startDate, 
        endDate, 
        includeInventory = true, 
        includeLaborCosts = true 
      } = params;
      
      // Récupérer les données de base
      const transactions = await this.getTransactions({ startDate, endDate });
      const expenses = await this.getExpenses({ startDate, endDate });
      
      // Calculer les totaux de vente
      const totalSales = transactions.reduce((sum, tx) => sum + tx.total, 0);
      const ticketCount = transactions.length;
      const averageTicket = ticketCount > 0 ? totalSales / ticketCount : 0;
      
      // Calculer les totaux de dépenses
      const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);
      
      // Données à collecter en parallèle
      const promises = [];
      
      // Ajouter la promesse pour l'inventaire si nécessaire
      if (includeInventory) {
        promises.push(this.getInventorySummary({ startDate, endDate }));
      } else {
        promises.push(Promise.resolve(null));
      }
      
      // Ajouter la promesse pour les coûts de main d'œuvre si nécessaire
      if (includeLaborCosts) {
        promises.push(this.getLaborCosts({ startDate, endDate }));
      } else {
        promises.push(Promise.resolve(null));
      }
      
      // Récupérer les données supplémentaires
      const [inventorySummary, laborCosts] = await Promise.all(promises);
      
      // Calculer les indicateurs financiers
      const costOfGoodsSold = inventorySummary ? inventorySummary.totalConsumption : 0;
      const laborCost = laborCosts ? laborCosts.totalCost : 0;
      
      const grossProfit = totalSales - costOfGoodsSold;
      const grossProfitMargin = totalSales > 0 ? (grossProfit / totalSales) * 100 : 0;
      
      const operatingProfit = grossProfit - laborCost - totalExpenses;
      const operatingProfitMargin = totalSales > 0 ? (operatingProfit / totalSales) * 100 : 0;
      
      // Construire l'objet de résultat
      return {
        period: {
          startDate: moment(startDate).format('YYYY-MM-DD'),
          endDate: moment(endDate).format('YYYY-MM-DD')
        },
        summary: {
          totalSales,
          ticketCount,
          averageTicket,
          totalExpenses,
          costOfGoodsSold,
          laborCost,
          grossProfit,
          grossProfitMargin,
          operatingProfit,
          operatingProfitMargin
        },
        transactions,
        expenses,
        inventory: inventorySummary,
        labor: laborCosts,
        kpis: {
          foodCostPercentage: totalSales > 0 ? (costOfGoodsSold / totalSales) * 100 : 0,
          laborCostPercentage: totalSales > 0 ? (laborCost / totalSales) * 100 : 0,
          expensePercentage: totalSales > 0 ? (totalExpenses / totalSales) * 100 : 0,
          profitPercentage: totalSales > 0 ? (operatingProfit / totalSales) * 100 : 0
        }
      };
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des données financières consolidées:', error);
      throw error;
    }
  }
  
  /**
   * Libère les ressources utilisées par le consolidateur
   */
  close() {
    clearInterval(this.cacheCleaner);
    this.cache.transactions.clear();
    this.cache.expenses.clear();
    this.cache.inventory.clear();
    
    this.logger.info('DataConsolidator fermé');
  }
}

module.exports = { DataConsolidator };
