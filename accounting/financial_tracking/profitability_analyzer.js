/**
 * Analyseur de rentabilité pour le restaurant "Le Vieux Moulin"
 * Analyse détaillée de la rentabilité par produit, catégorie, service, période, etc.
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const moment = require('moment');

/**
 * Classe d'analyse de rentabilité
 * @extends EventEmitter
 */
class ProfitabilityAnalyzer extends EventEmitter {
  /**
   * Crée une instance de l'analyseur de rentabilité
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataCollector - Collecteur de données
   * @param {Object} [options.configManager] - Gestionnaire de configuration
   * @param {Object} [options.inventoryCalculator] - Calculateur d'inventaire
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    if (!options.dataCollector) {
      throw new Error('Le collecteur de données est obligatoire');
    }
    
    this.dataCollector = options.dataCollector;
    this.configManager = options.configManager;
    this.inventoryCalculator = options.inventoryCalculator;
    this.logger = options.logger || console;
    
    // Charger la configuration
    this.config = this._loadConfig();
    
    // Cache des analyses pour éviter de recalculer les mêmes données
    this.analysisCache = new Map();
    this.cacheValidityDuration = 60 * 60 * 1000; // 1 heure en millisecondes
    
    this.logger.debug('ProfitabilityAnalyzer initialisé');
  }
  
  /**
   * Charge la configuration pour l'analyse de rentabilité
   * @returns {Object} Configuration
   * @private
   */
  _loadConfig() {
    if (this.configManager) {
      const profiConfig = this.configManager.getConfig('profitability_analysis');
      if (profiConfig) {
        return profiConfig;
      }
    }
    
    // Configuration par défaut
    return {
      defaultTaxRate: 0.10, // 10% de TVA pour la restauration
      alcoholTaxRate: 0.20, // 20% de TVA pour les boissons alcoolisées
      takeawayTaxRate: 0.055, // 5.5% de TVA pour les ventes à emporter
      laborCostAllocation: {
        method: 'revenue', // Allocation des coûts de main d'œuvre basée sur le chiffre d'affaires
        defaultRate: 0.30 // 30% du CA par défaut
      },
      overheadAllocation: {
        method: 'revenue', // Allocation des frais généraux basée sur le chiffre d'affaires
        defaultRate: 0.15 // 15% du CA par défaut
      },
      marginThresholds: {
        excellent: 0.70, // > 70%
        good: 0.60,      // > 60%
        average: 0.50,   // > 50%
        poor: 0.40,      // > 40%
        critical: 0.30   // > 30%
      },
      defaultAnalysisDimensions: ['product', 'category', 'period', 'service_type'],
      cacheEnabled: true,
      cacheValidityDuration: 60 * 60 * 1000 // 1 heure en millisecondes
    };
  }
  
