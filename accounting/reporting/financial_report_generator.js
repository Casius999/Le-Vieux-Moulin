/**
 * Générateur de rapports financiers
 * 
 * Ce module est responsable de la génération automatique des différents
 * rapports financiers nécessaires à la comptabilité du restaurant.
 */

'use strict';

const moment = require('moment');
const fs = require('fs');
const path = require('path');
const PDFDocument = require('pdfkit');
const XLSX = require('xlsx');
const { EventEmitter } = require('events');
const nodemailer = require('nodemailer');

/**
 * Classe principale de génération de rapports financiers
 */
class FinancialReportGenerator extends EventEmitter {
  /**
   * Crée une nouvelle instance du générateur de rapports
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataConsolidator - Consolidateur de données financières
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.alertService - Service d'alertes
   * @param {string} options.outputDir - Répertoire de sortie des rapports
   */
  constructor(options = {}) {
    super();
    
    this.dataConsolidator = options.dataConsolidator;
    this.configManager = options.configManager;
    this.alertService = options.alertService;
    this.outputDir = options.outputDir || './reports';
    
    // Charger la configuration des rapports
    this.reportConfig = this._loadReportConfig();
    
    // Créer le répertoire de sortie s'il n'existe pas
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
    
    // Configurations email pour l'envoi automatique des rapports
    this.emailConfig = this._loadEmailConfig();
    
    // Initialiser la queue de génération de rapports
    this.reportQueue = [];
    this.isProcessing = false;
  }
  
  /**
   * Charge la configuration des rapports
   * @returns {Object} - Configuration des rapports
   * @private
   */
  _loadReportConfig() {
    const defaultConfig = {
      daily: {
        sections: ['sales', 'expenses', 'staff', 'inventory'],
        formats: ['pdf', 'excel'],
        recipients: []
      },
      weekly: {
        sections: ['sales', 'expenses', 'staff', 'inventory', 'trends'],
        formats: ['pdf', 'excel'],
        recipients: []
      },
      monthly: {
        sections: ['sales', 'expenses', 'staff', 'inventory', 'trends', 'taxes', 'profit_loss'],
        formats: ['pdf', 'excel', 'csv'],
        recipients: []
      },
      quarterly: {
        sections: ['sales', 'expenses', 'staff', 'inventory', 'trends', 'taxes', 'profit_loss', 'balance_sheet'],
        formats: ['pdf', 'excel', 'csv'],
        recipients: []
      },
      annual: {
        sections: ['sales', 'expenses', 'staff', 'inventory', 'trends', 'taxes', 'profit_loss', 'balance_sheet', 'cash_flow'],
        formats: ['pdf', 'excel', 'csv'],
        recipients: []
      },
      custom: {
        sections: [],
        formats: ['pdf', 'excel'],
        recipients: []
      }
    };
    
    // Fusionner avec la configuration personnalisée si disponible
    if (this.configManager) {
      const customConfig = this.configManager.getConfig('accounting.reports', {});
      return { ...defaultConfig, ...customConfig };
    }
    
    return defaultConfig;
  }
  
  /**
   * Charge la configuration email
   * @returns {Object} - Configuration email
   * @private
   */
  _loadEmailConfig() {
    const defaultConfig = {
      enabled: false,
      transport: {
        host: 'smtp.example.com',
        port: 587,
        secure: false,
        auth: {
          user: 'user@example.com',
          pass: 'password'
        }
      },
      defaults: {
        from: '"Le Vieux Moulin" <accounting@levieuxmoulin.fr>',
        subject: 'Rapport financier - {reportType} - {period}'
      }
    };
    
    // Fusionner avec la configuration personnalisée si disponible
    if (this.configManager) {
      const customConfig = this.configManager.getConfig('accounting.email', {});
      return { ...defaultConfig, ...customConfig };
    }
    
    return defaultConfig;
  }
  
  /**
   * Génère un rapport financier
   * @param {Object} options - Options de génération
   * @param {string} options.type - Type de rapport (daily, weekly, monthly, quarterly, annual, custom)
   * @param {Date|string} options.startDate - Date de début de la période
   * @param {Date|string} options.endDate - Date de fin de la période
   * @param {Array<string>} options.sections - Sections à inclure (remplace la config par défaut si spécifié)
   * @param {Array<string>} options.formats - Formats à générer (remplace la config par défaut si spécifié)
   * @param {Array<Object>} options.recipients - Destinataires du rapport
   * @param {boolean} options.sendEmail - Envoyer le rapport par email
   * @returns {Promise<Object>} - Informations sur les rapports générés
   */
  async generateReport(options = {}) {
    const type = options.type || 'daily';
    const startDate = options.startDate ? moment(options.startDate) : moment().startOf('day');
    const endDate = options.endDate ? moment(options.endDate) : moment().endOf('day');
    
    // Si aucune date de fin n'est spécifiée, utiliser la date appropriée en fonction du type
    if (!options.endDate) {
      switch (type) {
        case 'weekly':
          endDate.endOf('week');
          startDate.startOf('week');
          break;
        case 'monthly':
          endDate.endOf('month');
          startDate.startOf('month');
          break;
        case 'quarterly':
          endDate.endOf('quarter');
          startDate.startOf('quarter');
          break;
        case 'annual':
          endDate.endOf('year');
          startDate.startOf('year');
          break;
      }
    }
    
    // Créer une tâche de génération
    const taskId = `${type}_${startDate.format('YYYYMMDD')}_${endDate.format('YYYYMMDD')}_${Date.now()}`;
    
    const reportTask = {
      id: taskId,
      type,
      startDate: startDate.toDate(),
      endDate: endDate.toDate(),
      sections: options.sections || this.reportConfig[type].sections,
      formats: options.formats || this.reportConfig[type].formats,
      recipients: options.recipients || this.reportConfig[type].recipients,
      sendEmail: options.sendEmail !== undefined ? options.sendEmail : true,
      status: 'pending',
      createdAt: new Date(),
      result: null
    };
    
    // Ajouter à la queue et traiter si possible
    this.reportQueue.push(reportTask);
    this._processQueue();
    
    // Retourner l'identifiant pour suivi
    return {
      taskId,
      status: 'queued',
      estimatedCompletion: new Date(Date.now() + 60000) // Estimation: 1 minute
    };
  }
  
