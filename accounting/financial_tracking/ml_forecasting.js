/**
 * Module de prévision financière basé sur des algorithmes d'IA/ML
 * Ce module permet de générer des prévisions financières et d'analyser
 * les tendances à partir des données historiques du restaurant.
 */

'use strict';

const moment = require('moment');
const stats = require('simple-statistics');
const EventEmitter = require('events');

/**
 * Classe de prévision financière utilisant des techniques d'IA/ML
 * @extends EventEmitter
 */
class MLForecasting extends EventEmitter {
  /**
   * Crée une instance du module de prévision financière
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataCollector - Instance du collecteur de données
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.logger - Logger pour tracer les opérations
   */
  constructor(options = {}) {
    super();
    
    this.dataCollector = options.dataCollector;
    this.configManager = options.configManager;
    this.logger = options.logger || console;
    
    // Charger la configuration
    this.config = this.configManager ?
      this.configManager.getConfig('financial_tracking.ml', {}) :
      {};
    
    // Configuration par défaut
    this.defaultConfig = {
      historyDays: 365, // Nombre de jours d'historique pour l'apprentissage
      forecastHorizon: 90, // Horizon de prévision en jours
      seasonalityPeriods: {
        weekly: 7, // Période hebdomadaire (7 jours)
        monthly: 30, // Période mensuelle (approximative)
        yearly: 365 // Période annuelle
      },
      forecastModels: ['arima', 'prophet', 'exponentialSmoothing'],
      anomalyDetectionThreshold: 2.5, // Z-score pour la détection d'anomalies
      confidenceInterval: 0.95 // Intervalle de confiance pour les prévisions
    };
    
    // Fusionner avec la configuration par défaut
    this.config = { ...this.defaultConfig, ...this.config };
    
    // État des dernières prévisions
    this.lastForecasts = {
      revenue: null,
      costs: null,
      margins: null,
      cashflow: null
    };
    
    // État des modèles
    this.models = {
      revenue: null,
      costs: null,
      margins: null,
      cashflow: null
    };
    
    this.logger.info('Module de prévision financière ML initialisé', { config: this.config });
  }
  
  /**
   * Initialise les modèles de prévision
   * @returns {Promise<boolean>} - Vrai si l'initialisation a réussi
   */
  async initialize() {
    try {
      this.logger.info('Initialisation des modèles de prévision ML');
      
      // Charger l'historique des données
      const historicalData = await this._loadHistoricalData();
      
      if (!historicalData) {
        this.logger.warn('Impossible d\'initialiser les modèles: données historiques insuffisantes');
        return false;
      }
      
      // Initialiser chaque modèle
      for (const dataType of Object.keys(historicalData)) {
        if (historicalData[dataType] && historicalData[dataType].length > 0) {
          this.models[dataType] = await this._initializeModel(dataType, historicalData[dataType]);
          this.logger.debug(`Modèle ${dataType} initialisé`);
        }
      }
      
      // Générer les prévisions initiales
      await this.generateForecasts();
      
      this.logger.info('Initialisation des modèles de prévision ML terminée');
      
      return true;
    } catch (error) {
      this.logger.error('Erreur lors de l\'initialisation des modèles de prévision ML', error);
      this.emit('ml:error', { type: 'initialization', error });
      return false;
    }
  }
  
