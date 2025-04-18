/**
 * Module de consolidation des données financières
 * 
 * Ce module centralise la collecte, la consolidation et la validation 
 * des données financières provenant des différents modules du système.
 */

'use strict';

const { EventEmitter } = require('events');
const moment = require('moment');
const _ = require('lodash');

/**
 * Classe principale de consolidation des données
 */
class DataConsolidator extends EventEmitter {
  /**
   * Initialise le consolidateur de données
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataCollector - Collecteur de données principal
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.systemIntegrator - Intégrateur système
   */
  constructor(options = {}) {
    super();
    
    this.dataCollector = options.dataCollector;
    this.configManager = options.configManager;
    this.systemIntegrator = options.systemIntegrator;
    
    // Configurer les sources de données
    this.dataSources = this._configureSources();
    
    // Initialiser le cache local pour les données fréquemment utilisées
    this.cache = {
      salesSummary: {
        data: null,
        timestamp: null,
        validityPeriod: 15 * 60 * 1000 // 15 minutes en millisecondes
      },
      expensesSummary: {
        data: null, 
        timestamp: null,
        validityPeriod: 30 * 60 * 1000 // 30 minutes
      },
      inventoryValue: {
        data: null,
        timestamp: null,
        validityPeriod: 60 * 60 * 1000 // 1 heure
      }
    };
  }
  
  /**
   * Configure les sources de données
   * @returns {Object} - Configuration des sources de données
   * @private
   */
  _configureSources() {
    // Sources par défaut
    const sources = {
      sales: {
        module: 'pos',
        endpoint: '/api/transactions',
        dataProcessor: this._processSalesData.bind(this)
      },
      expenses: {
        module: 'purchasing',
        endpoint: '/api/expenses',
        dataProcessor: this._processExpensesData.bind(this)
      },
      inventory: {
        module: 'inventory',
        endpoint: '/api/inventory/current',
        dataProcessor: this._processInventoryData.bind(this)
      },
      staff: {
        module: 'hr',
        endpoint: '/api/staff/hours',
        dataProcessor: this._processStaffData.bind(this)
      },
      marketing: {
        module: 'marketing',
        endpoint: '/api/campaigns/expenses',
        dataProcessor: this._processMarketingData.bind(this)
      }
    };
    
    // Charger la configuration personnalisée si disponible
    if (this.configManager) {
      const customSources = this.configManager.getConfig('accounting.dataSources', {});
      
      // Fusionner avec les sources par défaut
      return _.merge({}, sources, customSources);
    }
    
    return sources;
  }
  
