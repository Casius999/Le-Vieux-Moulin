/**
 * Module de tableau de bord financier pour Le Vieux Moulin
 * Ce module fournit les fonctionnalités pour générer et afficher des tableaux de bord
 * financiers en temps réel à partir des données consolidées des différents modules.
 */

'use strict';

const moment = require('moment');
const _ = require('lodash');
const { EventEmitter } = require('events');

// Importation des modules internes
const { DataCollector } = require('../common/data_collector');
const { SecurityUtils } = require('../common/security_utils');
const { ConfigManager } = require('../common/config_manager');
const { AlertService } = require('../common/alert_service');

/**
 * Classe principale gérant les tableaux de bord financiers
 */
class FinancialDashboard extends EventEmitter {
  /**
   * Crée une nouvelle instance de tableau de bord financier
   * @param {Object} options Options de configuration
   * @param {Object} options.dataSourceConfig Configuration des sources de données
   * @param {Object} options.dashboardConfig Configuration des tableaux de bord
   * @param {Object} options.refreshConfig Configuration des fréquences de rafraîchissement
   * @param {Object} options.alertConfig Configuration des alertes et notifications
   */
  constructor(options = {}) {
    super();
    
    this.dataSourceConfig = options.dataSourceConfig || {};
    this.dashboardConfig = options.dashboardConfig || {};
    this.refreshConfig = options.refreshConfig || { interval: 15 * 60 * 1000 }; // 15 minutes par défaut
    this.alertConfig = options.alertConfig || {};
    
    this.dataCollector = new DataCollector(this.dataSourceConfig);
    this.alertService = new AlertService(this.alertConfig);
    
    this.dashboards = {};
    this.cachedData = {};
    this.refreshTimers = {};
    
    this._initializeDashboards();
  }
  
  /**
   * Initialise tous les tableaux de bord configurés
   * @private
   */
  _initializeDashboards() {
    if (!this.dashboardConfig.dashboards || !Array.isArray(this.dashboardConfig.dashboards)) {
      console.warn('Aucun tableau de bord configuré');
      return;
    }
    
    for (const dashConfig of this.dashboardConfig.dashboards) {
      if (!dashConfig.id || !dashConfig.kpis || !Array.isArray(dashConfig.kpis)) {
        console.warn(`Configuration de tableau de bord invalide: ${JSON.stringify(dashConfig)}`);
        continue;
      }
      
      this.dashboards[dashConfig.id] = {
        config: dashConfig,
        data: {},
        lastUpdated: null
      };
      
      // Configurer le rafraîchissement automatique si activé
      if (dashConfig.autoRefresh !== false) {
        const interval = dashConfig.refreshInterval || this.refreshConfig.interval;
        this.refreshTimers[dashConfig.id] = setInterval(() => {
          this.refreshDashboard(dashConfig.id).catch(err => {
            console.error(`Erreur lors du rafraîchissement du tableau de bord ${dashConfig.id}:`, err);
          });
        }, interval);
      }
    }
  }
  
  /**
   * Rafraîchit les données d'un tableau de bord spécifique
   * @param {string} dashboardId Identifiant du tableau de bord à rafraîchir
   * @returns {Promise<Object>} Les données mises à jour du tableau de bord
   */
  async refreshDashboard(dashboardId) {
    const dashboard = this.dashboards[dashboardId];
    if (!dashboard) {
      throw new Error(`Tableau de bord non trouvé: ${dashboardId}`);
    }
    
    const kpiPromises = dashboard.config.kpis.map(kpiId => this._fetchKpiData(kpiId));
    const kpiResults = await Promise.all(kpiPromises);
    
    // Organiser les résultats par KPI
    const dashboardData = {};
    kpiResults.forEach((kpiData, index) => {
      const kpiId = dashboard.config.kpis[index];
      dashboardData[kpiId] = kpiData;
    });
    
    // Mettre à jour les données en cache
    dashboard.data = dashboardData;
    dashboard.lastUpdated = new Date();
    
    // Vérifier les conditions d'alerte
    this._checkAlertConditions(dashboardId, dashboardData);
    
    // Émettre un événement de mise à jour
    this.emit('dashboard:updated', { dashboardId, data: dashboardData });
    
    return dashboardData;
  }
  