  /**
   * Charge les données historiques pour l'apprentissage
   * @private
   * @returns {Promise<Object>} - Données historiques par type
   */
  async _loadHistoricalData() {
    try {
      const endDate = moment().startOf('day');
      const startDate = moment().subtract(this.config.historyDays, 'days').startOf('day');
      
      this.logger.debug('Chargement des données historiques', { startDate, endDate });
      
      // Récupérer les données financières via le dataCollector
      const financialData = await this.dataCollector.getFinancialTimeSeries({
        startDate,
        endDate,
        metrics: ['revenue', 'costs', 'margins', 'cashflow'],
        granularity: 'day'
      });
      
      if (!financialData || Object.keys(financialData).length === 0) {
        this.logger.warn('Aucune donnée historique trouvée');
        return null;
      }
      
      // Structurer les données pour l'apprentissage
      const structuredData = {};
      
      // Traiter chaque type de métrique
      for (const metricType in financialData) {
        structuredData[metricType] = financialData[metricType].map(item => ({
          date: moment(item.date).toDate(),
          value: item.value,
          // Ajouter des features temporelles
          dayOfWeek: moment(item.date).day(),
          dayOfMonth: moment(item.date).date(),
          month: moment(item.date).month(),
          isWeekend: [0, 6].includes(moment(item.date).day()),
          isHoliday: item.isHoliday || false,
          // Variables liées au business
          hasPromotion: item.hasPromotion || false,
          weatherCondition: item.weatherCondition || 'normal',
          specialEvent: item.specialEvent || null
        }));
      }
      
      this.logger.debug('Données historiques chargées', {
        dataPoints: Object.entries(structuredData).map(([key, value]) => `${key}: ${value.length}`).join(', ')
      });
      
      return structuredData;
    } catch (error) {
      this.logger.error('Erreur lors du chargement des données historiques', error);
      throw error;
    }
  }
  
  /**
   * Initialise un modèle pour un type de données spécifique
   * @private
   * @param {string} dataType - Type de données (revenue, costs, etc.)
   * @param {Array} data - Données historiques
   * @returns {Promise<Object>} - Modèle initialisé
   */
  async _initializeModel(dataType, data) {
    try {
      // Structure pour stocker les différents modèles
      const models = {};
      
      // Modèle 1: Moyenne mobile (approche simple)
      models.movingAverage = this._initMovingAverageModel(data);
      
      // Modèle 2: Lissage exponentiel (plus élaboré)
      models.exponentialSmoothing = this._initExponentialSmoothingModel(data);
      
      // Modèle 3: Décomposition (tendance, saisonnalité, résidus)
      models.decomposition = this._initDecompositionModel(data);
      
      // Modèle 4: Détection d'anomalies
      models.anomalyDetection = this._initAnomalyDetectionModel(data);
      
      // Méta-modèle: Sélection dynamique du meilleur modèle
      const modelPerformance = this._evaluateModels(data, models);
      
      return {
        models,
        modelPerformance,
        bestModel: this._selectBestModel(modelPerformance),
        lastTrainingData: data
      };
    } catch (error) {
      this.logger.error(`Erreur lors de l'initialisation du modèle ${dataType}`, error);
      throw error;
    }
  }
  
  /**
   * Initialise un modèle de moyenne mobile
   * @private
   * @param {Array} data - Données historiques
   * @returns {Object} - Modèle de moyenne mobile
   */
  _initMovingAverageModel(data) {
    // Paramètres pour différentes fenêtres temporelles
    const windowSizes = [7, 14, 30];
    const model = {
      type: 'movingAverage',
      windows: {},
      lastValues: data.slice(-windowSizes[windowSizes.length - 1]).map(d => d.value)
    };
    
    // Calculer les moyennes mobiles pour chaque taille de fenêtre
    for (const size of windowSizes) {
      // Extraire les valeurs numériques
      const values = data.map(d => d.value);
      
      // Calculer la moyenne mobile
      const maValues = [];
      for (let i = size - 1; i < values.length; i++) {
        const windowSum = values.slice(i - size + 1, i + 1).reduce((sum, val) => sum + val, 0);
        maValues.push(windowSum / size);
      }
      
      model.windows[size] = {
        values: maValues,
        lastValue: maValues[maValues.length - 1]
      };
    }
    
    return model;
  }
  