  /**
   * Récupère et consolide les données financières pour une période donnée
   * @param {Object} options - Options de consolidation
   * @param {Date|string} options.startDate - Date de début de la période
   * @param {Date|string} options.endDate - Date de fin de la période
   * @param {Array<string>} options.sources - Sources à inclure (toutes par défaut)
   * @param {boolean} options.forceRefresh - Forcer le rafraîchissement du cache
   * @returns {Promise<Object>} - Données financières consolidées
   */
  async consolidateFinancialData(options = {}) {
    const startDate = options.startDate ? moment(options.startDate) : moment().startOf('day');
    const endDate = options.endDate ? moment(options.endDate) : moment().endOf('day');
    const sources = options.sources || Object.keys(this.dataSources);
    const forceRefresh = options.forceRefresh || false;
    
    try {
      // Objet pour stocker les données consolidées
      const consolidatedData = {
        period: {
          start: startDate.toDate(),
          end: endDate.toDate(),
          durationDays: endDate.diff(startDate, 'days') + 1
        },
        sources: {},
        summary: {},
        metadata: {
          generatedAt: new Date(),
          dataQuality: {
            completeness: 0,
            consistency: 0,
            warnings: []
          }
        }
      };
      
      // Récupérer les données de chaque source
      for (const sourceName of sources) {
        if (!this.dataSources[sourceName]) {
          console.warn(`Source de données non configurée: ${sourceName}`);
          continue;
        }
        
        try {
          // Récupérer et traiter les données
          const sourceData = await this._fetchSourceData(sourceName, {
            startDate: startDate.format('YYYY-MM-DD'),
            endDate: endDate.format('YYYY-MM-DD'),
            forceRefresh
          });
          
          consolidatedData.sources[sourceName] = sourceData;
        } catch (error) {
          console.error(`Erreur lors de la récupération des données depuis ${sourceName}:`, error);
          
          consolidatedData.metadata.dataQuality.warnings.push({
            source: sourceName,
            error: error.message,
            impact: 'missing_data'
          });
        }
      }
      
      // Générer les récapitulatifs
      consolidatedData.summary = this._generateSummary(consolidatedData);
      
      // Évaluer la qualité des données
      this._evaluateDataQuality(consolidatedData);
      
      // Émettre un événement de consolidation terminée
      this.emit('data:consolidated', {
        period: consolidatedData.period,
        summary: consolidatedData.summary
      });
      
      return consolidatedData;
    } catch (error) {
      console.error('Erreur lors de la consolidation des données financières:', error);
      
      // Émettre un événement d'erreur
      this.emit('data:consolidation_error', {
        period: {
          start: startDate.toDate(),
          end: endDate.toDate()
        },
        error: error.message
      });
      
      throw error;
    }
  }
  
  /**
   * Récupère les données d'une source spécifique
   * @param {string} sourceName - Nom de la source
   * @param {Object} options - Options de récupération
   * @returns {Promise<Object>} - Données de la source
   * @private
   */
  async _fetchSourceData(sourceName, options = {}) {
    const source = this.dataSources[sourceName];
    const forceRefresh = options.forceRefresh || false;
    
    // Vérifier si les données sont en cache et valides
    if (!forceRefresh && this.cache[sourceName] && this.cache[sourceName].data) {
      const now = Date.now();
      const cacheAge = now - this.cache[sourceName].timestamp;
      
      if (cacheAge < this.cache[sourceName].validityPeriod) {
        return this.cache[sourceName].data;
      }
    }
    
    // Construire les paramètres de requête
    const queryParams = {
      startDate: options.startDate,
      endDate: options.endDate
    };
    
    // Récupérer les données via l'intégrateur système
    const rawData = await this.systemIntegrator.callModuleApi(
      source.module,
      source.endpoint,
      queryParams,
      { method: 'get' }
    );
    
    // Traiter les données avec le processeur spécifique à la source
    const processedData = source.dataProcessor(rawData, options);
    
    // Mettre en cache les données
    if (this.cache[sourceName]) {
      this.cache[sourceName].data = processedData;
      this.cache[sourceName].timestamp = Date.now();
    }
    
    return processedData;
  }
  
