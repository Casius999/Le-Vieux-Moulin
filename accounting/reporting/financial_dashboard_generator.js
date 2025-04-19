/**
 * Module de génération de tableaux de bord financiers
 * Génère des tableaux de bord financiers en temps réel et des visualisations
 * pour le management et le comptable
 */

'use strict';

const fs = require('fs');
const path = require('path');
const moment = require('moment');
const { createCanvas, loadImage, registerFont } = require('canvas');
const PDFDocument = require('pdfkit');
const ExcelJS = require('exceljs');
const ChartJS = require('chart.js');

class FinancialDashboardGenerator {
  /**
   * Crée une nouvelle instance du générateur de tableaux de bord
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataCollector - Instance du collecteur de données
   * @param {Object} options.configManager - Instance du gestionnaire de configuration
   * @param {Object} options.logger - Instance du logger
   */
  constructor(options = {}) {
    this.dataCollector = options.dataCollector;
    this.configManager = options.configManager;
    this.logger = options.logger || console;
    
    // Récupérer la configuration des tableaux de bord
    this.dashboardConfig = this.configManager?.getConfig('dashboards') || {};
    
    // Répertoire pour enregistrer les tableaux de bord
    this.outputDir = options.outputDir || path.join(process.cwd(), 'generated', 'dashboards');
    
    // S'assurer que le répertoire existe
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
    
    // Enregistrer les polices personnalisées si nécessaire
    this._registerFonts();
  }
  
  /**
   * Enregistre les polices personnalisées pour les graphiques et PDF
   * @private
   */
  _registerFonts() {
    try {
      const fontsDir = path.join(process.cwd(), 'assets', 'fonts');
      
      if (fs.existsSync(fontsDir)) {
        // Enregistrer les polices disponibles
        const fontFiles = fs.readdirSync(fontsDir).filter(f => f.endsWith('.ttf') || f.endsWith('.otf'));
        
        for (const fontFile of fontFiles) {
          const fontPath = path.join(fontsDir, fontFile);
          const fontName = path.basename(fontFile, path.extname(fontFile));
          
          registerFont(fontPath, { family: fontName });
          this.logger.debug(`Police enregistrée: ${fontName}`);
        }
      }
    } catch (error) {
      this.logger.warn('Erreur lors de l\'enregistrement des polices:', error);
    }
  }
  
  /**
   * Génère un tableau de bord financier quotidien
   * @param {Object} options - Options de génération
   * @param {Date} options.date - Date pour laquelle générer le tableau de bord
   * @param {string[]} options.formats - Formats à générer (pdf, excel, json)
   * @param {string} options.templateId - ID du template à utiliser
   * @returns {Promise<Object>} - Les chemins des fichiers générés
   */
  async generateDailyDashboard(options = {}) {
    try {
      const { date = new Date(), formats = ['pdf', 'excel'], templateId = 'default_daily' } = options;
      
      // Récupérer le template
      const template = this.dashboardConfig.templates?.[templateId] || this._getDefaultDailyTemplate();
      
      // Formater la date
      const formattedDate = moment(date).format('YYYY-MM-DD');
      const displayDate = moment(date).format('DD/MM/YYYY');
      
      // Définir la période
      const period = {
        startDate: moment(date).startOf('day').toDate(),
        endDate: moment(date).endOf('day').toDate()
      };
      
      // Collecter les données nécessaires
      const sales = await this.dataCollector.getTransactions(period);
      const expenses = await this.dataCollector.getExpenses(period);
      const inventoryMovements = await this.dataCollector.getInventoryMovements(period);
      const staffSchedule = await this.dataCollector.getStaffSchedule(period);
      
      // Préparer les données pour le tableau de bord
      const dashboardData = this._prepareDailyDashboardData(sales, expenses, inventoryMovements, staffSchedule, date);
      
      // Chemins des fichiers à générer
      const fileBasename = `dashboard_daily_${formattedDate}`;
      const generatedFiles = {};
      
      // Générer les différents formats
      for (const format of formats) {
        let filePath;
        
        switch (format.toLowerCase()) {
          case 'pdf':
            filePath = path.join(this.outputDir, `${fileBasename}.pdf`);
            await this._generatePDFDashboard(filePath, dashboardData, template, displayDate);
            generatedFiles.pdf = filePath;
            break;
            
          case 'excel':
            filePath = path.join(this.outputDir, `${fileBasename}.xlsx`);
            await this._generateExcelDashboard(filePath, dashboardData, template, displayDate);
            generatedFiles.excel = filePath;
            break;
            
          case 'json':
            filePath = path.join(this.outputDir, `${fileBasename}.json`);
            fs.writeFileSync(filePath, JSON.stringify(dashboardData, null, 2));
            generatedFiles.json = filePath;
            break;
            
          default:
            this.logger.warn(`Format non pris en charge: ${format}`);
        }
      }
      
      return {
        date: formattedDate,
        files: generatedFiles,
        data: dashboardData,
        template: templateId
      };
    } catch (error) {
      this.logger.error('Erreur lors de la génération du tableau de bord quotidien:', error);
      throw new Error(`Erreur de génération du tableau de bord: ${error.message}`);
    }
  }
  