  /**
   * Initialise un modèle de lissage exponentiel
   * @private
   * @param {Array} data - Données historiques
   * @returns {Object} - Modèle de lissage exponentiel
   */
  _initExponentialSmoothingModel(data) {
    // Paramètres du modèle
    const alphaValues = [0.1, 0.3, 0.5];
    const betaValues = [0.1, 0.3];
    const gammaValues = [0.1, 0.3];
    
    const model = {
      type: 'exponentialSmoothing',
      variants: {},
      bestVariant: null,
      bestMSE: Infinity
    };
    
    // Extraire les valeurs numériques
    const values = data.map(d => d.value);
    
    // Pour chaque combinaison de paramètres
    for (const alpha of alphaValues) {
      for (const beta of betaValues) {
        for (const gamma of gammaValues) {
          const variantName = `a${alpha}_b${beta}_g${gamma}`;
          
          // Lissage exponentiel triple (Holt-Winters)
          const result = this._applyHoltWinters(values, alpha, beta, gamma, 
            this.config.seasonalityPeriods.weekly);
          
          model.variants[variantName] = {
            alpha,
            beta,
            gamma,
            level: result.level,
            trend: result.trend,
            seasonal: result.seasonal,
            fitted: result.fitted,
            mse: result.mse
          };
          
          // Conserver la meilleure variante
          if (result.mse < model.bestMSE) {
            model.bestMSE = result.mse;
            model.bestVariant = variantName;
          }
        }
      }
    }
    
    return model;
  }
  
  /**
   * Applique le lissage exponentiel triple (Holt-Winters)
   * @private
   * @param {Array} values - Valeurs numériques
   * @param {number} alpha - Paramètre alpha (niveau)
   * @param {number} beta - Paramètre beta (tendance)
   * @param {number} gamma - Paramètre gamma (saisonnalité)
   * @param {number} period - Période saisonnière
   * @returns {Object} - Résultats du lissage
   */
  _applyHoltWinters(values, alpha, beta, gamma, period) {
    // Initialisation
    const n = values.length;
    const level = new Array(n);
    const trend = new Array(n);
    const seasonal = new Array(n);
    const fitted = new Array(n);
    let sumSquaredErrors = 0;
    
    // Initialiser le niveau et la tendance
    level[0] = values[0];
    trend[0] = 0;
    
    // Initialiser la saisonnalité (en supposant une saisonnalité additive)
    for (let i = 0; i < period; i++) {
      seasonal[i] = values[i] / level[0];
    }
    
    // Appliquer le lissage
    for (let t = 1; t < n; t++) {
      const s = t % period;
      
      if (t >= period) {
        // Niveau
        level[t] = alpha * (values[t] / seasonal[t - period]) + (1 - alpha) * (level[t - 1] + trend[t - 1]);
        // Tendance
        trend[t] = beta * (level[t] - level[t - 1]) + (1 - beta) * trend[t - 1];
        // Saisonnalité
        seasonal[t] = gamma * (values[t] / level[t]) + (1 - gamma) * seasonal[t - period];
        // Prévision pour t
        fitted[t] = (level[t - 1] + trend[t - 1]) * seasonal[t - period];
        // Erreur
        const error = values[t] - fitted[t];
        sumSquaredErrors += error * error;
      } else {
        level[t] = level[t - 1];
        trend[t] = trend[t - 1];
        seasonal[t] = seasonal[s];
        fitted[t] = values[t]; // Pas de prévision disponible encore
      }
    }
    
    // Calculer l'erreur quadratique moyenne
    const mse = sumSquaredErrors / (n - period);
    
    return { level, trend, seasonal, fitted, mse };
  }
  
  /**
   * Initialise un modèle de décomposition (tendance, saisonnalité, résidus)
   * @private
   * @param {Array} data - Données historiques
   * @returns {Object} - Modèle de décomposition
   */
  _initDecompositionModel(data) {
    const model = {
      type: 'decomposition',
      weekly: this._decomposeTimeSeries(data, this.config.seasonalityPeriods.weekly),
      monthly: this._decomposeTimeSeries(data, this.config.seasonalityPeriods.monthly)
    };
    
    return model;
  }
  
