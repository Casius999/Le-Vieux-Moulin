/**
 * Intégrateur des modèles d'IA/ML pour les prévisions financières
 * Ce module fait le lien entre le module de comptabilité et les modèles prédictifs
 * pour obtenir des prévisions financières précises.
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const axios = require('axios');

/**
 * Classe d'intégration avec les modèles d'IA/ML pour les prévisions financières
 * @extends EventEmitter
 */
class MLIntegrator extends EventEmitter {
  /**
   * Crée une instance de l'intégrateur ML
   * @param {Object} options - Options de configuration
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.securityUtils - Utilitaires de sécurité
   * @param {Object} options.logger - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    this.configManager = options.configManager;
    this.securityUtils = options.securityUtils;
    this.logger = options.logger || console;
    
    // Charger la configuration
    this.config = this._loadConfig();
    
    this.logger.debug('MLIntegrator initialisé');
  }
  
  /**
   * Charge la configuration pour l'intégration ML
   * @returns {Object} Configuration
   * @private
   */
  _loadConfig() {
    if (this.configManager) {
      const mlConfig = this.configManager.getConfig('ml_integration');
      if (mlConfig) {
        return mlConfig;
      }
    }
    
    // Configuration par défaut
    return {
      apiEndpoint: process.env.ML_API_ENDPOINT || 'http://localhost:5000/api/predictions',
      apiKey: process.env.ML_API_KEY || '',
      requestTimeout: 30000, // 30 secondes
      models: {
        revenue: 'revenue_forecast_v3',
        expenses: 'expense_forecast_v2',
        cash_flow: 'cash_flow_forecast_v2',
        inventory: 'inventory_optimization_v1'
      },
      cacheEnabled: true,
      cacheTTL: 3600 // 1 heure en secondes
    };
  }
  