  /**
   * Génère un tableau de bord financier mensuel
   * @param {Object} options - Options de génération
   * @param {Date} options.date - Mois pour lequel générer le tableau de bord
   * @param {string[]} options.formats - Formats à générer (pdf, excel, json)
   * @param {string} options.templateId - ID du template à utiliser
   * @returns {Promise<Object>} - Les chemins des fichiers générés
   */
  async generateMonthlyDashboard(options = {}) {
    try {
      const { date = new Date(), formats = ['pdf', 'excel'], templateId = 'default_monthly' } = options;
      
      // Récupérer le template
      const template = this.dashboardConfig.templates?.[templateId] || this._getDefaultMonthlyTemplate();
      
      // Formater le mois
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const formattedMonth = `${year}-${month.toString().padStart(2, '0')}`;
      const displayMonth = moment(date).format('MMMM YYYY');
      
      // Définir la période
      const period = {
        startDate: moment(date).startOf('month').toDate(),
        endDate: moment(date).endOf('month').toDate()
      };
      
      // Collecter les données nécessaires
      const sales = await this.dataCollector.getTransactions(period);
      const expenses = await this.dataCollector.getExpenses(period);
      const inventorySummary = await this.dataCollector.getInventorySummary(period);
      const laborCosts = await this.dataCollector.getLaborCosts(period);
      
      // Préparer les données pour le tableau de bord
      const dashboardData = this._prepareMonthlyDashboardData(sales, expenses, inventorySummary, laborCosts, period);
      
      // Chemins des fichiers à générer
      const fileBasename = `dashboard_monthly_${formattedMonth}`;
      const generatedFiles = {};
      
      // Générer les différents formats
      for (const format of formats) {
        let filePath;
        
        switch (format.toLowerCase()) {
          case 'pdf':
            filePath = path.join(this.outputDir, `${fileBasename}.pdf`);
            await this._generatePDFDashboard(filePath, dashboardData, template, displayMonth);
            generatedFiles.pdf = filePath;
            break;
            
          case 'excel':
            filePath = path.join(this.outputDir, `${fileBasename}.xlsx`);
            await this._generateExcelDashboard(filePath, dashboardData, template, displayMonth);
            generatedFiles.excel = filePath;
            break;
            
          case 'json':
            filePath = path.join(this.outputDir, `${fileBasename}.json`);
            fs.writeFileSync(filePath, JSON.stringify(dashboardData, null, 2));
            generatedFiles.json = filePath;
            break;
            
          default:
            this.logger.warn(`Format non pris en charge: ${format}`);
        }
      }
      
      return {
        period: formattedMonth,
        files: generatedFiles,
        data: dashboardData,
        template: templateId
      };
    } catch (error) {
      this.logger.error('Erreur lors de la génération du tableau de bord mensuel:', error);
      throw new Error(`Erreur de génération du tableau de bord: ${error.message}`);
    }
  }
  
  /**
   * Prépare les données pour un tableau de bord quotidien
   * @param {Array} sales - Transactions de vente
   * @param {Array} expenses - Dépenses
   * @param {Array} inventoryMovements - Mouvements de stock
   * @param {Array} staffSchedule - Planning du personnel
   * @param {Date} date - Date du tableau de bord
   * @returns {Object} Données structurées pour le tableau de bord
   * @private
   */
  _prepareDailyDashboardData(sales, expenses, inventoryMovements, staffSchedule, date) {
    // Calculer les totaux de vente
    const totalSales = sales.reduce((sum, tx) => sum + tx.total, 0);
    const ticketCount = sales.length;
    const averageTicket = ticketCount > 0 ? totalSales / ticketCount : 0;
    
    // Calcul du nombre de couverts (si disponible dans les données)
    const totalCovers = sales.reduce((sum, tx) => sum + (tx.covers || 1), 0);
    
    // Répartition par catégories
    const salesByCategory = this._groupSalesByCategory(sales);
    
    // Répartition par service (déjeuner/dîner)
    const salesByService = this._groupSalesByService(sales);
    
    // Répartition par mode de paiement
    const salesByPaymentMethod = this._groupSalesByPaymentMethod(sales);
    
    // Calcul des dépenses du jour
    const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);
    const expensesByCategory = this._groupExpensesByCategory(expenses);
    