  /**
   * Décompose une série temporelle en composantes (tendance, saisonnalité, résidus)
   * @private
   * @param {Array} data - Données historiques
   * @param {number} period - Période de saisonnalité
   * @returns {Object} - Composantes de la série
   */
  _decomposeTimeSeries(data, period) {
    // Extraire les valeurs
    const values = data.map(d => d.value);
    const n = values.length;
    
    // 1. Calculer la tendance avec une moyenne mobile centrée
    const trend = new Array(n).fill(null);
    const halfPeriod = Math.floor(period / 2);
    
    for (let i = halfPeriod; i < n - halfPeriod; i++) {
      let sum = 0;
      for (let j = i - halfPeriod; j <= i + halfPeriod; j++) {
        sum += values[j];
      }
      trend[i] = sum / period;
    }
    
    // 2. Calculer la composante désaisonnalisée (valeur / tendance)
    const detrended = new Array(n);
    for (let i = 0; i < n; i++) {
      if (trend[i] !== null) {
        detrended[i] = values[i] / trend[i];
      } else {
        detrended[i] = null;
      }
    }
    
    // 3. Calculer les indices saisonniers moyens
    const seasonal = new Array(n).fill(1);
    const seasonalIndices = new Array(period).fill(0);
    const seasonalCounts = new Array(period).fill(0);
    
    // Calculer les moyennes par position dans la période
    for (let i = 0; i < n; i++) {
      const pos = i % period;
      if (detrended[i] !== null) {
        seasonalIndices[pos] += detrended[i];
        seasonalCounts[pos]++;
      }
    }
    
    // Calculer les indices saisonniers moyens
    for (let i = 0; i < period; i++) {
      if (seasonalCounts[i] > 0) {
        seasonalIndices[i] /= seasonalCounts[i];
      }
    }
    
    // Normaliser les indices saisonniers
    const sum = seasonalIndices.reduce((a, b) => a + b, 0);
    const scaleFactor = period / sum;
    
    for (let i = 0; i < period; i++) {
      seasonalIndices[i] *= scaleFactor;
    }
    
    // Appliquer les indices saisonniers
    for (let i = 0; i < n; i++) {
      seasonal[i] = seasonalIndices[i % period];
    }
    
    // 4. Calculer les résidus
    const residuals = new Array(n);
    for (let i = 0; i < n; i++) {
      if (trend[i] !== null) {
        residuals[i] = values[i] / (trend[i] * seasonal[i]);
      } else {
        residuals[i] = null;
      }
    }
    
    return {
      period,
      trend,
      seasonal,
      seasonalIndices,
      residuals
    };
  }
  
  /**
   * Initialise un modèle de détection d'anomalies
   * @private
   * @param {Array} data - Données historiques
   * @returns {Object} - Modèle de détection d'anomalies
   */
  _initAnomalyDetectionModel(data) {
    const model = {
      type: 'anomalyDetection',
      methods: {}
    };
    
    // 1. Méthode Z-score
    model.methods.zscore = this._initZScoreMethod(data);
    
    // 2. Méthode de détection basée sur les résidus de la décomposition
    model.methods.decompositionResiduals = this._initDecompositionResidualMethod(data);
    
    return model;
  }
  
  /**
   * Initialise la méthode Z-score pour la détection d'anomalies
   * @private
   * @param {Array} data - Données historiques
   * @returns {Object} - Méthode Z-score
   */
  _initZScoreMethod(data) {
    // Extraire les valeurs
    const values = data.map(d => d.value);
    
    // Calculer la moyenne et l'écart-type
    const mean = stats.mean(values);
    const stdDev = stats.standardDeviation(values);
    
    // Calculer les Z-scores
    const zScores = values.map(value => (value - mean) / stdDev);
    
    // Détecter les anomalies
    const threshold = this.config.anomalyDetectionThreshold;
    const anomalies = [];
    
    for (let i = 0; i < data.length; i++) {
      if (Math.abs(zScores[i]) > threshold) {
        anomalies.push({
          date: data[i].date,
          value: data[i].value,
          zScore: zScores[i],
          isAnomaly: true
        });
      }
    }
    
    return {
      mean,
      stdDev,
      threshold,
      anomalies
    };
  }
  
  /**
   * Initialise la méthode de détection basée sur les résidus
   * @private
   * @param {Array} data - Données historiques
   * @returns {Object} - Méthode des résidus
   */
  _initDecompositionResidualMethod(data) {
    // Utiliser le modèle de décomposition hebdomadaire
    const decomp = this._decomposeTimeSeries(data, this.config.seasonalityPeriods.weekly);
    
    // Filtrer les résidus non-null
    const validResiduals = decomp.residuals.filter(r => r !== null);
    
    // Calculer les statistiques des résidus
    const mean = stats.mean(validResiduals);
    const stdDev = stats.standardDeviation(validResiduals);
    
    // Détecter les anomalies
    const threshold = this.config.anomalyDetectionThreshold;
    const anomalies = [];
    
    for (let i = 0; i < data.length; i++) {
      if (decomp.residuals[i] !== null) {
        const zScore = (decomp.residuals[i] - mean) / stdDev;
        
        if (Math.abs(zScore) > threshold) {
          anomalies.push({
            date: data[i].date,
            value: data[i].value,
            residual: decomp.residuals[i],
            zScore,
            isAnomaly: true
          });
        }
      }
    }
    
    return {
      mean,
      stdDev,
      threshold,
      anomalies
    };
  }
  