  /**
   * Traite la queue de génération de rapports
   * @private
   */
  async _processQueue() {
    // Si déjà en cours de traitement ou queue vide, ne rien faire
    if (this.isProcessing || this.reportQueue.length === 0) {
      return;
    }
    
    this.isProcessing = true;
    
    try {
      // Récupérer la prochaine tâche
      const task = this.reportQueue.shift();
      task.status = 'processing';
      
      // Émettre un événement de démarrage
      this.emit('report:generation_start', {
        taskId: task.id,
        type: task.type,
        period: {
          start: task.startDate,
          end: task.endDate
        }
      });
      
      console.log(`Génération du rapport ${task.type} du ${moment(task.startDate).format('DD/MM/YYYY')} au ${moment(task.endDate).format('DD/MM/YYYY')}...`);
      
      // Récupérer les données consolidées
      const consolidatedData = await this.dataConsolidator.consolidateFinancialData({
        startDate: task.startDate,
        endDate: task.endDate
      });
      
      // Préparer les données du rapport
      const reportData = this._prepareReportData(consolidatedData, task);
      
      // Générer les fichiers de rapport dans les formats demandés
      const generatedFiles = await this._generateReportFiles(reportData, task);
      
      // Envoyer par email si nécessaire
      if (task.sendEmail && task.recipients.length > 0 && this.emailConfig.enabled) {
        await this._sendReportByEmail(generatedFiles, reportData, task);
      }
      
      // Mettre à jour le statut de la tâche
      task.status = 'completed';
      task.completedAt = new Date();
      task.result = {
        files: generatedFiles,
        emailSent: task.sendEmail && task.recipients.length > 0 && this.emailConfig.enabled
      };
      
      // Émettre un événement de fin
      this.emit('report:generation_complete', {
        taskId: task.id,
        type: task.type,
        period: {
          start: task.startDate,
          end: task.endDate
        },
        files: generatedFiles
      });
      
      console.log(`Rapport ${task.type} généré avec succès`);
      
      // Continuer avec la tâche suivante si disponible
      this.isProcessing = false;
      this._processQueue();
      
    } catch (error) {
      console.error('Erreur lors de la génération du rapport:', error);
      
      // Mettre à jour le statut de la tâche actuelle
      const failedTask = this.reportQueue[0];
      if (failedTask) {
        failedTask.status = 'failed';
        failedTask.error = error.message;
        
        // Émettre un événement d'erreur
        this.emit('report:generation_error', {
          taskId: failedTask.id,
          type: failedTask.type,
          error: error.message
        });
        
        // Créer une alerte
        if (this.alertService) {
          this.alertService.danger('report_generation_error',
            `Erreur lors de la génération du rapport ${failedTask.type}: ${error.message}`,
            { taskId: failedTask.id, error: error.message }
          );
        }
      }
      
      // Continuer avec la tâche suivante
      this.isProcessing = false;
      this._processQueue();
    }
  }
  
  /**
   * Prépare les données pour le rapport
   * @param {Object} consolidatedData - Données consolidées
   * @param {Object} task - Tâche de génération
   * @returns {Object} - Données préparées pour le rapport
   * @private
   */
  _prepareReportData(consolidatedData, task) {
    const reportData = {
      metadata: {
        type: task.type,
        period: {
          start: task.startDate,
          end: task.endDate,
          label: this._formatPeriodLabel(task.startDate, task.endDate, task.type)
        },
        generatedAt: new Date(),
        restaurant: {
          name: "Le Vieux Moulin",
          address: "Camping 3 étoiles, Vensac, Gironde",
          phone: "+33 7 79 43 17 29"
        }
      },
      sections: {}
    };
    
    // Filtrer les données en fonction des sections demandées
    for (const section of task.sections) {
      switch (section) {
        case 'sales':
          reportData.sections.sales = this._prepareSalesSection(consolidatedData);
          break;
        
        case 'expenses':
          reportData.sections.expenses = this._prepareExpensesSection(consolidatedData);
          break;
        
        case 'staff':
          reportData.sections.staff = this._prepareStaffSection(consolidatedData);
          break;
        
        case 'inventory':
          reportData.sections.inventory = this._prepareInventorySection(consolidatedData);
          break;
          
        case 'trends':
          reportData.sections.trends = this._prepareTrendsSection(consolidatedData, task);
          break;
          
        case 'taxes':
          reportData.sections.taxes = this._prepareTaxesSection(consolidatedData);
          break;
          
        case 'profit_loss':
          reportData.sections.profit_loss = this._prepareProfitLossSection(consolidatedData);
          break;
          
        case 'balance_sheet':
          reportData.sections.balance_sheet = this._prepareBalanceSheetSection(consolidatedData);
          break;
          
        case 'cash_flow':
          reportData.sections.cash_flow = this._prepareCashFlowSection(consolidatedData);
          break;
      }
    }
    
    // Ajouter un résumé général
    reportData.summary = this._prepareSummarySection(consolidatedData, reportData.sections);
    
    return reportData;
  }
  
  /**
   * Formate le libellé de la période
   * @param {Date} startDate - Date de début
   * @param {Date} endDate - Date de fin
   * @param {string} type - Type de rapport
   * @returns {string} - Libellé formaté
   * @private
   */
  _formatPeriodLabel(startDate, endDate, type) {
    const start = moment(startDate);
    const end = moment(endDate);
    
    switch (type) {
      case 'daily':
        return start.format('DD MMMM YYYY');
      
      case 'weekly':
        return `Semaine ${start.isoWeek()} (${start.format('DD/MM/YYYY')} - ${end.format('DD/MM/YYYY')})`;
      
      case 'monthly':
        return start.format('MMMM YYYY');
      
      case 'quarterly':
        const quarter = Math.ceil((start.month() + 1) / 3);
        return `T${quarter} ${start.format('YYYY')}`;
      
      case 'annual':
        return start.format('YYYY');
      
      default:
        return `${start.format('DD/MM/YYYY')} - ${end.format('DD/MM/YYYY')}`;
    }
  }
  
  /**
   * Prépare la section des ventes
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section des ventes préparée
   * @private
   */
  _prepareSalesSection(consolidatedData) {
    const salesData = {
      overview: {
        totalSales: 0,
        transactionCount: 0,
        averageTicket: 0
      },
      byCategory: {},
      byPaymentMethod: {},
      byService: {},
      hourlyDistribution: {},
      topProducts: []
    };
    
    // Si aucune donnée de vente disponible, retourner la structure vide
    if (!consolidatedData.sources.sales) {
      return salesData;
    }
    
    const sales = consolidatedData.sources.sales;
    
    // Remplir les données de résumé
    salesData.overview.totalSales = sales.totalSales;
    salesData.overview.transactionCount = sales.transactions.length;
    salesData.overview.averageTicket = sales.averageTicket;
    
    // Remplir les données par catégorie
    salesData.byCategory = sales.byCategory;
    
    // Remplir les données par mode de paiement
    salesData.byPaymentMethod = sales.byPaymentMethod;
    
    // Remplir les données par service
    salesData.byService = sales.byService;
    
    // Calculer la distribution horaire (si disponible)
    if (sales.transactions && sales.transactions.length > 0) {
      // Initialiser les tranches horaires
      for (let i = 0; i < 24; i++) {
        salesData.hourlyDistribution[i] = { count: 0, total: 0 };
      }
      
      // Remplir les données
      sales.transactions.forEach(transaction => {
        const hour = moment(transaction.timestamp).hour();
        salesData.hourlyDistribution[hour].count++;
        salesData.hourlyDistribution[hour].total += transaction.total;
      });
    }
    
    // Essayer de récupérer les meilleurs produits (si disponible)
    if (consolidatedData.sources.products && consolidatedData.sources.products.topSelling) {
      salesData.topProducts = consolidatedData.sources.products.topSelling.slice(0, 10);
    }
    
    return salesData;
  }
  