  /**
   * Analyse la rentabilité globale du restaurant
   * @param {Object} options - Options d'analyse
   * @param {Date} options.startDate - Date de début de l'analyse
   * @param {Date} options.endDate - Date de fin de l'analyse
   * @param {Array<string>} [options.dimensions] - Dimensions d'analyse supplémentaires
   * @param {boolean} [options.includeDetails=false] - Inclure les détails par dimension
   * @param {boolean} [options.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résultats de l'analyse
   */
  async analyzeOverallProfitability({ startDate, endDate, dimensions, includeDetails = false, useCache = true }) {
    this.logger.debug(`Analyse de la rentabilité globale du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Vérifier si le résultat est déjà en cache
      const cacheKey = `overall_${startDate.getTime()}_${endDate.getTime()}_${includeDetails}`;
      if (useCache && this.config.cacheEnabled) {
        const cachedResult = this._getCachedResult(cacheKey);
        if (cachedResult) {
          this.logger.debug('Résultat trouvé en cache');
          return cachedResult;
        }
      }
      
      // Récupérer les données nécessaires
      const [transactions, expenses, laborCosts] = await Promise.all([
        this.dataCollector.getTransactions({ startDate, endDate, includeItems: true }),
        this.dataCollector.getExpenses({ startDate, endDate, includeDetails: true }),
        this.dataCollector.getLaborCosts({ startDate, endDate, includeDetails: true })
      ]);
      
      // Calculer les totaux
      const totalRevenue = transactions.reduce((sum, tx) => sum + tx.total, 0);
      const totalTax = transactions.reduce((sum, tx) => sum + tx.tax, 0);
      const totalRevenueExclTax = totalRevenue - totalTax;
      
      const totalCogs = transactions.reduce((sum, tx) => {
        return sum + (tx.items || []).reduce((itemSum, item) => {
          return itemSum + (item.cost || 0) * item.quantity;
        }, 0);
      }, 0);
      
      const totalLaborCost = laborCosts.reduce((sum, cost) => sum + cost.amount, 0);
      
      const totalOverheadCost = expenses
        .filter(expense => expense.category === 'overhead')
        .reduce((sum, expense) => sum + expense.amount, 0);
      
      const totalDirectCost = expenses
        .filter(expense => expense.category === 'direct')
        .reduce((sum, expense) => sum + expense.amount, 0);
      
      // Calculer les marges et ratios
      const grossProfit = totalRevenueExclTax - totalCogs - totalDirectCost;
      const grossMargin = totalRevenueExclTax > 0 ? grossProfit / totalRevenueExclTax : 0;
      
      const operatingProfit = grossProfit - totalLaborCost - totalOverheadCost;
      const operatingMargin = totalRevenueExclTax > 0 ? operatingProfit / totalRevenueExclTax : 0;
      
      const cogsRatio = totalRevenueExclTax > 0 ? totalCogs / totalRevenueExclTax : 0;
      const laborCostRatio = totalRevenueExclTax > 0 ? totalLaborCost / totalRevenueExclTax : 0;
      const overheadCostRatio = totalRevenueExclTax > 0 ? totalOverheadCost / totalRevenueExclTax : 0;
      
      // Construire le résultat
      const result = {
        period: {
          start: startDate,
          end: endDate,
          duration: moment(endDate).diff(moment(startDate), 'days') + 1
        },
        totals: {
          revenue: {
            total: totalRevenue,
            excludingTax: totalRevenueExclTax,
            tax: totalTax
          },
          costs: {
            cogs: totalCogs,
            labor: totalLaborCost,
            overhead: totalOverheadCost,
            direct: totalDirectCost,
            total: totalCogs + totalLaborCost + totalOverheadCost + totalDirectCost
          },
          profit: {
            gross: grossProfit,
            operating: operatingProfit
          }
        },
        ratios: {
          grossMargin: grossMargin,
          operatingMargin: operatingMargin,
          cogsRatio: cogsRatio,
          laborCostRatio: laborCostRatio,
          overheadCostRatio: overheadCostRatio,
          profitRatio: operatingMargin
        },
        performance: {
          grossMargin: this._categorizeMargin(grossMargin),
          operatingMargin: this._categorizeMargin(operatingMargin)
        },
        metadata: {
          generatedAt: new Date(),
          dimensions: dimensions || this.config.defaultAnalysisDimensions
        }
      };
      
      // Ajouter les détails par dimension si demandé
      if (includeDetails) {
        result.details = await this._analyzeDetailsByDimensions({
          transactions,
          expenses,
          laborCosts,
          dimensions: dimensions || this.config.defaultAnalysisDimensions,
          startDate,
          endDate
        });
      }
      
      // Mettre en cache le résultat
      if (this.config.cacheEnabled) {
        this._cacheResult(cacheKey, result);
      }
      
      // Émettre un événement d'analyse terminée
      this.emit('analysis:complete', {
        type: 'overall',
        period: {
          start: startDate,
          end: endDate
        }
      });
      
      return result;
    } catch (error) {
      this.logger.error('Erreur lors de l\'analyse de la rentabilité globale:', error);
      
      // Émettre un événement d'erreur
      this.emit('analysis:error', {
        type: 'overall',
        error: error.message,
        details: error,
        period: {
          start: startDate,
          end: endDate
        }
      });
      
      throw error;
    }
  }
  
  /**
   * Analyse la rentabilité par produit
   * @param {Object} options - Options d'analyse
   * @param {Date} options.startDate - Date de début de l'analyse
   * @param {Date} options.endDate - Date de fin de l'analyse
   * @param {string} [options.productId] - ID du produit spécifique à analyser
   * @param {string} [options.categoryId] - ID de la catégorie de produits à analyser
   * @param {boolean} [options.includeHistorical=false] - Inclure les données historiques
   * @param {boolean} [options.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résultats de l'analyse
   */
  async analyzeProductProfitability({ startDate, endDate, productId, categoryId, includeHistorical = false, useCache = true }) {
    const scope = productId ? `produit ${productId}` : 
                 categoryId ? `catégorie ${categoryId}` : 
                 'tous les produits';
    
    this.logger.debug(`Analyse de la rentabilité par produit (${scope}) du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Vérifier si le résultat est déjà en cache
      const cacheKey = `product_${startDate.getTime()}_${endDate.getTime()}_${productId || ''}_${categoryId || ''}_${includeHistorical}`;
      if (useCache && this.config.cacheEnabled) {
        const cachedResult = this._getCachedResult(cacheKey);
        if (cachedResult) {
          this.logger.debug('Résultat trouvé en cache');
          return cachedResult;
        }
      }
      
      // Récupérer les transactions avec les détails des produits
      const transactions = await this.dataCollector.getTransactions({
        startDate,
        endDate,
        includeItems: true,
        productId,
        categoryId
      });
      
      // Récupérer les coûts des produits
      const productCosts = await this.dataCollector.getProductCosts({
        startDate,
        endDate,
        productId,
        categoryId
      });
      
      // Organiser les données par produit
      const productMap = new Map();
      
      // Traiter chaque transaction
      for (const transaction of transactions) {
        const items = transaction.items || [];
        
        for (const item of items) {
          if (!item.productId) continue;
          
          if (!productMap.has(item.productId)) {
            productMap.set(item.productId, {
              id: item.productId,
              name: item.productName || item.productId,
              category: item.category || 'Non catégorisé',
              sales: {
                quantity: 0,
                revenue: 0,
                revenueExclTax: 0,
                tax: 0
              },
              costs: {
                cogs: 0,
                labor: 0,
                overhead: 0,
                total: 0
              },
              profit: {
                gross: 0,
                operating: 0
              },
              margins: {
                gross: 0,
                operating: 0
              },
              performance: {
                grossMargin: 'N/A',
                operatingMargin: 'N/A'
              }
            });
          }
          
          const product = productMap.get(item.productId);
          
          // Mettre à jour les ventes
          product.sales.quantity += item.quantity;
          product.sales.revenue += item.totalPrice;
          
          // Calculer la TVA
          const taxRate = this._getTaxRateForProduct(item);
          const priceExclTax = item.totalPrice / (1 + taxRate);
          const tax = item.totalPrice - priceExclTax;
          
          product.sales.revenueExclTax += priceExclTax;
          product.sales.tax += tax;
          
          // Mettre à jour les coûts
          const cost = item.cost || this._getProductCost(item.productId, productCosts) || 0;
          product.costs.cogs += cost * item.quantity;
        }
      }
      
      // Calculer les coûts de main d'œuvre et frais généraux pour chaque produit
      this._allocateLaborAndOverheadCosts(productMap, startDate, endDate);
      
      // Calculer les marges et la performance pour chaque produit
      for (const product of productMap.values()) {
        // Calculer les profits
        product.profit.gross = product.sales.revenueExclTax - product.costs.cogs;
        product.profit.operating = product.profit.gross - product.costs.labor - product.costs.overhead;
        
        // Calculer les marges
        product.margins.gross = product.sales.revenueExclTax > 0 ? 
          product.profit.gross / product.sales.revenueExclTax : 0;
        product.margins.operating = product.sales.revenueExclTax > 0 ? 
          product.profit.operating / product.sales.revenueExclTax : 0;
        
        // Évaluer la performance
        product.performance.grossMargin = this._categorizeMargin(product.margins.gross);
        product.performance.operatingMargin = this._categorizeMargin(product.margins.operating);
        
        // Mettre à jour le total des coûts
        product.costs.total = product.costs.cogs + product.costs.labor + product.costs.overhead;
      }
      
      // Convertir la map en tableau et trier par marge opérationnelle décroissante
      const productAnalysis = Array.from(productMap.values())
        .sort((a, b) => b.margins.operating - a.margins.operating);
      
      // Ajouter des données historiques si demandé
      let historicalData = null;
      if (includeHistorical) {
        historicalData = await this._getHistoricalProductData({
          productId,
          categoryId,
          endDate: startDate // Utiliser la date de début comme fin pour les données historiques
        });
      }
      
      // Construire le résultat
      const result = {
        period: {
          start: startDate,
          end: endDate,
          duration: moment(endDate).diff(moment(startDate), 'days') + 1
        },
        filter: {
          productId: productId || null,
          categoryId: categoryId || null
        },
        products: productAnalysis,
        summary: {
          productCount: productAnalysis.length,
          totalSales: {
            quantity: productAnalysis.reduce((sum, p) => sum + p.sales.quantity, 0),
            revenue: productAnalysis.reduce((sum, p) => sum + p.sales.revenue, 0),
            revenueExclTax: productAnalysis.reduce((sum, p) => sum + p.sales.revenueExclTax, 0)
          },
          totalCosts: {
            cogs: productAnalysis.reduce((sum, p) => sum + p.costs.cogs, 0),
            labor: productAnalysis.reduce((sum, p) => sum + p.costs.labor, 0),
            overhead: productAnalysis.reduce((sum, p) => sum + p.costs.overhead, 0),
            total: productAnalysis.reduce((sum, p) => sum + p.costs.total, 0)
          },
          totalProfit: {
            gross: productAnalysis.reduce((sum, p) => sum + p.profit.gross, 0),
            operating: productAnalysis.reduce((sum, p) => sum + p.profit.operating, 0)
          },
          averageMargins: {
            gross: productAnalysis.length > 0 ? 
              productAnalysis.reduce((sum, p) => sum + p.margins.gross, 0) / productAnalysis.length : 0,
            operating: productAnalysis.length > 0 ? 
              productAnalysis.reduce((sum, p) => sum + p.margins.operating, 0) / productAnalysis.length : 0
          },
          performanceDistribution: {
            excellent: productAnalysis.filter(p => p.performance.operatingMargin === 'excellent').length,
            good: productAnalysis.filter(p => p.performance.operatingMargin === 'good').length,
            average: productAnalysis.filter(p => p.performance.operatingMargin === 'average').length,
            poor: productAnalysis.filter(p => p.performance.operatingMargin === 'poor').length,
            critical: productAnalysis.filter(p => p.performance.operatingMargin === 'critical').length
          }
        },
        metadata: {
          generatedAt: new Date()
        }
      };
      
      // Ajouter les données historiques si présentes
      if (historicalData) {
        result.historical = historicalData;
      }
      
      // Mettre en cache le résultat
      if (this.config.cacheEnabled) {
        this._cacheResult(cacheKey, result);
      }
      
      // Émettre un événement d'analyse terminée
      this.emit('analysis:complete', {
        type: 'product',
        period: {
          start: startDate,
          end: endDate
        },
        filter: {
          productId: productId || null,
          categoryId: categoryId || null
        }
      });
      
      return result;
    } catch (error) {
      this.logger.error('Erreur lors de l\'analyse de la rentabilité par produit:', error);
      
      // Émettre un événement d'erreur
      this.emit('analysis:error', {
        type: 'product',
        error: error.message,
        details: error,
        period: {
          start: startDate,
          end: endDate
        },
        filter: {
          productId: productId || null,
          categoryId: categoryId || null
        }
      });
      
      throw error;
    }
  }
  