  /**
   * Évalue les performances des différents modèles
   * @private
   * @param {Array} data - Données historiques
   * @param {Object} models - Modèles à évaluer
   * @returns {Object} - Performances des modèles
   */
  _evaluateModels(data, models) {
    const performance = {};
    const values = data.map(d => d.value);
    
    // Diviser les données en ensembles d'entraînement et de test (validation)
    const trainSize = Math.floor(data.length * 0.8);
    const trainData = values.slice(0, trainSize);
    const testData = values.slice(trainSize);
    
    // Évaluer le modèle de moyenne mobile
    performance.movingAverage = {};
    for (const window in models.movingAverage.windows) {
      const maValues = models.movingAverage.windows[window].values;
      
      // Ne prendre que les prévisions correspondant aux données de test
      const forecastValues = maValues.slice(-(testData.length));
      
      // Calculer les erreurs
      const errors = testData.map((actual, i) => actual - forecastValues[i]);
      
      // Métriques d'erreur
      const mse = stats.sum(errors.map(e => e * e)) / errors.length;
      const mae = stats.sum(errors.map(e => Math.abs(e))) / errors.length;
      const mape = stats.sum(errors.map((e, i) => Math.abs(e) / Math.abs(testData[i]))) / errors.length * 100;
      
      performance.movingAverage[window] = { mse, mae, mape };
    }
    
    // Évaluer le modèle de lissage exponentiel
    performance.exponentialSmoothing = {};
    for (const variant in models.exponentialSmoothing.variants) {
      const fitted = models.exponentialSmoothing.variants[variant].fitted;
      
      // Ne prendre que les prévisions correspondant aux données de test
      const forecastValues = fitted.slice(-(testData.length));
      
      // Calculer les erreurs
      const errors = testData.map((actual, i) => actual - forecastValues[i]);
      
      // Métriques d'erreur
      const mse = stats.sum(errors.map(e => e * e)) / errors.length;
      const mae = stats.sum(errors.map(e => Math.abs(e))) / errors.length;
      const mape = stats.sum(errors.map((e, i) => Math.abs(e) / Math.abs(testData[i]))) / errors.length * 100;
      
      performance.exponentialSmoothing[variant] = { mse, mae, mape };
    }
    
    // Évaluer le modèle de décomposition
    performance.decomposition = {};
    for (const period of ['weekly', 'monthly']) {
      const decomp = models.decomposition[period];
      
      // Reconstruire les valeurs (tendance * saisonnalité)
      const fitted = decomp.trend.map((t, i) => 
        t !== null ? t * decomp.seasonal[i] : null
      );
      
      // Ne prendre que les prévisions correspondant aux données de test
      const validFitted = fitted.filter(f => f !== null);
      const forecastValues = validFitted.slice(-(testData.length));
      
      // Vérifier qu'il y a suffisamment de prévisions
      if (forecastValues.length === testData.length) {
        // Calculer les erreurs
        const errors = testData.map((actual, i) => actual - forecastValues[i]);
        
        // Métriques d'erreur
        const mse = stats.sum(errors.map(e => e * e)) / errors.length;
        const mae = stats.sum(errors.map(e => Math.abs(e))) / errors.length;
        const mape = stats.sum(errors.map((e, i) => Math.abs(e) / Math.abs(testData[i]))) / errors.length * 100;
        
        performance.decomposition[period] = { mse, mae, mape };
      } else {
        performance.decomposition[period] = { mse: Infinity, mae: Infinity, mape: Infinity };
      }
    }
    
    return performance;
  }
  