  /**
   * Traite les données de ventes
   * @param {Object} rawData - Données brutes
   * @param {Object} options - Options de traitement
   * @returns {Object} - Données traitées
   * @private
   */
  _processSalesData(rawData, options = {}) {
    // Exemple de traitement des données de ventes
    const processedData = {
      totalSales: 0,
      byCategory: {},
      byPaymentMethod: {},
      byService: {
        lunch: { total: 0, count: 0 },
        dinner: { total: 0, count: 0 }
      },
      averageTicket: 0,
      transactions: []
    };
    
    if (!rawData || !rawData.transactions || !Array.isArray(rawData.transactions)) {
      return processedData;
    }
    
    // Traiter chaque transaction
    rawData.transactions.forEach(transaction => {
      // Ajouter au total
      processedData.totalSales += transaction.total;
      
      // Ajouter à la catégorie
      const category = transaction.category || 'unknown';
      if (!processedData.byCategory[category]) {
        processedData.byCategory[category] = { total: 0, count: 0 };
      }
      processedData.byCategory[category].total += transaction.total;
      processedData.byCategory[category].count++;
      
      // Ajouter au mode de paiement
      const paymentMethod = transaction.paymentMethod || 'unknown';
      if (!processedData.byPaymentMethod[paymentMethod]) {
        processedData.byPaymentMethod[paymentMethod] = { total: 0, count: 0 };
      }
      processedData.byPaymentMethod[paymentMethod].total += transaction.total;
      processedData.byPaymentMethod[paymentMethod].count++;
      
      // Déterminer le service (déjeuner/dîner)
      const transactionTime = moment(transaction.timestamp);
      const service = transactionTime.hour() < 16 ? 'lunch' : 'dinner';
      processedData.byService[service].total += transaction.total;
      processedData.byService[service].count++;
      
      // Ajouter la transaction traitée
      processedData.transactions.push({
        id: transaction.id,
        timestamp: transaction.timestamp,
        total: transaction.total,
        items: transaction.items.length,
        service,
        paymentMethod,
        category
      });
    });
    
    // Calculer le ticket moyen
    const totalTransactions = processedData.transactions.length;
    processedData.averageTicket = totalTransactions > 0 ? 
      processedData.totalSales / totalTransactions : 0;
    
    return processedData;
  }
  
  /**
   * Traite les données de dépenses
   * @param {Object} rawData - Données brutes
   * @param {Object} options - Options de traitement
   * @returns {Object} - Données traitées
   * @private
   */
  _processExpensesData(rawData, options = {}) {
    // Exemple de traitement des données de dépenses
    const processedData = {
      totalExpenses: 0,
      byCategory: {},
      byVendor: {},
      fixedCosts: 0,
      variableCosts: 0,
      expenses: []
    };
    
    if (!rawData || !rawData.expenses || !Array.isArray(rawData.expenses)) {
      return processedData;
    }
    
    // Traiter chaque dépense
    rawData.expenses.forEach(expense => {
      // Ajouter au total
      processedData.totalExpenses += expense.amount;
      
      // Ajouter à la catégorie
      const category = expense.category || 'unknown';
      if (!processedData.byCategory[category]) {
        processedData.byCategory[category] = { total: 0, count: 0 };
      }
      processedData.byCategory[category].total += expense.amount;
      processedData.byCategory[category].count++;
      
      // Ajouter au fournisseur
      const vendor = expense.vendor || 'unknown';
      if (!processedData.byVendor[vendor]) {
        processedData.byVendor[vendor] = { total: 0, count: 0 };
      }
      processedData.byVendor[vendor].total += expense.amount;
      processedData.byVendor[vendor].count++;
      
      // Déterminer si c'est un coût fixe ou variable
      if (expense.costType === 'fixed') {
        processedData.fixedCosts += expense.amount;
      } else {
        processedData.variableCosts += expense.amount;
      }
      
      // Ajouter la dépense traitée
      processedData.expenses.push({
        id: expense.id,
        date: expense.date,
        amount: expense.amount,
        category,
        vendor,
        description: expense.description,
        costType: expense.costType
      });
    });
    
    return processedData;
  }
  
  /**
   * Traite les données d'inventaire
   * @param {Object} rawData - Données brutes
   * @param {Object} options - Options de traitement
   * @returns {Object} - Données traitées
   * @private
   */
  _processInventoryData(rawData, options = {}) {
    // Exemple de traitement des données d'inventaire
    const processedData = {
      totalValue: 0,
      byCategory: {},
      items: []
    };
    
    if (!rawData || !rawData.inventory || !Array.isArray(rawData.inventory)) {
      return processedData;
    }
    
    // Traiter chaque élément d'inventaire
    rawData.inventory.forEach(item => {
      const itemValue = item.quantity * item.unitCost;
      
      // Ajouter à la valeur totale
      processedData.totalValue += itemValue;
      
      // Ajouter à la catégorie
      const category = item.category || 'unknown';
      if (!processedData.byCategory[category]) {
        processedData.byCategory[category] = { total: 0, count: 0 };
      }
      processedData.byCategory[category].total += itemValue;
      processedData.byCategory[category].count++;
      
      // Ajouter l'élément traité
      processedData.items.push({
        id: item.id,
        name: item.name,
        quantity: item.quantity,
        unitCost: item.unitCost,
        totalValue: itemValue,
        category,
        expiryDate: item.expiryDate
      });
    });
    
    return processedData;
  }
  