  /**
   * Analyse la rentabilité par service
   * @param {Object} options - Options d'analyse
   * @param {Date} options.startDate - Date de début de l'analyse
   * @param {Date} options.endDate - Date de fin de l'analyse
   * @param {string} [options.serviceType] - Type de service à analyser (midi, soir, etc.)
   * @param {boolean} [options.includeDetails=false] - Inclure les détails par jour
   * @param {boolean} [options.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résultats de l'analyse
   */
  async analyzeServiceProfitability({ startDate, endDate, serviceType, includeDetails = false, useCache = true }) {
    const scope = serviceType ? `service ${serviceType}` : 'tous les services';
    
    this.logger.debug(`Analyse de la rentabilité par service (${scope}) du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Vérifier si le résultat est déjà en cache
      const cacheKey = `service_${startDate.getTime()}_${endDate.getTime()}_${serviceType || ''}_${includeDetails}`;
      if (useCache && this.config.cacheEnabled) {
        const cachedResult = this._getCachedResult(cacheKey);
        if (cachedResult) {
          this.logger.debug('Résultat trouvé en cache');
          return cachedResult;
        }
      }
      
      // Récupérer les transactions
      const transactions = await this.dataCollector.getTransactions({
        startDate,
        endDate,
        includeItems: true,
        serviceType
      });
      
      // Récupérer les coûts de main d'œuvre et ventilés par service
      const laborCosts = await this.dataCollector.getLaborCosts({
        startDate,
        endDate,
        includeDetails: true,
        groupBy: 'service'
      });
      
      // Organiser les données par type de service
      const serviceMap = new Map();
      
      // Définir les types de service par défaut si aucun n'est trouvé
      const defaultServiceTypes = ['midi', 'soir'];
      
      // Traiter chaque transaction
      for (const transaction of transactions) {
        const serviceId = transaction.serviceType || this._determineServiceType(transaction);
        
        if (!serviceMap.has(serviceId)) {
          serviceMap.set(serviceId, {
            id: serviceId,
            name: this._getServiceName(serviceId),
            transactions: 0,
            revenue: {
              total: 0,
              excludingTax: 0,
              tax: 0
            },
            costs: {
              cogs: 0,
              labor: 0,
              overhead: 0,
              total: 0
            },
            profit: {
              gross: 0,
              operating: 0
            },
            margins: {
              gross: 0,
              operating: 0
            },
            customers: 0,
            averageTicket: 0,
            performance: {
              grossMargin: 'N/A',
              operatingMargin: 'N/A'
            }
          });
        }
        
        const service = serviceMap.get(serviceId);
        
        // Mettre à jour les données de transaction
        service.transactions++;
        service.revenue.total += transaction.total;
        service.revenue.tax += transaction.tax || 0;
        service.revenue.excludingTax = service.revenue.total - service.revenue.tax;
        service.customers += transaction.customerCount || 1;
        
        // Calculer le coût des marchandises vendues
        const items = transaction.items || [];
        for (const item of items) {
          service.costs.cogs += (item.cost || 0) * item.quantity;
        }
      }
      
      // Ajouter les coûts de main d'œuvre par service
      for (const laborCost of laborCosts) {
        if (laborCost.serviceType && serviceMap.has(laborCost.serviceType)) {
          serviceMap.get(laborCost.serviceType).costs.labor += laborCost.amount;
        }
      }
      
      // Allouer les frais généraux à chaque service
      this._allocateOverheadToServices(serviceMap, startDate, endDate);
      
      // Calculer les métriques finales pour chaque service
      for (const service of serviceMap.values()) {
        // Calculer les profits
        service.profit.gross = service.revenue.excludingTax - service.costs.cogs;
        service.profit.operating = service.profit.gross - service.costs.labor - service.costs.overhead;
        
        // Calculer les marges
        service.margins.gross = service.revenue.excludingTax > 0 ? 
          service.profit.gross / service.revenue.excludingTax : 0;
        service.margins.operating = service.revenue.excludingTax > 0 ? 
          service.profit.operating / service.revenue.excludingTax : 0;
        
        // Calculer le ticket moyen
        service.averageTicket = service.customers > 0 ? 
          service.revenue.total / service.customers : 0;
        
        // Évaluer la performance
        service.performance.grossMargin = this._categorizeMargin(service.margins.gross);
        service.performance.operatingMargin = this._categorizeMargin(service.margins.operating);
        
        // Mettre à jour le total des coûts
        service.costs.total = service.costs.cogs + service.costs.labor + service.costs.overhead;
      }
      
      // Ajouter les services par défaut s'ils n'existent pas
      for (const serviceType of defaultServiceTypes) {
        if (!serviceMap.has(serviceType)) {
          serviceMap.set(serviceType, {
            id: serviceType,
            name: this._getServiceName(serviceType),
            transactions: 0,
            revenue: { total: 0, excludingTax: 0, tax: 0 },
            costs: { cogs: 0, labor: 0, overhead: 0, total: 0 },
            profit: { gross: 0, operating: 0 },
            margins: { gross: 0, operating: 0 },
            customers: 0,
            averageTicket: 0,
            performance: { grossMargin: 'N/A', operatingMargin: 'N/A' }
          });
        }
      }
      
      // Convertir la map en tableau et trier par chiffre d'affaires décroissant
      const serviceAnalysis = Array.from(serviceMap.values())
        .sort((a, b) => b.revenue.total - a.revenue.total);
      
      // Construire le résultat
      const result = {
        period: {
          start: startDate,
          end: endDate,
          duration: moment(endDate).diff(moment(startDate), 'days') + 1
        },
        filter: {
          serviceType: serviceType || null
        },
        services: serviceAnalysis,
        summary: {
          serviceCount: serviceAnalysis.length,
          totalTransactions: serviceAnalysis.reduce((sum, s) => sum + s.transactions, 0),
          totalRevenue: {
            total: serviceAnalysis.reduce((sum, s) => sum + s.revenue.total, 0),
            excludingTax: serviceAnalysis.reduce((sum, s) => sum + s.revenue.excludingTax, 0),
            tax: serviceAnalysis.reduce((sum, s) => sum + s.revenue.tax, 0)
          },
          totalCosts: {
            cogs: serviceAnalysis.reduce((sum, s) => sum + s.costs.cogs, 0),
            labor: serviceAnalysis.reduce((sum, s) => sum + s.costs.labor, 0),
            overhead: serviceAnalysis.reduce((sum, s) => sum + s.costs.overhead, 0),
            total: serviceAnalysis.reduce((sum, s) => sum + s.costs.total, 0)
          },
          totalProfit: {
            gross: serviceAnalysis.reduce((sum, s) => sum + s.profit.gross, 0),
            operating: serviceAnalysis.reduce((sum, s) => sum + s.profit.operating, 0)
          },
          totalCustomers: serviceAnalysis.reduce((sum, s) => sum + s.customers, 0),
          averageTicket: serviceAnalysis.reduce((sum, s) => sum + s.revenue.total, 0) / 
            serviceAnalysis.reduce((sum, s) => sum + s.customers, 0) || 0
        },
        metadata: {
          generatedAt: new Date()
        }
      };
      
      // Ajouter les détails par jour si demandé
      if (includeDetails) {
        result.details = await this._analyzeServiceDetailsByDay({
          transactions,
          laborCosts,
          startDate,
          endDate,
          serviceType
        });
      }
      
      // Mettre en cache le résultat
      if (this.config.cacheEnabled) {
        this._cacheResult(cacheKey, result);
      }
      
      // Émettre un événement d'analyse terminée
      this.emit('analysis:complete', {
        type: 'service',
        period: {
          start: startDate,
          end: endDate
        },
        filter: {
          serviceType: serviceType || null
        }
      });
      
      return result;
    } catch (error) {
      this.logger.error('Erreur lors de l\'analyse de la rentabilité par service:', error);
      
      // Émettre un événement d'erreur
      this.emit('analysis:error', {
        type: 'service',
        error: error.message,
        details: error,
        period: {
          start: startDate,
          end: endDate
        },
        filter: {
          serviceType: serviceType || null
        }
      });
      
      throw error;
    }
  }
  
  /**
   * Analyse la rentabilité par période (jour, semaine, mois)
   * @param {Object} options - Options d'analyse
   * @param {Date} options.startDate - Date de début de l'analyse
   * @param {Date} options.endDate - Date de fin de l'analyse
   * @param {string} [options.periodType='day'] - Type de période ('day', 'week', 'month')
   * @param {boolean} [options.includeTrends=false] - Inclure les tendances
   * @param {boolean} [options.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résultats de l'analyse
   */
  async analyzePeriodProfitability({ startDate, endDate, periodType = 'day', includeTrends = false, useCache = true }) {
    this.logger.debug(`Analyse de la rentabilité par ${periodType} du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Vérifier si le résultat est déjà en cache
      const cacheKey = `period_${startDate.getTime()}_${endDate.getTime()}_${periodType}_${includeTrends}`;
      if (useCache && this.config.cacheEnabled) {
        const cachedResult = this._getCachedResult(cacheKey);
        if (cachedResult) {
          this.logger.debug('Résultat trouvé en cache');
          return cachedResult;
        }
      }
      
      // Récupérer les données nécessaires
      const [transactions, expenses, laborCosts] = await Promise.all([
        this.dataCollector.getTransactions({ startDate, endDate, includeItems: true }),
        this.dataCollector.getExpenses({ startDate, endDate, includeDetails: true }),
        this.dataCollector.getLaborCosts({ startDate, endDate, includeDetails: true })
      ]);
      
      // Fonction pour obtenir la clé de période
      const getPeriodKey = (date) => {
        if (periodType === 'day') {
          return moment(date).format('YYYY-MM-DD');
        } else if (periodType === 'week') {
          // ISO week (lundi-dimanche)
          return `${moment(date).isoWeekYear()}-W${moment(date).isoWeek()}`;
        } else if (periodType === 'month') {
          return moment(date).format('YYYY-MM');
        }
        return moment(date).format('YYYY-MM-DD'); // Par défaut: jour
      };
      
      // Fonction pour obtenir le nom de la période
      const getPeriodName = (key) => {
        if (periodType === 'day') {
          return moment(key).format('DD/MM/YYYY');
        } else if (periodType === 'week') {
          const [year, week] = key.split('-W');
          return `Semaine ${week} ${year}`;
        } else if (periodType === 'month') {
          return moment(key).format('MMMM YYYY');
        }
        return key;
      };
      
      // Organiser les données par période
      const periodMap = new Map();
      
      // Initialiser toutes les périodes entre startDate et endDate
      let currentDate = moment(startDate);
      const lastDate = moment(endDate);
      
      while (currentDate.isSameOrBefore(lastDate, 'day')) {
        const key = getPeriodKey(currentDate.toDate());
        
        if (!periodMap.has(key)) {
          periodMap.set(key, {
            key,
            name: getPeriodName(key),
            startDate: null,
            endDate: null,
            transactions: 0,
            revenue: {
              total: 0,
              excludingTax: 0,
              tax: 0
            },
            costs: {
              cogs: 0,
              labor: 0,
              overhead: 0,
              direct: 0,
              total: 0
            },
            profit: {
              gross: 0,
              operating: 0
            },
            margins: {
              gross: 0,
              operating: 0
            },
            customers: 0,
            performance: {
              grossMargin: 'N/A',
              operatingMargin: 'N/A'
            }
          });
        }
        
        // Avancer à la période suivante
        if (periodType === 'day') {
          currentDate.add(1, 'day');
        } else if (periodType === 'week') {
          currentDate.add(1, 'week');
        } else if (periodType === 'month') {
          currentDate.add(1, 'month');
        } else {
          currentDate.add(1, 'day');
        }
      }
      
      // Traiter les transactions
      for (const transaction of transactions) {
        const key = getPeriodKey(transaction.date);
        
        if (!periodMap.has(key)) continue;
        
        const period = periodMap.get(key);
        
        // Mettre à jour les dates de la période
        if (!period.startDate || transaction.date < period.startDate) {
          period.startDate = new Date(transaction.date);
        }
        if (!period.endDate || transaction.date > period.endDate) {
          period.endDate = new Date(transaction.date);
        }
        
        // Mettre à jour les données de transaction
        period.transactions++;
        period.revenue.total += transaction.total;
        period.revenue.tax += transaction.tax || 0;
        period.revenue.excludingTax = period.revenue.total - period.revenue.tax;
        period.customers += transaction.customerCount || 1;
        
        // Calculer le coût des marchandises vendues
        const items = transaction.items || [];
        for (const item of items) {
          period.costs.cogs += (item.cost || 0) * item.quantity;
        }
      }
      
      // Traiter les dépenses
      for (const expense of expenses) {
        const key = getPeriodKey(expense.date);
        
        if (!periodMap.has(key)) continue;
        
        const period = periodMap.get(key);
        
        // Classer les dépenses
        if (expense.category === 'overhead') {
          period.costs.overhead += expense.amount;
        } else if (expense.category === 'direct') {
          period.costs.direct += expense.amount;
        }
      }
      
      // Traiter les coûts de main d'œuvre
      for (const laborCost of laborCosts) {
        const key = getPeriodKey(laborCost.date);
        
        if (!periodMap.has(key)) continue;
        
        const period = periodMap.get(key);
        
        // Ajouter les coûts de main d'œuvre
        period.costs.labor += laborCost.amount;
      }
      
      // Calculer les métriques finales pour chaque période
      for (const period of periodMap.values()) {
        // Calculer les profits
        period.profit.gross = period.revenue.excludingTax - period.costs.cogs - period.costs.direct;
        period.profit.operating = period.profit.gross - period.costs.labor - period.costs.overhead;
        
        // Calculer les marges
        period.margins.gross = period.revenue.excludingTax > 0 ? 
          period.profit.gross / period.revenue.excludingTax : 0;
        period.margins.operating = period.revenue.excludingTax > 0 ? 
          period.profit.operating / period.revenue.excludingTax : 0;
        
        // Évaluer la performance
        period.performance.grossMargin = this._categorizeMargin(period.margins.gross);
        period.performance.operatingMargin = this._categorizeMargin(period.margins.operating);
        
        // Mettre à jour le total des coûts
        period.costs.total = period.costs.cogs + period.costs.labor + period.costs.overhead + period.costs.direct;
      }
      
      // Convertir la map en tableau et trier par période
      const periodAnalysis = Array.from(periodMap.values())
        .filter(period => period.transactions > 0 || period.costs.total > 0) // Ne garder que les périodes avec activité
        .sort((a, b) => a.key.localeCompare(b.key));
      
      // Calculer les tendances si demandé
      let trends = null;
      if (includeTrends && periodAnalysis.length > 1) {
        trends = this._calculatePeriodTrends(periodAnalysis);
      }
      
      // Construire le résultat
      const result = {
        period: {
          start: startDate,
          end: endDate,
          duration: moment(endDate).diff(moment(startDate), 'days') + 1,
          type: periodType
        },
        periods: periodAnalysis,
        summary: {
          periodCount: periodAnalysis.length,
          totalTransactions: periodAnalysis.reduce((sum, p) => sum + p.transactions, 0),
          totalRevenue: {
            total: periodAnalysis.reduce((sum, p) => sum + p.revenue.total, 0),
            excludingTax: periodAnalysis.reduce((sum, p) => sum + p.revenue.excludingTax, 0),
            tax: periodAnalysis.reduce((sum, p) => sum + p.revenue.tax, 0)
          },
          totalCosts: {
            cogs: periodAnalysis.reduce((sum, p) => sum + p.costs.cogs, 0),
            labor: periodAnalysis.reduce((sum, p) => sum + p.costs.labor, 0),
            overhead: periodAnalysis.reduce((sum, p) => sum + p.costs.overhead, 0),
            direct: periodAnalysis.reduce((sum, p) => sum + p.costs.direct, 0),
            total: periodAnalysis.reduce((sum, p) => sum + p.costs.total, 0)
          },
          totalProfit: {
            gross: periodAnalysis.reduce((sum, p) => sum + p.profit.gross, 0),
            operating: periodAnalysis.reduce((sum, p) => sum + p.profit.operating, 0)
          },
          averageMargins: {
            gross: periodAnalysis.length > 0 ? 
              periodAnalysis.reduce((sum, p) => sum + p.margins.gross, 0) / periodAnalysis.length : 0,
            operating: periodAnalysis.length > 0 ? 
              periodAnalysis.reduce((sum, p) => sum + p.margins.operating, 0) / periodAnalysis.length : 0
          }
        },
        metadata: {
          generatedAt: new Date()
        }
      };
      
      // Ajouter les tendances si calculées
      if (trends) {
        result.trends = trends;
      }
      
      // Mettre en cache le résultat
      if (this.config.cacheEnabled) {
        this._cacheResult(cacheKey, result);
      }
      
      // Émettre un événement d'analyse terminée
      this.emit('analysis:complete', {
        type: 'period',
        period: {
          start: startDate,
          end: endDate,
          type: periodType
        }
      });
      
      return result;
    } catch (error) {
      this.logger.error('Erreur lors de l\'analyse de la rentabilité par période:', error);
      
      // Émettre un événement d'erreur
      this.emit('analysis:error', {
        type: 'period',
        error: error.message,
        details: error,
        period: {
          start: startDate,
          end: endDate,
          type: periodType
        }
      });
      
      throw error;
    }
  }
  
