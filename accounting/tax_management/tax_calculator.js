/**
 * Module de calcul de TVA et gestion fiscale pour Le Vieux Moulin
 * Ce module fournit les fonctionnalités de calcul et de déclaration de TVA,
 * ainsi que la gestion des obligations fiscales du restaurant.
 */

'use strict';

const moment = require('moment');
const { DataCollector } = require('../common/data_collector');
const { ConfigManager } = require('../common/config_manager');

/**
 * Classe principale pour les calculs et la gestion de la TVA
 */
class TaxCalculator {
  /**
   * Crée une nouvelle instance du calculateur de taxes
   * @param {Object} options - Options de configuration
   * @param {Object} options.vatRates - Configuration des taux de TVA
   * @param {Object} options.declarationPeriods - Périodes de déclaration
   * @param {DataCollector} options.dataCollector - Instance du collecteur de données
   * @param {ConfigManager} options.configManager - Instance du gestionnaire de configuration
   */
  constructor(options = {}) {
    this.vatRates = options.vatRates || {
      // Taux par défaut pour la France en restauration
      standard: 20.0, // Taux standard
      intermediate: 10.0, // Restauration sur place
      reduced: 5.5, // Vente à emporter (nourriture)
      superReduced: 2.1, // Produits très spécifiques
      zero: 0.0 // Exonéré
    };
    
    this.declarationPeriods = options.declarationPeriods || {
      type: 'monthly', // monthly, quarterly, annual
      deadline: 15, // Jours après la fin de période
      paymentDeadline: 20 // Jours après la fin de période
    };
    
    this.dataCollector = options.dataCollector || null;
    this.configManager = options.configManager || 
      (ConfigManager.getConfigManager ? ConfigManager.getConfigManager() : null);
    
    // Charger la configuration depuis le gestionnaire si disponible
    if (this.configManager) {
      const taxConfig = this.configManager.getConfig('tax', {});
      
      if (taxConfig.vatRates) {
        this.vatRates = { ...this.vatRates, ...taxConfig.vatRates };
      }
      
      if (taxConfig.declarationPeriods) {
        this.declarationPeriods = { ...this.declarationPeriods, ...taxConfig.declarationPeriods };
      }
    }
    
    // Configuration des catégories de produits et taux associés
    this.productCategories = {
      food_onsite: this.vatRates.intermediate, // Nourriture sur place
      food_takeaway: this.vatRates.reduced, // Nourriture à emporter
      alcoholic_beverages: this.vatRates.standard, // Boissons alcoolisées
      non_alcoholic_beverages_onsite: this.vatRates.intermediate, // Boissons non alcoolisées sur place
      non_alcoholic_beverages_takeaway: this.vatRates.reduced // Boissons non alcoolisées à emporter
    };
    
    // Mapping des comptes comptables pour la TVA
    this.vatAccounts = {
      // TVA collectée
      collected: {
        standard: '44571',
        intermediate: '44571',
        reduced: '44571',
        superReduced: '44571',
        zero: '44571'
      },
      // TVA déductible
      deductible: {
        goods: '44566', // Biens
        services: '44566', // Services
        fixed_assets: '44562' // Immobilisations
      }
    };
  }
  
