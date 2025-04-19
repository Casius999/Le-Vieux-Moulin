/**
 * Module d'exportation des données comptables
 * Génère des exports de données comptables dans différents formats
 * compatibles avec les logiciels de comptabilité
 */

'use strict';

const fs = require('fs');
const path = require('path');
const moment = require('moment');
const ExcelJS = require('exceljs');
const csv = require('fast-csv');
const PDFDocument = require('pdfkit');

/**
 * Classe responsable de l'exportation des données comptables
 */
class AccountingExporter {
  /**
   * Crée une nouvelle instance de l'exportateur
   * @param {Object} options - Options de configuration
   * @param {Object} options.configManager - Instance du gestionnaire de configuration
   * @param {Object} options.logger - Instance du logger
   * @param {Object} options.dataConsolidator - Instance du consolidateur de données
   */
  constructor(options = {}) {
    this.configManager = options.configManager;
    this.logger = options.logger || console;
    this.dataConsolidator = options.dataConsolidator;
    
    // Récupérer la configuration d'export
    this.exportConfig = this.configManager?.getConfig('export') || {};
    
    // Répertoire pour enregistrer les exports
    this.outputDir = options.outputDir || path.join(process.cwd(), 'exports');
    
    // S'assurer que le répertoire existe
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
    
    // Chemins spécifiques pour chaque type d'export
    this.exportPaths = {
      pdf: path.join(this.outputDir, 'pdf'),
      excel: path.join(this.outputDir, 'excel'),
      csv: path.join(this.outputDir, 'csv'),
      sage: path.join(this.outputDir, 'sage'),
      fec: path.join(this.outputDir, 'fec')
    };
    
    // Créer les sous-répertoires
    for (const dir of Object.values(this.exportPaths)) {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    }
    
    this.logger.info('AccountingExporter initialisé');
  }
  