  /**
   * Analyse la contribution d'un produit ou d'une catégorie
   * @param {Object} options - Options d'analyse
   * @param {Date} options.startDate - Date de début de l'analyse
   * @param {Date} options.endDate - Date de fin de l'analyse
   * @param {string} options.targetId - ID du produit ou de la catégorie
   * @param {string} options.targetType - Type de cible ('product' ou 'category')
   * @param {boolean} [options.useCache=true] - Utiliser le cache si disponible
   * @returns {Promise<Object>} Résultats de l'analyse
   */
  async analyzeContribution({ startDate, endDate, targetId, targetType, useCache = true }) {
    this.logger.debug(`Analyse de la contribution du ${targetType} ${targetId} du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Vérifier si le résultat est déjà en cache
      const cacheKey = `contribution_${startDate.getTime()}_${endDate.getTime()}_${targetType}_${targetId}`;
      if (useCache && this.config.cacheEnabled) {
        const cachedResult = this._getCachedResult(cacheKey);
        if (cachedResult) {
          this.logger.debug('Résultat trouvé en cache');
          return cachedResult;
        }
      }
      
      // Récupérer l'analyse globale
      const overallAnalysis = await this.analyzeOverallProfitability({
        startDate,
        endDate,
        useCache
      });
      
      // Récupérer l'analyse du produit ou de la catégorie
      let targetAnalysis;
      if (targetType === 'product') {
        targetAnalysis = await this.analyzeProductProfitability({
          startDate,
          endDate,
          productId: targetId,
          useCache
        });
      } else if (targetType === 'category') {
        targetAnalysis = await this.analyzeProductProfitability({
          startDate,
          endDate,
          categoryId: targetId,
          useCache
        });
      } else {
        throw new Error(`Type de cible non pris en charge: ${targetType}`);
      }
      
      // Extraire les données de la cible
      const targetData = targetType === 'product' ? 
        targetAnalysis.products.find(p => p.id === targetId) : 
        {
          id: targetId,
          name: targetAnalysis.filter.categoryId,
          sales: targetAnalysis.summary.totalSales,
          costs: targetAnalysis.summary.totalCosts,
          profit: targetAnalysis.summary.totalProfit,
          margins: targetAnalysis.summary.averageMargins
        };
      
      if (!targetData) {
        throw new Error(`${targetType} ${targetId} non trouvé dans les données analysées`);
      }
      
      // Calculer les contributions
      const revenueContribution = targetData.sales.revenue / overallAnalysis.totals.revenue.total;
      const profitContribution = targetData.profit.operating / overallAnalysis.totals.profit.operating;
      
      // Construire le résultat
      const result = {
        period: {
          start: startDate,
          end: endDate,
          duration: moment(endDate).diff(moment(startDate), 'days') + 1
        },
        target: {
          id: targetId,
          type: targetType,
          name: targetData.name
        },
        metrics: {
          sales: targetData.sales,
          costs: targetData.costs,
          profit: targetData.profit,
          margins: targetData.margins || {
            gross: targetData.profit.gross / targetData.sales.revenueExclTax,
            operating: targetData.profit.operating / targetData.sales.revenueExclTax
          }
        },
        contribution: {
          revenue: revenueContribution,
          profit: profitContribution,
          profitToRevenueRatio: profitContribution / revenueContribution
        },
        comparisonToAverage: {
          grossMargin: targetData.margins.gross / overallAnalysis.ratios.grossMargin,
          operatingMargin: targetData.margins.operating / overallAnalysis.ratios.operatingMargin
        },
        metadata: {
          generatedAt: new Date()
        }
      };
      
      // Mettre en cache le résultat
      if (this.config.cacheEnabled) {
        this._cacheResult(cacheKey, result);
      }
      
      // Émettre un événement d'analyse terminée
      this.emit('analysis:complete', {
        type: 'contribution',
        period: {
          start: startDate,
          end: endDate
        },
        target: {
          id: targetId,
          type: targetType
        }
      });
      
      return result;
    } catch (error) {
      this.logger.error('Erreur lors de l\'analyse de contribution:', error);
      
      // Émettre un événement d'erreur
      this.emit('analysis:error', {
        type: 'contribution',
        error: error.message,
        details: error,
        period: {
          start: startDate,
          end: endDate
        },
        target: {
          id: targetId,
          type: targetType
        }
      });
      
      throw error;
    }
  }
  
  /**
   * Génère un rapport de rentabilité au format spécifié
   * @param {Object} options - Options de rapport
   * @param {Object} options.analysisResult - Résultat d'analyse
   * @param {string} options.analysisType - Type d'analyse ('overall', 'product', 'service', 'period', 'contribution')
   * @param {string} options.format - Format du rapport ('json', 'csv', 'excel', 'pdf')
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<string>} Chemin du fichier généré
   */
  async generateProfitabilityReport({ analysisResult, analysisType, format, outputPath }) {
    this.logger.debug(`Génération du rapport de rentabilité de type ${analysisType} au format ${format}`);
    
    try {
      // Vérifier le type d'analyse
      if (!['overall', 'product', 'service', 'period', 'contribution'].includes(analysisType)) {
        throw new Error(`Type d'analyse non pris en charge: ${analysisType}`);
      }
      
      // Sélectionner la méthode d'export en fonction du format
      let exportFunction;
      
      switch (format.toLowerCase()) {
        case 'json':
          exportFunction = this._exportReportToJSON;
          break;
        case 'csv':
          exportFunction = this._exportReportToCSV;
          break;
        case 'excel':
          exportFunction = this._exportReportToExcel;
          break;
        case 'pdf':
          exportFunction = this._exportReportToPDF;
          break;
        default:
          throw new Error(`Format de rapport non pris en charge: ${format}`);
      }
      
      // Effectuer l'export
      await exportFunction.call(this, {
        analysisResult,
        analysisType,
        outputPath
      });
      
      // Émettre un événement de génération terminée
      this.emit('report:complete', {
        type: analysisType,
        format,
        path: outputPath
      });
      
      return outputPath;
    } catch (error) {
      this.logger.error(`Erreur lors de la génération du rapport de rentabilité:`, error);
      
      // Émettre un événement d'erreur
      this.emit('report:error', {
        type: analysisType,
        format,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Détermine le type de service pour une transaction
   * @param {Object} transaction - Transaction à analyser
   * @returns {string} Type de service identifié
   * @private
   */
  _determineServiceType(transaction) {
    // Par défaut, déterminer le service en fonction de l'heure
    const hour = moment(transaction.date).hour();
    
    if (hour >= 11 && hour < 15) {
      return 'midi';
    } else if (hour >= 18 && hour < 23) {
      return 'soir';
    } else {
      return 'autre';
    }
  }
  
  /**
   * Obtient le nom complet d'un type de service
   * @param {string} serviceId - Identifiant du service
   * @returns {string} Nom complet du service
   * @private
   */
  _getServiceName(serviceId) {
    const serviceNames = {
      'midi': 'Service du midi',
      'soir': 'Service du soir',
      'brunch': 'Brunch',
      'petit-dejeuner': 'Petit-déjeuner',
      'emporter': 'Vente à emporter',
      'livraison': 'Livraison',
      'autre': 'Autre service'
    };
    
    return serviceNames[serviceId] || serviceId;
  }
  
  /**
   * Obtient le taux de TVA pour un produit
   * @param {Object} item - Élément de produit
   * @returns {number} Taux de TVA (ex: 0.10 pour 10%)
   * @private
   */
  _getTaxRateForProduct(item) {
    // Si le taux de TVA est déjà spécifié
    if (item.taxRate !== undefined) {
      return item.taxRate;
    }
    
    // Déterminer en fonction de la catégorie et du type de service
    if (item.category === 'alcool' || item.category === 'alcohol') {
      return this.config.alcoholTaxRate;
    } else if (item.serviceType === 'emporter' || item.serviceType === 'takeaway') {
      return this.config.takeawayTaxRate;
    } else {
      return this.config.defaultTaxRate;
    }
  }
  
  /**
   * Obtient le coût d'un produit
   * @param {string} productId - ID du produit
   * @param {Array} productCosts - Liste des coûts de produits
   * @returns {number|null} Coût du produit ou null si non trouvé
   * @private
   */
  _getProductCost(productId, productCosts) {
    const productCost = productCosts.find(pc => pc.productId === productId);
    return productCost ? productCost.cost : null;
  }
  
  /**
   * Alloue les coûts de main d'œuvre et frais généraux aux produits
   * @param {Map} productMap - Map des produits
   * @param {Date} startDate - Date de début
   * @param {Date} endDate - Date de fin
   * @private
   */
  _allocateLaborAndOverheadCosts(productMap, startDate, endDate) {
    // Calculer le chiffre d'affaires total
    const totalRevenue = Array.from(productMap.values())
      .reduce((sum, product) => sum + product.sales.revenueExclTax, 0);
    
    if (totalRevenue <= 0) return;
    
    // Récupérer les méthodes d'allocation
    const laborMethod = this.config.laborCostAllocation.method;
    const overheadMethod = this.config.overheadAllocation.method;
    
    // Calculer les coûts totaux à allouer
    let totalLaborCost = 0;
    let totalOverheadCost = 0;
    
    if (this.dataCollector) {
      // Récupérer les coûts de main d'œuvre et frais généraux pour la période
      Promise.all([
        this.dataCollector.getLaborCosts({ startDate, endDate }),
        this.dataCollector.getExpenses({ 
          startDate, 
          endDate, 
          category: 'overhead'
        })
      ]).then(([laborCosts, overheadExpenses]) => {
        totalLaborCost = laborCosts.reduce((sum, cost) => sum + cost.amount, 0);
        totalOverheadCost = overheadExpenses.reduce((sum, expense) => sum + expense.amount, 0);
      }).catch(error => {
        this.logger.error('Erreur lors de la récupération des coûts pour allocation:', error);
        
        // Utiliser les taux par défaut si erreur
        totalLaborCost = totalRevenue * this.config.laborCostAllocation.defaultRate;
        totalOverheadCost = totalRevenue * this.config.overheadAllocation.defaultRate;
      });
    } else {
      // Utiliser les taux par défaut si pas de collecteur de données
      totalLaborCost = totalRevenue * this.config.laborCostAllocation.defaultRate;
      totalOverheadCost = totalRevenue * this.config.overheadAllocation.defaultRate;
    }
    
    // Allouer les coûts à chaque produit
    for (const product of productMap.values()) {
      // Allocation basée sur le chiffre d'affaires
      if (laborMethod === 'revenue') {
        const revenueShare = product.sales.revenueExclTax / totalRevenue;
        product.costs.labor = totalLaborCost * revenueShare;
      }
      
      if (overheadMethod === 'revenue') {
        const revenueShare = product.sales.revenueExclTax / totalRevenue;
        product.costs.overhead = totalOverheadCost * revenueShare;
      }
      
      // Autres méthodes d'allocation pourraient être implémentées ici
    }
  }
  
  /**
   * Alloue les frais généraux aux services
   * @param {Map} serviceMap - Map des services
   * @param {Date} startDate - Date de début
   * @param {Date} endDate - Date de fin
   * @private
   */
  _allocateOverheadToServices(serviceMap, startDate, endDate) {
    // Calculer le chiffre d'affaires total
    const totalRevenue = Array.from(serviceMap.values())
      .reduce((sum, service) => sum + service.revenue.excludingTax, 0);
    
    if (totalRevenue <= 0) return;
    
    // Calculer les frais généraux totaux à allouer
    let totalOverheadCost = 0;
    
    if (this.dataCollector) {
      // Récupérer les frais généraux pour la période
      this.dataCollector.getExpenses({ 
        startDate, 
        endDate, 
        category: 'overhead'
      }).then(overheadExpenses => {
        totalOverheadCost = overheadExpenses.reduce((sum, expense) => sum + expense.amount, 0);
      }).catch(error => {
        this.logger.error('Erreur lors de la récupération des frais généraux pour allocation:', error);
        
        // Utiliser le taux par défaut si erreur
        totalOverheadCost = totalRevenue * this.config.overheadAllocation.defaultRate;
      });
    } else {
      // Utiliser le taux par défaut si pas de collecteur de données
      totalOverheadCost = totalRevenue * this.config.overheadAllocation.defaultRate;
    }
    
    // Allouer les frais généraux à chaque service
    for (const service of serviceMap.values()) {
      const revenueShare = service.revenue.excludingTax / totalRevenue;
      service.costs.overhead = totalOverheadCost * revenueShare;
    }
  }
  
  /**
   * Catégorise la marge selon les seuils configurés
   * @param {number} margin - Marge à catégoriser
   * @returns {string} Catégorie de marge
   * @private
   */
  _categorizeMargin(margin) {
    const thresholds = this.config.marginThresholds;
    
    if (margin >= thresholds.excellent) return 'excellent';
    if (margin >= thresholds.good) return 'good';
    if (margin >= thresholds.average) return 'average';
    if (margin >= thresholds.poor) return 'poor';
    if (margin >= thresholds.critical) return 'critical';
    return 'unacceptable';
  }
  
  /**
   * Analyse les détails par dimensions
   * @param {Object} options - Options d'analyse
   * @param {Array} options.transactions - Transactions
   * @param {Array} options.expenses - Dépenses
   * @param {Array} options.laborCosts - Coûts de main d'œuvre
   * @param {Array} options.dimensions - Dimensions à analyser
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Détails par dimension
   * @private
   */
  async _analyzeDetailsByDimensions({ transactions, expenses, laborCosts, dimensions, startDate, endDate }) {
    const details = {};
    
    // Récupérer les données pour chaque dimension
    for (const dimension of dimensions) {
      switch (dimension) {
        case 'product':
          details.products = await this.analyzeProductProfitability({
            startDate,
            endDate,
            useCache: true
          });
          break;
        case 'category':
          // Récupérer les catégories de produits uniques
          const categories = [...new Set(transactions
            .flatMap(tx => tx.items || [])
            .map(item => item.category)
            .filter(Boolean))];
          
          details.categories = await Promise.all(
            categories.map(categoryId => this.analyzeProductProfitability({
              startDate,
              endDate,
              categoryId,
              useCache: true
            }))
          );
          break;
        case 'service_type':
          details.services = await this.analyzeServiceProfitability({
            startDate,
            endDate,
            useCache: true
          });
          break;
        case 'period':
          details.periods = await this.analyzePeriodProfitability({
            startDate,
            endDate,
            periodType: 'day',
            useCache: true
          });
          break;
        default:
          this.logger.warn(`Dimension non prise en charge: ${dimension}`);
      }
    }
    
    return details;
  }
  
  /**
   * Analyse les détails de service par jour
   * @param {Object} options - Options d'analyse
   * @param {Array} options.transactions - Transactions
   * @param {Array} options.laborCosts - Coûts de main d'œuvre
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @param {string} [options.serviceType] - Type de service à analyser
   * @returns {Promise<Object>} Détails par jour
   * @private
   */
  async _analyzeServiceDetailsByDay({ transactions, laborCosts, startDate, endDate, serviceType }) {
    // Organiser les données par jour
    const dayMap = new Map();
    
    // Initialiser tous les jours entre startDate et endDate
    let currentDate = moment(startDate);
    const lastDate = moment(endDate);
    
    while (currentDate.isSameOrBefore(lastDate, 'day')) {
      const key = currentDate.format('YYYY-MM-DD');
      
      dayMap.set(key, {
        date: currentDate.toDate(),
        services: new Map()
      });
      
      // Avancer au jour suivant
      currentDate.add(1, 'day');
    }
    
    // Traiter les transactions
    for (const transaction of transactions) {
      const dateKey = moment(transaction.date).format('YYYY-MM-DD');
      const service = transaction.serviceType || this._determineServiceType(transaction);
      
      // Filtrer par type de service si spécifié
      if (serviceType && service !== serviceType) continue;
      
      if (!dayMap.has(dateKey)) continue;
      
      const day = dayMap.get(dateKey);
      
      if (!day.services.has(service)) {
        day.services.set(service, {
          id: service,
          name: this._getServiceName(service),
          transactions: 0,
          revenue: {
            total: 0,
            excludingTax: 0,
            tax: 0
          },
          costs: {
            cogs: 0,
            labor: 0,
            overhead: 0,
            total: 0
          },
          customers: 0
        });
      }
      
      const serviceData = day.services.get(service);
      
      // Mettre à jour les données de transaction
      serviceData.transactions++;
      serviceData.revenue.total += transaction.total;
      serviceData.revenue.tax += transaction.tax || 0;
      serviceData.revenue.excludingTax = serviceData.revenue.total - serviceData.revenue.tax;
      serviceData.customers += transaction.customerCount || 1;
      
      // Calculer le coût des marchandises vendues
      const items = transaction.items || [];
      for (const item of items) {
        serviceData.costs.cogs += (item.cost || 0) * item.quantity;
      }
    }
    
    // Traiter les coûts de main d'œuvre
    for (const laborCost of laborCosts) {
      const dateKey = moment(laborCost.date).format('YYYY-MM-DD');
      
      if (!dayMap.has(dateKey)) continue;
      
      const day = dayMap.get(dateKey);
      
      // Si le coût a un service spécifique
      if (laborCost.serviceType) {
        // Filtrer par type de service si spécifié
        if (serviceType && laborCost.serviceType !== serviceType) continue;
        
        if (day.services.has(laborCost.serviceType)) {
          day.services.get(laborCost.serviceType).costs.labor += laborCost.amount;
        }
      } else {
        // Allouer au prorata du chiffre d'affaires
        const totalRevenue = Array.from(day.services.values())
          .reduce((sum, s) => sum + s.revenue.excludingTax, 0);
        
        if (totalRevenue > 0) {
          for (const service of day.services.values()) {
            const share = service.revenue.excludingTax / totalRevenue;
            service.costs.labor += laborCost.amount * share;
          }
        }
      }
    }
    
    // Allouer les frais généraux et calculer les totaux
    for (const day of dayMap.values()) {
      // Calculer le chiffre d'affaires total du jour
      const totalRevenue = Array.from(day.services.values())
        .reduce((sum, s) => sum + s.revenue.excludingTax, 0);
      
      // Estimer les frais généraux du jour
      const overhead = totalRevenue * this.config.overheadAllocation.defaultRate;
      
      // Allouer aux services
      for (const service of day.services.values()) {
        if (totalRevenue > 0) {
          const share = service.revenue.excludingTax / totalRevenue;
          service.costs.overhead = overhead * share;
        } else {
          service.costs.overhead = 0;
        }
        
        // Calculer le total des coûts
        service.costs.total = service.costs.cogs + service.costs.labor + service.costs.overhead;
      }
    }
    
    // Convertir la map en tableau et filtrer les jours sans service
    const dayDetails = Array.from(dayMap.values())
      .filter(day => day.services.size > 0)
      .map(day => ({
        date: day.date,
        services: Array.from(day.services.values())
      }))
      .sort((a, b) => a.date - b.date);
    
    return dayDetails;
  }
  
  /**
   * Calcule les tendances des périodes
   * @param {Array} periods - Périodes analysées
   * @returns {Object} Tendances calculées
   * @private
   */
  _calculatePeriodTrends(periods) {
    if (periods.length < 2) return null;
    
    // Extraire les séries temporelles
    const revenueSeries = periods.map(p => p.revenue.total);
    const cogsRatioSeries = periods.map(p => p.costs.cogs / p.revenue.excludingTax);
    const laborRatioSeries = periods.map(p => p.costs.labor / p.revenue.excludingTax);
    const grossMarginSeries = periods.map(p => p.margins.gross);
    const operatingMarginSeries = periods.map(p => p.margins.operating);
    
    // Calculer les variations
    const revenueChange = this._calculateTrend(revenueSeries);
    const cogsRatioChange = this._calculateTrend(cogsRatioSeries);
    const laborRatioChange = this._calculateTrend(laborRatioSeries);
    const grossMarginChange = this._calculateTrend(grossMarginSeries);
    const operatingMarginChange = this._calculateTrend(operatingMarginSeries);
    
    return {
      revenue: {
        trend: revenueChange,
        direction: revenueChange > 0 ? 'up' : (revenueChange < 0 ? 'down' : 'stable')
      },
      cogsRatio: {
        trend: cogsRatioChange,
        direction: cogsRatioChange > 0 ? 'up' : (cogsRatioChange < 0 ? 'down' : 'stable')
      },
      laborRatio: {
        trend: laborRatioChange,
        direction: laborRatioChange > 0 ? 'up' : (laborRatioChange < 0 ? 'down' : 'stable')
      },
      grossMargin: {
        trend: grossMarginChange,
        direction: grossMarginChange > 0 ? 'up' : (grossMarginChange < 0 ? 'down' : 'stable')
      },
      operatingMargin: {
        trend: operatingMarginChange,
        direction: operatingMarginChange > 0 ? 'up' : (operatingMarginChange < 0 ? 'down' : 'stable')
      }
    };
  }
  
  /**
   * Calcule la tendance d'une série temporelle
   * @param {Array} series - Série temporelle
   * @returns {number} Taux de variation moyen
   * @private
   */
  _calculateTrend(series) {
    if (series.length < 2) return 0;
    
    const variations = [];
    for (let i = 1; i < series.length; i++) {
      const prev = series[i - 1];
      const curr = series[i];
      
      if (prev !== 0) {
        variations.push((curr - prev) / prev);
      }
    }
    
    // Calculer la moyenne des variations
    if (variations.length === 0) return 0;
    
    return variations.reduce((sum, v) => sum + v, 0) / variations.length;
  }
  
  /**
   * Récupère les données historiques des produits
   * @param {Object} options - Options de recherche
   * @param {string} [options.productId] - ID du produit
   * @param {string} [options.categoryId] - ID de la catégorie
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Données historiques
   * @private
   */
  async _getHistoricalProductData({ productId, categoryId, endDate }) {
    // Calculer les périodes historiques
    const lastMonth = moment(endDate).subtract(1, 'month').toDate();
    const lastYear = moment(endDate).subtract(1, 'year').toDate();
    
    try {
      // Récupérer les analyses historiques
      const [lastMonthAnalysis, lastYearAnalysis] = await Promise.all([
        this.analyzeProductProfitability({
          startDate: moment(lastMonth).startOf('month').toDate(),
          endDate: moment(lastMonth).endOf('month').toDate(),
          productId,
          categoryId,
          useCache: true
        }),
        this.analyzeProductProfitability({
          startDate: moment(lastYear).date(1).toDate(),
          endDate: moment(lastYear).add(1, 'month').date(0).toDate(),
          productId,
          categoryId,
          useCache: true
        })
      ]);
      
      return {
        lastMonth: {
          period: {
            start: lastMonthAnalysis.period.start,
            end: lastMonthAnalysis.period.end
          },
          summary: lastMonthAnalysis.summary
        },
        lastYear: {
          period: {
            start: lastYearAnalysis.period.start,
            end: lastYearAnalysis.period.end
          },
          summary: lastYearAnalysis.summary
        }
      };
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des données historiques:', error);
      return null;
    }
  }
  
  /**
   * Récupère un résultat en cache
   * @param {string} key - Clé de cache
   * @returns {Object|null} Résultat en cache ou null si non trouvé ou expiré
   * @private
   */
  _getCachedResult(key) {
    if (!this.analysisCache.has(key)) {
      return null;
    }
    
    const cached = this.analysisCache.get(key);
    const now = Date.now();
    
    // Vérifier si le cache est expiré
    if (now - cached.timestamp > this.cacheValidityDuration) {
      this.analysisCache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  /**
   * Met en cache un résultat d'analyse
   * @param {string} key - Clé de cache
   * @param {Object} data - Données à mettre en cache
   * @private
   */
  _cacheResult(key, data) {
    this.analysisCache.set(key, {
      data,
      timestamp: Date.now()
    });
    
    // Nettoyer le cache si trop grand (plus de 100 entrées)
    if (this.analysisCache.size > 100) {
      const oldestKey = Array.from(this.analysisCache.entries())
        .sort(([, a], [, b]) => a.timestamp - b.timestamp)[0][0];
      
      this.analysisCache.delete(oldestKey);
    }
  }
  
  /**
   * Exporte un rapport au format JSON
   * @param {Object} options - Options d'export
   * @param {Object} options.analysisResult - Résultat d'analyse
   * @param {string} options.analysisType - Type d'analyse
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToJSON({ analysisResult, analysisType, outputPath }) {
    // Écrire le résultat tel quel
    const fs = require('fs').promises;
    await fs.writeFile(outputPath, JSON.stringify(analysisResult, null, 2), 'utf8');
  }
  
  /**
   * Exporte un rapport au format CSV
   * @param {Object} options - Options d'export
   * @param {Object} options.analysisResult - Résultat d'analyse
   * @param {string} options.analysisType - Type d'analyse
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToCSV({ analysisResult, analysisType, outputPath }) {
    // Fonction utilitaire pour échapper une valeur CSV
    const escape = (value) => {
      if (value === null || value === undefined) return '';
      return `"${String(value).replace(/"/g, '""')}"`;
    };
    
    let csvContent;
    
    switch (analysisType) {
      case 'product':
        // En-tête
        const productHeader = [
          'ID',
          'Nom',
          'Catégorie',
          'Quantité vendue',
          'CA (TTC)',
          'CA (HT)',
          'TVA',
          'Coût des marchandises',
          'Coût main d\'œuvre',
          'Frais généraux',
          'Coût total',
          'Marge brute',
          'Marge d\'exploitation',
          'Taux de marge brute',
          'Taux de marge d\'exploitation',
          'Performance'
        ].map(escape).join(',');
        
        // Données des produits
        const productRows = analysisResult.products.map(product => [
          product.id,
          product.name,
          product.category,
          product.sales.quantity,
          product.sales.revenue.toFixed(2),
          product.sales.revenueExclTax.toFixed(2),
          product.sales.tax.toFixed(2),
          product.costs.cogs.toFixed(2),
          product.costs.labor.toFixed(2),
          product.costs.overhead.toFixed(2),
          product.costs.total.toFixed(2),
          product.profit.gross.toFixed(2),
          product.profit.operating.toFixed(2),
          (product.margins.gross * 100).toFixed(2) + '%',
          (product.margins.operating * 100).toFixed(2) + '%',
          product.performance.operatingMargin
        ].map(escape).join(','));
        
        csvContent = [productHeader, ...productRows].join('\n');
        break;
        
      // Autres types d'analyse...
      
      default:
        // Export générique si le type n'est pas explicitement géré
        csvContent = JSON.stringify(analysisResult);
    }
    
    // Écrire le fichier
    const fs = require('fs').promises;
    await fs.writeFile(outputPath, csvContent, 'utf8');
  }
  
  /**
   * Exporte un rapport au format Excel
   * @param {Object} options - Options d'export
   * @param {Object} options.analysisResult - Résultat d'analyse
   * @param {string} options.analysisType - Type d'analyse
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToExcel({ analysisResult, analysisType, outputPath }) {
    // Dans une implémentation réelle, utiliser une bibliothèque comme ExcelJS
    // Ici, on utilise une approche simplifiée pour l'exemple
    await this._exportReportToCSV({ 
      analysisResult, 
      analysisType, 
      outputPath: outputPath.replace(/\.xlsx$/, '.csv') 
    });
    
    this.logger.warn('Export Excel non implémenté. Un fichier CSV a été généré à la place.');
  }
  
  /**
   * Exporte un rapport au format PDF
   * @param {Object} options - Options d'export
   * @param {Object} options.analysisResult - Résultat d'analyse
   * @param {string} options.analysisType - Type d'analyse
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToPDF({ analysisResult, analysisType, outputPath }) {
    // Dans une implémentation réelle, utiliser une bibliothèque comme PDFKit
    // Ici, on utilise une approche simplifiée pour l'exemple
    await this._exportReportToJSON({ 
      analysisResult, 
      analysisType, 
      outputPath: outputPath.replace(/\.pdf$/, '.json') 
    });
    
    this.logger.warn('Export PDF non implémenté. Un fichier JSON a été généré à la place.');
  }
}

// Exports
module.exports = {
  ProfitabilityAnalyzer
};