  /**
   * Prépare la section des dépenses
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section des dépenses préparée
   * @private
   */
  _prepareExpensesSection(consolidatedData) {
    const expensesData = {
      overview: {
        totalExpenses: 0,
        fixedCosts: 0,
        variableCosts: 0
      },
      byCategory: {},
      byVendor: {},
      largestExpenses: []
    };
    
    // Si aucune donnée de dépense disponible, retourner la structure vide
    if (!consolidatedData.sources.expenses) {
      return expensesData;
    }
    
    const expenses = consolidatedData.sources.expenses;
    
    // Remplir les données de résumé
    expensesData.overview.totalExpenses = expenses.totalExpenses;
    expensesData.overview.fixedCosts = expenses.fixedCosts;
    expensesData.overview.variableCosts = expenses.variableCosts;
    
    // Remplir les données par catégorie
    expensesData.byCategory = expenses.byCategory;
    
    // Remplir les données par fournisseur
    expensesData.byVendor = expenses.byVendor;
    
    // Trouver les plus grosses dépenses
    if (expenses.expenses && expenses.expenses.length > 0) {
      expensesData.largestExpenses = expenses.expenses
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 10);
    }
    
    return expensesData;
  }
  
  /**
   * Prépare la section du personnel
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section du personnel préparée
   * @private
   */
  _prepareStaffSection(consolidatedData) {
    const staffData = {
      overview: {
        totalHours: 0,
        totalCost: 0,
        averageHourlyCost: 0
      },
      byDepartment: {},
      byShift: {},
      staffEfficiency: {
        salesPerLaborHour: 0,
        laborCostPercentage: 0
      }
    };
    
    // Si aucune donnée de personnel disponible, retourner la structure vide
    if (!consolidatedData.sources.staff) {
      return staffData;
    }
    
    const staff = consolidatedData.sources.staff;
    const sales = consolidatedData.sources.sales || { totalSales: 0 };
    
    // Remplir les données de résumé
    staffData.overview.totalHours = staff.totalHours;
    staffData.overview.totalCost = staff.totalCost;
    staffData.overview.averageHourlyCost = staff.totalHours > 0 ? 
      staff.totalCost / staff.totalHours : 0;
    
    // Remplir les données par département
    staffData.byDepartment = staff.byDepartment;
    
    // Remplir les données par service
    staffData.byShift = staff.byShift;
    
    // Calculer l'efficacité
    staffData.staffEfficiency.salesPerLaborHour = staff.totalHours > 0 ? 
      sales.totalSales / staff.totalHours : 0;
    
    staffData.staffEfficiency.laborCostPercentage = sales.totalSales > 0 ? 
      (staff.totalCost / sales.totalSales) * 100 : 0;
    
    return staffData;
  }
  
  /**
   * Prépare la section d'inventaire
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section d'inventaire préparée
   * @private
   */
  _prepareInventorySection(consolidatedData) {
    const inventoryData = {
      overview: {
        totalValue: 0,
        itemCount: 0,
        averageItemValue: 0
      },
      byCategory: {},
      valuationMethod: 'weighted_average',
      inventory_turnover: 0,
      daysOfInventory: 0
    };
    
    // Si aucune donnée d'inventaire disponible, retourner la structure vide
    if (!consolidatedData.sources.inventory) {
      return inventoryData;
    }
    
    const inventory = consolidatedData.sources.inventory;
    const expenses = consolidatedData.sources.expenses || { totalExpenses: 0 };
    
    // Remplir les données de résumé
    inventoryData.overview.totalValue = inventory.totalValue;
    inventoryData.overview.itemCount = inventory.items ? inventory.items.length : 0;
    inventoryData.overview.averageItemValue = inventoryData.overview.itemCount > 0 ? 
      inventory.totalValue / inventoryData.overview.itemCount : 0;
    
    // Remplir les données par catégorie
    inventoryData.byCategory = inventory.byCategory;
    
    // Calculer les ratios d'inventaire
    // Pour simplifier, nous supposons que 60% des dépenses sont liées au COGS
    const costOfGoodsSold = expenses.totalExpenses * 0.6;
    
    // Turnover = COGS / Valeur moyenne de l'inventaire
    inventoryData.inventory_turnover = inventory.totalValue > 0 ? 
      costOfGoodsSold / inventory.totalValue : 0;
    
    // Jours d'inventaire = (Valeur moyenne de l'inventaire / COGS) * nombre de jours dans la période
    const daysInPeriod = moment(consolidatedData.period.end).diff(moment(consolidatedData.period.start), 'days') + 1;
    inventoryData.daysOfInventory = costOfGoodsSold > 0 ? 
      (inventory.totalValue / costOfGoodsSold) * daysInPeriod : 0;
    
    return inventoryData;
  }
  
  /**
   * Prépare la section des tendances
   * @param {Object} consolidatedData - Données consolidées
   * @param {Object} task - Tâche de génération
   * @returns {Object} - Section des tendances préparée
   * @private
   */
  _prepareTrendsSection(consolidatedData, task) {
    // Récupérer la période actuelle
    const currentStart = moment(task.startDate);
    const currentEnd = moment(task.endDate);
    
    // Calculer la période précédente (même durée)
    const periodDuration = currentEnd.diff(currentStart, 'days') + 1;
    const previousStart = moment(currentStart).subtract(periodDuration, 'days');
    const previousEnd = moment(previousStart).add(periodDuration - 1, 'days');
    
    // Récupérer la même période de l'année précédente
    const lastYearStart = moment(currentStart).subtract(1, 'year');
    const lastYearEnd = moment(currentEnd).subtract(1, 'year');
    
    // Formater les dates pour les libellés
    const currentPeriodLabel = this._formatPeriodLabel(currentStart.toDate(), currentEnd.toDate(), task.type);
    const previousPeriodLabel = this._formatPeriodLabel(previousStart.toDate(), previousEnd.toDate(), task.type);
    const lastYearPeriodLabel = this._formatPeriodLabel(lastYearStart.toDate(), lastYearEnd.toDate(), task.type);
    
    // Structure de base des tendances
    const trendsData = {
      comparisonPeriods: {
        current: {
          label: currentPeriodLabel,
          start: currentStart.toDate(),
          end: currentEnd.toDate()
        },
        previous: {
          label: previousPeriodLabel,
          start: previousStart.toDate(),
          end: previousEnd.toDate()
        },
        lastYear: {
          label: lastYearPeriodLabel,
          start: lastYearStart.toDate(),
          end: lastYearEnd.toDate()
        }
      },
      metrics: {
        sales: {
          current: 0,
          previous: null,
          lastYear: null,
          changeFromPrevious: null,
          changeFromLastYear: null
        },
        expenses: {
          current: 0,
          previous: null,
          lastYear: null,
          changeFromPrevious: null,
          changeFromLastYear: null
        },
        profit: {
          current: 0,
          previous: null,
          lastYear: null,
          changeFromPrevious: null,
          changeFromLastYear: null
        },
        averageTicket: {
          current: 0,
          previous: null,
          lastYear: null,
          changeFromPrevious: null,
          changeFromLastYear: null
        },
        laborCost: {
          current: 0,
          previous: null,
          lastYear: null,
          changeFromPrevious: null,
          changeFromLastYear: null
        }
      }
    };
    
    // Remplir les données actuelles
    if (consolidatedData.sources.sales) {
      trendsData.metrics.sales.current = consolidatedData.sources.sales.totalSales;
      trendsData.metrics.averageTicket.current = consolidatedData.sources.sales.averageTicket;
    }
    
    if (consolidatedData.sources.expenses) {
      trendsData.metrics.expenses.current = consolidatedData.sources.expenses.totalExpenses;
    }
    
    if (consolidatedData.sources.staff) {
      trendsData.metrics.laborCost.current = consolidatedData.sources.staff.totalCost;
    }
    
    // Calculer le profit actuel
    trendsData.metrics.profit.current = trendsData.metrics.sales.current - trendsData.metrics.expenses.current;
    
    // TODO: Récupérer les données historiques depuis la base de données
    // Pour l'exemple, nous simulons des données historiques
    
    // Données de la période précédente (simulation)
    trendsData.metrics.sales.previous = trendsData.metrics.sales.current * 0.95; // 5% de moins
    trendsData.metrics.expenses.previous = trendsData.metrics.expenses.current * 0.97; // 3% de moins
    trendsData.metrics.profit.previous = trendsData.metrics.sales.previous - trendsData.metrics.expenses.previous;
    trendsData.metrics.averageTicket.previous = trendsData.metrics.averageTicket.current * 0.98; // 2% de moins
    trendsData.metrics.laborCost.previous = trendsData.metrics.laborCost.current * 0.96; // 4% de moins
    
    // Données de l'année précédente (simulation)
    trendsData.metrics.sales.lastYear = trendsData.metrics.sales.current * 0.85; // 15% de moins
    trendsData.metrics.expenses.lastYear = trendsData.metrics.expenses.current * 0.88; // 12% de moins
    trendsData.metrics.profit.lastYear = trendsData.metrics.sales.lastYear - trendsData.metrics.expenses.lastYear;
    trendsData.metrics.averageTicket.lastYear = trendsData.metrics.averageTicket.current * 0.90; // 10% de moins
    trendsData.metrics.laborCost.lastYear = trendsData.metrics.laborCost.current * 0.92; // 8% de moins
    
    // Calculer les variations
    for (const [metricName, metric] of Object.entries(trendsData.metrics)) {
      if (metric.previous !== null && metric.previous !== 0) {
        metric.changeFromPrevious = ((metric.current - metric.previous) / metric.previous) * 100;
      }
      
      if (metric.lastYear !== null && metric.lastYear !== 0) {
        metric.changeFromLastYear = ((metric.current - metric.lastYear) / metric.lastYear) * 100;
      }
    }
    
    return trendsData;
  }
  
  /**
   * Prépare la section des taxes
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section des taxes préparée
   * @private
   */
  _prepareTaxesSection(consolidatedData) {
    const taxesData = {
      vat: {
        collected: {
          standard: 0, // 20%
          intermediate: 0, // 10%
          reduced: 0 // 5.5%
        },
        deductible: 0,
        balance: 0
      },
      otherTaxes: {}
    };
    
    // Si les données de ventes sont disponibles, calculer la TVA collectée
    if (consolidatedData.sources.sales && consolidatedData.sources.sales.transactions) {
      // Simuler les montants de TVA en fonction des catégories
      // Dans un système réel, ces données proviendraient de la base de données
      
      // Par exemple, supposons:
      // - 20% de TVA sur les boissons alcoolisées
      // - 10% de TVA sur la restauration sur place
      // - 5.5% de TVA sur la vente à emporter
      
      const salesByCategory = consolidatedData.sources.sales.byCategory;
      
      // TVA à 20% (boissons alcoolisées)
      if (salesByCategory.alcohol) {
        taxesData.vat.collected.standard = salesByCategory.alcohol.total * 0.20 / 1.20;
      }
      
      // TVA à 10% (service sur place)
      const onPremiseCategories = ['food', 'desserts', 'starters', 'mains', 'non_alcoholic'];
      onPremiseCategories.forEach(category => {
        if (salesByCategory[category]) {
          taxesData.vat.collected.intermediate += salesByCategory[category].total * 0.10 / 1.10;
        }
      });
      
      // TVA à 5.5% (vente à emporter)
      if (salesByCategory.takeaway) {
        taxesData.vat.collected.reduced = salesByCategory.takeaway.total * 0.055 / 1.055;
      }
    }
    
    // Si les données de dépenses sont disponibles, calculer la TVA déductible
    if (consolidatedData.sources.expenses && consolidatedData.sources.expenses.expenses) {
      // Simuler la TVA déductible (20% des dépenses éligibles)
      // Dans un système réel, le taux de TVA serait spécifique à chaque dépense
      
      // Supposons que 80% des dépenses sont éligibles à la déduction de TVA
      const eligibleExpenses = consolidatedData.sources.expenses.totalExpenses * 0.80;
      taxesData.vat.deductible = eligibleExpenses * 0.20 / 1.20;
    }
    
    // Calculer le solde de TVA
    const totalCollected = taxesData.vat.collected.standard + 
                          taxesData.vat.collected.intermediate + 
                          taxesData.vat.collected.reduced;
    
    taxesData.vat.balance = totalCollected - taxesData.vat.deductible;
    
    return taxesData;
  }
  
  /**
   * Prépare la section du compte de résultat
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section du compte de résultat préparée
   * @private
   */
  _prepareProfitLossSection(consolidatedData) {
    const plData = {
      revenues: {
        foodSales: 0,
        beverageSales: 0,
        otherSales: 0,
        totalRevenues: 0
      },
      expenses: {
        costOfGoods: {
          food: 0,
          beverages: 0,
          total: 0
        },
        operatingExpenses: {
          labor: 0,
          rent: 0,
          utilities: 0,
          marketing: 0,
          other: 0,
          total: 0
        },
        totalExpenses: 0
      },
      grossProfit: 0,
      operatingProfit: 0,
      netProfit: 0,
      profitMargins: {
        gross: 0,
        operating: 0,
        net: 0
      }
    };
    
    // Si les données de ventes sont disponibles
    if (consolidatedData.sources.sales && consolidatedData.sources.sales.byCategory) {
      const salesByCategory = consolidatedData.sources.sales.byCategory;
      
      // Catégoriser les ventes
      const foodCategories = ['food', 'mains', 'starters', 'desserts', 'takeaway'];
      const beverageCategories = ['alcohol', 'non_alcoholic', 'drinks', 'coffee'];
      
      // Calculer les ventes de nourriture
      foodCategories.forEach(category => {
        if (salesByCategory[category]) {
          plData.revenues.foodSales += salesByCategory[category].total;
        }
      });
      
      // Calculer les ventes de boissons
      beverageCategories.forEach(category => {
        if (salesByCategory[category]) {
          plData.revenues.beverageSales += salesByCategory[category].total;
        }
      });
      
      // Autres ventes
      plData.revenues.otherSales = consolidatedData.sources.sales.totalSales - 
                                   plData.revenues.foodSales - 
                                   plData.revenues.beverageSales;
      
      // Total des revenus
      plData.revenues.totalRevenues = consolidatedData.sources.sales.totalSales;
    }
    
    // Si les données d'inventaire sont disponibles
    if (consolidatedData.sources.inventory && consolidatedData.sources.inventory.byCategory) {
      const inventoryByCategory = consolidatedData.sources.inventory.byCategory;
      
      // Estimer le coût des marchandises vendues (simplifié pour l'exemple)
      // Dans un système réel, cela serait calculé à partir des mouvements de stock
      
      // Coût nourriture (~ 30% des ventes)
      plData.expenses.costOfGoods.food = plData.revenues.foodSales * 0.30;
      
      // Coût boissons (~ 25% des ventes)
      plData.expenses.costOfGoods.beverages = plData.revenues.beverageSales * 0.25;
      
      // Total coût des marchandises
      plData.expenses.costOfGoods.total = plData.expenses.costOfGoods.food + 
                                         plData.expenses.costOfGoods.beverages;
    }
    
    // Si les données de dépenses sont disponibles
    if (consolidatedData.sources.expenses && consolidatedData.sources.expenses.byCategory) {
      const expensesByCategory = consolidatedData.sources.expenses.byCategory;
      
      // Répartir les dépenses dans les bonnes catégories
      if (consolidatedData.sources.staff) {
        plData.expenses.operatingExpenses.labor = consolidatedData.sources.staff.totalCost;
      }
      
      if (expensesByCategory.rent) {
        plData.expenses.operatingExpenses.rent = expensesByCategory.rent.total;
      }
      
      if (expensesByCategory.utilities) {
        plData.expenses.operatingExpenses.utilities = expensesByCategory.utilities.total;
      }
      
      if (consolidatedData.sources.marketing) {
        plData.expenses.operatingExpenses.marketing = consolidatedData.sources.marketing.totalExpenses;
      } else if (expensesByCategory.marketing) {
        plData.expenses.operatingExpenses.marketing = expensesByCategory.marketing.total;
      }
      
      // Autres dépenses opérationnelles
      plData.expenses.operatingExpenses.other = consolidatedData.sources.expenses.totalExpenses - 
                                              plData.expenses.operatingExpenses.labor - 
                                              plData.expenses.operatingExpenses.rent - 
                                              plData.expenses.operatingExpenses.utilities - 
                                              plData.expenses.operatingExpenses.marketing;
      
      // S'assurer que les autres dépenses ne sont pas négatives
      if (plData.expenses.operatingExpenses.other < 0) {
        plData.expenses.operatingExpenses.other = 0;
      }
      
      // Total des dépenses opérationnelles
      plData.expenses.operatingExpenses.total = plData.expenses.operatingExpenses.labor + 
                                              plData.expenses.operatingExpenses.rent + 
                                              plData.expenses.operatingExpenses.utilities + 
                                              plData.expenses.operatingExpenses.marketing + 
                                              plData.expenses.operatingExpenses.other;
      
      // Total des dépenses
      plData.expenses.totalExpenses = plData.expenses.costOfGoods.total + 
                                    plData.expenses.operatingExpenses.total;
    }
    
    // Calculer les profits
    plData.grossProfit = plData.revenues.totalRevenues - plData.expenses.costOfGoods.total;
    plData.operatingProfit = plData.grossProfit - plData.expenses.operatingExpenses.total;
    
    // Pour simplifier, on considère que le profit net est égal au profit opérationnel
    // Dans un système réel, on déduirait les taxes, les intérêts, etc.
    plData.netProfit = plData.operatingProfit;
    
    // Calculer les marges
    if (plData.revenues.totalRevenues > 0) {
      plData.profitMargins.gross = (plData.grossProfit / plData.revenues.totalRevenues) * 100;
      plData.profitMargins.operating = (plData.operatingProfit / plData.revenues.totalRevenues) * 100;
      plData.profitMargins.net = (plData.netProfit / plData.revenues.totalRevenues) * 100;
    }
    
    return plData;
  }
  
  /**
   * Prépare la section du bilan
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section du bilan préparée
   * @private
   */
  _prepareBalanceSheetSection(consolidatedData) {
    // Note: Un vrai bilan nécessiterait des données comptables complètes
    // Pour l'exemple, nous créons une structure simplifiée avec des données simulées
    
    const balanceData = {
      assets: {
        currentAssets: {
          cash: 0,
          accounts_receivable: 0,
          inventory: 0,
          prepaid_expenses: 0,
          total: 0
        },
        fixedAssets: {
          equipment: 0,
          furniture: 0,
          vehicles: 0,
          buildings: 0,
          accumulatedDepreciation: 0,
          total: 0
        },
        totalAssets: 0
      },
      liabilities: {
        currentLiabilities: {
          accounts_payable: 0,
          short_term_debt: 0,
          accrued_expenses: 0,
          total: 0
        },
        longTermLiabilities: {
          long_term_debt: 0,
          deferred_taxes: 0,
          total: 0
        },
        totalLiabilities: 0
      },
      equity: {
        capital: 0,
        retained_earnings: 0,
        current_earnings: 0,
        total: 0
      },
      totalLiabilitiesAndEquity: 0
    };
    
    // Remplir avec les données disponibles ou simulées
    
    // Actifs courants
    balanceData.assets.currentAssets.cash = 50000; // Valeur simulée
    balanceData.assets.currentAssets.accounts_receivable = 5000; // Valeur simulée
    
    // Inventaire (si disponible)
    if (consolidatedData.sources.inventory) {
      balanceData.assets.currentAssets.inventory = consolidatedData.sources.inventory.totalValue;
    } else {
      balanceData.assets.currentAssets.inventory = 15000; // Valeur simulée
    }
    
    balanceData.assets.currentAssets.prepaid_expenses = 2000; // Valeur simulée
    
    // Total des actifs courants
    balanceData.assets.currentAssets.total = 
      balanceData.assets.currentAssets.cash + 
      balanceData.assets.currentAssets.accounts_receivable + 
      balanceData.assets.currentAssets.inventory + 
      balanceData.assets.currentAssets.prepaid_expenses;
    
    // Actifs immobilisés (simulés)
    balanceData.assets.fixedAssets.equipment = 80000;
    balanceData.assets.fixedAssets.furniture = 30000;
    balanceData.assets.fixedAssets.vehicles = 25000;
    balanceData.assets.fixedAssets.buildings = 0; // Supposons que le restaurant est loué
    balanceData.assets.fixedAssets.accumulatedDepreciation = -40000; // Valeur négative car c'est une déduction
    
    // Total des actifs immobilisés
    balanceData.assets.fixedAssets.total = 
      balanceData.assets.fixedAssets.equipment + 
      balanceData.assets.fixedAssets.furniture + 
      balanceData.assets.fixedAssets.vehicles + 
      balanceData.assets.fixedAssets.buildings + 
      balanceData.assets.fixedAssets.accumulatedDepreciation;
    
    // Total des actifs
    balanceData.assets.totalAssets = 
      balanceData.assets.currentAssets.total + 
      balanceData.assets.fixedAssets.total;
    
    // Passifs courants (simulés)
    balanceData.liabilities.currentLiabilities.accounts_payable = 15000;
    balanceData.liabilities.currentLiabilities.short_term_debt = 10000;
    balanceData.liabilities.currentLiabilities.accrued_expenses = 8000;
    
    // Total des passifs courants
    balanceData.liabilities.currentLiabilities.total = 
      balanceData.liabilities.currentLiabilities.accounts_payable + 
      balanceData.liabilities.currentLiabilities.short_term_debt + 
      balanceData.liabilities.currentLiabilities.accrued_expenses;
    
    // Passifs à long terme (simulés)
    balanceData.liabilities.longTermLiabilities.long_term_debt = 40000;
    balanceData.liabilities.longTermLiabilities.deferred_taxes = 5000;
    
    // Total des passifs à long terme
    balanceData.liabilities.longTermLiabilities.total = 
      balanceData.liabilities.longTermLiabilities.long_term_debt + 
      balanceData.liabilities.longTermLiabilities.deferred_taxes;
    
    // Total des passifs
    balanceData.liabilities.totalLiabilities = 
      balanceData.liabilities.currentLiabilities.total + 
      balanceData.liabilities.longTermLiabilities.total;
    
    // Capitaux propres (simulés)
    balanceData.equity.capital = 50000;
    balanceData.equity.retained_earnings = 20000;
    
    // Résultat de la période actuelle (si disponible dans P&L)
    if (consolidatedData.sections && consolidatedData.sections.profit_loss) {
      balanceData.equity.current_earnings = consolidatedData.sections.profit_loss.netProfit;
    } else {
      balanceData.equity.current_earnings = 12000; // Valeur simulée
    }
    
    // Total des capitaux propres
    balanceData.equity.total = 
      balanceData.equity.capital + 
      balanceData.equity.retained_earnings + 
      balanceData.equity.current_earnings;
    
    // Total passif + capitaux propres
    balanceData.totalLiabilitiesAndEquity = 
      balanceData.liabilities.totalLiabilities + 
      balanceData.equity.total;
    
    return balanceData;
  }
  
  /**
   * Prépare la section du tableau de flux de trésorerie
   * @param {Object} consolidatedData - Données consolidées
   * @returns {Object} - Section du tableau de flux de trésorerie préparée
   * @private
   */
  _prepareCashFlowSection(consolidatedData) {
    // Note: Un vrai tableau de flux de trésorerie nécessiterait des données comptables complètes
    // Pour l'exemple, nous créons une structure simplifiée avec des données simulées
    
    const cashFlowData = {
      operatingActivities: {
        netIncome: 0,
        adjustments: {
          depreciation: 0,
          changes_in_receivables: 0,
          changes_in_inventory: 0,
          changes_in_payables: 0,
          total: 0
        },
        netCashFromOperating: 0
      },
      investingActivities: {
        purchase_of_equipment: 0,
        sale_of_equipment: 0,
        netCashFromInvesting: 0
      },
      financingActivities: {
        loan_proceeds: 0,
        loan_repayments: 0,
        owner_investments: 0,
        owner_withdrawals: 0,
        netCashFromFinancing: 0
      },
      netCashIncrease: 0,
      cash: {
        beginning: 0,
        ending: 0
      }
    };
    
    // Résultat net (si disponible dans P&L)
    if (consolidatedData.sections && consolidatedData.sections.profit_loss) {
      cashFlowData.operatingActivities.netIncome = consolidatedData.sections.profit_loss.netProfit;
    } else {
      cashFlowData.operatingActivities.netIncome = 12000; // Valeur simulée
    }
    
    // Ajustements (simulés)
    cashFlowData.operatingActivities.adjustments.depreciation = 5000;
    cashFlowData.operatingActivities.adjustments.changes_in_receivables = -2000; // Augmentation des créances = négatif
    cashFlowData.operatingActivities.adjustments.changes_in_inventory = -1500; // Augmentation des stocks = négatif
    cashFlowData.operatingActivities.adjustments.changes_in_payables = 3000; // Augmentation des dettes = positif
    
    // Total des ajustements
    cashFlowData.operatingActivities.adjustments.total = 
      cashFlowData.operatingActivities.adjustments.depreciation + 
      cashFlowData.operatingActivities.adjustments.changes_in_receivables + 
      cashFlowData.operatingActivities.adjustments.changes_in_inventory + 
      cashFlowData.operatingActivities.adjustments.changes_in_payables;
    
    // Flux net des activités d'exploitation
    cashFlowData.operatingActivities.netCashFromOperating = 
      cashFlowData.operatingActivities.netIncome + 
      cashFlowData.operatingActivities.adjustments.total;
    
    // Activités d'investissement (simulées)
    cashFlowData.investingActivities.purchase_of_equipment = -8000; // Achat = négatif
    cashFlowData.investingActivities.sale_of_equipment = 2000; // Vente = positif
    
    // Flux net des activités d'investissement
    cashFlowData.investingActivities.netCashFromInvesting = 
      cashFlowData.investingActivities.purchase_of_equipment + 
      cashFlowData.investingActivities.sale_of_equipment;
    
    // Activités de financement (simulées)
    cashFlowData.financingActivities.loan_proceeds = 10000; // Emprunt = positif
    cashFlowData.financingActivities.loan_repayments = -6000; // Remboursement = négatif
    cashFlowData.financingActivities.owner_investments = 5000; // Apport = positif
    cashFlowData.financingActivities.owner_withdrawals = -4000; // Retrait = négatif
    
    // Flux net des activités de financement
    cashFlowData.financingActivities.netCashFromFinancing = 
      cashFlowData.financingActivities.loan_proceeds + 
      cashFlowData.financingActivities.loan_repayments + 
      cashFlowData.financingActivities.owner_investments + 
      cashFlowData.financingActivities.owner_withdrawals;
    
    // Variation nette de trésorerie
    cashFlowData.netCashIncrease = 
      cashFlowData.operatingActivities.netCashFromOperating + 
      cashFlowData.investingActivities.netCashFromInvesting + 
      cashFlowData.financingActivities.netCashFromFinancing;
    
    // Trésorerie (simulée)
    cashFlowData.cash.beginning = 45000;
    cashFlowData.cash.ending = cashFlowData.cash.beginning + cashFlowData.netCashIncrease;
    
    return cashFlowData;
  }
  
  /**
   * Prépare la section de résumé
   * @param {Object} consolidatedData - Données consolidées
   * @param {Object} sections - Sections du rapport
   * @returns {Object} - Section de résumé préparée
   * @private
   */
  _prepareSummarySection(consolidatedData, sections) {
    const summaryData = {
      keyFigures: {
        sales: 0,
        expenses: 0,
        profit: 0,
        profitMargin: 0
      },
      keyPerformanceIndicators: {
        averageTicket: 0,
        laborCostPercentage: 0,
        foodCostPercentage: 0,
        coverCount: 0
      },
      trends: {
        salesTrend: null,
        profitTrend: null
      },
      recommendations: []
    };
    
    // Remplir les chiffres clés
    if (sections.sales) {
      summaryData.keyFigures.sales = sections.sales.overview.totalSales;
      summaryData.keyPerformanceIndicators.averageTicket = sections.sales.overview.averageTicket;
      summaryData.keyPerformanceIndicators.coverCount = sections.sales.overview.transactionCount;
    }
    
    if (sections.expenses) {
      summaryData.keyFigures.expenses = sections.expenses.overview.totalExpenses;
    }
    
    // Calculer le profit et la marge
    summaryData.keyFigures.profit = summaryData.keyFigures.sales - summaryData.keyFigures.expenses;
    
    if (summaryData.keyFigures.sales > 0) {
      summaryData.keyFigures.profitMargin = (summaryData.keyFigures.profit / summaryData.keyFigures.sales) * 100;
    }
    
    // Remplir les KPIs
    if (sections.staff && summaryData.keyFigures.sales > 0) {
      summaryData.keyPerformanceIndicators.laborCostPercentage = 
        (sections.staff.overview.totalCost / summaryData.keyFigures.sales) * 100;
    }
    
    if (sections.profit_loss) {
      summaryData.keyPerformanceIndicators.foodCostPercentage = 
        (sections.profit_loss.expenses.costOfGoods.food / sections.profit_loss.revenues.foodSales) * 100;
    }
    
    // Remplir les tendances
    if (sections.trends) {
      summaryData.trends.salesTrend = sections.trends.metrics.sales.changeFromPrevious;
      summaryData.trends.profitTrend = sections.trends.metrics.profit.changeFromPrevious;
    }
    
    // Générer des recommandations basées sur les données
    if (summaryData.keyPerformanceIndicators.laborCostPercentage > 30) {
      summaryData.recommendations.push({
        area: 'labor',
        issue: 'Coût du travail élevé',
        recommendation: 'Analyser les plannings et optimiser les heures de travail en fonction de l\'affluence'
      });
    }
    
    if (summaryData.keyPerformanceIndicators.foodCostPercentage > 35) {
      summaryData.recommendations.push({
        area: 'food_cost',
        issue: 'Coût des matières premières élevé',
        recommendation: 'Revoir les fiches techniques et les portions des plats à forte marge'
      });
    }
    
    if (sections.sales && sections.sales.byService && 
        sections.sales.byService.lunch && sections.sales.byService.dinner) {
      const lunchSales = sections.sales.byService.lunch.total;
      const dinnerSales = sections.sales.byService.dinner.total;
      
      if (lunchSales < dinnerSales * 0.5) {
        summaryData.recommendations.push({
          area: 'sales_distribution',
          issue: 'Faibles ventes au déjeuner',
          recommendation: 'Développer une offre déjeuner plus attractive (formules, service rapide)'
        });
      }
    }
    
    return summaryData;
  }
  
  /**
   * Génère les fichiers de rapport dans différents formats
   * @param {Object} reportData - Données du rapport
   * @param {Object} task - Tâche de génération
   * @returns {Promise<Array<Object>>} - Liste des fichiers générés
   * @private
   */
  async _generateReportFiles(reportData, task) {
    const generatedFiles = [];
    
    // Créer le sous-répertoire pour ce type de rapport si nécessaire
    const reportTypeDir = path.join(this.outputDir, task.type);
    if (!fs.existsSync(reportTypeDir)) {
      fs.mkdirSync(reportTypeDir, { recursive: true });
    }
    
    // Créer le sous-répertoire pour cette période si nécessaire
    const startDate = moment(task.startDate).format('YYYY-MM-DD');
    const endDate = moment(task.endDate).format('YYYY-MM-DD');
    const periodDir = path.join(reportTypeDir, `${startDate}_${endDate}`);
    if (!fs.existsSync(periodDir)) {
      fs.mkdirSync(periodDir, { recursive: true });
    }
    
    // Générer les fichiers dans les formats demandés
    for (const format of task.formats) {
      try {
        let filePath;
        
        switch (format) {
          case 'pdf':
            filePath = await this._generatePdfReport(reportData, periodDir);
            break;
          
          case 'excel':
            filePath = await this._generateExcelReport(reportData, periodDir);
            break;
          
          case 'csv':
            filePath = await this._generateCsvReport(reportData, periodDir);
            break;
          
          default:
            console.warn(`Format non supporté: ${format}`);
            continue;
        }
        
        if (filePath) {
          generatedFiles.push({
            format,
            path: filePath,
            size: fs.statSync(filePath).size,
            url: path.relative(this.outputDir, filePath)
          });
        }
      } catch (error) {
        console.error(`Erreur lors de la génération du rapport en format ${format}:`, error);
        
        // Créer une alerte
        if (this.alertService) {
          this.alertService.warning('report_format_generation_error',
            `Erreur lors de la génération du rapport ${task.type} en format ${format}: ${error.message}`,
            { taskId: task.id, format, error: error.message }
          );
        }
      }
    }
    
    return generatedFiles;
  }
  
  /**
   * Génère un rapport au format PDF
   * @param {Object} reportData - Données du rapport
   * @param {string} outputDir - Répertoire de sortie
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generatePdfReport(reportData, outputDir) {
    return new Promise((resolve, reject) => {
      try {
        const filename = `rapport_${reportData.metadata.type}_${moment(reportData.metadata.period.start).format('YYYY-MM-DD')}.pdf`;
        const outputPath = path.join(outputDir, filename);
        
        // Créer un nouveau document PDF
        const doc = new PDFDocument({ margin: 50 });
        
        // Créer un flux d'écriture
        const stream = fs.createWriteStream(outputPath);
        doc.pipe(stream);
        
        // Ajouter l'en-tête
        doc.fontSize(20).text(`Rapport Financier - ${reportData.metadata.restaurant.name}`, { align: 'center' });
        doc.fontSize(14).text(`Période: ${reportData.metadata.period.label}`, { align: 'center' });
        doc.moveDown();
        
        // Ajouter le résumé
        doc.fontSize(16).text('Résumé', { underline: true });
        doc.fontSize(12).text(`Chiffre d'affaires: ${reportData.summary.keyFigures.sales.toFixed(2)}€`);
        doc.fontSize(12).text(`Dépenses: ${reportData.summary.keyFigures.expenses.toFixed(2)}€`);
        doc.fontSize(12).text(`Profit: ${reportData.summary.keyFigures.profit.toFixed(2)}€`);
        doc.fontSize(12).text(`Marge: ${reportData.summary.keyFigures.profitMargin.toFixed(2)}%`);
        doc.moveDown();
        
        // Ajouter les sections (exemple simplifié)
        if (reportData.sections.sales) {
          doc.fontSize(16).text('Ventes', { underline: true });
          doc.fontSize(12).text(`Total des ventes: ${reportData.sections.sales.overview.totalSales.toFixed(2)}€`);
          doc.fontSize(12).text(`Nombre de transactions: ${reportData.sections.sales.overview.transactionCount}`);
          doc.fontSize(12).text(`Ticket moyen: ${reportData.sections.sales.overview.averageTicket.toFixed(2)}€`);
          doc.moveDown();
          
          // Ventes par catégorie
          doc.fontSize(14).text('Ventes par catégorie');
          Object.entries(reportData.sections.sales.byCategory).forEach(([category, data]) => {
            doc.fontSize(10).text(`${category}: ${data.total.toFixed(2)}€ (${data.count} ventes)`);
          });
          doc.moveDown();
        }
        
        // Ajouter les autres sections de la même manière...
        
        // Ajouter les recommandations
        if (reportData.summary.recommendations.length > 0) {
          doc.fontSize(16).text('Recommandations', { underline: true });
          reportData.summary.recommendations.forEach((recommendation, index) => {
            doc.fontSize(12).text(`${index + 1}. ${recommendation.issue}:`);
            doc.fontSize(10).text(`${recommendation.recommendation}`);
            doc.moveDown(0.5);
          });
        }
        
        // Ajouter le pied de page
        doc.fontSize(8).text(`Généré le ${moment().format('DD/MM/YYYY à HH:mm')} - Le Vieux Moulin`, {
          align: 'center',
          bottom: 50
        });
        
        // Finaliser le document
        doc.end();
        
        // Attendre la fin de l'écriture
        stream.on('finish', () => {
          resolve(outputPath);
        });
        
        stream.on('error', (err) => {
          reject(err);
        });
        
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Génère un rapport au format Excel
   * @param {Object} reportData - Données du rapport
   * @param {string} outputDir - Répertoire de sortie
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generateExcelReport(reportData, outputDir) {
    try {
      const filename = `rapport_${reportData.metadata.type}_${moment(reportData.metadata.period.start).format('YYYY-MM-DD')}.xlsx`;
      const outputPath = path.join(outputDir, filename);
      
      // Créer un nouveau classeur
      const workbook = XLSX.utils.book_new();
      
      // Créer une feuille de résumé
      const summaryData = [
        ['Rapport Financier - ' + reportData.metadata.restaurant.name],
        ['Période: ' + reportData.metadata.period.label],
        [''],
        ['Résumé'],
        ['Chiffre d\'affaires', reportData.summary.keyFigures.sales],
        ['Dépenses', reportData.summary.keyFigures.expenses],
        ['Profit', reportData.summary.keyFigures.profit],
        ['Marge', reportData.summary.keyFigures.profitMargin + '%'],
        ['']
      ];
      
      // Ajouter les KPIs
      summaryData.push(['Indicateurs de performance']);
      summaryData.push(['Ticket moyen', reportData.summary.keyPerformanceIndicators.averageTicket]);
      summaryData.push(['Coût de personnel (%)', reportData.summary.keyPerformanceIndicators.laborCostPercentage + '%']);
      summaryData.push(['Food cost (%)', reportData.summary.keyPerformanceIndicators.foodCostPercentage + '%']);
      summaryData.push(['']);
      
      // Ajouter les recommandations
      if (reportData.summary.recommendations.length > 0) {
        summaryData.push(['Recommandations']);
        reportData.summary.recommendations.forEach(recommendation => {
          summaryData.push([recommendation.issue, recommendation.recommendation]);
        });
      }
      
      // Créer la feuille de résumé
      const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);
      XLSX.utils.book_append_sheet(workbook, summarySheet, 'Résumé');
      
      // Créer une feuille pour chaque section
      if (reportData.sections.sales) {
        const salesData = [
          ['Ventes'],
          ['Total des ventes', reportData.sections.sales.overview.totalSales],
          ['Nombre de transactions', reportData.sections.sales.overview.transactionCount],
          ['Ticket moyen', reportData.sections.sales.overview.averageTicket],
          [''],
          ['Ventes par catégorie']
        ];
        
        // Ajouter les ventes par catégorie
        Object.entries(reportData.sections.sales.byCategory).forEach(([category, data]) => {
          salesData.push([category, data.total, data.count]);
        });
        
        // Créer la feuille des ventes
        const salesSheet = XLSX.utils.aoa_to_sheet(salesData);
        XLSX.utils.book_append_sheet(workbook, salesSheet, 'Ventes');
      }
      
      // Ajouter d'autres feuilles pour les autres sections...
      
      // Écrire le fichier
      XLSX.writeFile(workbook, outputPath);
      
      return outputPath;
    } catch (error) {
      throw error;
    }
  }
  
  /**
   * Génère un rapport au format CSV
   * @param {Object} reportData - Données du rapport
   * @param {string} outputDir - Répertoire de sortie
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generateCsvReport(reportData, outputDir) {
    try {
      const filename = `rapport_${reportData.metadata.type}_${moment(reportData.metadata.period.start).format('YYYY-MM-DD')}.csv`;
      const outputPath = path.join(outputDir, filename);
      
      // Créer un contenu CSV simple
      let csvContent = 'Catégorie,Valeur\n';
      csvContent += `Période,${reportData.metadata.period.label}\n`;
      csvContent += `Chiffre d'affaires,${reportData.summary.keyFigures.sales}\n`;
      csvContent += `Dépenses,${reportData.summary.keyFigures.expenses}\n`;
      csvContent += `Profit,${reportData.summary.keyFigures.profit}\n`;
      csvContent += `Marge,${reportData.summary.keyFigures.profitMargin}%\n`;
      
      // Ajouter d'autres données...
      
      // Écrire le fichier
      fs.writeFileSync(outputPath, csvContent);
      
      return outputPath;
    } catch (error) {
      throw error;
    }
  }
  
  /**
   * Envoie les rapports par email
   * @param {Array<Object>} files - Fichiers à envoyer
   * @param {Object} reportData - Données du rapport
   * @param {Object} task - Tâche de génération
   * @returns {Promise<void>}
   * @private
   */
  async _sendReportByEmail(files, reportData, task) {
    if (!this.emailConfig.enabled || files.length === 0 || task.recipients.length === 0) {
      return;
    }
    
    try {
      // Créer le transporteur
      const transporter = nodemailer.createTransport(this.emailConfig.transport);
      
      // Préparer le sujet avec variables remplacées
      let subject = this.emailConfig.defaults.subject
        .replace('{reportType}', task.type)
        .replace('{period}', reportData.metadata.period.label);
      
      // Préparer le corps du message
      const body = `
        <h2>Rapport financier - ${reportData.metadata.restaurant.name}</h2>
        <p>Période: <strong>${reportData.metadata.period.label}</strong></p>
        
        <h3>Résumé des chiffres clés</h3>
        <ul>
          <li>Chiffre d'affaires: <strong>${reportData.summary.keyFigures.sales.toFixed(2)}€</strong></li>
          <li>Dépenses: <strong>${reportData.summary.keyFigures.expenses.toFixed(2)}€</strong></li>
          <li>Profit: <strong>${reportData.summary.keyFigures.profit.toFixed(2)}€</strong></li>
          <li>Marge: <strong>${reportData.summary.keyFigures.profitMargin.toFixed(2)}%</strong></li>
        </ul>
        
        <p>Veuillez trouver ci-joint le rapport complet.</p>
        
        <p>Cordialement,<br>
        Le système de gestion du Vieux Moulin</p>
      `;
      
      // Préparer les pièces jointes
      const attachments = files.map(file => ({
        filename: path.basename(file.path),
        path: file.path
      }));
      
      // Envoyer l'email à chaque destinataire
      for (const recipient of task.recipients) {
        // Options d'envoi
        const mailOptions = {
          from: this.emailConfig.defaults.from,
          to: recipient.email,
          subject,
          html: body,
          attachments
        };
        
        // Envoyer l'email
        await transporter.sendMail(mailOptions);
        
        console.log(`Email envoyé à ${recipient.email}`);
      }
      
    } catch (error) {
      console.error('Erreur lors de l\'envoi des rapports par email:', error);
      
      // Créer une alerte
      if (this.alertService) {
        this.alertService.warning('report_email_error',
          `Erreur lors de l'envoi des rapports par email: ${error.message}`,
          { taskId: task.id, error: error.message }
        );
      }
      
      throw error;
    }
  }
  
  /**
   * Récupère l'état d'une tâche de génération
   * @param {string} taskId - Identifiant de la tâche
   * @returns {Object|null} - État de la tâche ou null si non trouvée
   */
  getTaskStatus(taskId) {
    // Chercher dans la queue
    const queuedTask = this.reportQueue.find(task => task.id === taskId);
    if (queuedTask) {
      return {
        id: queuedTask.id,
        status: queuedTask.status,
        type: queuedTask.type,
        period: {
          start: queuedTask.startDate,
          end: queuedTask.endDate
        },
        createdAt: queuedTask.createdAt,
        estimatedCompletion: queuedTask.estimatedCompletion
      };
    }
    
    // TODO: Rechercher dans l'historique des tâches (à implémenter)
    
    return null;
  }
}

module.exports = { FinancialReportGenerator };