  /**
   * Sélectionne le meilleur modèle en fonction des performances
   * @private
   * @param {Object} modelPerformance - Performances des modèles
   * @returns {Object} - Information sur le meilleur modèle
   */
  _selectBestModel(modelPerformance) {
    let bestModel = null;
    let bestType = null;
    let bestMSE = Infinity;
    
    // Parcourir les types de modèles
    for (const modelType in modelPerformance) {
      // Parcourir les variantes du modèle
      for (const variant in modelPerformance[modelType]) {
        const mse = modelPerformance[modelType][variant].mse;
        
        if (mse < bestMSE) {
          bestMSE = mse;
          bestType = modelType;
          bestModel = variant;
        }
      }
    }
    
    return {
      type: bestType,
      variant: bestModel,
      mse: bestMSE
    };
  }
  
  /**
   * Génère des prévisions financières
   * @param {Object} options - Options de prévision
   * @param {number} options.horizon - Horizon de prévision en jours
   * @param {Array} options.metrics - Métriques à prévoir
   * @returns {Promise<Object>} - Prévisions financières
   */
  async generateForecasts(options = {}) {
    try {
      const horizon = options.horizon || this.config.forecastHorizon;
      const metrics = options.metrics || ['revenue', 'costs', 'margins', 'cashflow'];
      
      this.logger.info('Génération des prévisions financières', { horizon, metrics });
      
      const forecasts = {};
      
      // Pour chaque métrique demandée
      for (const metric of metrics) {
        if (this.models[metric]) {
          forecasts[metric] = await this._generateMetricForecast(metric, horizon);
        }
      }
      
      // Mettre à jour les dernières prévisions
      this.lastForecasts = forecasts;
      
      // Émettre un événement
      this.emit('forecast:updated', { forecasts });
      
      return forecasts;
    } catch (error) {
      this.logger.error('Erreur lors de la génération des prévisions', error);
      this.emit('ml:error', { type: 'forecast', error });
      throw error;
    }
  }
  
  /**
   * Génère une prévision pour une métrique spécifique
   * @private
   * @param {string} metric - Métrique à prévoir
   * @param {number} horizon - Horizon de prévision en jours
   * @returns {Promise<Object>} - Prévision pour la métrique
   */
  async _generateMetricForecast(metric, horizon) {
    try {
      const model = this.models[metric];
      const bestModelInfo = model.bestModel;
      
      // Données historiques récentes pour la prévision
      const lastData = model.lastTrainingData.slice(-30).map(d => d.value);
      
      // Générer la prévision selon le meilleur modèle
      let forecast;
      let confidenceBounds;
      
      switch (bestModelInfo.type) {
        case 'movingAverage':
          forecast = this._generateMovingAverageForecast(
            model.models.movingAverage, 
            lastData, 
            parseInt(bestModelInfo.variant), 
            horizon
          );
          break;
        
        case 'exponentialSmoothing':
          const variant = model.models.exponentialSmoothing.variants[bestModelInfo.variant];
          forecast = this._generateExponentialSmoothingForecast(
            variant, 
            lastData, 
            horizon
          );
          break;
        
        case 'decomposition':
          forecast = this._generateDecompositionForecast(
            model.models.decomposition[bestModelInfo.variant], 
            lastData, 
            horizon
          );
          break;
        
        default:
          // Fallback: moyenne mobile simple
          forecast = this._generateMovingAverageForecast(
            model.models.movingAverage, 
            lastData, 
            7, 
            horizon
          );
      }
      
      // Calculer les intervalles de confiance
      confidenceBounds = this._calculateConfidenceBounds(
        forecast, 
        model.modelPerformance[bestModelInfo.type][bestModelInfo.variant].mse,
        this.config.confidenceInterval
      );
      
      // Créer les dates pour les prévisions
      const forecastDates = [];
      const today = moment().startOf('day');
      
      for (let i = 1; i <= horizon; i++) {
        forecastDates.push(moment(today).add(i, 'days').toDate());
      }
      
      // Construire la prévision finale
      return {
        metric,
        horizon,
        dates: forecastDates,
        values: forecast,
        lowerBound: confidenceBounds.lower,
        upperBound: confidenceBounds.upper,
        model: bestModelInfo.type,
        variant: bestModelInfo.variant,
        confidence: this.config.confidenceInterval,
        generatedAt: new Date()
      };
    } catch (error) {
      this.logger.error(`Erreur lors de la génération de la prévision pour ${metric}`, error);
      throw error;
    }
  }
  