  /**
   * Calcule la TVA pour une transaction
   * @param {Object} transaction - Données de la transaction
   * @param {Object} options - Options de calcul
   * @returns {Object} - Résultat du calcul de TVA
   */
  calculateTransactionVAT(transaction, options = {}) {
    // Vérification des entrées
    if (!transaction || !transaction.items || !Array.isArray(transaction.items)) {
      throw new Error('Transaction invalide ou items manquants');
    }
    
    const result = {
      transactionId: transaction.id,
      transactionDate: transaction.date,
      totalAmountWithTax: 0,
      totalAmountWithoutTax: 0,
      totalVatAmount: 0,
      vatBreakdown: {},
      items: []
    };
    
    // Traiter chaque item de la transaction
    for (const item of transaction.items) {
      // Déterminer le taux de TVA applicable
      const vatRate = this._getVatRateForItem(item, transaction.type, options);
      const vatRateKey = this._getVatRateKey(vatRate);
      
      // Calculer les montants
      const amountWithTax = item.quantity * item.unitPrice;
      const amountWithoutTax = amountWithTax / (1 + vatRate / 100);
      const vatAmount = amountWithTax - amountWithoutTax;
      
      // Ajouter au total
      result.totalAmountWithTax += amountWithTax;
      result.totalAmountWithoutTax += amountWithoutTax;
      result.totalVatAmount += vatAmount;
      
      // Mettre à jour la répartition par taux
      if (!result.vatBreakdown[vatRateKey]) {
        result.vatBreakdown[vatRateKey] = {
          rate: vatRate,
          baseAmount: 0,
          vatAmount: 0,
          accountNumber: this.vatAccounts.collected[vatRateKey]
        };
      }
      
      result.vatBreakdown[vatRateKey].baseAmount += amountWithoutTax;
      result.vatBreakdown[vatRateKey].vatAmount += vatAmount;
      
      // Ajouter les détails par item
      result.items.push({
        itemId: item.id,
        itemName: item.name,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        amountWithTax,
        amountWithoutTax,
        vatRate,
        vatAmount
      });
    }
    
    // Arrondir les montants pour éviter les problèmes de précision
    result.totalAmountWithTax = parseFloat(result.totalAmountWithTax.toFixed(2));
    result.totalAmountWithoutTax = parseFloat(result.totalAmountWithoutTax.toFixed(2));
    result.totalVatAmount = parseFloat(result.totalVatAmount.toFixed(2));
    
    // Arrondir les montants dans la répartition
    for (const key in result.vatBreakdown) {
      result.vatBreakdown[key].baseAmount = parseFloat(result.vatBreakdown[key].baseAmount.toFixed(2));
      result.vatBreakdown[key].vatAmount = parseFloat(result.vatBreakdown[key].vatAmount.toFixed(2));
    }
    
    return result;
  }
  
  /**
   * Génère un rapport de TVA pour une période donnée
   * @param {Object} options - Options du rapport
   * @param {Date|string} options.startDate - Date de début de la période
   * @param {Date|string} options.endDate - Date de fin de la période
   * @param {boolean} options.includeDetails - Inclure les détails des transactions
   * @returns {Promise<Object>} - Rapport de TVA
   */
  async generateVATReport(options = {}) {
    try {
      // Normaliser les dates
      const startDate = options.startDate ? moment(options.startDate).startOf('day') : 
        moment().startOf('month').startOf('day');
      const endDate = options.endDate ? moment(options.endDate).endOf('day') : 
        moment().endOf('month').endOf('day');
      
      // Vérifier la validité des dates
      if (endDate.isBefore(startDate)) {
        throw new Error('La date de fin doit être postérieure à la date de début');
      }
      
      // Récupérer les données de vente pour la période
      const salesData = await this._getSalesData({
        startDate: startDate.toDate(),
        endDate: endDate.toDate(),
        includeDetails: !!options.includeDetails
      });
      
      // Récupérer les données d'achat pour la période
      const purchasesData = await this._getPurchasesData({
        startDate: startDate.toDate(),
        endDate: endDate.toDate(),
        includeDetails: !!options.includeDetails
      });
      
      // Calculer la TVA collectée
      const collectedVAT = this._calculateCollectedVAT(salesData);
      
      // Calculer la TVA déductible
      const deductibleVAT = this._calculateDeductibleVAT(purchasesData);
      
      // Calculer le solde de TVA
      const vatBalance = this._calculateVATBalance(collectedVAT, deductibleVAT);
      
      // Déterminer les dates de déclaration et paiement
      const declarationDate = this._calculateDeclarationDate(endDate);
      const paymentDate = this._calculatePaymentDate(endDate);
      
      // Construire le rapport
      const report = {
        period: {
          start: startDate.toDate(),
          end: endDate.toDate(),
          type: this._getPeriodType(startDate, endDate)
        },
        collected: collectedVAT,
        deductible: deductibleVAT,
        balance: vatBalance,
        dates: {
          declaration: declarationDate,
          payment: paymentDate
        },
        metadata: {
          generatedAt: new Date(),
          currency: 'EUR',
          taxRegime: 'FR'
        }
      };
      
      // Ajouter les détails des transactions si demandé
      if (options.includeDetails) {
        report.details = {
          sales: salesData.details || [],
          purchases: purchasesData.details || []
        };
      }
      
      return report;
    } catch (error) {
      console.error('Erreur lors de la génération du rapport de TVA:', error);
      throw new Error(`Échec de la génération du rapport de TVA: ${error.message}`);
    }
  }
  
