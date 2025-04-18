/**
 * Module de vérification de l'intégrité des données financières
 * 
 * Ce module est responsable de la vérification, de la validation et du contrôle
 * de cohérence des données financières pour garantir leur exactitude.
 */

'use strict';

const moment = require('moment');
const { EventEmitter } = require('events');

/**
 * Classe principale de vérification d'intégrité financière
 */
class FinancialIntegrityChecker extends EventEmitter {
  /**
   * Crée une nouvelle instance du vérificateur d'intégrité
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataConsolidator - Consolidateur de données
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.alertService - Service d'alertes
   */
  constructor(options = {}) {
    super();
    
    this.dataConsolidator = options.dataConsolidator;
    this.configManager = options.configManager;
    this.alertService = options.alertService;
    
    // Charger la configuration des règles d'intégrité
    this.integrityRules = this._loadIntegrityRules();
    
    // Historique des vérifications
    this.checkHistory = [];
  }
  
  /**
   * Charge les règles d'intégrité depuis la configuration
   * @returns {Object} - Règles d'intégrité
   * @private
   */
  _loadIntegrityRules() {
    const defaultRules = {
      balance: {
        enabled: true,
        tolerance: 0.01, // 1 centime d'euro
        description: "Vérifier l'équilibre comptable"
      },
      salesVerification: {
        enabled: true,
        tolerance: 0.05, // 5%
        description: "Vérifier la cohérence des ventes"
      },
      expensesVerification: {
        enabled: true,
        tolerance: 0.05, // 5%
        description: "Vérifier la cohérence des dépenses"
      },
      inventoryVerification: {
        enabled: true,
        tolerance: 0.10, // 10%
        description: "Vérifier la cohérence de l'inventaire"
      },
      taxVerification: {
        enabled: true,
        tolerance: 0.01, // 1%
        description: "Vérifier les calculs de TVA"
      },
      anomalyDetection: {
        enabled: true,
        thresholds: {
          sales: 0.30, // 30% d'écart par rapport à la moyenne
          expenses: 0.30, // 30% d'écart par rapport à la moyenne
          profit: 0.40 // 40% d'écart par rapport à la moyenne
        },
        description: "Détecter les anomalies financières"
      }
    };
    
    // Fusionner avec la configuration personnalisée si disponible
    if (this.configManager) {
      const customRules = this.configManager.getConfig('accounting.integrityRules', {});
      return { ...defaultRules, ...customRules };
    }
    
    return defaultRules;
  }
  