    // Calcul du coût des marchandises vendues
    const costOfGoodsSold = this._calculateCostOfGoodsSold(inventoryMovements);
    
    // Calcul des coûts de personnel
    const laborCosts = this._calculateLaborCosts(staffSchedule);
    
    // Calcul des indicateurs financiers
    const grossProfit = totalSales - costOfGoodsSold;
    const grossProfitMargin = totalSales > 0 ? (grossProfit / totalSales) * 100 : 0;
    
    const operatingProfit = grossProfit - laborCosts - expensesByCategory.operating;
    const operatingProfitMargin = totalSales > 0 ? (operatingProfit / totalSales) * 100 : 0;
    
    // Récupérer les données historiques pour comparaison
    const yesterday = new Date(date);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const lastWeek = new Date(date);
    lastWeek.setDate(lastWeek.getDate() - 7);
    
    // TODO: Implémenter la récupération de données historiques pour comparaison
    
    return {
      date: moment(date).format('YYYY-MM-DD'),
      summary: {
        totalSales,
        ticketCount,
        averageTicket,
        totalCovers,
        totalExpenses,
        grossProfit,
        grossProfitMargin,
        operatingProfit,
        operatingProfitMargin,
        costOfGoodsSold,
        laborCosts
      },
      details: {
        salesByCategory,
        salesByService,
        salesByPaymentMethod,
        expensesByCategory
      },
      kpis: {
        foodCostPercentage: totalSales > 0 ? (costOfGoodsSold / totalSales) * 100 : 0,
        laborCostPercentage: totalSales > 0 ? (laborCosts / totalSales) * 100 : 0,
        salesPerCover: totalCovers > 0 ? totalSales / totalCovers : 0
      },
      comparison: {
        // Données à remplir avec les comparaisons historiques
        yesterdayChange: 0,
        lastWeekChange: 0
      }
    };
  }
  
  /**
   * Prépare les données pour un tableau de bord mensuel
   * @param {Array} sales - Transactions de vente
   * @param {Array} expenses - Dépenses
   * @param {Object} inventorySummary - Résumé des mouvements de stock
   * @param {Object} laborCosts - Coûts de main d'œuvre
   * @param {Object} period - Période du tableau de bord
   * @returns {Object} Données structurées pour le tableau de bord
   * @private
   */
  _prepareMonthlyDashboardData(sales, expenses, inventorySummary, laborCosts, period) {
    // Calculer les totaux de vente
    const totalSales = sales.reduce((sum, tx) => sum + tx.total, 0);
    const ticketCount = sales.length;
    const averageTicket = ticketCount > 0 ? totalSales / ticketCount : 0;
    
    // Calcul des dépenses totales
    const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);
    
    // Répartition par catégories
    const salesByCategory = this._groupSalesByCategory(sales);
    
    // Répartition des dépenses par catégorie
    const expensesByCategory = this._groupExpensesByCategory(expenses);
    
    // Coût des marchandises vendues
    const costOfGoodsSold = inventorySummary.totalConsumption || 0;
    
    // Total des coûts de personnel
    const totalLaborCosts = laborCosts.totalCost || 0;
    
    // Calcul des indicateurs financiers mensuels
    const grossProfit = totalSales - costOfGoodsSold;
    const grossProfitMargin = totalSales > 0 ? (grossProfit / totalSales) * 100 : 0;
    
    const operatingExpenses = expensesByCategory.operating || 0;
    const operatingProfit = grossProfit - totalLaborCosts - operatingExpenses;
    const operatingProfitMargin = totalSales > 0 ? (operatingProfit / totalSales) * 100 : 0;
    
    // Évolution des ventes par jour du mois
    const salesByDay = this._groupSalesByDay(sales, period);
    
    // Répartition des coûts
    const costBreakdown = {
      costOfGoodsSold,
      laborCosts: totalLaborCosts,
      rent: expensesByCategory.rent || 0,
      utilities: expensesByCategory.utilities || 0,
      marketing: expensesByCategory.marketing || 0,
      other: expensesByCategory.other || 0
    };
    
    return {
      period: {
        startDate: moment(period.startDate).format('YYYY-MM-DD'),
        endDate: moment(period.endDate).format('YYYY-MM-DD')
      },
      summary: {
        totalSales,
        ticketCount,
        averageTicket,
        totalExpenses,
        grossProfit,
        grossProfitMargin,
        operatingProfit,
        operatingProfitMargin,
        totalLaborCosts
      },
      details: {
        salesByCategory,
        salesByDay,
        expensesByCategory,
        costBreakdown,
        inventorySummary
      },
      kpis: {
        foodCostPercentage: totalSales > 0 ? (costOfGoodsSold / totalSales) * 100 : 0,
        laborCostPercentage: totalSales > 0 ? (totalLaborCosts / totalSales) * 100 : 0,
        profitPerDay: operatingProfit / moment(period.endDate).diff(moment(period.startDate), 'days'),
        inventoryTurnover: costOfGoodsSold / (inventorySummary.averageInventoryValue || 1)
      }
    };
  }
  
  /**
   * Génère un tableau de bord au format PDF
   * @param {string} filePath - Chemin du fichier à générer
   * @param {Object} data - Données du tableau de bord
   * @param {Object} template - Template à utiliser
   * @param {string} displayDate - Date à afficher
   * @returns {Promise<void>}
   * @private
   */
  async _generatePDFDashboard(filePath, data, template, displayDate) {
    return new Promise((resolve, reject) => {
      try {
        const doc = new PDFDocument({
          size: 'A4',
          margins: { top: 50, bottom: 50, left: 50, right: 50 },
          info: {
            Title: `Tableau de bord financier - ${displayDate}`,
            Author: 'Le Vieux Moulin - Module Comptabilité',
            Subject: 'Tableau de bord financier',
            Keywords: 'finance, comptabilité, restaurant',
            CreationDate: new Date()
          }
        });
        
        // Ouvrir le flux d'écriture
        const stream = fs.createWriteStream(filePath);
        doc.pipe(stream);
        
        // En-tête
        doc.fontSize(20).font('Helvetica-Bold').text('Le Vieux Moulin', { align: 'center' });
        doc.fontSize(16).font('Helvetica').text(`Tableau de Bord Financier - ${displayDate}`, { align: 'center' });
        doc.moveDown(2);
        
        // Résumé
        doc.fontSize(14).font('Helvetica-Bold').text('Résumé financier', { underline: true });
        doc.moveDown(1);
        
        const summary = data.summary;
        
        doc.fontSize(11).font('Helvetica');
        doc.text(`Chiffre d'affaires: ${summary.totalSales.toFixed(2)} €`);
        doc.text(`Nombre de tickets: ${summary.ticketCount}`);
        doc.text(`Ticket moyen: ${summary.averageTicket.toFixed(2)} €`);
        doc.text(`Marge brute: ${summary.grossProfit.toFixed(2)} € (${summary.grossProfitMargin.toFixed(2)}%)`);
        doc.text(`Résultat d'exploitation: ${summary.operatingProfit.toFixed(2)} € (${summary.operatingProfitMargin.toFixed(2)}%)`);
        
        doc.moveDown(2);
        
        // KPIs
        doc.fontSize(14).font('Helvetica-Bold').text('Indicateurs clés', { underline: true });
        doc.moveDown(1);
        
        const kpis = data.kpis;
        
        doc.fontSize(11).font('Helvetica');
        doc.text(`Ratio food cost: ${kpis.foodCostPercentage.toFixed(2)}%`);
        doc.text(`Ratio coût personnel: ${kpis.laborCostPercentage.toFixed(2)}%`);
        
        if (kpis.salesPerCover) {
          doc.text(`CA par couvert: ${kpis.salesPerCover.toFixed(2)} €`);
        }
        
        doc.moveDown(2);
        
        // Détails des ventes par catégorie
        doc.fontSize(14).font('Helvetica-Bold').text('Répartition des ventes', { underline: true });
        doc.moveDown(1);
        
        const salesByCategory = data.details.salesByCategory;
        doc.fontSize(11).font('Helvetica');
        
        // Tableau de répartition
        const categoryTable = {
          headers: ['Catégorie', 'Montant', 'Pourcentage'],
          rows: []
        };
        
        for (const [category, amount] of Object.entries(salesByCategory)) {
          const percentage = (amount / summary.totalSales * 100).toFixed(2);
          categoryTable.rows.push([
            category,
            `${amount.toFixed(2)} €`,
            `${percentage}%`
          ]);
        }
        
        this._drawTable(doc, categoryTable, { x: 50, y: doc.y, width: 500 });
        
        // Finaliser le document
        doc.end();
        
        // Gestion du flux
        stream.on('finish', () => resolve(filePath));
        stream.on('error', reject);
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Génère un tableau de bord au format Excel
   * @param {string} filePath - Chemin du fichier à générer
   * @param {Object} data - Données du tableau de bord
   * @param {Object} template - Template à utiliser
   * @param {string} displayDate - Date à afficher
   * @returns {Promise<void>}
   * @private
   */
  async _generateExcelDashboard(filePath, data, template, displayDate) {
    try {
      const workbook = new ExcelJS.Workbook();
      
      // Métadonnées
      workbook.creator = 'Le Vieux Moulin - Module Comptabilité';
      workbook.lastModifiedBy = 'Système Automatisé';
      workbook.created = new Date();
      workbook.modified = new Date();
      
      // Feuille de résumé
      const summarySheet = workbook.addWorksheet('Résumé');
      
      // En-tête
      summarySheet.mergeCells('A1:F1');
      summarySheet.mergeCells('A2:F2');
      const titleCell = summarySheet.getCell('A1');
      titleCell.value = 'Le Vieux Moulin';
      titleCell.font = { size: 16, bold: true };
      titleCell.alignment = { horizontal: 'center' };
      
      const subtitleCell = summarySheet.getCell('A2');
      subtitleCell.value = `Tableau de Bord Financier - ${displayDate}`;
      subtitleCell.font = { size: 14 };
      subtitleCell.alignment = { horizontal: 'center' };
      
      // Résumé financier
      summarySheet.getCell('A4').value = 'Résumé Financier';
      summarySheet.getCell('A4').font = { bold: true, size: 12 };
      
      const summary = data.summary;
      
      summarySheet.getCell('A5').value = 'Chiffre d\'affaires';
      summarySheet.getCell('B5').value = summary.totalSales;
      summarySheet.getCell('B5').numFmt = '#,##0.00 €';
      
      summarySheet.getCell('A6').value = 'Nombre de tickets';
      summarySheet.getCell('B6').value = summary.ticketCount;
      
      summarySheet.getCell('A7').value = 'Ticket moyen';
      summarySheet.getCell('B7').value = summary.averageTicket;
      summarySheet.getCell('B7').numFmt = '#,##0.00 €';
      
      summarySheet.getCell('A8').value = 'Marge brute';
      summarySheet.getCell('B8').value = summary.grossProfit;
      summarySheet.getCell('B8').numFmt = '#,##0.00 €';
      
      summarySheet.getCell('A9').value = 'Taux de marge brute';
      summarySheet.getCell('B9').value = summary.grossProfitMargin / 100;
      summarySheet.getCell('B9').numFmt = '0.00%';
      
      summarySheet.getCell('A10').value = 'Résultat d\'exploitation';
      summarySheet.getCell('B10').value = summary.operatingProfit;
      summarySheet.getCell('B10').numFmt = '#,##0.00 €';
      
      summarySheet.getCell('A11').value = 'Taux de résultat d\'exploitation';
      summarySheet.getCell('B11').value = summary.operatingProfitMargin / 100;
      summarySheet.getCell('B11').numFmt = '0.00%';
      
      // Indicateurs clés
      summarySheet.getCell('A13').value = 'Indicateurs Clés';
      summarySheet.getCell('A13').font = { bold: true, size: 12 };
      
      const kpis = data.kpis;
      
      summarySheet.getCell('A14').value = 'Ratio food cost';
      summarySheet.getCell('B14').value = kpis.foodCostPercentage / 100;
      summarySheet.getCell('B14').numFmt = '0.00%';
      
      summarySheet.getCell('A15').value = 'Ratio coût personnel';
      summarySheet.getCell('B15').value = kpis.laborCostPercentage / 100;
      summarySheet.getCell('B15').numFmt = '0.00%';
      
      if (kpis.salesPerCover) {
        summarySheet.getCell('A16').value = 'CA par couvert';
        summarySheet.getCell('B16').value = kpis.salesPerCover;
        summarySheet.getCell('B16').numFmt = '#,##0.00 €';
      }
      
      // Répartition des ventes
      const salesSheet = workbook.addWorksheet('Ventes par Catégorie');
      
      salesSheet.getCell('A1').value = 'Catégorie';
      salesSheet.getCell('B1').value = 'Montant';
      salesSheet.getCell('C1').value = 'Pourcentage';
      
      salesSheet.getRow(1).font = { bold: true };
      
      const salesByCategory = data.details.salesByCategory;
      let rowIndex = 2;
      
      for (const [category, amount] of Object.entries(salesByCategory)) {
        salesSheet.getCell(`A${rowIndex}`).value = category;
        salesSheet.getCell(`B${rowIndex}`).value = amount;
        salesSheet.getCell(`B${rowIndex}`).numFmt = '#,##0.00 €';
        salesSheet.getCell(`C${rowIndex}`).value = amount / summary.totalSales;
        salesSheet.getCell(`C${rowIndex}`).numFmt = '0.00%';
        rowIndex++;
      }
      
      // Ajouter d'autres feuilles selon les besoins
      
      // Enregistrer le fichier
      await workbook.xlsx.writeFile(filePath);
      
      return filePath;
    } catch (error) {
      this.logger.error('Erreur lors de la génération du tableau de bord Excel:', error);
      throw error;
    }
  }
  
  /**
   * Groupe les ventes par catégorie
   * @param {Array} sales - Transactions de vente
   * @returns {Object} Montant total par catégorie
   * @private
   */
  _groupSalesByCategory(sales) {
    const categories = {};
    
    for (const transaction of sales) {
      for (const item of transaction.items || []) {
        const category = item.category || 'Non catégorisé';
        
        if (!categories[category]) {
          categories[category] = 0;
        }
        
        categories[category] += item.total || 0;
      }
    }
    
    return categories;
  }
  
  /**
   * Groupe les ventes par service (déjeuner/dîner)
   * @param {Array} sales - Transactions de vente
   * @returns {Object} Montant total par service
   * @private
   */
  _groupSalesByService(sales) {
    const services = {
      lunch: 0,
      dinner: 0
    };
    
    for (const transaction of sales) {
      const date = new Date(transaction.date);
      const hours = date.getHours();
      
      // Considérer les transactions entre 11h et 15h comme déjeuner, le reste comme dîner
      const service = hours >= 11 && hours < 15 ? 'lunch' : 'dinner';
      services[service] += transaction.total || 0;
    }
    
    return services;
  }
  
  /**
   * Groupe les ventes par mode de paiement
   * @param {Array} sales - Transactions de vente
   * @returns {Object} Montant total par mode de paiement
   * @private
   */
  _groupSalesByPaymentMethod(sales) {
    const paymentMethods = {};
    
    for (const transaction of sales) {
      for (const payment of transaction.payments || []) {
        // Ignorer les remboursements et rendus de monnaie
        if (payment.type === 'CHANGE' || payment.amount <= 0) {
          continue;
        }
        
        const method = payment.method || 'Inconnu';
        
        if (!paymentMethods[method]) {
          paymentMethods[method] = 0;
        }
        
        paymentMethods[method] += payment.amount || 0;
      }
    }
    
    return paymentMethods;
  }
  
  /**
   * Groupe les dépenses par catégorie
   * @param {Array} expenses - Dépenses
   * @returns {Object} Montant total par catégorie
   * @private
   */
  _groupExpensesByCategory(expenses) {
    const categories = {
      supplies: 0,
      utilities: 0,
      rent: 0,
      marketing: 0,
      maintenance: 0,
      operating: 0,
      other: 0
    };
    
    for (const expense of expenses) {
      const category = expense.category || 'other';
      
      if (category in categories) {
        categories[category] += expense.amount || 0;
      } else {
        categories.other += expense.amount || 0;
      }
    }
    
    return categories;
  }
  
  /**
   * Calcule le coût des marchandises vendues
   * @param {Array} inventoryMovements - Mouvements de stock
   * @returns {number} Coût total des marchandises vendues
   * @private
   */
  _calculateCostOfGoodsSold(inventoryMovements) {
    return inventoryMovements
      .filter(movement => movement.type === 'CONSUMPTION')
      .reduce((sum, movement) => sum + (movement.cost || 0), 0);
  }
  
  /**
   * Calcule les coûts de personnel
   * @param {Array} staffSchedule - Planning du personnel
   * @returns {number} Coût total du personnel
   * @private
   */
  _calculateLaborCosts(staffSchedule) {
    return staffSchedule
      .reduce((sum, shift) => sum + (shift.cost || 0), 0);
  }
  
  /**
   * Groupe les ventes par jour
   * @param {Array} sales - Transactions de vente
   * @param {Object} period - Période à analyser
   * @returns {Object} Montant total par jour
   * @private
   */
  _groupSalesByDay(sales, period) {
    const result = {};
    
    // Initialiser tous les jours de la période
    const startDate = moment(period.startDate);
    const endDate = moment(period.endDate);
    const dayCount = endDate.diff(startDate, 'days') + 1;
    
    for (let i = 0; i < dayCount; i++) {
      const currentDate = moment(startDate).add(i, 'days');
      const dateKey = currentDate.format('YYYY-MM-DD');
      result[dateKey] = 0;
    }
    
    // Agréger les ventes par jour
    for (const transaction of sales) {
      const dateKey = moment(transaction.date).format('YYYY-MM-DD');
      
      if (dateKey in result) {
        result[dateKey] += transaction.total || 0;
      }
    }
    
    return result;
  }
  
  /**
   * Dessine un tableau dans un document PDF
   * @param {PDFDocument} doc - Document PDF
   * @param {Object} table - Configuration du tableau
   * @param {Object} options - Options de dessin
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
   * Retourne le template par défaut pour un tableau de bord quotidien
   * @returns {Object} Configuration du template
   * @private
   */
  _getDefaultDailyTemplate() {
    return {
      id: 'default_daily',
      name: 'Template de tableau de bord quotidien par défaut',
      sections: [
        {
          id: 'summary',
          title: 'Résumé financier',
          type: 'summary',
          fields: [
            'totalSales',
            'ticketCount',
            'averageTicket',
            'grossProfit',
            'grossProfitMargin',
            'operatingProfit',
            'operatingProfitMargin'
          ]
        },
        {
          id: 'kpis',
          title: 'Indicateurs clés',
          type: 'kpis',
          fields: [
            'foodCostPercentage',
            'laborCostPercentage',
            'salesPerCover'
          ]
        },
        {
          id: 'sales_category',
          title: 'Répartition des ventes par catégorie',
          type: 'chart',
          chartType: 'pie',
          dataSource: 'salesByCategory'
        },
        {
          id: 'sales_service',
          title: 'Répartition par service',
          type: 'chart',
          chartType: 'pie',
          dataSource: 'salesByService'
        },
        {
          id: 'payment_methods',
          title: 'Répartition par mode de paiement',
          type: 'chart',
          chartType: 'pie',
          dataSource: 'salesByPaymentMethod'
        }
      ]
    };
  }
  
  /**
   * Retourne le template par défaut pour un tableau de bord mensuel
   * @returns {Object} Configuration du template
   * @private
   */
  _getDefaultMonthlyTemplate() {
    return {
      id: 'default_monthly',
      name: 'Template de tableau de bord mensuel par défaut',
      sections: [
        {
          id: 'summary',
          title: 'Résumé financier mensuel',
          type: 'summary',
          fields: [
            'totalSales',
            'ticketCount',
            'averageTicket',
            'grossProfit',
            'grossProfitMargin',
            'operatingProfit',
            'operatingProfitMargin'
          ]
        },
        {
          id: 'kpis',
          title: 'Indicateurs clés',
          type: 'kpis',
          fields: [
            'foodCostPercentage',
            'laborCostPercentage',
            'profitPerDay',
            'inventoryTurnover'
          ]
        },
        {
          id: 'sales_trend',
          title: 'Évolution des ventes',
          type: 'chart',
          chartType: 'line',
          dataSource: 'salesByDay'
        },
        {
          id: 'sales_category',
          title: 'Répartition des ventes par catégorie',
          type: 'chart',
          chartType: 'pie',
          dataSource: 'salesByCategory'
        },
        {
          id: 'cost_breakdown',
          title: 'Répartition des coûts',
          type: 'chart',
          chartType: 'pie',
          dataSource: 'costBreakdown'
        }
      ]
    };
  }
}

module.exports = { FinancialDashboardGenerator };