  /**
   * Génère les écritures comptables pour la TVA
   * @param {Object} vatReport - Rapport de TVA
   * @returns {Object} - Écritures comptables
   */
  generateVATEntries(vatReport) {
    if (!vatReport || !vatReport.period || !vatReport.collected || !vatReport.deductible) {
      throw new Error('Rapport de TVA incomplet ou invalide');
    }
    
    const entries = [];
    const entryDate = moment(vatReport.period.end).add(1, 'day').toDate();
    
    // Générer une écriture par taux de TVA collectée
    Object.entries(vatReport.collected.byRate).forEach(([rateKey, data]) => {
      entries.push({
        date: entryDate,
        journalCode: 'OD', // Journal des opérations diverses
        description: `TVA collectée ${rateKey} - Période du ${moment(vatReport.period.start).format('DD/MM/YYYY')} au ${moment(vatReport.period.end).format('DD/MM/YYYY')}`,
        entries: [
          {
            account: '707000', // Ventes (à ajuster selon le plan comptable)
            label: `Base HT - TVA ${data.rate}%`,
            debit: 0,
            credit: data.baseAmount
          },
          {
            account: data.accountNumber || this.vatAccounts.collected[rateKey],
            label: `TVA collectée ${data.rate}%`,
            debit: 0,
            credit: data.vatAmount
          },
          {
            account: '411000', // Clients (à ajuster selon le plan comptable)
            label: `Total TTC - TVA ${data.rate}%`,
            debit: data.baseAmount + data.vatAmount,
            credit: 0
          }
        ]
      });
    });
    
    // Générer une écriture par type de TVA déductible
    Object.entries(vatReport.deductible.byType).forEach(([typeKey, data]) => {
      entries.push({
        date: entryDate,
        journalCode: 'OD', // Journal des opérations diverses
        description: `TVA déductible ${typeKey} - Période du ${moment(vatReport.period.start).format('DD/MM/YYYY')} au ${moment(vatReport.period.end).format('DD/MM/YYYY')}`,
        entries: [
          {
            account: typeKey === 'goods' ? '607000' : (typeKey === 'services' ? '615000' : '215000'), // Comptes différents selon le type
            label: `Base HT - TVA déductible ${typeKey}`,
            debit: data.baseAmount,
            credit: 0
          },
          {
            account: this.vatAccounts.deductible[typeKey],
            label: `TVA déductible ${typeKey}`,
            debit: data.vatAmount,
            credit: 0
          },
          {
            account: '401000', // Fournisseurs (à ajuster selon le plan comptable)
            label: `Total TTC - TVA déductible ${typeKey}`,
            debit: 0,
            credit: data.baseAmount + data.vatAmount
          }
        ]
      });
    });
    
    // Générer l'écriture de liquidation si le solde est dû
    if (vatReport.balance.balanceDue > 0) {
      entries.push({
        date: moment(vatReport.dates.declaration).toDate(),
        journalCode: 'OD', // Journal des opérations diverses
        description: `Liquidation TVA - Période du ${moment(vatReport.period.start).format('DD/MM/YYYY')} au ${moment(vatReport.period.end).format('DD/MM/YYYY')}`,
        entries: [
          {
            account: '44571', // TVA collectée
            label: 'TVA collectée',
            debit: vatReport.collected.totalVatAmount,
            credit: 0
          },
          {
            account: '44566', // TVA déductible sur ABS
            label: 'TVA déductible sur biens et services',
            debit: 0,
            credit: vatReport.deductible.totalVatAmount
          },
          {
            account: '44551', // TVA à payer
            label: 'TVA à payer',
            debit: 0,
            credit: vatReport.balance.balanceDue
          }
        ]
      });
      
      // Générer l'écriture de paiement de la TVA
      entries.push({
        date: moment(vatReport.dates.payment).toDate(),
        journalCode: 'BQ', // Journal de banque
        description: `Paiement TVA - Période du ${moment(vatReport.period.start).format('DD/MM/YYYY')} au ${moment(vatReport.period.end).format('DD/MM/YYYY')}`,
        entries: [
          {
            account: '44551', // TVA à payer
            label: 'Règlement TVA',
            debit: vatReport.balance.balanceDue,
            credit: 0
          },
          {
            account: '512000', // Banque (à ajuster selon le plan comptable)
            label: 'Règlement TVA',
            debit: 0,
            credit: vatReport.balance.balanceDue
          }
        ]
      });
    }
    // Si crédit de TVA
    else if (vatReport.balance.balanceDue < 0) {
      entries.push({
        date: moment(vatReport.dates.declaration).toDate(),
        journalCode: 'OD', // Journal des opérations diverses
        description: `Liquidation TVA (crédit) - Période du ${moment(vatReport.period.start).format('DD/MM/YYYY')} au ${moment(vatReport.period.end).format('DD/MM/YYYY')}`,
        entries: [
          {
            account: '44571', // TVA collectée
            label: 'TVA collectée',
            debit: vatReport.collected.totalVatAmount,
            credit: 0
          },
          {
            account: '44566', // TVA déductible sur ABS
            label: 'TVA déductible sur biens et services',
            debit: 0,
            credit: vatReport.deductible.totalVatAmount
          },
          {
            account: '44567', // Crédit de TVA à reporter
            label: 'Crédit de TVA à reporter',
            debit: 0,
            credit: Math.abs(vatReport.balance.balanceDue)
          }
        ]
      });
    }
    
    return {
      entries,
      metadata: {
        generatedAt: new Date(),
        period: vatReport.period,
        vatReportId: vatReport.id || `VAT_${moment(vatReport.period.start).format('YYYYMM')}_${moment(vatReport.period.end).format('YYYYMM')}`
      }
    };
  }
  
