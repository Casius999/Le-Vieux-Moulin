/**
 * Module de calcul de TVA pour Le Vieux Moulin
 * Ce module gère le calcul automatique de la TVA selon les différentes règles et taux
 * applicables à la restauration en France.
 */

'use strict';

const _ = require('lodash');
const moment = require('moment');

/**
 * Classe principale pour le calcul de TVA
 */
class VATCalculator {
  /**
   * Crée une nouvelle instance du calculateur de TVA
   * @param {Object} options Options de configuration
   * @param {Object} options.vatRates Configuration des taux de TVA
   * @param {Object} options.productCategories Mapping des catégories de produits
   * @param {Object} options.specialProducts Configuration pour produits spécifiques
   */
  constructor(options = {}) {
    // Configuration par défaut pour la France (restauration)
    this.vatRates = options.vatRates || {
      standard: 20.0,     // Taux standard
      intermediate: 10.0, // Taux intermédiaire (restauration sur place)
      reduced: 5.5,       // Taux réduit (nourriture à emporter)
      superReduced: 2.1   // Taux super réduit (non utilisé en restauration)
    };
    
    // Mapping des catégories de produits aux taux de TVA
    this.productCategories = options.productCategories || {
      food_onsite: 'intermediate',      // Nourriture sur place
      food_takeaway: 'reduced',         // Nourriture à emporter
      alcohol: 'standard',              // Boissons alcoolisées
      non_alcoholic_drinks: 'intermediate', // Boissons non alcoolisées sur place
      non_alcoholic_takeaway: 'reduced' // Boissons non alcoolisées à emporter
    };
    
    // Configuration spéciale pour certains produits
    this.specialProducts = options.specialProducts || {};
  }
  
  /**
   * Calcule la TVA pour un produit spécifique
   * @param {Object} product Produit avec informations de prix et catégorie
   * @param {boolean} isTakeaway Indique si le produit est vendu à emporter
   * @returns {Object} Détails de la TVA calculée
   */
  calculateProductVAT(product, isTakeaway = false) {
    if (!product || typeof product !== 'object') {
      throw new Error('Produit invalide pour le calcul de TVA');
    }
    
    const priceWithTax = parseFloat(product.price || 0);
    if (isNaN(priceWithTax) || priceWithTax < 0) {
      throw new Error('Prix invalide pour le calcul de TVA');
    }
    
    // Déterminer le taux de TVA applicable
    let vatRateKey;
    
    // Vérifier d'abord si c'est un produit spécial avec un taux spécifique
    if (product.id && this.specialProducts[product.id]) {
      vatRateKey = this.specialProducts[product.id];
    } else {
      // Sinon, utiliser la catégorie du produit
      let category = product.category || 'food_onsite';
      
      // Ajuster la catégorie si c'est à emporter
      if (isTakeaway) {
        if (category === 'food_onsite') {
          category = 'food_takeaway';
        } else if (category === 'non_alcoholic_drinks') {
          category = 'non_alcoholic_takeaway';
        }
        // Les boissons alcoolisées restent au taux standard même en vente à emporter
      }
      
      vatRateKey = this.productCategories[category] || 'standard';
    }
    
    const vatRate = this.vatRates[vatRateKey];
    
    // Calcul de la TVA
    const priceWithoutTax = priceWithTax / (1 + vatRate/100);
    const vatAmount = priceWithTax - priceWithoutTax;
    
    return {
      priceWithTax,
      priceWithoutTax: parseFloat(priceWithoutTax.toFixed(4)),
      vatAmount: parseFloat(vatAmount.toFixed(4)),
      vatRate,
      vatRateKey
    };
  }
  