  /**
   * Traite les données de personnel
   * @param {Object} rawData - Données brutes
   * @param {Object} options - Options de traitement
   * @returns {Object} - Données traitées
   * @private
   */
  _processStaffData(rawData, options = {}) {
    // Exemple de traitement des données de personnel
    const processedData = {
      totalHours: 0,
      totalCost: 0,
      byDepartment: {},
      byShift: {},
      employees: []
    };
    
    if (!rawData || !rawData.shifts || !Array.isArray(rawData.shifts)) {
      return processedData;
    }
    
    // Traiter chaque horaire
    rawData.shifts.forEach(shift => {
      const hours = shift.hours || 0;
      const hourlyRate = shift.hourlyRate || 0;
      const cost = hours * hourlyRate;
      
      // Ajouter au total
      processedData.totalHours += hours;
      processedData.totalCost += cost;
      
      // Ajouter au département
      const department = shift.department || 'unknown';
      if (!processedData.byDepartment[department]) {
        processedData.byDepartment[department] = { hours: 0, cost: 0 };
      }
      processedData.byDepartment[department].hours += hours;
      processedData.byDepartment[department].cost += cost;
      
      // Ajouter au service
      const shiftType = shift.shiftType || 'unknown';
      if (!processedData.byShift[shiftType]) {
        processedData.byShift[shiftType] = { hours: 0, cost: 0 };
      }
      processedData.byShift[shiftType].hours += hours;
      processedData.byShift[shiftType].cost += cost;
      
      // Ajouter l'employé traité
      const employeeId = shift.employeeId;
      const existingEmployee = processedData.employees.find(e => e.id === employeeId);
      
      if (existingEmployee) {
        existingEmployee.hours += hours;
        existingEmployee.cost += cost;
        existingEmployee.shifts.push({
          date: shift.date,
          hours,
          cost,
          shiftType
        });
      } else {
        processedData.employees.push({
          id: employeeId,
          name: shift.employeeName,
          department,
          hours,
          cost,
          shifts: [{
            date: shift.date,
            hours,
            cost,
            shiftType
          }]
        });
      }
    });
    
    return processedData;
  }
  
  /**
   * Traite les données de marketing
   * @param {Object} rawData - Données brutes
   * @param {Object} options - Options de traitement
   * @returns {Object} - Données traitées
   * @private
   */
  _processMarketingData(rawData, options = {}) {
    // Exemple de traitement des données de marketing
    const processedData = {
      totalExpenses: 0,
      byChannel: {},
      byCampaign: {},
      campaigns: []
    };
    
    if (!rawData || !rawData.campaigns || !Array.isArray(rawData.campaigns)) {
      return processedData;
    }
    
    // Traiter chaque campagne
    rawData.campaigns.forEach(campaign => {
      const expense = campaign.expense || 0;
      
      // Ajouter au total
      processedData.totalExpenses += expense;
      
      // Ajouter au canal
      const channel = campaign.channel || 'unknown';
      if (!processedData.byChannel[channel]) {
        processedData.byChannel[channel] = { total: 0, count: 0 };
      }
      processedData.byChannel[channel].total += expense;
      processedData.byChannel[channel].count++;
      
      // Ajouter à la campagne
      const campaignType = campaign.type || 'unknown';
      if (!processedData.byCampaign[campaignType]) {
        processedData.byCampaign[campaignType] = { total: 0, count: 0 };
      }
      processedData.byCampaign[campaignType].total += expense;
      processedData.byCampaign[campaignType].count++;
      
      // Ajouter la campagne traitée
      processedData.campaigns.push({
        id: campaign.id,
        name: campaign.name,
        startDate: campaign.startDate,
        endDate: campaign.endDate,
        expense,
        channel,
        type: campaignType,
        metrics: campaign.metrics || {}
      });
    });
    
    return processedData;
  }
  