  /**
   * Vérifie la cohérence des données de TVA
   * @param {Object} vatReport - Rapport de TVA à vérifier
   * @returns {Object} - Résultat de la vérification
   */
  checkVATConsistency(vatReport) {
    if (!vatReport || !vatReport.collected || !vatReport.deductible) {
      throw new Error('Rapport de TVA incomplet ou invalide');
    }
    
    const result = {
      isConsistent: true,
      issues: [],
      warnings: []
    };
    
    // Vérifier la cohérence des totaux collectés
    const collectedSum = Object.values(vatReport.collected.byRate)
      .reduce((sum, data) => sum + data.vatAmount, 0);
    
    if (Math.abs(collectedSum - vatReport.collected.totalVatAmount) > 0.01) {
      result.isConsistent = false;
      result.issues.push({
        type: 'total_mismatch',
        entity: 'collected',
        expected: vatReport.collected.totalVatAmount,
        calculated: collectedSum,
        difference: vatReport.collected.totalVatAmount - collectedSum
      });
    }
    
    // Vérifier la cohérence des totaux déductibles
    const deductibleSum = Object.values(vatReport.deductible.byType)
      .reduce((sum, data) => sum + data.vatAmount, 0);
    
    if (Math.abs(deductibleSum - vatReport.deductible.totalVatAmount) > 0.01) {
      result.isConsistent = false;
      result.issues.push({
        type: 'total_mismatch',
        entity: 'deductible',
        expected: vatReport.deductible.totalVatAmount,
        calculated: deductibleSum,
        difference: vatReport.deductible.totalVatAmount - deductibleSum
      });
    }
    
    // Vérifier la cohérence du solde
    const expectedBalance = vatReport.collected.totalVatAmount - vatReport.deductible.totalVatAmount;
    
    if (Math.abs(expectedBalance - vatReport.balance.balanceDue) > 0.01) {
      result.isConsistent = false;
      result.issues.push({
        type: 'balance_mismatch',
        expected: expectedBalance,
        calculated: vatReport.balance.balanceDue,
        difference: expectedBalance - vatReport.balance.balanceDue
      });
    }
    
    // Vérifier les taux de TVA inhabituels
    for (const [rateKey, data] of Object.entries(vatReport.collected.byRate)) {
      if (!Object.values(this.vatRates).includes(data.rate)) {
        result.warnings.push({
          type: 'unusual_rate',
          entity: 'collected',
          rate: data.rate,
          baseAmount: data.baseAmount,
          vatAmount: data.vatAmount
        });
      }
    }
    
    return result;
  }
  