  /**
   * Effectue une vérification complète de l'intégrité des données financières
   * @param {Object} options - Options de vérification
   * @param {Date|string} options.date - Date de vérification
   * @param {Array<string>} options.rules - Règles spécifiques à vérifier (toutes par défaut)
   * @returns {Promise<Object>} - Résultats de la vérification
   */
  async checkFinancialIntegrity(options = {}) {
    const date = options.date ? moment(options.date) : moment();
    const rules = options.rules || Object.keys(this.integrityRules);
    
    // Préparer l'objet de résultats
    const results = {
      timestamp: new Date(),
      period: {
        date: date.format('YYYY-MM-DD'),
        month: date.format('YYYY-MM'),
        year: date.format('YYYY')
      },
      status: 'success',
      checks: {},
      summary: {
        total: 0,
        passed: 0,
        failed: 0,
        warnings: 0,
        errors: []
      }
    };
    
    // Récupérer les données consolidées
    const consolidatedData = await this.dataConsolidator.consolidateFinancialData({
      startDate: date.clone().startOf('day').format('YYYY-MM-DD'),
      endDate: date.clone().endOf('day').format('YYYY-MM-DD')
    });
    
    // Récupérer les données du mois en cours pour comparaison
    const monthData = await this.dataConsolidator.consolidateFinancialData({
      startDate: date.clone().startOf('month').format('YYYY-MM-DD'),
      endDate: date.clone().endOf('month').format('YYYY-MM-DD')
    });
    
    // Effectuer chaque vérification demandée
    for (const rule of rules) {
      if (!this.integrityRules[rule] || !this.integrityRules[rule].enabled) {
        continue;
      }
      
      try {
        let checkResult;
        
        switch (rule) {
          case 'balance':
            checkResult = await this._checkAccountingBalance(consolidatedData);
            break;
          
          case 'salesVerification':
            checkResult = await this._checkSalesIntegrity(consolidatedData);
            break;
          
          case 'expensesVerification':
            checkResult = await this._checkExpensesIntegrity(consolidatedData);
            break;
          
          case 'inventoryVerification':
            checkResult = await this._checkInventoryIntegrity(consolidatedData);
            break;
          
          case 'taxVerification':
            checkResult = await this._checkTaxIntegrity(consolidatedData);
            break;
          
          case 'anomalyDetection':
            checkResult = await this._detectFinancialAnomalies(consolidatedData, monthData);
            break;
          
          default:
            results.checks[rule] = {
              status: 'skipped',
              message: `Règle non reconnue: ${rule}`
            };
            continue;
        }
        
        // Stocker le résultat
        results.checks[rule] = checkResult;
        
        // Mettre à jour le compteur
        results.summary.total++;
        
        if (checkResult.status === 'passed') {
          results.summary.passed++;
        } else if (checkResult.status === 'warning') {
          results.summary.warnings++;
        } else if (checkResult.status === 'failed') {
          results.summary.failed++;
          results.summary.errors.push({
            rule,
            message: checkResult.message,
            details: checkResult.details
          });
        }
      } catch (error) {
        console.error(`Erreur lors de la vérification de la règle ${rule}:`, error);
        
        // Stocker l'erreur
        results.checks[rule] = {
          status: 'error',
          message: `Erreur lors de la vérification: ${error.message}`,
          error: error.message,
          stack: error.stack
        };
        
        // Mettre à jour le compteur
        results.summary.total++;
        results.summary.failed++;
        results.summary.errors.push({
          rule,
          message: `Erreur lors de la vérification: ${error.message}`,
          error: true
        });
      }
    }
    
    // Déterminer le statut global
    if (results.summary.failed > 0) {
      results.status = 'failed';
    } else if (results.summary.warnings > 0) {
      results.status = 'warning';
    }
    
    // Ajouter à l'historique
    this.checkHistory.push({
      timestamp: results.timestamp,
      date: date.format('YYYY-MM-DD'),
      status: results.status,
      summary: results.summary
    });
    
    // Limiter l'historique à 100 entrées
    if (this.checkHistory.length > 100) {
      this.checkHistory.shift();
    }
    
    // Émettre un événement de fin de vérification
    this.emit('integrity:check_complete', {
      date: date.format('YYYY-MM-DD'),
      status: results.status,
      failures: results.summary.failed,
      warnings: results.summary.warnings
    });
    
    // Créer des alertes si nécessaire
    if (results.status === 'failed' && this.alertService) {
      this.alertService.danger('financial_integrity_failure',
        `${results.summary.failed} échec(s) d'intégrité financière détecté(s) pour la date ${date.format('DD/MM/YYYY')}`,
        {
          date: date.format('YYYY-MM-DD'),
          failures: results.summary.errors
        }
      );
    } else if (results.status === 'warning' && this.alertService) {
      this.alertService.warning('financial_integrity_warning',
        `${results.summary.warnings} avertissement(s) d'intégrité financière détecté(s) pour la date ${date.format('DD/MM/YYYY')}`,
        {
          date: date.format('YYYY-MM-DD'),
          checksWithWarnings: Object.entries(results.checks)
            .filter(([_, check]) => check.status === 'warning')
            .map(([rule, _]) => rule)
        }
      );
    }
    
    return results;
  }
  
  /**
   * Vérifie l'équilibre comptable (débit = crédit)
   * @param {Object} data - Données consolidées
   * @returns {Object} - Résultat de la vérification
   * @private
   */
  async _checkAccountingBalance(data) {
    const result = {
      status: 'passed',
      message: "L'équilibre comptable est respecté",
      details: {
        debits: 0,
        credits: 0,
        difference: 0,
        tolerance: this.integrityRules.balance.tolerance
      }
    };
    
    // Dans un système comptable réel, on vérifierait l'égalité entre
    // les totaux des débits et des crédits dans le grand livre
    
    // Ici, nous faisons une simulation simplifiée en considérant :
    // - Les ventes comme des crédits
    // - Les dépenses comme des débits
    
    // Calcul des crédits
    if (data.sources.sales) {
      result.details.credits += data.sources.sales.totalSales;
    }
    
    // Calcul des débits
    if (data.sources.expenses) {
      result.details.debits += data.sources.expenses.totalExpenses;
    }
    
    // Calculer la différence absolue
    result.details.difference = Math.abs(result.details.credits - result.details.debits);
    
    // Vérifier si la différence est inférieure à la tolérance
    if (result.details.difference > result.details.tolerance) {
      result.status = 'failed';
      result.message = `Déséquilibre comptable détecté: différence de ${result.details.difference.toFixed(2)}€`;
    }
    
    return result;
  }
  