  /**
   * Génère un résumé des données consolidées
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Résumé des données
   * @private
   */
  _generateSummary(consolidatedData) {
    const summary = {
      financials: {
        revenue: 0,
        expenses: 0,
        profit: 0,
        profitMargin: 0
      },
      kpis: {
        averageTicket: 0,
        laborCostPercentage: 0,
        foodCostPercentage: 0,
        inventoryTurnover: 0
      },
      trends: {
        salesGrowth: null,
        expenseGrowth: null,
        profitGrowth: null
      }
    };
    
    // Calculer les financials
    if (consolidatedData.sources.sales) {
      summary.financials.revenue = consolidatedData.sources.sales.totalSales;
    }
    
    if (consolidatedData.sources.expenses) {
      summary.financials.expenses = consolidatedData.sources.expenses.totalExpenses;
    }
    
    summary.financials.profit = summary.financials.revenue - summary.financials.expenses;
    summary.financials.profitMargin = summary.financials.revenue > 0 ? 
      (summary.financials.profit / summary.financials.revenue) * 100 : 0;
    
    // Calculer les KPIs
    if (consolidatedData.sources.sales) {
      summary.kpis.averageTicket = consolidatedData.sources.sales.averageTicket;
    }
    
    if (consolidatedData.sources.staff && summary.financials.revenue > 0) {
      summary.kpis.laborCostPercentage = 
        (consolidatedData.sources.staff.totalCost / summary.financials.revenue) * 100;
    }
    
    if (consolidatedData.sources.inventory && summary.financials.revenue > 0) {
      // Calculer le food cost à partir des données d'inventaire et de ventes
      // Exemple simplifié: supposons que 40% des dépenses d'inventaire sont liées à la nourriture
      const foodCost = consolidatedData.sources.inventory.totalValue * 0.4;
      summary.kpis.foodCostPercentage = (foodCost / summary.financials.revenue) * 100;
      
      // Calculer la rotation des stocks
      // Formule: Coût des marchandises vendues / Valeur moyenne des stocks
      const averageInventoryValue = consolidatedData.sources.inventory.totalValue;
      const costOfGoodsSold = summary.financials.expenses * 0.6; // Exemple simplifié: 60% des dépenses sont CoGS
      
      summary.kpis.inventoryTurnover = averageInventoryValue > 0 ? 
        costOfGoodsSold / averageInventoryValue : 0;
    }
    
    // Définir d'autres calculs complexes selon les besoins
    // ...
    
    return summary;
  }
  