  /**
   * Détermine le taux de TVA applicable pour un item
   * @param {Object} item - Item de la transaction
   * @param {string} transactionType - Type de transaction (onsite, takeaway)
   * @param {Object} options - Options supplémentaires
   * @returns {number} - Taux de TVA applicable
   * @private
   */
  _getVatRateForItem(item, transactionType = 'onsite', options = {}) {
    // Si le taux est explicitement défini sur l'item
    if (item.vatRate !== undefined) {
      return Number(item.vatRate);
    }
    
    // Si l'item a une catégorie fiscale définie
    if (item.taxCategory) {
      return this._getVatRateByCategory(item.taxCategory);
    }
    
    // Déterminer en fonction de la catégorie de produit et du type de transaction
    if (item.category) {
      // Construire la clé de recherche
      let categoryKey = item.category.toLowerCase();
      
      // Ajouter le type de transaction pour les produits sensibles au type
      if (item.category.includes('food') || item.category.includes('beverage')) {
        categoryKey += '_' + transactionType;
      }
      
      // Rechercher dans la configuration
      if (this.productCategories[categoryKey] !== undefined) {
        return this.productCategories[categoryKey];
      }
    }
    
    // Cas particuliers
    if (item.isAlcoholic) {
      return this.vatRates.standard; // Taux standard pour l'alcool
    }
    
    // Valeur par défaut selon le type de transaction
    return transactionType === 'onsite' ? this.vatRates.intermediate : this.vatRates.reduced;
  }
  
  /**
   * Récupère le taux de TVA par catégorie fiscale
   * @param {string} category - Catégorie fiscale
   * @returns {number} - Taux de TVA
   * @private
   */
  _getVatRateByCategory(category) {
    switch (category.toLowerCase()) {
      case 'standard':
        return this.vatRates.standard;
      case 'intermediate':
        return this.vatRates.intermediate;
      case 'reduced':
        return this.vatRates.reduced;
      case 'super_reduced':
        return this.vatRates.superReduced;
      case 'zero':
        return this.vatRates.zero;
      default:
        return this.vatRates.intermediate; // Taux intermédiaire par défaut
    }
  }
  
  /**
   * Détermine la clé de taux de TVA à partir de la valeur
   * @param {number} rate - Taux de TVA
   * @returns {string} - Clé du taux
   * @private
   */
  _getVatRateKey(rate) {
    // Rechercher la clé correspondant au taux
    for (const [key, value] of Object.entries(this.vatRates)) {
      if (Math.abs(value - rate) < 0.01) {
        return key;
      }
    }
    
    // Si non trouvé, utiliser une clé générique
    return `rate_${rate}`;
  }
  
  /**
   * Récupère les données de vente
   * @param {Object} options - Options de filtrage
   * @returns {Promise<Object>} - Données de vente
   * @private
   */
  async _getSalesData(options = {}) {
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    return this.dataCollector.getSalesData(options);
  }
  
  /**
   * Récupère les données d'achat
   * @param {Object} options - Options de filtrage
   * @returns {Promise<Object>} - Données d'achat
   * @private
   */
  async _getPurchasesData(options = {}) {
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    return this.dataCollector.getExpensesData(options);
  }
  