  /**
   * Calcule la TVA pour un ticket complet
   * @param {Object} ticket Ticket avec lignes de produits
   * @returns {Object} Détails de la TVA calculée pour le ticket
   */
  calculateTicketVAT(ticket) {
    if (!ticket || !ticket.items || !Array.isArray(ticket.items)) {
      throw new Error('Ticket invalide pour le calcul de TVA');
    }
    
    // Initialiser les totaux par taux de TVA
    const vatBreakdown = {};
    Object.keys(this.vatRates).forEach(key => {
      vatBreakdown[key] = {
        rate: this.vatRates[key],
        baseAmount: 0,
        vatAmount: 0,
        totalAmount: 0
      };
    });
    
    // Pour chaque produit du ticket
    ticket.items.forEach(item => {
      const isTakeaway = ticket.takeaway || item.takeaway || false;
      const quantity = parseFloat(item.quantity || 1);
      
      // Calculer la TVA pour ce produit
      const vatDetails = this.calculateProductVAT(item, isTakeaway);
      const vatRateKey = vatDetails.vatRateKey;
      
      // Mettre à jour les totaux pour ce taux de TVA
      vatBreakdown[vatRateKey].baseAmount += vatDetails.priceWithoutTax * quantity;
      vatBreakdown[vatRateKey].vatAmount += vatDetails.vatAmount * quantity;
      vatBreakdown[vatRateKey].totalAmount += vatDetails.priceWithTax * quantity;
    });
    
    // Calculer les totaux globaux
    let totalBaseAmount = 0;
    let totalVatAmount = 0;
    let totalAmount = 0;
    
    // Arrondir et finaliser les montants
    Object.keys(vatBreakdown).forEach(key => {
      vatBreakdown[key].baseAmount = parseFloat(vatBreakdown[key].baseAmount.toFixed(2));
      vatBreakdown[key].vatAmount = parseFloat(vatBreakdown[key].vatAmount.toFixed(2));
      vatBreakdown[key].totalAmount = parseFloat(vatBreakdown[key].totalAmount.toFixed(2));
      
      totalBaseAmount += vatBreakdown[key].baseAmount;
      totalVatAmount += vatBreakdown[key].vatAmount;
      totalAmount += vatBreakdown[key].totalAmount;
    });
    
    // Vérifier s'il y a un écart de centimes dû aux arrondis
    const computedTotal = parseFloat(totalAmount.toFixed(2));
    const ticketTotal = parseFloat(ticket.total || 0);
    
    let roundingAdjustment = 0;
    if (ticketTotal > 0 && Math.abs(computedTotal - ticketTotal) <= 0.02) {
      roundingAdjustment = ticketTotal - computedTotal;
      totalAmount = ticketTotal;
    }
    
    return {
      breakdown: vatBreakdown,
      totalBaseAmount: parseFloat(totalBaseAmount.toFixed(2)),
      totalVatAmount: parseFloat(totalVatAmount.toFixed(2)),
      totalAmount: parseFloat(totalAmount.toFixed(2)),
      roundingAdjustment: parseFloat(roundingAdjustment.toFixed(2)),
      ticketNumber: ticket.number,
      ticketDate: ticket.date,
      isTakeaway: ticket.takeaway || false
    };
  }
  