  /**
   * Évalue la qualité des données consolidées
   * @param {Object} consolidatedData - Données consolidées
   * @private
   */
  _evaluateDataQuality(consolidatedData) {
    let completenessScore = 100;
    let consistencyScore = 100;
    
    // Vérifier la complétude des données
    const requiredSources = ['sales', 'expenses', 'inventory', 'staff'];
    
    for (const source of requiredSources) {
      if (!consolidatedData.sources[source]) {
        completenessScore -= 25; // Réduire de 25% par source manquante
        
        consolidatedData.metadata.dataQuality.warnings.push({
          type: 'missing_source',
          source,
          impact: 'high'
        });
      }
    }
    
    // Vérifier la cohérence des données
    // Exemple: Les ventes doivent être supérieures aux dépenses pour un restaurant rentable
    if (consolidatedData.sources.sales && consolidatedData.sources.expenses) {
      if (consolidatedData.sources.sales.totalSales < consolidatedData.sources.expenses.totalExpenses) {
        consistencyScore -= 30;
        
        consolidatedData.metadata.dataQuality.warnings.push({
          type: 'business_anomaly',
          description: 'Les dépenses sont supérieures aux ventes pour cette période',
          impact: 'high'
        });
      }
    }
    
    // Exemple: Le ticket moyen doit être dans des limites raisonnables
    if (consolidatedData.sources.sales && consolidatedData.sources.sales.averageTicket) {
      const averageTicket = consolidatedData.sources.sales.averageTicket;
      
      if (averageTicket < 5 || averageTicket > 500) {
        consistencyScore -= 20;
        
        consolidatedData.metadata.dataQuality.warnings.push({
          type: 'data_anomaly',
          description: `Ticket moyen anormal: ${averageTicket.toFixed(2)}€`,
          impact: 'medium'
        });
      }
    }
    
    // Mettre à jour les scores de qualité
    consolidatedData.metadata.dataQuality.completeness = Math.max(0, completenessScore);
    consolidatedData.metadata.dataQuality.consistency = Math.max(0, consistencyScore);
  }
  
  /**
   * Récupère les KPIs financiers actuels
   * @returns {Promise<Object>} - KPIs financiers
   */
  async getCurrentFinancialKPIs() {
    // Récupérer les données pour la journée en cours
    const today = moment().format('YYYY-MM-DD');
    
    const consolidatedData = await this.consolidateFinancialData({
      startDate: today,
      endDate: today
    });
    
    return {
      daily: consolidatedData.summary,
      mtd: await this._calculateMTDKPIs(),
      ytd: await this._calculateYTDKPIs()
    };
  }
  
  /**
   * Calcule les KPIs du mois en cours
   * @returns {Promise<Object>} - KPIs du mois
   * @private
   */
  async _calculateMTDKPIs() {
    const startOfMonth = moment().startOf('month').format('YYYY-MM-DD');
    const today = moment().format('YYYY-MM-DD');
    
    const consolidatedData = await this.consolidateFinancialData({
      startDate: startOfMonth,
      endDate: today
    });
    
    // Ajouter des projections pour la fin du mois
    const daysInMonth = moment().daysInMonth();
    const daysPassed = moment().date();
    const remainingDays = daysInMonth - daysPassed;
    
    const projectionMultiplier = daysInMonth / daysPassed;
    
    const mtdSummary = {
      ...consolidatedData.summary,
      projections: {
        revenue: consolidatedData.summary.financials.revenue * projectionMultiplier,
        expenses: consolidatedData.summary.financials.expenses * projectionMultiplier,
        profit: consolidatedData.summary.financials.profit * projectionMultiplier
      }
    };
    
    return mtdSummary;
  }
  
  /**
   * Calcule les KPIs de l'année en cours
   * @returns {Promise<Object>} - KPIs de l'année
   * @private
   */
  async _calculateYTDKPIs() {
    const startOfYear = moment().startOf('year').format('YYYY-MM-DD');
    const today = moment().format('YYYY-MM-DD');
    
    const consolidatedData = await this.consolidateFinancialData({
      startDate: startOfYear,
      endDate: today
    });
    
    // Ajouter des projections pour la fin de l'année
    const daysInYear = moment().isLeapYear() ? 366 : 365;
    const dayOfYear = moment().dayOfYear();
    const remainingDays = daysInYear - dayOfYear;
    
    const projectionMultiplier = daysInYear / dayOfYear;
    
    const ytdSummary = {
      ...consolidatedData.summary,
      projections: {
        revenue: consolidatedData.summary.financials.revenue * projectionMultiplier,
        expenses: consolidatedData.summary.financials.expenses * projectionMultiplier,
        profit: consolidatedData.summary.financials.profit * projectionMultiplier
      }
    };
    
    return ytdSummary;
  }
}

module.exports = { DataConsolidator };