  /**
   * Calcule la TVA collectée à partir des données de vente
   * @param {Object} salesData - Données de vente
   * @returns {Object} - TVA collectée
   * @private
   */
  _calculateCollectedVAT(salesData) {
    // Structure pour stocker les résultats
    const result = {
      totalVatAmount: 0,
      totalBaseAmount: 0,
      byRate: {}
    };
    
    // Traiter chaque transaction
    for (const transaction of salesData.transactions || []) {
      // Calculer la TVA pour cette transaction
      const vatResult = this.calculateTransactionVAT(transaction);
      
      // Ajouter aux totaux
      result.totalVatAmount += vatResult.totalVatAmount;
      result.totalBaseAmount += vatResult.totalAmountWithoutTax;
      
      // Agréger par taux
      for (const [rateKey, data] of Object.entries(vatResult.vatBreakdown)) {
        if (!result.byRate[rateKey]) {
          result.byRate[rateKey] = {
            rate: data.rate,
            baseAmount: 0,
            vatAmount: 0,
            accountNumber: data.accountNumber
          };
        }
        
        result.byRate[rateKey].baseAmount += data.baseAmount;
        result.byRate[rateKey].vatAmount += data.vatAmount;
      }
    }
    
    // Arrondir les montants
    result.totalVatAmount = parseFloat(result.totalVatAmount.toFixed(2));
    result.totalBaseAmount = parseFloat(result.totalBaseAmount.toFixed(2));
    
    for (const key in result.byRate) {
      result.byRate[key].baseAmount = parseFloat(result.byRate[key].baseAmount.toFixed(2));
      result.byRate[key].vatAmount = parseFloat(result.byRate[key].vatAmount.toFixed(2));
    }
    
    return result;
  }
  
  /**
   * Calcule la TVA déductible à partir des données d'achat
   * @param {Object} purchasesData - Données d'achat
   * @returns {Object} - TVA déductible
   * @private
   */
  _calculateDeductibleVAT(purchasesData) {
    // Structure pour stocker les résultats
    const result = {
      totalVatAmount: 0,
      totalBaseAmount: 0,
      byRate: {},
      byType: {
        goods: { baseAmount: 0, vatAmount: 0 },
        services: { baseAmount: 0, vatAmount: 0 },
        fixed_assets: { baseAmount: 0, vatAmount: 0 }
      }
    };
    
    // Traiter chaque achat
    for (const purchase of purchasesData.purchases || []) {
      // Déterminer le type d'achat
      const purchaseType = this._determinePurchaseType(purchase);
      
      // Parcourir les items
      for (const item of purchase.items || []) {
        // Récupérer le taux de TVA
        const vatRate = item.vatRate || this.vatRates.standard;
        const vatRateKey = this._getVatRateKey(vatRate);
        
        // Calculer les montants
        const baseAmount = item.amountWithoutTax || (item.amount / (1 + vatRate / 100));
        const vatAmount = item.vatAmount || (item.amount - baseAmount);
        
        // Ajouter aux totaux
        result.totalVatAmount += vatAmount;
        result.totalBaseAmount += baseAmount;
        
        // Agréger par taux
        if (!result.byRate[vatRateKey]) {
          result.byRate[vatRateKey] = {
            rate: vatRate,
            baseAmount: 0,
            vatAmount: 0
          };
        }
        
        result.byRate[vatRateKey].baseAmount += baseAmount;
        result.byRate[vatRateKey].vatAmount += vatAmount;
        
        // Agréger par type
        result.byType[purchaseType].baseAmount += baseAmount;
        result.byType[purchaseType].vatAmount += vatAmount;
      }
    }
    
    // Arrondir les montants
    result.totalVatAmount = parseFloat(result.totalVatAmount.toFixed(2));
    result.totalBaseAmount = parseFloat(result.totalBaseAmount.toFixed(2));
    
    for (const key in result.byRate) {
      result.byRate[key].baseAmount = parseFloat(result.byRate[key].baseAmount.toFixed(2));
      result.byRate[key].vatAmount = parseFloat(result.byRate[key].vatAmount.toFixed(2));
    }
    
    for (const key in result.byType) {
      result.byType[key].baseAmount = parseFloat(result.byType[key].baseAmount.toFixed(2));
      result.byType[key].vatAmount = parseFloat(result.byType[key].vatAmount.toFixed(2));
    }
    
    return result;
  }
  