  /**
   * Calcule la TVA pour un ensemble de transactions sur une période
   * @param {Array<Object>} transactions Liste des transactions
   * @param {Object} period Période de calcul (startDate, endDate)
   * @returns {Object} Rapport détaillé de TVA pour la période
   */
  calculatePeriodVAT(transactions, period = {}) {
    if (!Array.isArray(transactions)) {
      throw new Error('Liste de transactions invalide pour le calcul de TVA');
    }
    
    // Filtrer les transactions par période si spécifiée
    let filteredTransactions = transactions;
    if (period.startDate || period.endDate) {
      const startDate = period.startDate ? moment(period.startDate).startOf('day') : moment(0);
      const endDate = period.endDate ? moment(period.endDate).endOf('day') : moment().endOf('day');
      
      filteredTransactions = transactions.filter(tx => {
        const txDate = moment(tx.date);
        return txDate.isSameOrAfter(startDate) && txDate.isSameOrBefore(endDate);
      });
    }
    
    // Initialiser les totaux par taux de TVA
    const vatTotals = {};
    Object.keys(this.vatRates).forEach(key => {
      vatTotals[key] = {
        rate: this.vatRates[key],
        baseAmount: 0,
        vatAmount: 0,
        totalAmount: 0,
        transactionCount: 0
      };
    });
    
    // Variables pour les totaux globaux
    let totalTransactions = 0;
    let totalBaseAmount = 0;
    let totalVatAmount = 0;
    let totalAmount = 0;
    
    // Calculer la TVA pour chaque transaction
    filteredTransactions.forEach(transaction => {
      try {
        const vatDetails = this.calculateTicketVAT(transaction);
        totalTransactions++;
        
        // Mettre à jour les totaux par taux
        Object.keys(vatDetails.breakdown).forEach(key => {
          const breakdown = vatDetails.breakdown[key];
          if (breakdown.totalAmount > 0) {
            vatTotals[key].baseAmount += breakdown.baseAmount;
            vatTotals[key].vatAmount += breakdown.vatAmount;
            vatTotals[key].totalAmount += breakdown.totalAmount;
            vatTotals[key].transactionCount++;
          }
        });
        
        // Mettre à jour les totaux globaux
        totalBaseAmount += vatDetails.totalBaseAmount;
        totalVatAmount += vatDetails.totalVatAmount;
        totalAmount += vatDetails.totalAmount;
      } catch (error) {
        console.error(`Erreur lors du calcul de TVA pour la transaction ${transaction.id || 'inconnu'}:`, error);
      }
    });
    
    // Arrondir les montants finaux
    Object.keys(vatTotals).forEach(key => {
      vatTotals[key].baseAmount = parseFloat(vatTotals[key].baseAmount.toFixed(2));
      vatTotals[key].vatAmount = parseFloat(vatTotals[key].vatAmount.toFixed(2));
      vatTotals[key].totalAmount = parseFloat(vatTotals[key].totalAmount.toFixed(2));
    });
    
    // Générer le rapport de TVA
    return {
      period: {
        startDate: period.startDate ? moment(period.startDate).format('YYYY-MM-DD') : null,
        endDate: period.endDate ? moment(period.endDate).format('YYYY-MM-DD') : null,
        description: this._generatePeriodDescription(period)
      },
      vatTotals,
      totalTransactions,
      totalBaseAmount: parseFloat(totalBaseAmount.toFixed(2)),
      totalVatAmount: parseFloat(totalVatAmount.toFixed(2)),
      totalAmount: parseFloat(totalAmount.toFixed(2)),
      generatedAt: new Date(),
      currency: 'EUR'
    };
  }
  
  /**
   * Calcule un rapport de TVA complet (collectée et déductible)
   * @param {Object} options Options du rapport
   * @param {Array<Object>} options.salesTransactions Transactions de vente
   * @param {Array<Object>} options.purchaseTransactions Transactions d'achat
   * @param {Object} options.period Période du rapport
   * @returns {Object} Rapport complet de TVA
   */
  generateVATReport(options = {}) {
    const salesTransactions = options.salesTransactions || [];
    const purchaseTransactions = options.purchaseTransactions || [];
    const period = options.period || {};
    
    // Calculer la TVA collectée (ventes)
    const collectedVAT = this.calculatePeriodVAT(salesTransactions, period);
    
    // Calculer la TVA déductible (achats)
    const deductibleVAT = this._calculateDeductibleVAT(purchaseTransactions, period);
    
    // Calculer la balance de TVA
    const vatBalance = this._calculateVATBalance(collectedVAT, deductibleVAT);
    
    // Ajouter des méta-informations
    const reportMetadata = {
      reportType: 'VAT',
      reportPeriod: this._generatePeriodDescription(period),
      generatedAt: new Date(),
      version: '1.0',
      currency: 'EUR',
      companyInfo: options.companyInfo || {},
      declarationStatus: 'draft',
      declarationDeadline: this._calculateDeclarationDeadline(period)
    };
    
    return {
      metadata: reportMetadata,
      collected: collectedVAT,
      deductible: deductibleVAT,
      balance: vatBalance
    };
  }
  
  /**
   * Calcule la TVA déductible pour une période
   * @param {Array<Object>} transactions Transactions d'achat
   * @param {Object} period Période de calcul
   * @returns {Object} Détails de la TVA déductible
   * @private
   */
  _calculateDeductibleVAT(transactions, period) {
    // La logique ressemble à calculatePeriodVAT mais adaptée aux achats
    // Par simplicité, nous utilisons la même méthode avec des ajustements mineurs
    
    const deductibleReport = this.calculatePeriodVAT(transactions, period);
    
    // Ajuster quelques propriétés pour refléter qu'il s'agit de TVA déductible
    deductibleReport.isDeductible = true;
    
    // Ajout des détails de récupérabilité de la TVA
    Object.keys(deductibleReport.vatTotals).forEach(key => {
      // Par défaut, toute la TVA est récupérable
      deductibleReport.vatTotals[key].recoverable = deductibleReport.vatTotals[key].vatAmount;
      deductibleReport.vatTotals[key].nonRecoverable = 0;
    });
    
    // Calculer les totaux de TVA récupérable
    deductibleReport.totalRecoverableVAT = deductibleReport.totalVatAmount;
    deductibleReport.totalNonRecoverableVAT = 0;
    
    return deductibleReport;
  }
  