  /**
   * Récupère les données pour un KPI spécifique
   * @param {string} kpiId Identifiant du KPI
   * @returns {Promise<Object>} Données du KPI
   * @private
   */
  async _fetchKpiData(kpiId) {
    const kpiConfig = this.dashboardConfig.kpis.find(k => k.id === kpiId);
    if (!kpiConfig) {
      throw new Error(`Configuration de KPI non trouvée: ${kpiId}`);
    }
    
    // Récupérer les données brutes en fonction du type de KPI
    let rawData;
    
    try {
      switch (kpiConfig.type) {
        case 'sales':
          rawData = await this.dataCollector.getSalesData(kpiConfig.parameters);
          break;
        case 'expenses':
          rawData = await this.dataCollector.getExpensesData(kpiConfig.parameters);
          break;
        case 'profit':
          rawData = await this.dataCollector.getProfitData(kpiConfig.parameters);
          break;
        case 'inventory':
          rawData = await this.dataCollector.getInventoryData(kpiConfig.parameters);
          break;
        case 'custom':
          if (kpiConfig.dataFetcher && typeof kpiConfig.dataFetcher === 'function') {
            rawData = await kpiConfig.dataFetcher(this.dataCollector, kpiConfig.parameters);
          } else {
            throw new Error(`Fetcher personnalisé non défini pour le KPI ${kpiId}`);
          }
          break;
        default:
          throw new Error(`Type de KPI non pris en charge: ${kpiConfig.type}`);
      }
    } catch (error) {
      console.error(`Erreur lors de la récupération des données pour le KPI ${kpiId}:`, error);
      return {
        error: true,
        message: error.message,
        timestamp: new Date()
      };
    }
    
    // Traiter et formater les données
    const processedData = this._processKpiData(rawData, kpiConfig);
    
    return {
      id: kpiId,
      name: kpiConfig.name,
      value: processedData.value,
      formattedValue: this._formatKpiValue(processedData.value, kpiConfig.format),
      trend: processedData.trend,
      comparisonValue: processedData.comparisonValue,
      comparisonLabel: processedData.comparisonLabel,
      status: this._getKpiStatus(processedData.value, kpiConfig.thresholds),
      metadata: processedData.metadata,
      timestamp: new Date()
    };
  }
  
  /**
   * Traite les données brutes pour un KPI selon sa configuration
   * @param {Object} rawData Données brutes du KPI
   * @param {Object} kpiConfig Configuration du KPI
   * @returns {Object} Données traitées
   * @private
   */
  _processKpiData(rawData, kpiConfig) {
    let value, trend = 0, comparisonValue, comparisonLabel, metadata = {};
    
    // Extraire la valeur principale selon la configuration
    if (kpiConfig.valueExtractor && typeof kpiConfig.valueExtractor === 'function') {
      value = kpiConfig.valueExtractor(rawData);
    } else if (kpiConfig.valuePath) {
      value = _.get(rawData, kpiConfig.valuePath);
    } else {
      // Valeur par défaut ou calcul simple
      value = rawData.value || 0;
    }
    
    // Calculer les tendances et comparaisons si configurées
    if (kpiConfig.comparison) {
      const comparison = kpiConfig.comparison;
      
      if (comparison.type === 'previous_period') {
        comparisonValue = rawData.previousPeriod || 0;
        comparisonLabel = comparison.label || 'vs période précédente';
        
        if (comparisonValue !== 0) {
          trend = ((value - comparisonValue) / Math.abs(comparisonValue)) * 100;
        }
      } else if (comparison.type === 'target') {
        comparisonValue = comparison.targetValue || 0;
        comparisonLabel = comparison.label || 'vs objectif';
        
        if (comparisonValue !== 0) {
          trend = ((value - comparisonValue) / Math.abs(comparisonValue)) * 100;
        }
      } else if (comparison.type === 'custom' && comparison.calculator && typeof comparison.calculator === 'function') {
        const result = comparison.calculator(value, rawData);
        trend = result.trend;
        comparisonValue = result.comparisonValue;
        comparisonLabel = result.label || 'Comparaison personnalisée';
      }
    }
    
    // Extraire les métadonnées supplémentaires si configurées
    if (kpiConfig.metadataExtractor && typeof kpiConfig.metadataExtractor === 'function') {
      metadata = kpiConfig.metadataExtractor(rawData);
    } else if (kpiConfig.metadataPaths && typeof kpiConfig.metadataPaths === 'object') {
      for (const [key, path] of Object.entries(kpiConfig.metadataPaths)) {
        metadata[key] = _.get(rawData, path);
      }
    }
    
    return {
      value,
      trend,
      comparisonValue,
      comparisonLabel,
      metadata
    };
  }
  
