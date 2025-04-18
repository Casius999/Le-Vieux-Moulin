/**
 * Module d'exportation comptable
 * 
 * Ce module permet d'exporter les données financières dans différents formats
 * compatibles avec les logiciels de comptabilité standards.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const moment = require('moment');
const XLSX = require('xlsx');
const { EventEmitter } = require('events');

/**
 * Classe principale d'exportation comptable
 */
class AccountingExporter extends EventEmitter {
  /**
   * Crée une nouvelle instance de l'exportateur comptable
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataConsolidator - Consolidateur de données
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.alertService - Service d'alertes
   * @param {string} options.outputDir - Répertoire de sortie des exports
   */
  constructor(options = {}) {
    super();
    
    this.dataConsolidator = options.dataConsolidator;
    this.configManager = options.configManager;
    this.alertService = options.alertService;
    this.outputDir = options.outputDir || './exports';
    
    // Charger la configuration des exports
    this.exportConfig = this._loadExportConfig();
    
    // Créer le répertoire de sortie s'il n'existe pas
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
    
    // Historique des exports
    this.exportHistory = [];
  }
  
  /**
   * Charge la configuration des exports
   * @returns {Object} - Configuration des exports
   * @private
   */
  _loadExportConfig() {
    const defaultConfig = {
      formats: {
        sage: {
          enabled: true,
          description: "Format Sage Compta",
          extension: ".csv",
          delimiter: ";",
          dateFormat: "DD/MM/YYYY",
          encoding: "utf8"
        },
        ebp: {
          enabled: true,
          description: "Format EBP",
          extension: ".csv",
          delimiter: ";",
          dateFormat: "DD/MM/YYYY",
          encoding: "utf8"
        },
        quickbooks: {
          enabled: true,
          description: "Format QuickBooks",
          extension: ".iif",
          delimiter: "\t",
          dateFormat: "MM/DD/YYYY",
          encoding: "utf8"
        },
        excel: {
          enabled: true,
          description: "Format Excel",
          extension: ".xlsx",
          dateFormat: "YYYY-MM-DD",
          encoding: "utf8"
        },
        fec: {
          enabled: true,
          description: "Format FEC (Fichier des Écritures Comptables)",
          extension: ".txt",
          delimiter: "\t",
          dateFormat: "YYYYMMDD",
          encoding: "utf8"
        }
      },
      accountMapping: {
        sales: {
          food: "707100",
          beverages: "707200",
          alcohol: "707300",
          takeaway: "707400",
          other: "708000"
        },
        expenses: {
          food: "607100",
          beverages: "607200",
          rent: "613000",
          utilities: "606000",
          salaries: "641000",
          socialCharges: "645000",
          maintenance: "615000",
          advertising: "623000",
          insurance: "616000",
          bankFees: "627000",
          other: "628000"
        },
        taxes: {
          vatCollected: "445710",
          vatDeductible: "445660",
          vatToPay: "445510"
        },
        bank: {
          bankAccount: "512000",
          cashAccount: "531000"
        }
      },
      companyInfo: {
        name: "SARL Le Vieux Moulin",
        address: "Camping 3 étoiles, Vensac, Gironde",
        phone: "+33 7 79 43 17 29",
        siret: "00000000000000", // À remplacer par le vrai SIRET
        vatNumber: "FR00000000000", // À remplacer par le vrai numéro de TVA
        fiscalYear: {
          start: "01-01",
          end: "12-31"
        }
      }
    };
    
    // Fusionner avec la configuration personnalisée si disponible
    if (this.configManager) {
      const customConfig = this.configManager.getConfig('accounting.export', {});
      return {
        formats: { ...defaultConfig.formats, ...customConfig.formats },
        accountMapping: { ...defaultConfig.accountMapping, ...customConfig.accountMapping },
        companyInfo: { ...defaultConfig.companyInfo, ...customConfig.companyInfo }
      };
    }
    
    return defaultConfig;
  }
  