  /**
   * Calcule la balance de TVA (TVA collectée - TVA déductible)
   * @param {Object} collectedVAT Détails de la TVA collectée
   * @param {Object} deductibleVAT Détails de la TVA déductible
   * @returns {Object} Balance de TVA
   * @private
   */
  _calculateVATBalance(collectedVAT, deductibleVAT) {
    // Initialiser la structure de balance par taux
    const balanceByRate = {};
    
    // Traiter d'abord la TVA collectée
    Object.keys(collectedVAT.vatTotals).forEach(key => {
      const rate = collectedVAT.vatTotals[key].rate;
      balanceByRate[key] = {
        rate,
        collected: collectedVAT.vatTotals[key].vatAmount,
        deductible: 0,
        balance: collectedVAT.vatTotals[key].vatAmount
      };
    });
    
    // Puis la TVA déductible
    Object.keys(deductibleVAT.vatTotals).forEach(key => {
      if (balanceByRate[key]) {
        balanceByRate[key].deductible = deductibleVAT.vatTotals[key].recoverable;
        balanceByRate[key].balance = balanceByRate[key].collected - balanceByRate[key].deductible;
      } else {
        balanceByRate[key] = {
          rate: deductibleVAT.vatTotals[key].rate,
          collected: 0,
          deductible: deductibleVAT.vatTotals[key].recoverable,
          balance: -deductibleVAT.vatTotals[key].recoverable
        };
      }
    });
    
    // Calculer les totaux globaux
    const totalCollected = collectedVAT.totalVatAmount;
    const totalDeductible = deductibleVAT.totalRecoverableVAT;
    const netBalance = totalCollected - totalDeductible;
    
    return {
      balanceByRate,
      totalCollected,
      totalDeductible,
      netBalance,
      isCredit: netBalance < 0,
      isDue: netBalance > 0,
      amount: Math.abs(netBalance),
      currency: 'EUR'
    };
  }
  
  /**
   * Génère une description lisible de la période
   * @param {Object} period Période à décrire
   * @returns {string} Description de la période
   * @private
   */
  _generatePeriodDescription(period) {
    if (!period) return 'Période indéfinie';
    
    if (period.year && period.month) {
      return `${moment(`${period.year}-${period.month}-01`).format('MMMM YYYY')}`;
    }
    
    if (period.year && period.quarter) {
      return `${period.quarter}e trimestre ${period.year}`;
    }
    
    if (period.year) {
      return `Année ${period.year}`;
    }
    
    if (period.startDate && period.endDate) {
      return `Du ${moment(period.startDate).format('DD/MM/YYYY')} au ${moment(period.endDate).format('DD/MM/YYYY')}`;
    }
    
    if (period.startDate) {
      return `À partir du ${moment(period.startDate).format('DD/MM/YYYY')}`;
    }
    
    if (period.endDate) {
      return `Jusqu'au ${moment(period.endDate).format('DD/MM/YYYY')}`;
    }
    
    return 'Période indéfinie';
  }
  
  /**
   * Calcule la date limite de déclaration de TVA
   * @param {Object} period Période concernée
   * @returns {Date} Date limite de déclaration
   * @private
   */
  _calculateDeclarationDeadline(period) {
    if (!period) return null;
    
    let endDate;
    
    if (period.year && period.month) {
      // Déclaration mensuelle: le mois suivant
      endDate = moment(`${period.year}-${period.month}-01`).endOf('month');
    } else if (period.year && period.quarter) {
      // Déclaration trimestrielle: fin du trimestre
      const lastMonthOfQuarter = period.quarter * 3;
      endDate = moment(`${period.year}-${lastMonthOfQuarter}-01`).endOf('month');
    } else if (period.year) {
      // Déclaration annuelle: fin d'année
      endDate = moment(`${period.year}-12-31`);
    } else if (period.endDate) {
      endDate = moment(period.endDate);
    } else {
      return null;
    }
    
    // La date limite est généralement le mois suivant la fin de période
    return endDate.add(20, 'days').toDate();
  }
}

module.exports = {
  VATCalculator
};