  /**
   * Obtient des prévisions de chiffre d'affaires
   * @param {Object} options - Options de prévision
   * @param {Date} options.startDate - Date de début de la prévision
   * @param {Date} options.endDate - Date de fin de la prévision
   * @param {string} [options.granularity='daily'] - Granularité ('daily', 'weekly', 'monthly')
   * @param {Object} [options.additionalFactors] - Facteurs additionnels à prendre en compte
   * @returns {Promise<Object>} Prévisions de chiffre d'affaires
   */
  async getRevenueForecast(options = {}) {
    this.logger.debug('Demande de prévision de chiffre d\'affaires', options);
    
    if (!options.startDate || !options.endDate) {
      throw new Error('Les dates de début et fin sont obligatoires pour la prévision de chiffre d\'affaires');
    }
    
    try {
      // Préparer les données pour la requête
      const requestData = {
        model: this.config.models.revenue,
        params: {
          start_date: options.startDate.toISOString().split('T')[0],
          end_date: options.endDate.toISOString().split('T')[0],
          granularity: options.granularity || 'daily'
        },
        context: {
          historical_period: options.historicalPeriod || 90, // Jours d'historique à utiliser
          include_weather: options.includeWeather !== undefined ? options.includeWeather : true,
          include_seasonality: options.includeSeasonality !== undefined ? options.includeSeasonality : true,
          include_events: options.includeEvents !== undefined ? options.includeEvents : true
        }
      };
      
      // Ajouter des facteurs additionnels si fournis
      if (options.additionalFactors) {
        requestData.factors = options.additionalFactors;
      }
      
      // Effectuer la requête aux modèles ML
      const response = await this._makeMLRequest('revenue/forecast', requestData);
      
      // Traiter et formater les résultats
      const formattedResults = this._formatRevenueForecast(response);
      
      this.logger.debug('Prévision de chiffre d\'affaires obtenue');
      
      // Émettre un événement pour la prévision
      this.emit('forecast:generated', {
        type: 'revenue',
        period: {
          start: options.startDate,
          end: options.endDate
        },
        granularity: options.granularity || 'daily'
      });
      
      return formattedResults;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des prévisions de chiffre d\'affaires:', error);
      
      // Émettre un événement d'erreur
      this.emit('forecast:error', {
        type: 'revenue',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Obtient des prévisions de dépenses
   * @param {Object} options - Options de prévision
   * @param {Date} options.startDate - Date de début de la prévision
   * @param {Date} options.endDate - Date de fin de la prévision
   * @param {string} [options.granularity='daily'] - Granularité ('daily', 'weekly', 'monthly')
   * @param {Array<string>} [options.categories] - Catégories de dépenses à inclure
   * @returns {Promise<Object>} Prévisions de dépenses
   */
  async getExpenseForecast(options = {}) {
    this.logger.debug('Demande de prévision de dépenses', options);
    
    if (!options.startDate || !options.endDate) {
      throw new Error('Les dates de début et fin sont obligatoires pour la prévision de dépenses');
    }
    
    try {
      // Préparer les données pour la requête
      const requestData = {
        model: this.config.models.expenses,
        params: {
          start_date: options.startDate.toISOString().split('T')[0],
          end_date: options.endDate.toISOString().split('T')[0],
          granularity: options.granularity || 'daily'
        },
        context: {
          historical_period: options.historicalPeriod || 90, // Jours d'historique à utiliser
          include_seasonality: options.includeSeasonality !== undefined ? options.includeSeasonality : true,
          include_fixed_costs: options.includeFixedCosts !== undefined ? options.includeFixedCosts : true
        }
      };
      
      // Ajouter des catégories spécifiques si fournies
      if (options.categories && Array.isArray(options.categories)) {
        requestData.params.categories = options.categories;
      }
      
      // Effectuer la requête aux modèles ML
      const response = await this._makeMLRequest('expenses/forecast', requestData);
      
      // Traiter et formater les résultats
      const formattedResults = this._formatExpenseForecast(response);
      
      this.logger.debug('Prévision de dépenses obtenue');
      
      // Émettre un événement pour la prévision
      this.emit('forecast:generated', {
        type: 'expenses',
        period: {
          start: options.startDate,
          end: options.endDate
        },
        granularity: options.granularity || 'daily'
      });
      
      return formattedResults;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des prévisions de dépenses:', error);
      
      // Émettre un événement d'erreur
      this.emit('forecast:error', {
        type: 'expenses',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Obtient des prévisions de trésorerie
   * @param {Object} options - Options de prévision
   * @param {Date} options.startDate - Date de début de la prévision
   * @param {Date} options.endDate - Date de fin de la prévision
   * @param {string} [options.granularity='daily'] - Granularité ('daily', 'weekly', 'monthly')
   * @param {boolean} [options.includeRevenue=true] - Inclure les prévisions de revenus
   * @param {boolean} [options.includeExpenses=true] - Inclure les prévisions de dépenses
   * @returns {Promise<Object>} Prévisions de trésorerie
   */
  async getCashFlowForecast(options = {}) {
    this.logger.debug('Demande de prévision de trésorerie', options);
    
    if (!options.startDate || !options.endDate) {
      throw new Error('Les dates de début et fin sont obligatoires pour la prévision de trésorerie');
    }
    
    try {
      // Préparer les données pour la requête
      const requestData = {
        model: this.config.models.cash_flow,
        params: {
          start_date: options.startDate.toISOString().split('T')[0],
          end_date: options.endDate.toISOString().split('T')[0],
          granularity: options.granularity || 'daily',
          include_revenue: options.includeRevenue !== undefined ? options.includeRevenue : true,
          include_expenses: options.includeExpenses !== undefined ? options.includeExpenses : true
        },
        context: {
          historical_period: options.historicalPeriod || 90, // Jours d'historique à utiliser
          initial_balance: options.initialBalance || null, // Solde initial, null pour utiliser le solde actuel
          payment_terms: options.paymentTerms || {} // Conditions de paiement par type
        }
      };
      
      // Effectuer la requête aux modèles ML
      const response = await this._makeMLRequest('cash_flow/forecast', requestData);
      
      // Traiter et formater les résultats
      const formattedResults = this._formatCashFlowForecast(response);
      
      this.logger.debug('Prévision de trésorerie obtenue');
      
      // Émettre un événement pour la prévision
      this.emit('forecast:generated', {
        type: 'cash_flow',
        period: {
          start: options.startDate,
          end: options.endDate
        },
        granularity: options.granularity || 'daily'
      });
      
      return formattedResults;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des prévisions de trésorerie:', error);
      
      // Émettre un événement d'erreur
      this.emit('forecast:error', {
        type: 'cash_flow',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Obtient des recommandations d'optimisation des stocks
   * @param {Object} options - Options d'optimisation
   * @param {Array<string>} [options.categories] - Catégories de produits à analyser
   * @param {number} [options.forecastDays=30] - Nombre de jours de prévision
   * @param {boolean} [options.considerSeasonality=true] - Prendre en compte la saisonnalité
   * @returns {Promise<Object>} Recommandations d'optimisation
   */
  async getInventoryOptimization(options = {}) {
    this.logger.debug('Demande d\'optimisation des stocks', options);
    
    try {
      // Préparer les données pour la requête
      const requestData = {
        model: this.config.models.inventory,
        params: {
          forecast_days: options.forecastDays || 30,
          consider_seasonality: options.considerSeasonality !== undefined ? options.considerSeasonality : true,
          service_level: options.serviceLevel || 0.95 // Niveau de service cible (95% par défaut)
        }
      };
      
      // Ajouter des catégories spécifiques si fournies
      if (options.categories && Array.isArray(options.categories)) {
        requestData.params.categories = options.categories;
      }
      
      // Effectuer la requête aux modèles ML
      const response = await this._makeMLRequest('inventory/optimize', requestData);
      
      // Traiter et formater les résultats
      const formattedResults = this._formatInventoryOptimization(response);
      
      this.logger.debug('Optimisation des stocks obtenue');
      
      // Émettre un événement pour l'optimisation
      this.emit('optimization:generated', {
        type: 'inventory',
        forecastDays: options.forecastDays || 30
      });
      
      return formattedResults;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des optimisations de stocks:', error);
      
      // Émettre un événement d'erreur
      this.emit('optimization:error', {
        type: 'inventory',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Détecte les anomalies dans les données financières
   * @param {Object} options - Options de détection
   * @param {string} options.dataType - Type de données ('revenue', 'expenses', 'transactions')
   * @param {Date} options.startDate - Date de début de l'analyse
   * @param {Date} options.endDate - Date de fin de l'analyse
   * @param {number} [options.sensitivityLevel=0.9] - Niveau de sensibilité (0-1)
   * @returns {Promise<Object>} Anomalies détectées
   */
  async detectAnomalies(options = {}) {
    this.logger.debug('Demande de détection d\'anomalies', options);
    
    if (!options.dataType) {
      throw new Error('Le type de données est obligatoire pour la détection d\'anomalies');
    }
    
    if (!options.startDate || !options.endDate) {
      throw new Error('Les dates de début et fin sont obligatoires pour la détection d\'anomalies');
    }
    
    try {
      // Préparer les données pour la requête
      const requestData = {
        params: {
          data_type: options.dataType,
          start_date: options.startDate.toISOString().split('T')[0],
          end_date: options.endDate.toISOString().split('T')[0],
          sensitivity_level: options.sensitivityLevel || 0.9
        }
      };
      
      // Effectuer la requête aux modèles ML
      const response = await this._makeMLRequest('anomalies/detect', requestData);
      
      // Traiter et formater les résultats
      const formattedResults = this._formatAnomalyDetection(response);
      
      this.logger.debug('Détection d\'anomalies terminée');
      
      // Émettre un événement pour la détection
      this.emit('anomaly:detection', {
        type: options.dataType,
        period: {
          start: options.startDate,
          end: options.endDate
        },
        anomalyCount: formattedResults.anomalies.length
      });
      
      return formattedResults;
    } catch (error) {
      this.logger.error('Erreur lors de la détection d\'anomalies:', error);
      
      // Émettre un événement d'erreur
      this.emit('anomaly:error', {
        type: options.dataType,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Effectue une requête au service de ML
   * @param {string} endpoint - Point d'API à appeler
   * @param {Object} data - Données de la requête
   * @returns {Promise<Object>} Réponse du service ML
   * @private
   */
  async _makeMLRequest(endpoint, data) {
    try {
      const apiUrl = `${this.config.apiEndpoint}/${endpoint}`;
      
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };
      
      // Ajouter la clé API si disponible
      if (this.config.apiKey) {
        headers['Authorization'] = `Bearer ${this.config.apiKey}`;
      }
      
      const response = await axios({
        method: 'POST',
        url: apiUrl,
        headers,
        data,
        timeout: this.config.requestTimeout
      });
      
      return response.data;
    } catch (error) {
      this.logger.error(`Erreur lors de la requête ML à ${endpoint}:`, error);
      
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'erreur
        throw new Error(`Erreur API ML (${error.response.status}): ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        throw new Error('Pas de réponse du service ML. Vérifiez la connectivité au service.');
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        throw error;
      }
    }
  }
  
  /**
   * Formate les résultats de prévision de chiffre d'affaires
   * @param {Object} rawResponse - Réponse brute de l'API
   * @returns {Object} Résultats formatés
   * @private
   */
  _formatRevenueForecast(rawResponse) {
    if (!rawResponse || !rawResponse.data || !Array.isArray(rawResponse.data.forecast)) {
      throw new Error('Format de réponse de prévision de chiffre d\'affaires invalide');
    }
    
    // Transformer les données pour qu'elles soient plus faciles à utiliser
    const forecast = rawResponse.data.forecast.map(item => ({
      date: new Date(item.date),
      revenue: item.value,
      lowerBound: item.lower_bound,
      upperBound: item.upper_bound,
      confidenceLevel: item.confidence_level || 0.9
    }));
    
    // Ajouter des métadonnées et des statistiques
    const result = {
      forecast,
      metadata: {
        generated: new Date(),
        modelVersion: rawResponse.metadata?.model_version || 'unknown',
        params: rawResponse.metadata?.params || {}
      },
      stats: {
        total: forecast.reduce((sum, item) => sum + item.revenue, 0),
        average: forecast.reduce((sum, item) => sum + item.revenue, 0) / forecast.length,
        min: Math.min(...forecast.map(item => item.revenue)),
        max: Math.max(...forecast.map(item => item.revenue))
      }
    };
    
    // Ajouter des insights si disponibles
    if (rawResponse.insights) {
      result.insights = rawResponse.insights;
    }
    
    return result;
  }
  
  /**
   * Formate les résultats de prévision de dépenses
   * @param {Object} rawResponse - Réponse brute de l'API
   * @returns {Object} Résultats formatés
   * @private
   */
  _formatExpenseForecast(rawResponse) {
    if (!rawResponse || !rawResponse.data || !Array.isArray(rawResponse.data.forecast)) {
      throw new Error('Format de réponse de prévision de dépenses invalide');
    }
    
    // Transformer les données pour qu'elles soient plus faciles à utiliser
    const forecast = rawResponse.data.forecast.map(item => ({
      date: new Date(item.date),
      total: item.total,
      byCategory: item.categories || {},
      lowerBound: item.lower_bound,
      upperBound: item.upper_bound,
      confidenceLevel: item.confidence_level || 0.9
    }));
    
    // Ajouter des métadonnées et des statistiques
    const result = {
      forecast,
      metadata: {
        generated: new Date(),
        modelVersion: rawResponse.metadata?.model_version || 'unknown',
        params: rawResponse.metadata?.params || {}
      },
      stats: {
        total: forecast.reduce((sum, item) => sum + item.total, 0),
        average: forecast.reduce((sum, item) => sum + item.total, 0) / forecast.length,
        min: Math.min(...forecast.map(item => item.total)),
        max: Math.max(...forecast.map(item => item.total))
      }
    };
    
    // Calculer les totaux par catégorie
    if (forecast.length > 0 && forecast[0].byCategory) {
      const categories = Object.keys(forecast[0].byCategory);
      result.stats.byCategory = {};
      
      for (const category of categories) {
        result.stats.byCategory[category] = forecast.reduce((sum, item) => sum + (item.byCategory[category] || 0), 0);
      }
    }
    
    // Ajouter des insights si disponibles
    if (rawResponse.insights) {
      result.insights = rawResponse.insights;
    }
    
    return result;
  }
  
  /**
   * Formate les résultats de prévision de trésorerie
   * @param {Object} rawResponse - Réponse brute de l'API
   * @returns {Object} Résultats formatés
   * @private
   */
  _formatCashFlowForecast(rawResponse) {
    if (!rawResponse || !rawResponse.data || !Array.isArray(rawResponse.data.forecast)) {
      throw new Error('Format de réponse de prévision de trésorerie invalide');
    }
    
    // Transformer les données pour qu'elles soient plus faciles à utiliser
    const forecast = rawResponse.data.forecast.map(item => ({
      date: new Date(item.date),
      balance: item.balance,
      inflow: item.inflow || 0,
      outflow: item.outflow || 0,
      netFlow: (item.inflow || 0) - (item.outflow || 0),
      lowerBound: item.lower_bound,
      upperBound: item.upper_bound,
      confidenceLevel: item.confidence_level || 0.9
    }));
    
    // Ajouter des métadonnées et des statistiques
    const result = {
      forecast,
      metadata: {
        generated: new Date(),
        modelVersion: rawResponse.metadata?.model_version || 'unknown',
        params: rawResponse.metadata?.params || {},
        initialBalance: rawResponse.data.initial_balance
      },
      stats: {
        totalInflow: forecast.reduce((sum, item) => sum + item.inflow, 0),
        totalOutflow: forecast.reduce((sum, item) => sum + item.outflow, 0),
        netFlow: forecast.reduce((sum, item) => sum + item.netFlow, 0),
        minBalance: Math.min(...forecast.map(item => item.balance)),
        maxBalance: Math.max(...forecast.map(item => item.balance))
      }
    };
    
    // Ajouter des alertes de liquidité
    result.alerts = {
      negativeCashflow: forecast.filter(item => item.balance < 0).map(item => ({
        date: item.date,
        balance: item.balance,
        severity: item.balance < -5000 ? 'high' : 'medium'
      }))
    };
    
    // Ajouter des insights si disponibles
    if (rawResponse.insights) {
      result.insights = rawResponse.insights;
    }
    
    return result;
  }
  
  /**
   * Formate les résultats d'optimisation des stocks
   * @param {Object} rawResponse - Réponse brute de l'API
   * @returns {Object} Résultats formatés
   * @private
   */
  _formatInventoryOptimization(rawResponse) {
    if (!rawResponse || !rawResponse.data || !Array.isArray(rawResponse.data.recommendations)) {
      throw new Error('Format de réponse d\'optimisation des stocks invalide');
    }
    
    // Transformer les recommandations
    const recommendations = rawResponse.data.recommendations.map(item => ({
      itemId: item.item_id,
      name: item.name,
      category: item.category,
      currentStock: item.current_stock,
      recommendedStock: item.recommended_stock,
      minLevel: item.min_level,
      maxLevel: item.max_level,
      reorderPoint: item.reorder_point,
      suggestedOrder: Math.max(0, item.recommended_stock - item.current_stock),
      projectedUsage: item.projected_usage,
      confidence: item.confidence || 0.9,
      priority: item.priority || 'medium'
    }));
    
    // Ajouter des métadonnées et des statistiques
    const result = {
      recommendations,
      metadata: {
        generated: new Date(),
        modelVersion: rawResponse.metadata?.model_version || 'unknown',
        params: rawResponse.metadata?.params || {}
      },
      stats: {
        totalItems: recommendations.length,
        totalCurrentValue: recommendations.reduce((sum, item) => sum + (item.currentStock * (item.cost || 0)), 0),
        totalRecommendedValue: recommendations.reduce((sum, item) => sum + (item.recommendedStock * (item.cost || 0)), 0),
        itemsToOrder: recommendations.filter(item => item.suggestedOrder > 0).length,
        totalOrderValue: recommendations.reduce((sum, item) => sum + (item.suggestedOrder * (item.cost || 0)), 0)
      }
    };
    
    // Regrouper par catégorie
    const categorySummary = {};
    for (const item of recommendations) {
      if (!categorySummary[item.category]) {
        categorySummary[item.category] = {
          count: 0,
          currentValue: 0,
          recommendedValue: 0,
          orderValue: 0
        };
      }
      
      categorySummary[item.category].count++;
      categorySummary[item.category].currentValue += (item.currentStock * (item.cost || 0));
      categorySummary[item.category].recommendedValue += (item.recommendedStock * (item.cost || 0));
      categorySummary[item.category].orderValue += (item.suggestedOrder * (item.cost || 0));
    }
    
    result.stats.byCategory = categorySummary;
    
    // Ajouter des insights si disponibles
    if (rawResponse.insights) {
      result.insights = rawResponse.insights;
    }
    
    return result;
  }
  
  /**
   * Formate les résultats de détection d'anomalies
   * @param {Object} rawResponse - Réponse brute de l'API
   * @returns {Object} Résultats formatés
   * @private
   */
  _formatAnomalyDetection(rawResponse) {
    if (!rawResponse || !rawResponse.data) {
      throw new Error('Format de réponse de détection d\'anomalies invalide');
    }
    
    // Transformer les anomalies détectées
    const anomalies = rawResponse.data.anomalies.map(item => ({
      id: item.id,
      date: new Date(item.date),
      type: item.type,
      value: item.value,
      expectedValue: item.expected_value,
      deviation: item.deviation,
      deviationPercentage: item.deviation_percentage,
      severity: item.severity || 'medium',
      description: item.description || '',
      category: item.category || null,
      relatedItems: item.related_items || []
    }));
    
    // Ajouter des métadonnées et des statistiques
    const result = {
      anomalies,
      metadata: {
        generated: new Date(),
        modelVersion: rawResponse.metadata?.model_version || 'unknown',
        params: rawResponse.metadata?.params || {}
      },
      stats: {
        totalAnomalies: anomalies.length,
        bySeverity: {
          high: anomalies.filter(item => item.severity === 'high').length,
          medium: anomalies.filter(item => item.severity === 'medium').length,
          low: anomalies.filter(item => item.severity === 'low').length
        }
      }
    };
    
    // Regrouper par type
    const typeSummary = {};
    for (const anomaly of anomalies) {
      if (!typeSummary[anomaly.type]) {
        typeSummary[anomaly.type] = 0;
      }
      
      typeSummary[anomaly.type]++;
    }
    
    result.stats.byType = typeSummary;
    
    // Ajouter des insights si disponibles
    if (rawResponse.insights) {
      result.insights = rawResponse.insights;
    }
    
    return result;
  }
}

// Exports
module.exports = {
  MLIntegrator
};