  /**
   * Génère une prévision avec le modèle de moyenne mobile
   * @private
   * @param {Object} model - Modèle de moyenne mobile
   * @param {Array} data - Données récentes
   * @param {number} window - Taille de la fenêtre
   * @param {number} horizon - Horizon de prévision
   * @returns {Array} - Valeurs prévues
   */
  _generateMovingAverageForecast(model, data, window, horizon) {
    const forecast = [];
    const extendedData = [...data];
    
    // Pour chaque jour de l'horizon
    for (let i = 0; i < horizon; i++) {
      // Calculer la moyenne des 'window' dernières valeurs
      const sum = extendedData.slice(-window).reduce((a, b) => a + b, 0);
      const prediction = sum / window;
      
      // Ajouter à la prévision
      forecast.push(prediction);
      
      // Ajouter la prévision aux données pour la prévision suivante
      extendedData.push(prediction);
    }
    
    return forecast;
  }
  
  /**
   * Génère une prévision avec le modèle de lissage exponentiel
   * @private
   * @param {Object} variant - Variante du modèle
   * @param {Array} data - Données récentes
   * @param {number} horizon - Horizon de prévision
   * @returns {Array} - Valeurs prévues
   */
  _generateExponentialSmoothingForecast(variant, data, horizon) {
    const forecast = [];
    
    // Paramètres du modèle
    const alpha = variant.alpha;
    const beta = variant.beta;
    const gamma = variant.gamma;
    
    // Valeurs finales du modèle
    const lastLevel = variant.level[variant.level.length - 1];
    const lastTrend = variant.trend[variant.trend.length - 1];
    const seasonal = variant.seasonal;
    const period = seasonal.length;
    
    // Pour chaque jour de l'horizon
    for (let i = 0; i < horizon; i++) {
      const seasonalIndex = seasonal[(data.length + i) % period];
      const prediction = (lastLevel + (i + 1) * lastTrend) * seasonalIndex;
      
      // Ajouter à la prévision
      forecast.push(prediction);
    }
    
    return forecast;
  }
  
  /**
   * Génère une prévision avec le modèle de décomposition
   * @private
   * @param {Object} decomp - Modèle de décomposition
   * @param {Array} data - Données récentes
   * @param {number} horizon - Horizon de prévision
   * @returns {Array} - Valeurs prévues
   */
  _generateDecompositionForecast(decomp, data, horizon) {
    const forecast = [];
    const period = decomp.period;
    
    // Estimer la tendance future (régression linéaire simple)
    const trendValues = decomp.trend.filter(t => t !== null);
    const n = trendValues.length;
    
    let sumX = 0;
    let sumY = 0;
    let sumXY = 0;
    let sumX2 = 0;
    
    for (let i = 0; i < n; i++) {
      sumX += i;
      sumY += trendValues[i];
      sumXY += i * trendValues[i];
      sumX2 += i * i;
    }
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // Dernière valeur de la tendance
    const lastTrend = trendValues[n - 1];
    
    // Pour chaque jour de l'horizon
    for (let i = 0; i < horizon; i++) {
      // Extrapoler la tendance
      const futureTrend = lastTrend + slope * (i + 1);
      
      // Récupérer l'indice saisonnier
      const seasonalIndex = decomp.seasonalIndices[(data.length + i) % period];
      
      // Calculer la prévision
      const prediction = futureTrend * seasonalIndex;
      
      // Ajouter à la prévision
      forecast.push(prediction);
    }
    
    return forecast;
  }
  