  /**
   * Détermine le type d'achat pour la TVA
   * @param {Object} purchase - Données de l'achat
   * @returns {string} - Type d'achat (goods, services, fixed_assets)
   * @private
   */
  _determinePurchaseType(purchase) {
    // Si le type est explicitement défini
    if (purchase.type) {
      const type = purchase.type.toLowerCase();
      
      if (type.includes('service')) {
        return 'services';
      } else if (type.includes('asset') || type.includes('immobilisation')) {
        return 'fixed_assets';
      } else if (type.includes('good') || type.includes('product') || type.includes('marchandise')) {
        return 'goods';
      }
    }
    
    // Déterminer en fonction de la catégorie de produit
    if (purchase.category) {
      const category = purchase.category.toLowerCase();
      
      if (category.includes('service') || 
          category.includes('consult') || 
          category.includes('maint')) {
        return 'services';
      } else if (category.includes('asset') || 
                 category.includes('equipment') || 
                 category.includes('furniture')) {
        return 'fixed_assets';
      }
    }
    
    // Valeur par défaut
    return 'goods';
  }
  
  /**
   * Calcule le solde de TVA
   * @param {Object} collectedVAT - TVA collectée
   * @param {Object} deductibleVAT - TVA déductible
   * @returns {Object} - Solde de TVA
   * @private
   */
  _calculateVATBalance(collectedVAT, deductibleVAT) {
    const balanceDue = parseFloat((collectedVAT.totalVatAmount - deductibleVAT.totalVatAmount).toFixed(2));
    
    return {
      balanceDue,
      isCredit: balanceDue < 0,
      status: balanceDue > 0 ? 'to_pay' : (balanceDue < 0 ? 'credit' : 'zero')
    };
  }
  
  /**
   * Calcule la date de déclaration
   * @param {Date|moment.Moment} periodEndDate - Date de fin de période
   * @returns {Date} - Date de déclaration
   * @private
   */
  _calculateDeclarationDate(periodEndDate) {
    return moment(periodEndDate)
      .add(1, 'month')
      .startOf('month')
      .add(this.declarationPeriods.deadline - 1, 'days')
      .toDate();
  }
  
  /**
   * Calcule la date de paiement
   * @param {Date|moment.Moment} periodEndDate - Date de fin de période
   * @returns {Date} - Date de paiement
   * @private
   */
  _calculatePaymentDate(periodEndDate) {
    return moment(periodEndDate)
      .add(1, 'month')
      .startOf('month')
      .add(this.declarationPeriods.paymentDeadline - 1, 'days')
      .toDate();
  }
  
  /**
   * Détermine le type de période
   * @param {Date|moment.Moment} startDate - Date de début
   * @param {Date|moment.Moment} endDate - Date de fin
   * @returns {string} - Type de période (month, quarter, year, custom)
   * @private
   */
  _getPeriodType(startDate, endDate) {
    const start = moment(startDate);
    const end = moment(endDate);
    
    // Vérifier si c'est un mois complet
    if (start.date() === 1 && end.date() === end.daysInMonth() && 
        start.month() === end.month() && start.year() === end.year()) {
      return 'month';
    }
    
    // Vérifier si c'est un trimestre complet
    if (start.date() === 1 && end.date() === end.daysInMonth() && 
        Math.floor(start.month() / 3) === Math.floor(end.month() / 3) && 
        start.year() === end.year() && 
        (end.month() - start.month() === 2)) {
      return 'quarter';
    }
    
    // Vérifier si c'est une année complète
    if (start.date() === 1 && start.month() === 0 && 
        end.date() === 31 && end.month() === 11 && 
        start.year() === end.year()) {
      return 'year';
    }
    
    // Période personnalisée
    return 'custom';
  }
}

module.exports = { TaxCalculator };