  /**
   * Formate la valeur d'un KPI selon le format spécifié
   * @param {*} value Valeur à formater
   * @param {string} format Format à appliquer
   * @returns {string} Valeur formatée
   * @private
   */
  _formatKpiValue(value, format) {
    if (value === undefined || value === null) {
      return 'N/A';
    }
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
      case 'percentage':
        return new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value / 100);
      case 'number':
        return new Intl.NumberFormat('fr-FR').format(value);
      case 'decimal':
        return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
      case 'integer':
        return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(value);
      case 'date':
        return moment(value).format('DD/MM/YYYY');
      case 'datetime':
        return moment(value).format('DD/MM/YYYY HH:mm');
      case 'time':
        return moment(value).format('HH:mm:ss');
      case 'duration':
        return moment.duration(value, 'seconds').humanize();
      default:
        return String(value);
    }
  }
  
  /**
   * Détermine le statut d'un KPI en fonction des seuils configurés
   * @param {*} value Valeur du KPI
   * @param {Object} thresholds Configuration des seuils
   * @returns {string} Statut du KPI ('success', 'warning', 'danger', 'info')
   * @private
   */
  _getKpiStatus(value, thresholds = {}) {
    if (!thresholds || typeof thresholds !== 'object') {
      return 'info';
    }
    
    if (thresholds.type === 'range') {
      if (thresholds.danger && 
          ((thresholds.direction === 'below' && value <= thresholds.danger) ||
           (thresholds.direction !== 'below' && value >= thresholds.danger))) {
        return 'danger';
      }
      
      if (thresholds.warning && 
          ((thresholds.direction === 'below' && value <= thresholds.warning) ||
           (thresholds.direction !== 'below' && value >= thresholds.warning))) {
        return 'warning';
      }
      
      if (thresholds.success && 
          ((thresholds.direction === 'below' && value <= thresholds.success) ||
           (thresholds.direction !== 'below' && value >= thresholds.success))) {
        return 'success';
      }
    } else if (thresholds.type === 'threshold') {
      if (thresholds.target) {
        const diff = Math.abs(value - thresholds.target);
        const percentDiff = thresholds.target !== 0 ? (diff / Math.abs(thresholds.target)) * 100 : 0;
        
        if (thresholds.dangerThreshold && percentDiff >= thresholds.dangerThreshold) {
          return 'danger';
        }
        
        if (thresholds.warningThreshold && percentDiff >= thresholds.warningThreshold) {
          return 'warning';
        }
        
        return 'success';
      }
    } else if (thresholds.type === 'custom' && thresholds.evaluator && typeof thresholds.evaluator === 'function') {
      return thresholds.evaluator(value);
    }
    
    return 'info';
  }
  
  /**
   * Vérifie les conditions d'alerte pour un tableau de bord
   * @param {string} dashboardId Identifiant du tableau de bord
   * @param {Object} dashboardData Données du tableau de bord
   * @private
   */
  _checkAlertConditions(dashboardId, dashboardData) {
    const dashboard = this.dashboards[dashboardId];
    if (!dashboard || !dashboard.config.alerts || !Array.isArray(dashboard.config.alerts)) {
      return;
    }
    
    for (const alertConfig of dashboard.config.alerts) {
      if (!alertConfig.id || !alertConfig.condition) {
        continue;
      }
      
      try {
        // Évaluer la condition d'alerte
        let isTriggered = false;
        
        if (typeof alertConfig.condition === 'function') {
          isTriggered = alertConfig.condition(dashboardData);
        } else if (typeof alertConfig.condition === 'string') {
          // Simple évaluation d'expression (à utiliser avec précaution)
          const conditionFn = new Function('data', `return ${alertConfig.condition};`);
          isTriggered = conditionFn(dashboardData);
        }
        
        if (isTriggered) {
          // Construire le message d'alerte
          const message = typeof alertConfig.message === 'function'
            ? alertConfig.message(dashboardData)
            : alertConfig.message || `Alerte déclenchée: ${alertConfig.id}`;
          
          // Envoyer l'alerte
          this.alertService.sendAlert({
            id: alertConfig.id,
            level: alertConfig.level || 'warning',
            message,
            source: `dashboard:${dashboardId}`,
            timestamp: new Date(),
            data: alertConfig.includeData ? dashboardData : undefined,
            recipients: alertConfig.recipients
          });
          
          // Émettre un événement d'alerte
          this.emit('alert:triggered', {
            alertId: alertConfig.id,
            dashboardId,
            level: alertConfig.level || 'warning',
            message,
            timestamp: new Date()
          });
        }
      } catch (error) {
        console.error(`Erreur lors de l'évaluation de l'alerte ${alertConfig.id}:`, error);
      }
    }
  }
  
  /**
   * Récupère les données d'un tableau de bord spécifique
   * @param {string} dashboardId Identifiant du tableau de bord
   * @returns {Object} Données du tableau de bord
   */
  getDashboardData(dashboardId) {
    const dashboard = this.dashboards[dashboardId];
    if (!dashboard) {
      throw new Error(`Tableau de bord non trouvé: ${dashboardId}`);
    }
    
    return {
      id: dashboardId,
      name: dashboard.config.name || dashboardId,
      data: dashboard.data,
      lastUpdated: dashboard.lastUpdated,
      config: {
        layout: dashboard.config.layout,
        refreshInterval: dashboard.config.refreshInterval || this.refreshConfig.interval,
        autoRefresh: dashboard.config.autoRefresh
      }
    };
  }
  
  /**
   * Récupère la liste de tous les tableaux de bord disponibles
   * @returns {Array<Object>} Liste des tableaux de bord
   */
  getAllDashboards() {
    return Object.keys(this.dashboards).map(id => ({
      id,
      name: this.dashboards[id].config.name || id,
      description: this.dashboards[id].config.description,
      lastUpdated: this.dashboards[id].lastUpdated
    }));
  }
  
  /**
   * Définit ou met à jour la configuration d'un tableau de bord
   * @param {string} dashboardId Identifiant du tableau de bord
   * @param {Object} config Nouvelle configuration
   */
  updateDashboardConfig(dashboardId, config) {
    // Vérifier si le tableau de bord existe déjà
    if (this.dashboards[dashboardId]) {
      // Arrêter le timer de rafraîchissement existant
      if (this.refreshTimers[dashboardId]) {
        clearInterval(this.refreshTimers[dashboardId]);
        delete this.refreshTimers[dashboardId];
      }
      
      // Mettre à jour la configuration
      this.dashboards[dashboardId].config = {
        ...this.dashboards[dashboardId].config,
        ...config
      };
    } else {
      // Créer un nouveau tableau de bord
      this.dashboards[dashboardId] = {
        config,
        data: {},
        lastUpdated: null
      };
    }
    
    // Configurer le rafraîchissement automatique si activé
    if (config.autoRefresh !== false) {
      const interval = config.refreshInterval || this.refreshConfig.interval;
      this.refreshTimers[dashboardId] = setInterval(() => {
        this.refreshDashboard(dashboardId).catch(err => {
          console.error(`Erreur lors du rafraîchissement du tableau de bord ${dashboardId}:`, err);
        });
      }, interval);
    }
    
    // Émettre un événement de mise à jour de configuration
    this.emit('dashboard:configUpdated', {
      dashboardId,
      config: this.dashboards[dashboardId].config
    });
    
    return this.dashboards[dashboardId].config;
  }
  
  /**
   * Supprime un tableau de bord
   * @param {string} dashboardId Identifiant du tableau de bord à supprimer
   */
  removeDashboard(dashboardId) {
    if (!this.dashboards[dashboardId]) {
      throw new Error(`Tableau de bord non trouvé: ${dashboardId}`);
    }
    
    // Arrêter le timer de rafraîchissement
    if (this.refreshTimers[dashboardId]) {
      clearInterval(this.refreshTimers[dashboardId]);
      delete this.refreshTimers[dashboardId];
    }
    
    // Supprimer le tableau de bord
    delete this.dashboards[dashboardId];
    
    // Émettre un événement de suppression
    this.emit('dashboard:removed', { dashboardId });
  }
  
  /**
   * Nettoie les ressources utilisées (timers, connexions, etc.)
   */
  dispose() {
    // Arrêter tous les timers de rafraîchissement
    for (const [dashboardId, timer] of Object.entries(this.refreshTimers)) {
      clearInterval(timer);
    }
    
    this.refreshTimers = {};
    this.removeAllListeners();
    
    // Libérer les autres ressources
    if (this.dataCollector && typeof this.dataCollector.dispose === 'function') {
      this.dataCollector.dispose();
    }
    
    if (this.alertService && typeof this.alertService.dispose === 'function') {
      this.alertService.dispose();
    }
  }
}

module.exports = {
  FinancialDashboard
};