  /**
   * Calcule les intervalles de confiance pour une prévision
   * @private
   * @param {Array} forecast - Prévision
   * @param {number} mse - Erreur quadratique moyenne du modèle
   * @param {number} confidenceLevel - Niveau de confiance (0-1)
   * @returns {Object} - Bornes inférieure et supérieure
   */
  _calculateConfidenceBounds(forecast, mse, confidenceLevel) {
    // Écart-type des erreurs
    const stdErr = Math.sqrt(mse);
    
    // Facteur Z pour l'intervalle de confiance
    const alpha = 1 - confidenceLevel;
    // Approximation du facteur Z
    let zFactor;
    
    if (confidenceLevel === 0.95) {
      zFactor = 1.96;
    } else if (confidenceLevel === 0.90) {
      zFactor = 1.645;
    } else if (confidenceLevel === 0.99) {
      zFactor = 2.576;
    } else {
      // Approximation pour d'autres niveaux de confiance
      zFactor = stats.quantileNormal(1 - alpha / 2);
    }
    
    // Calculer les bornes
    const lower = forecast.map(f => f - zFactor * stdErr);
    const upper = forecast.map(f => f + zFactor * stdErr);
    
    return { lower, upper };
  }
  
  /**
   * Détecte les anomalies dans les données récentes
   * @param {Object} options - Options de détection
   * @param {string} options.metric - Métrique à analyser
   * @param {number} options.days - Nombre de jours à analyser
   * @returns {Promise<Array>} - Anomalies détectées
   */
  async detectAnomalies(options = {}) {
    try {
      const metric = options.metric || 'revenue';
      const days = options.days || 30;
      
      this.logger.info(`Détection d'anomalies pour ${metric} sur ${days} jours`);
      
      if (!this.models[metric]) {
        throw new Error(`Modèle non disponible pour la métrique ${metric}`);
      }
      
      // Récupérer les données récentes
      const endDate = moment().startOf('day');
      const startDate = moment().subtract(days, 'days').startOf('day');
      
      const recentData = await this.dataCollector.getFinancialTimeSeries({
        startDate,
        endDate,
        metrics: [metric],
        granularity: 'day'
      });
      
      if (!recentData || !recentData[metric]) {
        throw new Error(`Données non disponibles pour la métrique ${metric}`);
      }
      
      // Utiliser le modèle de détection d'anomalies
      const anomalyModel = this.models[metric].models.anomalyDetection;
      
      // Appliquer la méthode Z-score
      const zScoreAnomalies = this._detectZScoreAnomalies(
        recentData[metric],
        anomalyModel.methods.zscore
      );
      
      // Émettre un événement pour les anomalies détectées
      if (zScoreAnomalies.length > 0) {
        this.emit('anomaly:detected', {
          metric,
          anomalies: zScoreAnomalies
        });
      }
      
      return zScoreAnomalies;
    } catch (error) {
      this.logger.error('Erreur lors de la détection d\'anomalies', error);
      this.emit('ml:error', { type: 'anomaly_detection', error });
      throw error;
    }
  }
  
  /**
   * Détecte les anomalies avec la méthode Z-score
   * @private
   * @param {Array} data - Données à analyser
   * @param {Object} model - Modèle Z-score
   * @returns {Array} - Anomalies détectées
   */
  _detectZScoreAnomalies(data, model) {
    const anomalies = [];
    
    // Extraire les valeurs
    const values = data.map(d => d.value);
    
    // Calculer les Z-scores
    const zScores = values.map(value => (value - model.mean) / model.stdDev);
    
    // Détecter les anomalies
    for (let i = 0; i < data.length; i++) {
      if (Math.abs(zScores[i]) > model.threshold) {
        anomalies.push({
          date: data[i].date,
          value: data[i].value,
          zScore: zScores[i],
          severity: this._calculateAnomalySeverity(Math.abs(zScores[i])),
          expected: model.mean,
          deviation: Math.abs(data[i].value - model.mean),
          deviationPercentage: Math.abs((data[i].value - model.mean) / model.mean) * 100
        });
      }
    }
    
    return anomalies;
  }
  
  /**
   * Calcule la sévérité d'une anomalie
   * @private
   * @param {number} absZScore - Valeur absolue du Z-score
   * @returns {string} - Niveau de sévérité
   */
  _calculateAnomalySeverity(absZScore) {
    if (absZScore > 5) {
      return 'critical';
    } else if (absZScore > 4) {
      return 'high';
    } else if (absZScore > 3) {
      return 'medium';
    } else {
      return 'low';
    }
  }
}

module.exports = MLForecasting;