  /**
   * Exporte les données comptables pour une période donnée
   * @param {Object} options - Options d'exportation
   * @param {Date|string} options.startDate - Date de début de la période
   * @param {Date|string} options.endDate - Date de fin de la période
   * @param {string} options.format - Format d'export (sage, ebp, quickbooks, excel, fec)
   * @param {boolean} options.includeDrafts - Inclure les écritures en brouillon
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   */
  async exportAccountingData(options = {}) {
    const startDate = options.startDate ? moment(options.startDate) : moment().startOf('month');
    const endDate = options.endDate ? moment(options.endDate) : moment().endOf('month');
    const format = options.format || 'sage';
    const includeDrafts = options.includeDrafts !== undefined ? options.includeDrafts : false;
    
    try {
      // Vérifier si le format est supporté
      if (!this.exportConfig.formats[format] || !this.exportConfig.formats[format].enabled) {
        throw new Error(`Format d'export non supporté: ${format}`);
      }
      
      // Récupérer les données consolidées pour la période
      const consolidatedData = await this.dataConsolidator.consolidateFinancialData({
        startDate: startDate.format('YYYY-MM-DD'),
        endDate: endDate.format('YYYY-MM-DD')
      });
      
      // Préparer les données comptables (écritures, etc.)
      const accountingData = this._prepareAccountingData(consolidatedData, { includeDrafts });
      
      // Exporter dans le format demandé
      const exportResult = await this._exportToFormat(accountingData, format, {
        startDate,
        endDate
      });
      
      // Enregistrer dans l'historique
      this.exportHistory.push({
        timestamp: new Date(),
        period: {
          start: startDate.format('YYYY-MM-DD'),
          end: endDate.format('YYYY-MM-DD')
        },
        format,
        filePath: exportResult.filePath,
        fileSize: exportResult.fileSize,
        entriesCount: accountingData.entries.length
      });
      
      // Limiter l'historique à 100 entrées
      if (this.exportHistory.length > 100) {
        this.exportHistory.shift();
      }
      
      // Émettre un événement d'export réussi
      this.emit('export:complete', {
        format,
        period: {
          start: startDate.format('YYYY-MM-DD'),
          end: endDate.format('YYYY-MM-DD')
        },
        entriesCount: accountingData.entries.length,
        filePath: exportResult.filePath
      });
      
      return {
        status: 'success',
        format,
        period: {
          start: startDate.format('YYYY-MM-DD'),
          end: endDate.format('YYYY-MM-DD')
        },
        filePath: exportResult.filePath,
        fileSize: exportResult.fileSize,
        entriesCount: accountingData.entries.length
      };
    } catch (error) {
      console.error(`Erreur lors de l'export comptable au format ${format}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('export:error', {
        format,
        period: {
          start: startDate.format('YYYY-MM-DD'),
          end: endDate.format('YYYY-MM-DD')
        },
        error: error.message
      });
      
      // Créer une alerte
      if (this.alertService) {
        this.alertService.danger('accounting_export_error',
          `Erreur lors de l'export comptable au format ${format}: ${error.message}`,
          {
            period: {
              start: startDate.format('YYYY-MM-DD'),
              end: endDate.format('YYYY-MM-DD')
            },
            format,
            error: error.message
          }
        );
      }
      
      throw error;
    }
  }
  
  /**
   * Prépare les données comptables à partir des données consolidées
   * @param {Object} consolidatedData - Données consolidées
   * @param {Object} options - Options de préparation
   * @returns {Object} - Données comptables formatées
   * @private
   */
  _prepareAccountingData(consolidatedData, options = {}) {
    const { includeDrafts } = options;
    
    // Structure pour les données comptables
    const accountingData = {
      period: consolidatedData.period,
      journal: "VTE", // Journal des ventes par défaut
      entries: [],
      summary: {
        debit: 0,
        credit: 0,
        balance: 0
      }
    };
    
    // 1. Traiter les ventes
    if (consolidatedData.sources.sales) {
      this._processSalesData(consolidatedData.sources.sales, accountingData);
    }
    
    // 2. Traiter les dépenses
    if (consolidatedData.sources.expenses) {
      this._processExpensesData(consolidatedData.sources.expenses, accountingData);
    }
    
    // 3. Traiter les données de personnel
    if (consolidatedData.sources.staff) {
      this._processStaffData(consolidatedData.sources.staff, accountingData);
    }
    
    // 4. Traiter la TVA
    this._processVatData(consolidatedData, accountingData);
    
    // Calculer les totaux
    let totalDebit = 0;
    let totalCredit = 0;
    
    for (const entry of accountingData.entries) {
      totalDebit += entry.debit || 0;
      totalCredit += entry.credit || 0;
    }
    
    accountingData.summary.debit = totalDebit;
    accountingData.summary.credit = totalCredit;
    accountingData.summary.balance = totalCredit - totalDebit;
    
    return accountingData;
  }
  
  /**
   * Traite les données de ventes pour les transformer en écritures comptables
   * @param {Object} salesData - Données de ventes
   * @param {Object} accountingData - Données comptables à mettre à jour
   * @private
   */
  _processSalesData(salesData, accountingData) {
    // Traiter les ventes par catégorie
    for (const [category, data] of Object.entries(salesData.byCategory)) {
      // Déterminer le compte comptable
      let accountNumber;
      
      if (category === 'alcohol' && this.exportConfig.accountMapping.sales.alcohol) {
        accountNumber = this.exportConfig.accountMapping.sales.alcohol;
      } else if (category === 'takeaway' && this.exportConfig.accountMapping.sales.takeaway) {
        accountNumber = this.exportConfig.accountMapping.sales.takeaway;
      } else if (['food', 'desserts', 'starters', 'mains'].includes(category) && this.exportConfig.accountMapping.sales.food) {
        accountNumber = this.exportConfig.accountMapping.sales.food;
      } else if (['drinks', 'non_alcoholic', 'beverages'].includes(category) && this.exportConfig.accountMapping.sales.beverages) {
        accountNumber = this.exportConfig.accountMapping.sales.beverages;
      } else {
        accountNumber = this.exportConfig.accountMapping.sales.other;
      }
      
      // Créer l'écriture
      const entry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "VTE",
        accountNumber,
        label: `Ventes ${category} du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
        debit: 0,
        credit: data.total,
        reference: `V${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category
      };
      
      accountingData.entries.push(entry);
    }
    
    // Créer l'écriture de contrepartie (encaissement)
    // Nous supposons que les ventes sont réparties entre espèces et cartes bancaires
    
    const cashRatio = 0.2; // 20% des ventes en espèces (exemple)
    const cardRatio = 0.8; // 80% des ventes en cartes bancaires (exemple)
    
    // Encaissement en espèces
    if (salesData.totalSales * cashRatio > 0) {
      const cashEntry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "VTE",
        accountNumber: this.exportConfig.accountMapping.bank.cashAccount,
        label: `Encaissement espèces du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
        debit: salesData.totalSales * cashRatio,
        credit: 0,
        reference: `V${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category: 'encaissement'
      };
      
      accountingData.entries.push(cashEntry);
    }
    
    // Encaissement par carte bancaire
    if (salesData.totalSales * cardRatio > 0) {
      const cardEntry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "VTE",
        accountNumber: this.exportConfig.accountMapping.bank.bankAccount,
        label: `Encaissement CB du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
        debit: salesData.totalSales * cardRatio,
        credit: 0,
        reference: `V${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category: 'encaissement'
      };
      
      accountingData.entries.push(cardEntry);
    }
  }
  
  /**
   * Traite les données de dépenses pour les transformer en écritures comptables
   * @param {Object} expensesData - Données de dépenses
   * @param {Object} accountingData - Données comptables à mettre à jour
   * @private
   */
  _processExpensesData(expensesData, accountingData) {
    // Traiter les dépenses par catégorie
    for (const [category, data] of Object.entries(expensesData.byCategory)) {
      // Déterminer le compte comptable
      let accountNumber;
      
      if (category === 'food' && this.exportConfig.accountMapping.expenses.food) {
        accountNumber = this.exportConfig.accountMapping.expenses.food;
      } else if (category === 'beverages' && this.exportConfig.accountMapping.expenses.beverages) {
        accountNumber = this.exportConfig.accountMapping.expenses.beverages;
      } else if (category === 'rent' && this.exportConfig.accountMapping.expenses.rent) {
        accountNumber = this.exportConfig.accountMapping.expenses.rent;
      } else if (category === 'utilities' && this.exportConfig.accountMapping.expenses.utilities) {
        accountNumber = this.exportConfig.accountMapping.expenses.utilities;
      } else if (category === 'maintenance' && this.exportConfig.accountMapping.expenses.maintenance) {
        accountNumber = this.exportConfig.accountMapping.expenses.maintenance;
      } else if (category === 'advertising' && this.exportConfig.accountMapping.expenses.advertising) {
        accountNumber = this.exportConfig.accountMapping.expenses.advertising;
      } else if (category === 'insurance' && this.exportConfig.accountMapping.expenses.insurance) {
        accountNumber = this.exportConfig.accountMapping.expenses.insurance;
      } else if (category === 'bankFees' && this.exportConfig.accountMapping.expenses.bankFees) {
        accountNumber = this.exportConfig.accountMapping.expenses.bankFees;
      } else {
        accountNumber = this.exportConfig.accountMapping.expenses.other;
      }
      
      // Créer l'écriture
      const entry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "ACH", // Journal des achats
        accountNumber,
        label: `Dépenses ${category} du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
        debit: data.total,
        credit: 0,
        reference: `A${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category
      };
      
      accountingData.entries.push(entry);
    }
    
    // Créer l'écriture de contrepartie (paiement)
    const paymentEntry = {
      date: moment(accountingData.period.end).format('YYYY-MM-DD'),
      journal: "ACH",
      accountNumber: this.exportConfig.accountMapping.bank.bankAccount,
      label: `Paiement fournisseurs du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
      debit: 0,
      credit: expensesData.totalExpenses,
      reference: `A${moment(accountingData.period.end).format('YYYYMMDD')}`,
      category: 'paiement'
    };
    
    accountingData.entries.push(paymentEntry);
  }
  
  /**
   * Traite les données de personnel pour les transformer en écritures comptables
   * @param {Object} staffData - Données de personnel
   * @param {Object} accountingData - Données comptables à mettre à jour
   * @private
   */
  _processStaffData(staffData, accountingData) {
    // Créer l'écriture pour les salaires
    const salaryEntry = {
      date: moment(accountingData.period.end).format('YYYY-MM-DD'),
      journal: "OD", // Journal des opérations diverses
      accountNumber: this.exportConfig.accountMapping.expenses.salaries,
      label: `Salaires du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
      debit: staffData.totalCost * 0.7, // Approximation: 70% du coût total sont des salaires bruts
      credit: 0,
      reference: `S${moment(accountingData.period.end).format('YYYYMMDD')}`,
      category: 'salaries'
    };
    
    accountingData.entries.push(salaryEntry);
    
    // Créer l'écriture pour les charges sociales
    const socialChargesEntry = {
      date: moment(accountingData.period.end).format('YYYY-MM-DD'),
      journal: "OD",
      accountNumber: this.exportConfig.accountMapping.expenses.socialCharges,
      label: `Charges sociales du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
      debit: staffData.totalCost * 0.3, // Approximation: 30% du coût total sont des charges sociales
      credit: 0,
      reference: `S${moment(accountingData.period.end).format('YYYYMMDD')}`,
      category: 'social_charges'
    };
    
    accountingData.entries.push(socialChargesEntry);
    
    // Créer l'écriture de contrepartie (paiement)
    const paymentEntry = {
      date: moment(accountingData.period.end).format('YYYY-MM-DD'),
      journal: "OD",
      accountNumber: this.exportConfig.accountMapping.bank.bankAccount,
      label: `Paiement salaires et charges du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
      debit: 0,
      credit: staffData.totalCost,
      reference: `S${moment(accountingData.period.end).format('YYYYMMDD')}`,
      category: 'payment'
    };
    
    accountingData.entries.push(paymentEntry);
  }
  
  /**
   * Traite les données de TVA pour les transformer en écritures comptables
   * @param {Object} consolidatedData - Données consolidées
   * @param {Object} accountingData - Données comptables à mettre à jour
   * @private
   */
  _processVatData(consolidatedData, accountingData) {
    // Calculer la TVA collectée
    let vatCollected = 0;
    let vatDeductible = 0;
    
    // TVA collectée sur les ventes
    if (consolidatedData.sources.sales) {
      const sales = consolidatedData.sources.sales;
      
      // TVA à 20% (standard)
      if (sales.byCategory.alcohol) {
        const taxableAmount = sales.byCategory.alcohol.total / 1.20;
        const vat = sales.byCategory.alcohol.total - taxableAmount;
        vatCollected += vat;
      }
      
      // TVA à 10% (service sur place)
      const onPremiseCategories = ['food', 'desserts', 'starters', 'mains', 'non_alcoholic'];
      for (const category of onPremiseCategories) {
        if (sales.byCategory[category]) {
          const taxableAmount = sales.byCategory[category].total / 1.10;
          const vat = sales.byCategory[category].total - taxableAmount;
          vatCollected += vat;
        }
      }
      
      // TVA à 5.5% (vente à emporter)
      if (sales.byCategory.takeaway) {
        const taxableAmount = sales.byCategory.takeaway.total / 1.055;
        const vat = sales.byCategory.takeaway.total - taxableAmount;
        vatCollected += vat;
      }
    }
    
    // TVA déductible sur les achats
    if (consolidatedData.sources.expenses) {
      // Approximation: 80% des dépenses sont éligibles à la déduction de TVA à 20%
      const eligibleExpenses = consolidatedData.sources.expenses.totalExpenses * 0.80;
      vatDeductible = eligibleExpenses * 0.20 / 1.20;
    }
    
    // Créer l'écriture pour la TVA collectée
    if (vatCollected > 0) {
      const vatCollectedEntry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "OD", // Journal des opérations diverses
        accountNumber: this.exportConfig.accountMapping.taxes.vatCollected,
        label: `TVA collectée du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
        debit: 0,
        credit: vatCollected,
        reference: `T${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category: 'vat_collected'
      };
      
      accountingData.entries.push(vatCollectedEntry);
    }
    
    // Créer l'écriture pour la TVA déductible
    if (vatDeductible > 0) {
      const vatDeductibleEntry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "OD",
        accountNumber: this.exportConfig.accountMapping.taxes.vatDeductible,
        label: `TVA déductible du ${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`,
        debit: vatDeductible,
        credit: 0,
        reference: `T${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category: 'vat_deductible'
      };
      
      accountingData.entries.push(vatDeductibleEntry);
    }
    
    // Créer l'écriture pour la TVA à payer si c'est la fin du mois
    const isEndOfMonth = moment(accountingData.period.end).isSame(moment(accountingData.period.end).endOf('month'), 'day');
    
    if (isEndOfMonth && vatCollected > vatDeductible) {
      const vatToPayEntry = {
        date: moment(accountingData.period.end).format('YYYY-MM-DD'),
        journal: "OD",
        accountNumber: this.exportConfig.accountMapping.taxes.vatToPay,
        label: `TVA à payer pour ${moment(accountingData.period.end).format('MMMM YYYY')}`,
        debit: vatCollected - vatDeductible,
        credit: 0,
        reference: `T${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category: 'vat_to_pay'
      };
      
      accountingData.entries.push(vatToPayEntry);
      
      // Contrepartie sur le compte bancaire
      const vatPaymentEntry = {
        date: moment(accountingData.period.end).add(15, 'days').format('YYYY-MM-DD'), // Paiement 15 jours après la fin du mois
        journal: "OD",
        accountNumber: this.exportConfig.accountMapping.bank.bankAccount,
        label: `Paiement TVA pour ${moment(accountingData.period.end).format('MMMM YYYY')}`,
        debit: 0,
        credit: vatCollected - vatDeductible,
        reference: `T${moment(accountingData.period.end).format('YYYYMMDD')}`,
        category: 'vat_payment'
      };
      
      accountingData.entries.push(vatPaymentEntry);
    }
  }
  
  /**
   * Exporte les données comptables dans le format spécifié
   * @param {Object} accountingData - Données comptables
   * @param {string} format - Format d'export
   * @param {Object} options - Options d'export
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportToFormat(accountingData, format, options = {}) {
    const { startDate, endDate } = options;
    const formatConfig = this.exportConfig.formats[format];
    
    // Créer le sous-répertoire pour ce format si nécessaire
    const formatDir = path.join(this.outputDir, format);
    if (!fs.existsSync(formatDir)) {
      fs.mkdirSync(formatDir, { recursive: true });
    }
    
    // Définir le chemin du fichier de sortie
    const fileName = `export_${format}_${startDate.format('YYYYMMDD')}_${endDate.format('YYYYMMDD')}${formatConfig.extension}`;
    const filePath = path.join(formatDir, fileName);
    
    let result;
    
    switch (format) {
      case 'sage':
        result = await this._exportToSage(accountingData, filePath, formatConfig);
        break;
      
      case 'ebp':
        result = await this._exportToEBP(accountingData, filePath, formatConfig);
        break;
      
      case 'quickbooks':
        result = await this._exportToQuickBooks(accountingData, filePath, formatConfig);
        break;
      
      case 'excel':
        result = await this._exportToExcel(accountingData, filePath, formatConfig);
        break;
      
      case 'fec':
        result = await this._exportToFEC(accountingData, filePath, formatConfig);
        break;
      
      default:
        throw new Error(`Format d'export non supporté: ${format}`);
    }
    
    console.log(`Export comptable au format ${format} généré: ${filePath}`);
    
    return {
      filePath,
      fileSize: fs.statSync(filePath).size,
      format
    };
  }
  
  /**
   * Exporte les données comptables au format Sage
   * @param {Object} accountingData - Données comptables
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} formatConfig - Configuration du format
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportToSage(accountingData, filePath, formatConfig) {
    return new Promise((resolve, reject) => {
      try {
        // Créer l'en-tête du fichier
        let content = `JournalCode;EcritureNum;EcritureDate;CompteNum;CompteLib;CompAuxNum;CompAuxLib;PieceRef;PieceDate;EcritureLib;Debit;Credit;EcritureLet;DateLet;ValidDate;Montantdevise;Idevise\n`;
        
        // Ajouter chaque écriture
        accountingData.entries.forEach((entry, index) => {
          const entryNum = `E${String(index + 1).padStart(5, '0')}`;
          const debit = entry.debit.toFixed(2).replace('.', ',');
          const credit = entry.credit.toFixed(2).replace('.', ',');
          
          content += `${entry.journal};${entryNum};${moment(entry.date).format(formatConfig.dateFormat)};${entry.accountNumber};;;;;;${entry.label};${debit};${credit};;;;\n`;
        });
        
        // Écrire le fichier
        fs.writeFileSync(filePath, content, { encoding: formatConfig.encoding });
        
        resolve({ filePath });
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Exporte les données comptables au format EBP
   * @param {Object} accountingData - Données comptables
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} formatConfig - Configuration du format
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportToEBP(accountingData, filePath, formatConfig) {
    return new Promise((resolve, reject) => {
      try {
        // Créer l'en-tête du fichier
        let content = `Journal;Date;Compte;Libellé;Montant;Sens;Référence\n`;
        
        // Ajouter chaque écriture
        accountingData.entries.forEach(entry => {
          const date = moment(entry.date).format(formatConfig.dateFormat);
          let montant, sens;
          
          if (entry.debit > 0) {
            montant = entry.debit.toFixed(2).replace('.', ',');
            sens = 'D';
          } else {
            montant = entry.credit.toFixed(2).replace('.', ',');
            sens = 'C';
          }
          
          content += `${entry.journal};${date};${entry.accountNumber};${entry.label};${montant};${sens};${entry.reference}\n`;
        });
        
        // Écrire le fichier
        fs.writeFileSync(filePath, content, { encoding: formatConfig.encoding });
        
        resolve({ filePath });
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Exporte les données comptables au format QuickBooks
   * @param {Object} accountingData - Données comptables
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} formatConfig - Configuration du format
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportToQuickBooks(accountingData, filePath, formatConfig) {
    return new Promise((resolve, reject) => {
      try {
        // Créer l'en-tête du fichier (format IIF)
        let content = `!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\t\n`;
        content += `!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\t\n`;
        content += `!ENDTRNS\t\t\t\t\t\t\t\t\n`;
        
        // Grouper les écritures par référence
        const entriesByReference = accountingData.entries.reduce((acc, entry) => {
          if (!acc[entry.reference]) {
            acc[entry.reference] = [];
          }
          
          acc[entry.reference].push(entry);
          return acc;
        }, {});
        
        // Générer les transactions QuickBooks
        let trnsId = 1;
        let splId = 1;
        
        for (const [reference, entries] of Object.entries(entriesByReference)) {
          const date = moment(entries[0].date).format(formatConfig.dateFormat);
          const journalType = entries[0].journal;
          
          // Première ligne de la transaction
          content += `TRNS\t${trnsId}\tGENERAL JOURNAL\t${date}\t${entries[0].accountNumber}\t\t${entries[0].debit > 0 ? entries[0].debit.toFixed(2) : -entries[0].credit.toFixed(2)}\t${entries[0].label}\t\n`;
          
          // Lignes de ventilation
          for (let i = 1; i < entries.length; i++) {
            const entry = entries[i];
            content += `SPL\t${splId}\tGENERAL JOURNAL\t${date}\t${entry.accountNumber}\t\t${entry.debit > 0 ? entry.debit.toFixed(2) : -entry.credit.toFixed(2)}\t${entry.label}\t\n`;
            splId++;
          }
          
          // Fin de la transaction
          content += `ENDTRNS\t\t\t\t\t\t\t\t\n`;
          trnsId++;
        }
        
        // Écrire le fichier
        fs.writeFileSync(filePath, content, { encoding: formatConfig.encoding });
        
        resolve({ filePath });
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Exporte les données comptables au format Excel
   * @param {Object} accountingData - Données comptables
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} formatConfig - Configuration du format
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportToExcel(accountingData, filePath, formatConfig) {
    try {
      // Créer un nouveau classeur
      const workbook = XLSX.utils.book_new();
      
      // Créer la feuille principale des écritures
      const entriesData = [
        ['Date', 'Journal', 'Compte', 'Libellé', 'Débit', 'Crédit', 'Référence', 'Catégorie']
      ];
      
      // Ajouter chaque écriture
      accountingData.entries.forEach(entry => {
        entriesData.push([
          moment(entry.date).format(formatConfig.dateFormat),
          entry.journal,
          entry.accountNumber,
          entry.label,
          entry.debit > 0 ? entry.debit : '',
          entry.credit > 0 ? entry.credit : '',
          entry.reference,
          entry.category
        ]);
      });
      
      // Ajouter le total
      entriesData.push(['', '', '', 'TOTAL', accountingData.summary.debit, accountingData.summary.credit, '', '']);
      
      // Créer la feuille
      const entriesSheet = XLSX.utils.aoa_to_sheet(entriesData);
      
      // Ajouter la feuille au classeur
      XLSX.utils.book_append_sheet(workbook, entriesSheet, 'Écritures');
      
      // Créer une feuille de résumé
      const summaryData = [
        ['Résumé Comptable'],
        ['Période', `${moment(accountingData.period.start).format('DD/MM/YYYY')} au ${moment(accountingData.period.end).format('DD/MM/YYYY')}`],
        [''],
        ['Total Débit', accountingData.summary.debit],
        ['Total Crédit', accountingData.summary.credit],
        ['Balance', accountingData.summary.balance],
        ['Nombre d\'écritures', accountingData.entries.length]
      ];
      
      // Créer la feuille
      const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);
      
      // Ajouter la feuille au classeur
      XLSX.utils.book_append_sheet(workbook, summarySheet, 'Résumé');
      
      // Écrire le classeur dans un fichier
      XLSX.writeFile(workbook, filePath);
      
      return { filePath };
    } catch (error) {
      throw error;
    }
  }
  
  /**
   * Exporte les données comptables au format FEC (Fichier des Écritures Comptables)
   * @param {Object} accountingData - Données comptables
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} formatConfig - Configuration du format
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportToFEC(accountingData, filePath, formatConfig) {
    return new Promise((resolve, reject) => {
      try {
        // En-tête obligatoire pour le FEC
        const headers = [
          'JournalCode', 'JournalLib', 'EcritureNum', 'EcritureDate', 'CompteNum',
          'CompteLib', 'CompAuxNum', 'CompAuxLib', 'PieceRef', 'PieceDate',
          'EcritureLib', 'Debit', 'Credit', 'EcritureLet', 'DateLet',
          'ValidDate', 'Montantdevise', 'Idevise'
        ];
        
        // Définir les libellés des journaux
        const journalLibs = {
          'VTE': 'Journal des Ventes',
          'ACH': 'Journal des Achats',
          'BNQ': 'Journal de Banque',
          'OD': 'Journal des Opérations Diverses'
        };
        
        // Définir les libellés des comptes (simplifié pour l'exemple)
        const compteLibs = {
          '512000': 'Banque',
          '531000': 'Caisse',
          '607100': 'Achats de marchandises - Food',
          '607200': 'Achats de marchandises - Beverages',
          '613000': 'Loyers',
          '606000': 'Achats non stockés - Énergies',
          '641000': 'Rémunération du personnel',
          '645000': 'Charges de sécurité sociale',
          '707100': 'Ventes de produits - Food',
          '707200': 'Ventes de produits - Beverages',
          '707300': 'Ventes de produits - Alcool',
          '707400': 'Ventes de produits - Takeaway',
          '708000': 'Autres produits des activités annexes',
          '445710': 'TVA collectée',
          '445660': 'TVA déductible',
          '445510': 'TVA à payer'
        };
        
        // Créer le contenu du fichier
        let content = headers.join(formatConfig.delimiter) + '\n';
        
        // Ajouter chaque écriture
        accountingData.entries.forEach((entry, index) => {
          const entryNum = `${entry.journal}${String(index + 1).padStart(5, '0')}`;
          const journalLib = journalLibs[entry.journal] || entry.journal;
          const compteLib = compteLibs[entry.accountNumber] || `Compte ${entry.accountNumber}`;
          const ecritureDate = moment(entry.date).format(formatConfig.dateFormat);
          const pieceDate = ecritureDate;
          const debit = entry.debit.toFixed(2).replace('.', ',');
          const credit = entry.credit.toFixed(2).replace('.', ',');
          
          // Ligne d'écriture au format FEC
          const line = [
            entry.journal,
            journalLib,
            entryNum,
            ecritureDate,
            entry.accountNumber,
            compteLib,
            '', // CompAuxNum
            '', // CompAuxLib
            entry.reference,
            pieceDate,
            entry.label,
            debit,
            credit,
            '', // EcritureLet
            '', // DateLet
            ecritureDate, // ValidDate
            '', // Montantdevise
            '' // Idevise
          ];
          
          content += line.join(formatConfig.delimiter) + '\n';
        });
        
        // Écrire le fichier
        fs.writeFileSync(filePath, content, { encoding: formatConfig.encoding });
        
        resolve({ filePath });
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Génère un fichier de balance générale
   * @param {Object} options - Options de génération
   * @param {Date|string} options.startDate - Date de début de la période
   * @param {Date|string} options.endDate - Date de fin de la période
   * @param {string} options.format - Format de sortie (pdf, excel, csv)
   * @returns {Promise<Object>} - Informations sur le fichier généré
   */
  async generateBalanceSheet(options = {}) {
    const startDate = options.startDate ? moment(options.startDate) : moment().startOf('month');
    const endDate = options.endDate ? moment(options.endDate) : moment().endOf('month');
    const format = options.format || 'excel';
    
    try {
      // Récupérer les données consolidées pour la période
      const consolidatedData = await this.dataConsolidator.consolidateFinancialData({
        startDate: startDate.format('YYYY-MM-DD'),
        endDate: endDate.format('YYYY-MM-DD')
      });
      
      // Préparer les données comptables
      const accountingData = this._prepareAccountingData(consolidatedData);
      
      // Créer le sous-répertoire pour les balances
      const balanceDir = path.join(this.outputDir, 'balance');
      if (!fs.existsSync(balanceDir)) {
        fs.mkdirSync(balanceDir, { recursive: true });
      }
      
      // Générer la balance générale
      const balanceData = this._generateBalanceData(accountingData);
      
      // Définir le chemin du fichier de sortie
      const fileName = `balance_${startDate.format('YYYYMMDD')}_${endDate.format('YYYYMMDD')}.${format === 'excel' ? 'xlsx' : format}`;
      const filePath = path.join(balanceDir, fileName);
      
      // Exporter dans le format demandé
      let result;
      
      switch (format) {
        case 'excel':
          result = await this._exportBalanceToExcel(balanceData, filePath, {
            startDate,
            endDate
          });
          break;
        
        case 'csv':
          result = await this._exportBalanceToCSV(balanceData, filePath, {
            startDate,
            endDate
          });
          break;
        
        default:
          throw new Error(`Format non supporté pour la balance: ${format}`);
      }
      
      console.log(`Balance générale générée: ${filePath}`);
      
      return {
        status: 'success',
        filePath,
        fileSize: fs.statSync(filePath).size,
        format
      };
    } catch (error) {
      console.error('Erreur lors de la génération de la balance générale:', error);
      
      // Créer une alerte
      if (this.alertService) {
        this.alertService.danger('balance_generation_error',
          `Erreur lors de la génération de la balance générale: ${error.message}`,
          {
            period: {
              start: startDate.format('YYYY-MM-DD'),
              end: endDate.format('YYYY-MM-DD')
            },
            format,
            error: error.message
          }
        );
      }
      
      throw error;
    }
  }
  
  /**
   * Génère les données de la balance générale
   * @param {Object} accountingData - Données comptables
   * @returns {Object} - Données de la balance
   * @private
   */
  _generateBalanceData(accountingData) {
    // Initialiser les données de la balance
    const balanceData = {
      accounts: {},
      totals: {
        debitStart: 0,
        creditStart: 0,
        debitMovement: 0,
        creditMovement: 0,
        debitEnd: 0,
        creditEnd: 0
      }
    };
    
    // Traiter chaque écriture pour générer la balance
    accountingData.entries.forEach(entry => {
      // Créer ou récupérer le compte
      if (!balanceData.accounts[entry.accountNumber]) {
        balanceData.accounts[entry.accountNumber] = {
          number: entry.accountNumber,
          label: this._getAccountLabel(entry.accountNumber),
          debitStart: 0,
          creditStart: 0,
          debitMovement: 0,
          creditMovement: 0,
          debitEnd: 0,
          creditEnd: 0
        };
      }
      
      // Ajouter les mouvements
      if (entry.debit > 0) {
        balanceData.accounts[entry.accountNumber].debitMovement += entry.debit;
        balanceData.totals.debitMovement += entry.debit;
      } else if (entry.credit > 0) {
        balanceData.accounts[entry.accountNumber].creditMovement += entry.credit;
        balanceData.totals.creditMovement += entry.credit;
      }
    });
    
    // Calculer les soldes de fin de période
    for (const account of Object.values(balanceData.accounts)) {
      // Solde de fin = Solde de début + Mouvements
      account.debitEnd = account.debitStart + account.debitMovement;
      account.creditEnd = account.creditStart + account.creditMovement;
      
      // Ajuster les soldes si débit > crédit ou crédit > débit
      if (account.debitEnd > account.creditEnd) {
        account.debitEnd -= account.creditEnd;
        account.creditEnd = 0;
      } else if (account.creditEnd > account.debitEnd) {
        account.creditEnd -= account.debitEnd;
        account.debitEnd = 0;
      } else {
        account.debitEnd = 0;
        account.creditEnd = 0;
      }
      
      // Mettre à jour les totaux
      balanceData.totals.debitEnd += account.debitEnd;
      balanceData.totals.creditEnd += account.creditEnd;
    }
    
    return balanceData;
  }
  
  /**
   * Récupère le libellé d'un compte comptable
   * @param {string} accountNumber - Numéro de compte
   * @returns {string} - Libellé du compte
   * @private
   */
  _getAccountLabel(accountNumber) {
    // Définir les libellés des comptes (simplifié pour l'exemple)
    const compteLibs = {
      '512000': 'Banque',
      '531000': 'Caisse',
      '607100': 'Achats de marchandises - Food',
      '607200': 'Achats de marchandises - Beverages',
      '613000': 'Loyers',
      '606000': 'Achats non stockés - Énergies',
      '641000': 'Rémunération du personnel',
      '645000': 'Charges de sécurité sociale',
      '707100': 'Ventes de produits - Food',
      '707200': 'Ventes de produits - Beverages',
      '707300': 'Ventes de produits - Alcool',
      '707400': 'Ventes de produits - Takeaway',
      '708000': 'Autres produits des activités annexes',
      '445710': 'TVA collectée',
      '445660': 'TVA déductible',
      '445510': 'TVA à payer'
    };
    
    return compteLibs[accountNumber] || `Compte ${accountNumber}`;
  }
  
  /**
   * Exporte la balance générale au format Excel
   * @param {Object} balanceData - Données de la balance
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} options - Options d'export
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportBalanceToExcel(balanceData, filePath, options = {}) {
    try {
      const { startDate, endDate } = options;
      
      // Créer un nouveau classeur
      const workbook = XLSX.utils.book_new();
      
      // Créer la feuille de balance
      const balanceSheet = [
        [`Balance Générale du ${startDate.format('DD/MM/YYYY')} au ${endDate.format('DD/MM/YYYY')}`],
        [''],
        ['Compte', 'Libellé', 'Débit initial', 'Crédit initial', 'Mouvements débit', 'Mouvements crédit', 'Solde débit', 'Solde crédit']
      ];
      
      // Ajouter chaque compte
      for (const account of Object.values(balanceData.accounts)) {
        balanceSheet.push([
          account.number,
          account.label,
          account.debitStart,
          account.creditStart,
          account.debitMovement,
          account.creditMovement,
          account.debitEnd,
          account.creditEnd
        ]);
      }
      
      // Ajouter la ligne de total
      balanceSheet.push([
        'TOTAL',
        '',
        balanceData.totals.debitStart,
        balanceData.totals.creditStart,
        balanceData.totals.debitMovement,
        balanceData.totals.creditMovement,
        balanceData.totals.debitEnd,
        balanceData.totals.creditEnd
      ]);
      
      // Créer la feuille
      const sheet = XLSX.utils.aoa_to_sheet(balanceSheet);
      
      // Définir les styles pour le titre
      sheet['!merges'] = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: 7 } } // Fusionner les cellules pour le titre
      ];
      
      // Ajouter la feuille au classeur
      XLSX.utils.book_append_sheet(workbook, sheet, 'Balance');
      
      // Écrire le classeur dans un fichier
      XLSX.writeFile(workbook, filePath);
      
      return { filePath };
    } catch (error) {
      throw error;
    }
  }
  
  /**
   * Exporte la balance générale au format CSV
   * @param {Object} balanceData - Données de la balance
   * @param {string} filePath - Chemin du fichier de sortie
   * @param {Object} options - Options d'export
   * @returns {Promise<Object>} - Informations sur l'export réalisé
   * @private
   */
  async _exportBalanceToCSV(balanceData, filePath, options = {}) {
    return new Promise((resolve, reject) => {
      try {
        const { startDate, endDate } = options;
        
        // Créer l'en-tête du fichier
        let content = `"Balance Générale du ${startDate.format('DD/MM/YYYY')} au ${endDate.format('DD/MM/YYYY')}"\n\n`;
        content += `"Compte";"Libellé";"Débit initial";"Crédit initial";"Mouvements débit";"Mouvements crédit";"Solde débit";"Solde crédit"\n`;
        
        // Ajouter chaque compte
        for (const account of Object.values(balanceData.accounts)) {
          content += `"${account.number}";"${account.label}";"${account.debitStart}";"${account.creditStart}";"${account.debitMovement}";"${account.creditMovement}";"${account.debitEnd}";"${account.creditEnd}"\n`;
        }
        
        // Ajouter la ligne de total
        content += `"TOTAL";"";"${balanceData.totals.debitStart}";"${balanceData.totals.creditStart}";"${balanceData.totals.debitMovement}";"${balanceData.totals.creditMovement}";"${balanceData.totals.debitEnd}";"${balanceData.totals.creditEnd}"\n`;
        
        // Écrire le fichier
        fs.writeFileSync(filePath, content, { encoding: 'utf8' });
        
        resolve({ filePath });
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Récupère l'historique des exports
   * @param {Object} options - Options de filtrage
   * @param {number} options.limit - Nombre maximum de résultats
   * @param {string} options.format - Filtrer par format
   * @returns {Array<Object>} - Historique des exports
   */
  getExportHistory(options = {}) {
    const limit = options.limit || 100;
    const format = options.format;
    
    // Filtrer par format si spécifié
    let filteredHistory = this.exportHistory;
    
    if (format) {
      filteredHistory = filteredHistory.filter(export => export.format === format);
    }
    
    // Trier par date décroissante (plus récent en premier)
    filteredHistory.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Limiter le nombre de résultats
    return filteredHistory.slice(0, limit);
  }
}

module.exports = { AccountingExporter };