  /**
   * Génère un export comptable pour une période donnée
   * @param {Object} params - Paramètres d'export
   * @param {Date|string} params.startDate - Date de début
   * @param {Date|string} params.endDate - Date de fin
   * @param {string[]} params.formats - Formats à générer (pdf, excel, csv, sage, fec)
   * @param {string} params.type - Type de rapport (daily, monthly, quarterly, annual)
   * @param {Object} params.options - Options spécifiques au format
   * @returns {Promise<Object>} - Les chemins des fichiers générés
   */
  async generateAccountingExport(params = {}) {
    try {
      const { 
        startDate,
        endDate,
        formats = ['excel', 'pdf'],
        type = 'monthly',
        options = {}
      } = params;
      
      // Normaliser les dates
      const start = startDate instanceof Date ? startDate : new Date(startDate);
      const end = endDate instanceof Date ? endDate : new Date(endDate);
      
      // Vérifier la validité des dates
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        throw new Error('Dates invalides fournies pour l\'export comptable');
      }
      
      // Formater les dates pour les noms de fichiers
      const formattedStartDate = moment(start).format('YYYY-MM-DD');
      const formattedEndDate = moment(end).format('YYYY-MM-DD');
      
      // Récupérer les données comptables consolidées
      const accountingData = await this.dataConsolidator.getConsolidatedFinancialData({
        startDate: start,
        endDate: end,
        includeInventory: true,
        includeLaborCosts: true
      });
      
      // Résultat des exports
      const exportResults = {
        period: {
          startDate: formattedStartDate,
          endDate: formattedEndDate,
          type
        },
        files: {}
      };
      
      // Générer les exports dans chaque format demandé
      for (const format of formats) {
        let filePath;
        
        switch (format.toLowerCase()) {
          case 'pdf':
            filePath = await this._generatePdfExport(accountingData, type, options);
            exportResults.files.pdf = filePath;
            break;
            
          case 'excel':
            filePath = await this._generateExcelExport(accountingData, type, options);
            exportResults.files.excel = filePath;
            break;
            
          case 'csv':
            filePath = await this._generateCsvExport(accountingData, type, options);
            exportResults.files.csv = filePath;
            break;
            
          case 'sage':
            filePath = await this._generateSageExport(accountingData, type, options);
            exportResults.files.sage = filePath;
            break;
            
          case 'fec':
            filePath = await this._generateFecExport(accountingData, type, options);
            exportResults.files.fec = filePath;
            break;
            
          default:
            this.logger.warn(`Format d'export non pris en charge: ${format}`);
        }
      }
      
      this.logger.info(`Export comptable généré pour la période du ${formattedStartDate} au ${formattedEndDate}`);
      
      return exportResults;
    } catch (error) {
      this.logger.error('Erreur lors de la génération de l\'export comptable:', error);
      throw error;
    }
  }
  
  /**
   * Génère un export au format PDF
   * @param {Object} data - Données comptables
   * @param {string} type - Type de rapport
   * @param {Object} options - Options spécifiques
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generatePdfExport(data, type, options = {}) {
    return new Promise((resolve, reject) => {
      try {
        // Déterminer le nom du fichier
        const fileName = `comptabilite_${type}_${data.period.startDate}_${data.period.endDate}.pdf`;
        const filePath = path.join(this.exportPaths.pdf, fileName);
        
        // Créer le document PDF
        const doc = new PDFDocument({
          size: 'A4',
          margins: { top: 50, bottom: 50, left: 40, right: 40 },
          info: {
            Title: `Rapport Comptable - ${type}`,
            Author: 'Le Vieux Moulin - Module Comptabilité',
            Subject: 'Données comptables',
            Keywords: 'comptabilité, finance, restaurant',
            CreationDate: new Date()
          }
        });
        
        // Flux d'écriture
        const stream = fs.createWriteStream(filePath);
        doc.pipe(stream);
        
        // Titre et en-tête
        doc.fontSize(18).font('Helvetica-Bold').text('Le Vieux Moulin', { align: 'center' });
        doc.moveDown(0.5);
        
        doc.fontSize(14).font('Helvetica').text(`Rapport Comptable - ${this._formatReportType(type)}`, { align: 'center' });
        doc.moveDown(0.5);
        
        doc.fontSize(12).text(`Période : du ${this._formatDate(data.period.startDate)} au ${this._formatDate(data.period.endDate)}`, { align: 'center' });
        doc.moveDown(2);
        
        // Résumé financier
        doc.fontSize(14).font('Helvetica-Bold').text('Résumé Financier', { underline: true });
        doc.moveDown(1);
        
        const summary = data.summary;
        
        doc.fontSize(11).font('Helvetica');
        doc.text(`Chiffre d'affaires: ${this._formatCurrency(summary.totalSales)}`);
        doc.text(`Marge brute: ${this._formatCurrency(summary.grossProfit)} (${this._formatPercentage(summary.grossProfitMargin)})`);
        doc.text(`Résultat d'exploitation: ${this._formatCurrency(summary.operatingProfit)} (${this._formatPercentage(summary.operatingProfitMargin)})`);
        
        doc.moveDown(1);
        doc.text(`Coût des marchandises vendues: ${this._formatCurrency(summary.costOfGoodsSold)}`);
        doc.text(`Frais de personnel: ${this._formatCurrency(summary.laborCost)}`);
        doc.text(`Autres dépenses: ${this._formatCurrency(summary.totalExpenses)}`);
        
        doc.moveDown(2);
        
        // Indicateurs clés
        doc.fontSize(14).font('Helvetica-Bold').text('Indicateurs Clés', { underline: true });
        doc.moveDown(1);
        
        const kpis = data.kpis;
        
        doc.fontSize(11).font('Helvetica');
        doc.text(`Ratio Food Cost: ${this._formatPercentage(kpis.foodCostPercentage)}`);
        doc.text(`Ratio Coût Personnel: ${this._formatPercentage(kpis.laborCostPercentage)}`);
        doc.text(`Ratio Dépenses: ${this._formatPercentage(kpis.expensePercentage)}`);
        doc.text(`Taux de Profit: ${this._formatPercentage(kpis.profitPercentage)}`);
        
        doc.moveDown(2);
        
        // Répartition des revenus
        if (data.transactions && data.transactions.length > 0) {
          doc.fontSize(14).font('Helvetica-Bold').text('Répartition des Revenus', { underline: true });
          doc.moveDown(1);
          
          // Grouper les transactions par catégorie
          const salesByCategory = this._groupSalesByCategory(data.transactions);
          
          // Tableau de répartition
          const categoryTable = {
            headers: ['Catégorie', 'Montant', 'Pourcentage'],
            rows: []
          };
          
          for (const [category, amount] of Object.entries(salesByCategory)) {
            const percentage = (amount / summary.totalSales * 100).toFixed(2);
            categoryTable.rows.push([
              category,
              this._formatCurrency(amount),
              `${percentage}%`
            ]);
          }
          
          this._drawTable(doc, categoryTable, { x: 40, y: doc.y, width: 500 });
          
          doc.moveDown(2);
        }
        
        // Répartition des dépenses
        if (data.expenses && data.expenses.length > 0) {
          doc.fontSize(14).font('Helvetica-Bold').text('Répartition des Dépenses', { underline: true });
          doc.moveDown(1);
          
          // Grouper les dépenses par catégorie
          const expensesByCategory = this._groupExpensesByCategory(data.expenses);
          
          // Tableau de répartition
          const expenseTable = {
            headers: ['Catégorie', 'Montant', 'Pourcentage'],
            rows: []
          };
          
          for (const [category, amount] of Object.entries(expensesByCategory)) {
            const percentage = (amount / summary.totalExpenses * 100).toFixed(2);
            expenseTable.rows.push([
              this._formatExpenseCategory(category),
              this._formatCurrency(amount),
              `${percentage}%`
            ]);
          }
          
          this._drawTable(doc, expenseTable, { x: 40, y: doc.y, width: 500 });
          
          doc.moveDown(2);
        }
        
        // Informations sur l'inventaire
        if (data.inventory) {
          doc.fontSize(14).font('Helvetica-Bold').text('Valeur des Stocks', { underline: true });
          doc.moveDown(1);
          
          doc.fontSize(11).font('Helvetica');
          doc.text(`Valeur d'ouverture: ${this._formatCurrency(data.inventory.openingInventoryValue)}`);
          doc.text(`Valeur de clôture: ${this._formatCurrency(data.inventory.closingInventoryValue)}`);
          doc.text(`Achats de la période: ${this._formatCurrency(data.inventory.totalPurchases)}`);
          doc.text(`Consommation de la période: ${this._formatCurrency(data.inventory.totalConsumption)}`);
          
          doc.moveDown(2);
        }
        
        // Pied de page
        const pageCount = doc.bufferedPageRange().count;
        for (let i = 0; i < pageCount; i++) {
          doc.switchToPage(i);
          
          // Position en bas de page
          const bottom = doc.page.height - 50;
          
          doc.fontSize(8).font('Helvetica').text(
            `Le Vieux Moulin - Rapport généré le ${moment().format('DD/MM/YYYY HH:mm')} - Page ${i + 1} sur ${pageCount}`,
            50, bottom, { align: 'center', width: doc.page.width - 100 }
          );
        }
        
        // Finaliser le document
        doc.end();
        
        // Gestion des événements du flux
        stream.on('finish', () => resolve(filePath));
        stream.on('error', reject);
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Génère un export au format Excel
   * @param {Object} data - Données comptables
   * @param {string} type - Type de rapport
   * @param {Object} options - Options spécifiques
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generateExcelExport(data, type, options = {}) {
    try {
      // Déterminer le nom du fichier
      const fileName = `comptabilite_${type}_${data.period.startDate}_${data.period.endDate}.xlsx`;
      const filePath = path.join(this.exportPaths.excel, fileName);
      
      // Créer le workbook
      const workbook = new ExcelJS.Workbook();
      
      // Métadonnées
      workbook.creator = 'Le Vieux Moulin - Module Comptabilité';
      workbook.lastModifiedBy = 'Système Automatisé';
      workbook.created = new Date();
      workbook.modified = new Date();
      
      // Feuille de résumé
      const summarySheet = workbook.addWorksheet('Résumé Financier');
      
      // Mise en forme des colonnes
      summarySheet.columns = [
        { header: 'Indicateur', key: 'indicator', width: 30 },
        { header: 'Valeur', key: 'value', width: 15 },
        { header: 'Pourcentage', key: 'percentage', width: 15 }
      ];
      
      // Style des en-têtes
      summarySheet.getRow(1).font = { bold: true };
      summarySheet.getRow(1).alignment = { horizontal: 'center' };
      
      // Données de résumé
      const summary = data.summary;
      const rows = [
        { indicator: 'Chiffre d\'affaires', value: summary.totalSales },
        { indicator: 'Coût des marchandises vendues', value: summary.costOfGoodsSold, percentage: summary.costOfGoodsSold / summary.totalSales },
        { indicator: 'Marge brute', value: summary.grossProfit, percentage: summary.grossProfitMargin / 100 },
        { indicator: 'Frais de personnel', value: summary.laborCost, percentage: summary.laborCost / summary.totalSales },
        { indicator: 'Autres dépenses', value: summary.totalExpenses, percentage: summary.totalExpenses / summary.totalSales },
        { indicator: 'Résultat d\'exploitation', value: summary.operatingProfit, percentage: summary.operatingProfitMargin / 100 }
      ];
      
      // Ajouter les données
      summarySheet.addRows(rows);
      
      // Format monétaire
      summarySheet.getColumn('value').numFmt = '# ##0.00 €';
      summarySheet.getColumn('percentage').numFmt = '0.00%';
      
      // Feuille des ventes
      if (data.transactions && data.transactions.length > 0) {
        const salesSheet = workbook.addWorksheet('Ventes');
        
        // Colonnes des ventes
        salesSheet.columns = [
          { header: 'ID', key: 'id', width: 15 },
          { header: 'Date', key: 'date', width: 12 },
          { header: 'Total', key: 'total', width: 12 },
          { header: 'TVA', key: 'taxTotal', width: 12 },
          { header: 'Méthode de paiement', key: 'paymentMethod', width: 20 }
        ];
        
        // Style des en-têtes
        salesSheet.getRow(1).font = { bold: true };
        salesSheet.getRow(1).alignment = { horizontal: 'center' };
        
        // Ajouter les transactions
        salesSheet.addRows(data.transactions);
        
        // Format monétaire et date
        salesSheet.getColumn('total').numFmt = '# ##0.00 €';
        salesSheet.getColumn('taxTotal').numFmt = '# ##0.00 €';
        salesSheet.getColumn('date').numFmt = 'dd/mm/yyyy';
        
        // Ajouter les détails des ventes par catégorie
        const salesByCategory = this._groupSalesByCategory(data.transactions);
        
        // Insérer un espace
        salesSheet.addRow([]);
        salesSheet.addRow([]);
        
        // Ajouter un titre pour les ventes par catégorie
        const categoryTitleRow = salesSheet.addRow(['Répartition par catégorie']);
        categoryTitleRow.font = { bold: true, size: 12 };
        
        // En-têtes des catégories
        const categoryHeaderRow = salesSheet.addRow(['Catégorie', 'Montant', 'Pourcentage']);
        categoryHeaderRow.font = { bold: true };
        
        // Données des catégories
        for (const [category, amount] of Object.entries(salesByCategory)) {
          const percentage = amount / summary.totalSales;
          salesSheet.addRow([category, amount, percentage]);
        }
        
        // Format pour les nouvelles colonnes
        const categoryDataStartRow = salesSheet.rowCount - Object.keys(salesByCategory).length + 1;
        const categoryDataEndRow = salesSheet.rowCount;
        
        for (let i = categoryDataStartRow; i <= categoryDataEndRow; i++) {
          salesSheet.getCell(`B${i}`).numFmt = '# ##0.00 €';
          salesSheet.getCell(`C${i}`).numFmt = '0.00%';
        }
      }
      
      // Feuille des dépenses
      if (data.expenses && data.expenses.length > 0) {
        const expensesSheet = workbook.addWorksheet('Dépenses');
        
        // Colonnes des dépenses
        expensesSheet.columns = [
          { header: 'ID', key: 'id', width: 15 },
          { header: 'Date', key: 'date', width: 12 },
          { header: 'Montant', key: 'amount', width: 12 },
          { header: 'Catégorie', key: 'category', width: 20 },
          { header: 'Description', key: 'description', width: 30 },
          { header: 'Référence', key: 'referenceNumber', width: 15 }
        ];
        
        // Style des en-têtes
        expensesSheet.getRow(1).font = { bold: true };
        expensesSheet.getRow(1).alignment = { horizontal: 'center' };
        
        // Ajouter les dépenses
        expensesSheet.addRows(data.expenses);
        
        // Format monétaire et date
        expensesSheet.getColumn('amount').numFmt = '# ##0.00 €';
        expensesSheet.getColumn('date').numFmt = 'dd/mm/yyyy';
        
        // Ajouter les détails des dépenses par catégorie
        const expensesByCategory = this._groupExpensesByCategory(data.expenses);
        
        // Insérer un espace
        expensesSheet.addRow([]);
        expensesSheet.addRow([]);
        
        // Ajouter un titre pour les dépenses par catégorie
        const categoryTitleRow = expensesSheet.addRow(['Répartition par catégorie']);
        categoryTitleRow.font = { bold: true, size: 12 };
        
        // En-têtes des catégories
        const categoryHeaderRow = expensesSheet.addRow(['Catégorie', 'Montant', 'Pourcentage']);
        categoryHeaderRow.font = { bold: true };
        
        // Données des catégories
        for (const [category, amount] of Object.entries(expensesByCategory)) {
          const percentage = amount / summary.totalExpenses;
          expensesSheet.addRow([this._formatExpenseCategory(category), amount, percentage]);
        }
        
        // Format pour les nouvelles colonnes
        const categoryDataStartRow = expensesSheet.rowCount - Object.keys(expensesByCategory).length + 1;
        const categoryDataEndRow = expensesSheet.rowCount;
        
        for (let i = categoryDataStartRow; i <= categoryDataEndRow; i++) {
          expensesSheet.getCell(`B${i}`).numFmt = '# ##0.00 €';
          expensesSheet.getCell(`C${i}`).numFmt = '0.00%';
        }
      }
      
      // Sauvegarder le workbook
      await workbook.xlsx.writeFile(filePath);
      
      return filePath;
    } catch (error) {
      this.logger.error('Erreur lors de la génération de l\'export Excel:', error);
      throw error;
    }
  }
  
  /**
   * Génère un export au format CSV
   * @param {Object} data - Données comptables
   * @param {string} type - Type de rapport
   * @param {Object} options - Options spécifiques
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generateCsvExport(data, type, options = {}) {
    try {
      // Déterminer le dossier pour les fichiers CSV
      const csvDir = path.join(this.exportPaths.csv, `${type}_${data.period.startDate}_${data.period.endDate}`);
      
      // Créer le dossier s'il n'existe pas
      if (!fs.existsSync(csvDir)) {
        fs.mkdirSync(csvDir, { recursive: true });
      }
      
      // Fichiers à générer
      const filesPromises = [];
      
      // Générer le CSV des transactions
      if (data.transactions && data.transactions.length > 0) {
        const transactionsFile = path.join(csvDir, 'transactions.csv');
        
        const transactionsPromise = new Promise((resolve, reject) => {
          const stream = fs.createWriteStream(transactionsFile);
          
          // Transformer les données pour le CSV
          const csvTransactions = data.transactions.map(tx => ({
            ID: tx.id,
            Date: moment(tx.date).format('YYYY-MM-DD'),
            Total: tx.total.toFixed(2),
            TVA: tx.taxTotal.toFixed(2),
            'Mode de paiement': tx.paymentMethod || 'Non spécifié',
            Couverts: tx.covers || 0
          }));
          
          csv
            .write(csvTransactions, { headers: true })
            .pipe(stream)
            .on('finish', () => resolve(transactionsFile))
            .on('error', reject);
        });
        
        filesPromises.push(transactionsPromise);
      }
      
      // Générer le CSV des dépenses
      if (data.expenses && data.expenses.length > 0) {
        const expensesFile = path.join(csvDir, 'depenses.csv');
        
        const expensesPromise = new Promise((resolve, reject) => {
          const stream = fs.createWriteStream(expensesFile);
          
          // Transformer les données pour le CSV
          const csvExpenses = data.expenses.map(exp => ({
            ID: exp.id,
            Date: moment(exp.date).format('YYYY-MM-DD'),
            Montant: exp.amount.toFixed(2),
            Catégorie: exp.category || 'Non catégorisé',
            Description: exp.description || '',
            Référence: exp.referenceNumber || ''
          }));
          
          csv
            .write(csvExpenses, { headers: true })
            .pipe(stream)
            .on('finish', () => resolve(expensesFile))
            .on('error', reject);
        });
        
        filesPromises.push(expensesPromise);
      }
      
      // Générer le CSV de résumé
      const summaryFile = path.join(csvDir, 'resume.csv');
      
      const summaryPromise = new Promise((resolve, reject) => {
        const stream = fs.createWriteStream(summaryFile);
        
        // Données de résumé
        const summary = data.summary;
        const csvSummary = [
          { Indicateur: 'Chiffre d\'affaires', Valeur: summary.totalSales.toFixed(2), Pourcentage: '' },
          { Indicateur: 'Coût des marchandises vendues', Valeur: summary.costOfGoodsSold.toFixed(2), Pourcentage: (summary.costOfGoodsSold / summary.totalSales * 100).toFixed(2) + '%' },
          { Indicateur: 'Marge brute', Valeur: summary.grossProfit.toFixed(2), Pourcentage: summary.grossProfitMargin.toFixed(2) + '%' },
          { Indicateur: 'Frais de personnel', Valeur: summary.laborCost.toFixed(2), Pourcentage: (summary.laborCost / summary.totalSales * 100).toFixed(2) + '%' },
          { Indicateur: 'Autres dépenses', Valeur: summary.totalExpenses.toFixed(2), Pourcentage: (summary.totalExpenses / summary.totalSales * 100).toFixed(2) + '%' },
          { Indicateur: 'Résultat d\'exploitation', Valeur: summary.operatingProfit.toFixed(2), Pourcentage: summary.operatingProfitMargin.toFixed(2) + '%' }
        ];
        
        csv
          .write(csvSummary, { headers: true })
          .pipe(stream)
          .on('finish', () => resolve(summaryFile))
          .on('error', reject);
      });
      
      filesPromises.push(summaryPromise);
      
      // Attendre que tous les fichiers soient générés
      await Promise.all(filesPromises);
      
      // Retourner le chemin du dossier
      return csvDir;
    } catch (error) {
      this.logger.error('Erreur lors de la génération de l\'export CSV:', error);
      throw error;
    }
  }
  
  /**
   * Génère un export au format Sage
   * @param {Object} data - Données comptables
   * @param {string} type - Type de rapport
   * @param {Object} options - Options spécifiques
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generateSageExport(data, type, options = {}) {
    try {
      // Déterminer le nom du fichier
      const fileName = `sage_export_${type}_${data.period.startDate}_${data.period.endDate}.csv`;
      const filePath = path.join(this.exportPaths.sage, fileName);
      
      // Récupérer le mapping des comptes
      const accountMapping = this.exportConfig.sage?.accountMapping || this._getDefaultAccountMapping();
      
      // Créer les données pour l'export Sage
      const sageEntries = [];
      
      // Ajouter les transactions de vente
      if (data.transactions && data.transactions.length > 0) {
        for (const transaction of data.transactions) {
          const date = moment(transaction.date).format('DD/MM/YYYY');
          const journal = 'VEN'; // Journal des ventes
          const accountNumber = accountMapping.sales_account || '707000'; // Compte de vente
          const reference = transaction.id;
          const label = `Vente du ${date}`;
          const amount = transaction.total.toFixed(2);
          
          // Écriture comptable pour la vente
          sageEntries.push({
            JournalCode: journal,
            Date: date,
            NumPiece: reference,
            CompteGénéral: accountNumber,
            CompteAuxiliaire: '',
            Libellé: label,
            Débit: '',
            Crédit: amount,
            CodeTaxe: 'C10', // TVA collectée 10%
            Devise: 'EUR'
          });
          
          // Écriture pour la TVA
          if (transaction.taxTotal) {
            const vatAccountNumber = accountMapping.vat_collected || '445710'; // TVA collectée
            
            sageEntries.push({
              JournalCode: journal,
              Date: date,
              NumPiece: reference,
              CompteGénéral: vatAccountNumber,
              CompteAuxiliaire: '',
              Libellé: `TVA sur ${label}`,
              Débit: '',
              Crédit: transaction.taxTotal.toFixed(2),
              CodeTaxe: '',
              Devise: 'EUR'
            });
          }
          
          // Écriture pour la contrepartie (caisse ou banque)
          const paymentMethod = transaction.paymentMethod || 'CARD';
          const contrepartieAccount = paymentMethod === 'CASH' ? 
            accountMapping.cash_account || '531000' : // Caisse
            accountMapping.bank_account || '512000';  // Banque
          
          sageEntries.push({
            JournalCode: journal,
            Date: date,
            NumPiece: reference,
            CompteGénéral: contrepartieAccount,
            CompteAuxiliaire: '',
            Libellé: `Règlement ${label}`,
            Débit: (parseFloat(amount) + (transaction.taxTotal || 0)).toFixed(2),
            Crédit: '',
            CodeTaxe: '',
            Devise: 'EUR'
          });
        }
      }
      
      // Ajouter les dépenses
      if (data.expenses && data.expenses.length > 0) {
        for (const expense of data.expenses) {
          const date = moment(expense.date).format('DD/MM/YYYY');
          const journal = 'ACH'; // Journal des achats
          const category = expense.category || 'other';
          const accountNumber = accountMapping[`expense_${category.toLowerCase()}`] || accountMapping.expense_other || '606000'; // Compte de charge
          const reference = expense.referenceNumber || expense.id;
          const label = expense.description || `Dépense ${category}`;
          const amount = expense.amount.toFixed(2);
          
          // Écriture comptable pour la dépense
          sageEntries.push({
            JournalCode: journal,
            Date: date,
            NumPiece: reference,
            CompteGénéral: accountNumber,
            CompteAuxiliaire: '',
            Libellé: label,
            Débit: amount,
            Crédit: '',
            CodeTaxe: 'D10', // TVA déductible 10%
            Devise: 'EUR'
          });
          
          // Écriture pour la contrepartie (banque généralement)
          const paymentMethod = expense.paymentMethod || 'BANK';
          const contrepartieAccount = paymentMethod === 'CASH' ? 
            accountMapping.cash_account || '531000' : // Caisse
            accountMapping.bank_account || '512000';  // Banque
          
          sageEntries.push({
            JournalCode: journal,
            Date: date,
            NumPiece: reference,
            CompteGénéral: contrepartieAccount,
            CompteAuxiliaire: '',
            Libellé: `Règlement ${label}`,
            Débit: '',
            Crédit: amount,
            CodeTaxe: '',
            Devise: 'EUR'
          });
        }
      }
      
      // Écrire le fichier CSV
      return new Promise((resolve, reject) => {
        const stream = fs.createWriteStream(filePath);
        
        csv
          .write(sageEntries, { headers: true })
          .pipe(stream)
          .on('finish', () => resolve(filePath))
          .on('error', reject);
      });
    } catch (error) {
      this.logger.error('Erreur lors de la génération de l\'export Sage:', error);
      throw error;
    }
  }
  
  /**
   * Génère un export au format FEC (Fichier des Écritures Comptables)
   * @param {Object} data - Données comptables
   * @param {string} type - Type de rapport
   * @param {Object} options - Options spécifiques
   * @returns {Promise<string>} - Chemin du fichier généré
   * @private
   */
  async _generateFecExport(data, type, options = {}) {
    try {
      // Récupérer l'année fiscale
      const year = moment(data.period.startDate).year();
      
      // Déterminer le nom du fichier
      const fileName = `FEC${year}_${type}_${data.period.startDate}_${data.period.endDate}.txt`;
      const filePath = path.join(this.exportPaths.fec, fileName);
      
      // Récupérer le mapping des comptes
      const accountMapping = this.exportConfig.sage?.accountMapping || this._getDefaultAccountMapping();
      
      // Récupérer les informations de l'entreprise
      const companyInfo = this.exportConfig.companyInfo || {
        siret: '12345678901234',
        siren: '123456789',
        name: 'LE VIEUX MOULIN'
      };
      
      // Créer les données pour l'export FEC
      const fecEntries = [];
      
      // Numéro d'écriture (Journal + numéro séquentiel pour chaque écriture)
      let ecritureNum = 0;
      
      // Ajouter les transactions de vente
      if (data.transactions && data.transactions.length > 0) {
        for (const transaction of data.transactions) {
          ecritureNum++;
          
          const dateEcr = moment(transaction.date).format('YYYYMMDD');
          const journal = 'VEN'; // Journal des ventes
          const ecritureLib = `Vente du ${moment(transaction.date).format('DD/MM/YYYY')}`;
          const pieceRef = transaction.id;
          
          // Écriture comptable pour la vente (crédit)
          const compteNum = accountMapping.sales_account || '707000'; // Compte de vente
          const debit = 0;
          const credit = transaction.total;
          
          fecEntries.push([
            `JournalCode=${journal}`,
            `JournalLib=Journal des ventes`,
            `EcritureNum=${ecritureNum}`,
            `EcritureDate=${dateEcr}`,
            `CompteNum=${compteNum}`,
            `CompteLib=Ventes`,
            `PieceRef=${pieceRef}`,
            `PieceDate=${dateEcr}`,
            `EcritureLib=${ecritureLib}`,
            `Debit=${debit.toFixed(2)}`,
            `Credit=${credit.toFixed(2)}`,
            `EcritureLet=`,
            `DateLet=`,
            `ValidDate=${dateEcr}`,
            `Montantdevise=${credit.toFixed(2)}`,
            `Idevise=EUR`
          ].join('\t'));
          
          // Écriture pour la contrepartie (débit)
          const paymentMethod = transaction.paymentMethod || 'CARD';
          const contrepartieAccount = paymentMethod === 'CASH' ? 
            accountMapping.cash_account || '531000' : // Caisse
            accountMapping.bank_account || '512000';  // Banque
          
          const contrepartieLib = paymentMethod === 'CASH' ? 'Caisse' : 'Banque';
          
          fecEntries.push([
            `JournalCode=${journal}`,
            `JournalLib=Journal des ventes`,
            `EcritureNum=${ecritureNum}`,
            `EcritureDate=${dateEcr}`,
            `CompteNum=${contrepartieAccount}`,
            `CompteLib=${contrepartieLib}`,
            `PieceRef=${pieceRef}`,
            `PieceDate=${dateEcr}`,
            `EcritureLib=${ecritureLib}`,
            `Debit=${credit.toFixed(2)}`,
            `Credit=${debit.toFixed(2)}`,
            `EcritureLet=`,
            `DateLet=`,
            `ValidDate=${dateEcr}`,
            `Montantdevise=${credit.toFixed(2)}`,
            `Idevise=EUR`
          ].join('\t'));
        }
      }
      
      // Ajouter les dépenses
      if (data.expenses && data.expenses.length > 0) {
        for (const expense of data.expenses) {
          ecritureNum++;
          
          const dateEcr = moment(expense.date).format('YYYYMMDD');
          const journal = 'ACH'; // Journal des achats
          const ecritureLib = expense.description || `Dépense ${expense.category || 'diverse'}`;
          const pieceRef = expense.referenceNumber || expense.id;
          
          // Écriture comptable pour la dépense (débit)
          const category = expense.category || 'other';
          const compteNum = accountMapping[`expense_${category.toLowerCase()}`] || accountMapping.expense_other || '606000';
          const debit = expense.amount;
          const credit = 0;
          
          fecEntries.push([
            `JournalCode=${journal}`,
            `JournalLib=Journal des achats`,
            `EcritureNum=${ecritureNum}`,
            `EcritureDate=${dateEcr}`,
            `CompteNum=${compteNum}`,
            `CompteLib=Charges ${category}`,
            `PieceRef=${pieceRef}`,
            `PieceDate=${dateEcr}`,
            `EcritureLib=${ecritureLib}`,
            `Debit=${debit.toFixed(2)}`,
            `Credit=${credit.toFixed(2)}`,
            `EcritureLet=`,
            `DateLet=`,
            `ValidDate=${dateEcr}`,
            `Montantdevise=${debit.toFixed(2)}`,
            `Idevise=EUR`
          ].join('\t'));
          
          // Écriture pour la contrepartie (crédit)
          const paymentMethod = expense.paymentMethod || 'BANK';
          const contrepartieAccount = paymentMethod === 'CASH' ? 
            accountMapping.cash_account || '531000' : // Caisse
            accountMapping.bank_account || '512000';  // Banque
          
          const contrepartieLib = paymentMethod === 'CASH' ? 'Caisse' : 'Banque';
          
          fecEntries.push([
            `JournalCode=${journal}`,
            `JournalLib=Journal des achats`,
            `EcritureNum=${ecritureNum}`,
            `EcritureDate=${dateEcr}`,
            `CompteNum=${contrepartieAccount}`,
            `CompteLib=${contrepartieLib}`,
            `PieceRef=${pieceRef}`,
            `PieceDate=${dateEcr}`,
            `EcritureLib=${ecritureLib}`,
            `Debit=${credit.toFixed(2)}`,
            `Credit=${debit.toFixed(2)}`,
            `EcritureLet=`,
            `DateLet=`,
            `ValidDate=${dateEcr}`,
            `Montantdevise=${debit.toFixed(2)}`,
            `Idevise=EUR`
          ].join('\t'));
        }
      }
      
      // Créer l'en-tête FEC
      const header = [
        'JournalCode',
        'JournalLib',
        'EcritureNum',
        'EcritureDate',
        'CompteNum',
        'CompteLib',
        'PieceRef',
        'PieceDate',
        'EcritureLib',
        'Debit',
        'Credit',
        'EcritureLet',
        'DateLet',
        'ValidDate',
        'Montantdevise',
        'Idevise'
      ].join('\t');
      
      // Écrire le fichier
      const content = [header].concat(fecEntries).join('\n');
      fs.writeFileSync(filePath, content);
      
      return filePath;
    } catch (error) {
      this.logger.error('Erreur lors de la génération de l\'export FEC:', error);
      throw error;
    }
  }
  
  /**
   * Groupe les ventes par catégorie
   * @param {Array} transactions - Transactions
   * @returns {Object} - Montant par catégorie
   * @private
   */
  _groupSalesByCategory(transactions) {
    const categories = {};
    
    for (const transaction of transactions) {
      for (const item of transaction.items || []) {
        const category = item.category || 'Non catégorisé';
        
        if (!categories[category]) {
          categories[category] = 0;
        }
        
        categories[category] += item.total || 0;
      }
    }
    
    // Si aucun détail d'item n'est disponible, catégoriser par transaction complète
    if (Object.keys(categories).length === 0) {
      for (const transaction of transactions) {
        const category = 'Ventes générales';
        
        if (!categories[category]) {
          categories[category] = 0;
        }
        
        categories[category] += transaction.total || 0;
      }
    }
    
    return categories;
  }
  
  /**
   * Groupe les dépenses par catégorie
   * @param {Array} expenses - Dépenses
   * @returns {Object} - Montant par catégorie
   * @private
   */
  _groupExpensesByCategory(expenses) {
    const categories = {};
    
    for (const expense of expenses) {
      const category = expense.category || 'other';
      
      if (!categories[category]) {
        categories[category] = 0;
      }
      
      categories[category] += expense.amount || 0;
    }
    
    return categories;
  }
  
  /**
   * Dessine un tableau dans un document PDF
   * @param {PDFDocument} doc - Document PDF
   * @param {Object} table - Configuration du tableau (headers, rows)
   * @param {Object} options - Options de dessin (x, y, width)
   * @private
   */
  _drawTable(doc, table, options = {}) {
    const { x = 50, y = doc.y, width = 500 } = options;
    
    const { headers, rows } = table;
    const columnCount = headers.length;
    const columnWidth = width / columnCount;
    
    let currentY = y;
    
    // En-têtes
    doc.font('Helvetica-Bold');
    for (let i = 0; i < headers.length; i++) {
      doc.text(headers[i], x + (i * columnWidth), currentY, {
        width: columnWidth,
        align: 'left'
      });
    }
    
    currentY += 20;
    
    // Ligne de séparation
    doc.moveTo(x, currentY - 10)
       .lineTo(x + width, currentY - 10)
       .stroke();
    
    // Lignes de données
    doc.font('Helvetica');
    for (const row of rows) {
      for (let i = 0; i < row.length; i++) {
        doc.text(row[i], x + (i * columnWidth), currentY, {
          width: columnWidth,
          align: i === 0 ? 'left' : 'right'
        });
      }
      
      currentY += 20;
    }
    
    // Mettre à jour la position du curseur
    doc.y = currentY + 10;
  }
  
  /**
   * Formate un montant en devise
   * @param {number} amount - Montant à formater
   * @returns {string} - Montant formaté
   * @private
   */
  _formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
  }
  
  /**
   * Formate un pourcentage
   * @param {number} value - Valeur à formater
   * @returns {string} - Pourcentage formaté
   * @private
   */
  _formatPercentage(value) {
    return `${value.toFixed(2)}%`;
  }
  
  /**
   * Formate une date
   * @param {string|Date} date - Date à formater
   * @returns {string} - Date formatée
   * @private
   */
  _formatDate(date) {
    return moment(date).format('DD/MM/YYYY');
  }
  
  /**
   * Formate le type de rapport
   * @param {string} type - Type de rapport
   * @returns {string} - Type formaté
   * @private
   */
  _formatReportType(type) {
    switch (type) {
      case 'daily':
        return 'Journalier';
      case 'weekly':
        return 'Hebdomadaire';
      case 'monthly':
        return 'Mensuel';
      case 'quarterly':
        return 'Trimestriel';
      case 'annual':
        return 'Annuel';
      default:
        return type;
    }
  }
  
  /**
   * Formate une catégorie de dépense
   * @param {string} category - Catégorie
   * @returns {string} - Catégorie formatée
   * @private
   */
  _formatExpenseCategory(category) {
    const categoryMap = {
      supplies: 'Fournitures',
      utilities: 'Charges (eau, électricité, etc.)',
      rent: 'Loyer',
      marketing: 'Marketing',
      maintenance: 'Maintenance',
      operating: 'Frais d\'exploitation',
      other: 'Autres dépenses'
    };
    
    return categoryMap[category] || category;
  }
  
  /**
   * Retourne le mapping des comptes par défaut
   * @returns {Object} - Mapping des comptes
   * @private
   */
  _getDefaultAccountMapping() {
    return {
      // Comptes de produits
      sales_account: '707000', // Ventes de marchandises
      sales_food: '707100',    // Ventes de nourriture
      sales_beverage: '707200', // Ventes de boissons
      
      // Comptes de charges
      expense_supplies: '607000',  // Achats de marchandises
      expense_utilities: '606100', // Eau, électricité, etc.
      expense_rent: '613000',      // Loyers
      expense_marketing: '623000', // Publicité
      expense_maintenance: '615000', // Entretien et réparations
      expense_operating: '628000',   // Charges diverses de gestion courante
      expense_other: '628100',       // Autres charges
      
      // Comptes de trésorerie
      bank_account: '512000',  // Banque
      cash_account: '531000',  // Caisse
      
      // Comptes de TVA
      vat_collected: '445710', // TVA collectée
      vat_deductible: '445660' // TVA déductible
    };
  }
}

module.exports = { AccountingExporter };