  /**
   * Vérifie l'intégrité des données de ventes
   * @param {Object} data - Données consolidées
   * @returns {Object} - Résultat de la vérification
   * @private
   */
  async _checkSalesIntegrity(data) {
    const result = {
      status: 'passed',
      message: "Les données de ventes sont cohérentes",
      details: {
        checks: {},
        tolerance: this.integrityRules.salesVerification.tolerance
      }
    };
    
    // Vérifier que les données de ventes existent
    if (!data.sources.sales) {
      result.status = 'warning';
      result.message = "Impossible de vérifier l'intégrité des ventes: données manquantes";
      return result;
    }
    
    const sales = data.sources.sales;
    
    // 1. Vérifier que le total des ventes correspond à la somme des ventes par catégorie
    let categoriesTotal = 0;
    
    for (const [_, categoryData] of Object.entries(sales.byCategory)) {
      categoriesTotal += categoryData.total;
    }
    
    const totalDifference = Math.abs(sales.totalSales - categoriesTotal);
    const totalDifferencePercent = sales.totalSales > 0 ? totalDifference / sales.totalSales : 0;
    
    result.details.checks.categoriesTotal = {
      expected: sales.totalSales,
      actual: categoriesTotal,
      difference: totalDifference,
      differencePercent: totalDifferencePercent,
      passed: totalDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.categoriesTotal.passed) {
      result.status = 'failed';
      result.message = `Incohérence dans les totaux de ventes: différence de ${totalDifference.toFixed(2)}€ (${(totalDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    // 2. Vérifier que le total des ventes correspond à la somme des ventes par méthode de paiement
    let paymentMethodsTotal = 0;
    
    for (const [_, methodData] of Object.entries(sales.byPaymentMethod)) {
      paymentMethodsTotal += methodData.total;
    }
    
    const paymentDifference = Math.abs(sales.totalSales - paymentMethodsTotal);
    const paymentDifferencePercent = sales.totalSales > 0 ? paymentDifference / sales.totalSales : 0;
    
    result.details.checks.paymentMethodsTotal = {
      expected: sales.totalSales,
      actual: paymentMethodsTotal,
      difference: paymentDifference,
      differencePercent: paymentDifferencePercent,
      passed: paymentDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.paymentMethodsTotal.passed && result.status === 'passed') {
      result.status = 'failed';
      result.message = `Incohérence dans les totaux de ventes par méthode de paiement: différence de ${paymentDifference.toFixed(2)}€ (${(paymentDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    // 3. Vérifier que le ticket moyen est cohérent avec le total et le nombre de transactions
    const calculatedAvgTicket = sales.transactions.length > 0 ? 
      sales.totalSales / sales.transactions.length : 0;
    
    const ticketDifference = Math.abs(sales.averageTicket - calculatedAvgTicket);
    const ticketDifferencePercent = sales.averageTicket > 0 ? ticketDifference / sales.averageTicket : 0;
    
    result.details.checks.averageTicket = {
      expected: calculatedAvgTicket,
      actual: sales.averageTicket,
      difference: ticketDifference,
      differencePercent: ticketDifferencePercent,
      passed: ticketDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.averageTicket.passed && result.status === 'passed') {
      result.status = 'warning';
      result.message = `Anomalie dans le calcul du ticket moyen: différence de ${ticketDifference.toFixed(2)}€ (${(ticketDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    return result;
  }
  
  /**
   * Vérifie l'intégrité des données de dépenses
   * @param {Object} data - Données consolidées
   * @returns {Object} - Résultat de la vérification
   * @private
   */
  async _checkExpensesIntegrity(data) {
    const result = {
      status: 'passed',
      message: "Les données de dépenses sont cohérentes",
      details: {
        checks: {},
        tolerance: this.integrityRules.expensesVerification.tolerance
      }
    };
    
    // Vérifier que les données de dépenses existent
    if (!data.sources.expenses) {
      result.status = 'warning';
      result.message = "Impossible de vérifier l'intégrité des dépenses: données manquantes";
      return result;
    }
    
    const expenses = data.sources.expenses;
    
    // 1. Vérifier que le total des dépenses correspond à la somme des dépenses par catégorie
    let categoriesTotal = 0;
    
    for (const [_, categoryData] of Object.entries(expenses.byCategory)) {
      categoriesTotal += categoryData.total;
    }
    
    const totalDifference = Math.abs(expenses.totalExpenses - categoriesTotal);
    const totalDifferencePercent = expenses.totalExpenses > 0 ? totalDifference / expenses.totalExpenses : 0;
    
    result.details.checks.categoriesTotal = {
      expected: expenses.totalExpenses,
      actual: categoriesTotal,
      difference: totalDifference,
      differencePercent: totalDifferencePercent,
      passed: totalDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.categoriesTotal.passed) {
      result.status = 'failed';
      result.message = `Incohérence dans les totaux de dépenses: différence de ${totalDifference.toFixed(2)}€ (${(totalDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    // 2. Vérifier que le total des dépenses correspond à la somme des dépenses par fournisseur
    let vendorsTotal = 0;
    
    for (const [_, vendorData] of Object.entries(expenses.byVendor)) {
      vendorsTotal += vendorData.total;
    }
    
    const vendorDifference = Math.abs(expenses.totalExpenses - vendorsTotal);
    const vendorDifferencePercent = expenses.totalExpenses > 0 ? vendorDifference / expenses.totalExpenses : 0;
    
    result.details.checks.vendorsTotal = {
      expected: expenses.totalExpenses,
      actual: vendorsTotal,
      difference: vendorDifference,
      differencePercent: vendorDifferencePercent,
      passed: vendorDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.vendorsTotal.passed && result.status === 'passed') {
      result.status = 'failed';
      result.message = `Incohérence dans les totaux de dépenses par fournisseur: différence de ${vendorDifference.toFixed(2)}€ (${(vendorDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    // 3. Vérifier que la somme des coûts fixes et variables correspond au total des dépenses
    const fixedVariableTotal = expenses.fixedCosts + expenses.variableCosts;
    const fixedVariableDifference = Math.abs(expenses.totalExpenses - fixedVariableTotal);
    const fixedVariableDifferencePercent = expenses.totalExpenses > 0 ? fixedVariableDifference / expenses.totalExpenses : 0;
    
    result.details.checks.fixedVariableTotal = {
      expected: expenses.totalExpenses,
      actual: fixedVariableTotal,
      difference: fixedVariableDifference,
      differencePercent: fixedVariableDifferencePercent,
      passed: fixedVariableDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.fixedVariableTotal.passed && result.status === 'passed') {
      result.status = 'warning';
      result.message = `Anomalie dans la répartition des coûts fixes/variables: différence de ${fixedVariableDifference.toFixed(2)}€ (${(fixedVariableDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    return result;
  }
  
  /**
   * Vérifie l'intégrité des données d'inventaire
   * @param {Object} data - Données consolidées
   * @returns {Object} - Résultat de la vérification
   * @private
   */
  async _checkInventoryIntegrity(data) {
    const result = {
      status: 'passed',
      message: "Les données d'inventaire sont cohérentes",
      details: {
        checks: {},
        tolerance: this.integrityRules.inventoryVerification.tolerance
      }
    };
    
    // Vérifier que les données d'inventaire existent
    if (!data.sources.inventory) {
      result.status = 'warning';
      result.message = "Impossible de vérifier l'intégrité de l'inventaire: données manquantes";
      return result;
    }
    
    const inventory = data.sources.inventory;
    
    // 1. Vérifier que le total de l'inventaire correspond à la somme des valeurs par catégorie
    let categoriesTotal = 0;
    
    for (const [_, categoryData] of Object.entries(inventory.byCategory)) {
      categoriesTotal += categoryData.total;
    }
    
    const totalDifference = Math.abs(inventory.totalValue - categoriesTotal);
    const totalDifferencePercent = inventory.totalValue > 0 ? totalDifference / inventory.totalValue : 0;
    
    result.details.checks.categoriesTotal = {
      expected: inventory.totalValue,
      actual: categoriesTotal,
      difference: totalDifference,
      differencePercent: totalDifferencePercent,
      passed: totalDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.categoriesTotal.passed) {
      result.status = 'failed';
      result.message = `Incohérence dans les totaux d'inventaire: différence de ${totalDifference.toFixed(2)}€ (${(totalDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    // 2. Vérifier que le total de l'inventaire correspond à la somme des valeurs des items
    let itemsTotal = 0;
    
    if (inventory.items && Array.isArray(inventory.items)) {
      for (const item of inventory.items) {
        itemsTotal += item.totalValue;
      }
      
      const itemsDifference = Math.abs(inventory.totalValue - itemsTotal);
      const itemsDifferencePercent = inventory.totalValue > 0 ? itemsDifference / inventory.totalValue : 0;
      
      result.details.checks.itemsTotal = {
        expected: inventory.totalValue,
        actual: itemsTotal,
        difference: itemsDifference,
        differencePercent: itemsDifferencePercent,
        passed: itemsDifferencePercent <= result.details.tolerance
      };
      
      if (!result.details.checks.itemsTotal.passed && result.status === 'passed') {
        result.status = 'failed';
        result.message = `Incohérence dans les totaux d'inventaire par article: différence de ${itemsDifference.toFixed(2)}€ (${(itemsDifferencePercent * 100).toFixed(2)}%)`;
      }
    }
    
    return result;
  }
  
  /**
   * Vérifie l'intégrité des calculs de TVA
   * @param {Object} data - Données consolidées
   * @returns {Object} - Résultat de la vérification
   * @private
   */
  async _checkTaxIntegrity(data) {
    const result = {
      status: 'passed',
      message: "Les calculs de TVA sont corrects",
      details: {
        checks: {},
        tolerance: this.integrityRules.taxVerification.tolerance
      }
    };
    
    // Cette vérification nécessiterait des données détaillées sur la TVA
    // Pour l'exemple, nous allons faire une vérification simplifiée
    
    if (!data.sources.sales) {
      result.status = 'warning';
      result.message = "Impossible de vérifier les calculs de TVA: données de ventes manquantes";
      return result;
    }
    
    // Supposons que nous ayons une répartition approximative des ventes par taux de TVA
    // Dans un système réel, ces données proviendraient de la base de données
    
    // Simuler les taux de TVA pour les différentes catégories de ventes
    const salesByCategory = data.sources.sales.byCategory;
    
    let totalTaxableAmount = 0;
    let totalVAT = 0;
    
    // TVA à 20% (standard)
    if (salesByCategory.alcohol) {
      const taxableAmount = salesByCategory.alcohol.total / 1.20;
      const vat = salesByCategory.alcohol.total - taxableAmount;
      
      totalTaxableAmount += taxableAmount;
      totalVAT += vat;
    }
    
    // TVA à 10% (service sur place)
    const onPremiseCategories = ['food', 'desserts', 'starters', 'mains', 'non_alcoholic'];
    for (const category of onPremiseCategories) {
      if (salesByCategory[category]) {
        const taxableAmount = salesByCategory[category].total / 1.10;
        const vat = salesByCategory[category].total - taxableAmount;
        
        totalTaxableAmount += taxableAmount;
        totalVAT += vat;
      }
    }
    
    // TVA à 5.5% (vente à emporter)
    if (salesByCategory.takeaway) {
      const taxableAmount = salesByCategory.takeaway.total / 1.055;
      const vat = salesByCategory.takeaway.total - taxableAmount;
      
      totalTaxableAmount += taxableAmount;
      totalVAT += vat;
    }
    
    // Calculer le montant total HT et TTC
    const totalHT = totalTaxableAmount;
    const totalTTC = totalHT + totalVAT;
    
    // Vérifier la cohérence avec le total des ventes
    const ttcDifference = Math.abs(data.sources.sales.totalSales - totalTTC);
    const ttcDifferencePercent = data.sources.sales.totalSales > 0 ? ttcDifference / data.sources.sales.totalSales : 0;
    
    result.details.checks.totalTTC = {
      expected: data.sources.sales.totalSales,
      actual: totalTTC,
      difference: ttcDifference,
      differencePercent: ttcDifferencePercent,
      passed: ttcDifferencePercent <= result.details.tolerance
    };
    
    if (!result.details.checks.totalTTC.passed) {
      result.status = 'failed';
      result.message = `Incohérence dans les calculs de TVA: différence de ${ttcDifference.toFixed(2)}€ (${(ttcDifferencePercent * 100).toFixed(2)}%)`;
    }
    
    result.details.summary = {
      totalHT: totalHT,
      totalVAT: totalVAT,
      totalTTC: totalTTC,
      vatRate: totalHT > 0 ? (totalVAT / totalHT) * 100 : 0
    };
    
    return result;
  }
  
  /**
   * Détecte les anomalies financières
   * @param {Object} data - Données consolidées du jour
   * @param {Object} monthData - Données consolidées du mois
   * @returns {Object} - Résultat de la détection
   * @private
   */
  async _detectFinancialAnomalies(data, monthData) {
    const result = {
      status: 'passed',
      message: "Aucune anomalie financière détectée",
      details: {
        checks: {},
        thresholds: this.integrityRules.anomalyDetection.thresholds
      }
    };
    
    // Vérifier que les données nécessaires existent
    if (!data.sources.sales || !monthData.sources.sales) {
      result.status = 'warning';
      result.message = "Impossible de détecter les anomalies: données insuffisantes";
      return result;
    }
    
    // Calculer les moyennes mensuelles
    const daysInMonth = moment(data.period.end).daysInMonth();
    
    const avgDailySales = monthData.sources.sales.totalSales / daysInMonth;
    const avgDailyExpenses = monthData.sources.expenses ? monthData.sources.expenses.totalExpenses / daysInMonth : 0;
    const avgDailyProfit = avgDailySales - avgDailyExpenses;
    
    // 1. Vérifier si les ventes sont anormalement basses ou élevées
    const salesDeviation = avgDailySales > 0 ? 
      Math.abs(data.sources.sales.totalSales - avgDailySales) / avgDailySales : 0;
    
    result.details.checks.sales = {
      value: data.sources.sales.totalSales,
      average: avgDailySales,
      deviation: salesDeviation,
      threshold: result.details.thresholds.sales,
      passed: salesDeviation <= result.details.thresholds.sales
    };
    
    if (!result.details.checks.sales.passed) {
      result.status = 'warning';
      result.message = `Anomalie détectée: les ventes s'écartent de ${(salesDeviation * 100).toFixed(2)}% de la moyenne mensuelle`;
    }
    
    // 2. Vérifier si les dépenses sont anormalement basses ou élevées
    if (data.sources.expenses && avgDailyExpenses > 0) {
      const expensesDeviation = Math.abs(data.sources.expenses.totalExpenses - avgDailyExpenses) / avgDailyExpenses;
      
      result.details.checks.expenses = {
        value: data.sources.expenses.totalExpenses,
        average: avgDailyExpenses,
        deviation: expensesDeviation,
        threshold: result.details.thresholds.expenses,
        passed: expensesDeviation <= result.details.thresholds.expenses
      };
      
      if (!result.details.checks.expenses.passed && result.status === 'passed') {
        result.status = 'warning';
        result.message = `Anomalie détectée: les dépenses s'écartent de ${(expensesDeviation * 100).toFixed(2)}% de la moyenne mensuelle`;
      }
    }
    
    // 3. Vérifier si le profit est anormalement bas ou élevé
    const dailyProfit = data.sources.sales.totalSales - (data.sources.expenses ? data.sources.expenses.totalExpenses : 0);
    
    if (avgDailyProfit !== 0) {
      const profitDeviation = Math.abs(dailyProfit - avgDailyProfit) / Math.abs(avgDailyProfit);
      
      result.details.checks.profit = {
        value: dailyProfit,
        average: avgDailyProfit,
        deviation: profitDeviation,
        threshold: result.details.thresholds.profit,
        passed: profitDeviation <= result.details.thresholds.profit
      };
      
      if (!result.details.checks.profit.passed && result.status === 'passed') {
        result.status = 'warning';
        result.message = `Anomalie détectée: le profit s'écarte de ${(profitDeviation * 100).toFixed(2)}% de la moyenne mensuelle`;
      }
    }
    
    // Si plusieurs anomalies détectées, changer le message
    const failedChecks = Object.values(result.details.checks).filter(check => !check.passed).length;
    
    if (failedChecks > 1) {
      result.status = 'warning';
      result.message = `${failedChecks} anomalies financières détectées`;
    }
    
    return result;
  }
  
  /**
   * Vérifie l'intégrité des données financières sur une période
   * @param {Object} options - Options de vérification
   * @param {Date|string} options.startDate - Date de début
   * @param {Date|string} options.endDate - Date de fin
   * @param {string} options.frequency - Fréquence (daily, weekly, monthly)
   * @returns {Promise<Object>} - Résultats de la vérification
   */
  async checkPeriodIntegrity(options = {}) {
    const startDate = options.startDate ? moment(options.startDate) : moment().subtract(1, 'month').startOf('month');
    const endDate = options.endDate ? moment(options.endDate) : moment().subtract(1, 'month').endOf('month');
    const frequency = options.frequency || 'daily';
    
    // Préparer l'objet de résultats
    const results = {
      period: {
        start: startDate.format('YYYY-MM-DD'),
        end: endDate.format('YYYY-MM-DD'),
        frequency
      },
      checks: [],
      summary: {
        total: 0,
        passed: 0,
        warnings: 0,
        failed: 0
      }
    };
    
    // Déterminer les dates à vérifier selon la fréquence
    const dates = [];
    let currentDate = startDate.clone();
    
    while (currentDate.isSameOrBefore(endDate)) {
      dates.push(currentDate.clone());
      
      if (frequency === 'daily') {
        currentDate.add(1, 'day');
      } else if (frequency === 'weekly') {
        currentDate.add(1, 'week');
      } else if (frequency === 'monthly') {
        currentDate.add(1, 'month');
      }
    }
    
    // Effectuer les vérifications pour chaque date
    for (const date of dates) {
      const checkResult = await this.checkFinancialIntegrity({
        date: date
      });
      
      // Ajouter aux résultats
      results.checks.push({
        date: date.format('YYYY-MM-DD'),
        status: checkResult.status,
        summary: checkResult.summary
      });
      
      // Mettre à jour le compteur
      results.summary.total++;
      
      if (checkResult.status === 'passed') {
        results.summary.passed++;
      } else if (checkResult.status === 'warning') {
        results.summary.warnings++;
      } else if (checkResult.status === 'failed') {
        results.summary.failed++;
      }
    }
    
    // Créer une alerte si des problèmes sont détectés sur plusieurs jours
    if (results.summary.failed > 0 && this.alertService) {
      this.alertService.danger('period_integrity_failure',
        `Problèmes d'intégrité financière détectés sur ${results.summary.failed} jours dans la période du ${startDate.format('DD/MM/YYYY')} au ${endDate.format('DD/MM/YYYY')}`,
        {
          period: results.period,
          failedDays: results.checks.filter(check => check.status === 'failed').map(check => check.date)
        }
      );
    } else if (results.summary.warnings > 2 && this.alertService) {
      this.alertService.warning('period_integrity_warnings',
        `Avertissements d'intégrité financière détectés sur ${results.summary.warnings} jours dans la période du ${startDate.format('DD/MM/YYYY')} au ${endDate.format('DD/MM/YYYY')}`,
        {
          period: results.period,
          warningDays: results.checks.filter(check => check.status === 'warning').map(check => check.date)
        }
      );
    }
    
    return results;
  }
  
  /**
   * Récupère l'historique des vérifications
   * @param {Object} options - Options de filtrage
   * @param {number} options.limit - Nombre maximum de résultats
   * @param {string} options.status - Filtrer par statut (passed, warning, failed)
   * @returns {Array<Object>} - Historique des vérifications
   */
  getCheckHistory(options = {}) {
    const limit = options.limit || 100;
    const status = options.status;
    
    // Filtrer par statut si spécifié
    let filteredHistory = this.checkHistory;
    
    if (status) {
      filteredHistory = filteredHistory.filter(check => check.status === status);
    }
    
    // Trier par date décroissante (plus récent en premier)
    filteredHistory.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Limiter le nombre de résultats
    return filteredHistory.slice(0, limit);
  }
}

module.exports = { FinancialIntegrityChecker };
