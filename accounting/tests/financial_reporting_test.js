/**
 * Tests pour le module de génération de rapports financiers
 * 
 * Ce fichier contient les tests unitaires et d'intégration pour valider
 * le bon fonctionnement du module de génération de rapports financiers.
 */

'use strict';

const { ReportGenerator } = require('../reporting/report_generator');
const FinancialReportGenerator = require('../reporting/financial_report_generator');
const path = require('path');
const fs = require('fs');
const os = require('os');
const assert = require('assert');

// Mock du collecteur de données pour les tests
class MockDataCollector {
  constructor() {
    this.mockData = {
      transactions: this._generateMockTransactions(),
      inventory: this._generateMockInventory(),
      expenses: this._generateMockExpenses(),
      employees: this._generateMockEmployees()
    };
  }

  // Génération de données de transaction fictives
  _generateMockTransactions() {
    const transactions = [];
    const currentDate = new Date();
    const startDate = new Date(currentDate);
    startDate.setDate(startDate.getDate() - 30); // 30 jours en arrière

    // Générer des ventes sur 30 jours
    for (let i = 0; i < 30; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      
      // Générer entre 10 et 50 transactions par jour
      const transactionsCount = 10 + Math.floor(Math.random() * 40);
      
      // Chiffre d'affaires total du jour
      let dailyRevenue = 0;
      
      for (let j = 0; j < transactionsCount; j++) {
        // Montant entre 20 et 100€
        const amount = 20 + Math.random() * 80;
        dailyRevenue += amount;
        
        transactions.push({
          id: `TRX-${date.toISOString().slice(0, 10)}-${j}`,
          date: new Date(date),
          type: 'sale',
          amount: amount,
          paymentMethod: ['cash', 'card', 'card', 'card'][Math.floor(Math.random() * 4)], // 75% carte, 25% espèces
          items: [
            {
              category: ['food', 'beverage', 'dessert'][Math.floor(Math.random() * 3)],
              quantity: 1 + Math.floor(Math.random() * 3),
              price: amount / (1 + Math.floor(Math.random() * 3)),
              name: 'Article test'
            }
          ]
        });
      }
    }
    
    return transactions;
  }

  // Génération de données de stock fictives
  _generateMockInventory() {
    return [
      {
        id: 'INV-001',
        name: 'Farine T55',
        category: 'dry_goods',
        quantity: 25,
        unit: 'kg',
        unitPrice: 1.2,
        totalValue: 30,
        lastUpdated: new Date()
      },
      {
        id: 'INV-002',
        name: 'Tomates',
        category: 'fresh_produce',
        quantity: 15,
        unit: 'kg',
        unitPrice: 2.5,
        totalValue: 37.5,
        lastUpdated: new Date()
      },
      {
        id: 'INV-003',
        name: 'Mozzarella',
        category: 'dairy',
        quantity: 10,
        unit: 'kg',
        unitPrice: 8.5,
        totalValue: 85,
        lastUpdated: new Date()
      },
      {
        id: 'INV-004',
        name: 'Vin rouge',
        category: 'beverage',
        quantity: 30,
        unit: 'bottle',
        unitPrice: 6.5,
        totalValue: 195,
        lastUpdated: new Date()
      }
    ];
  }

  // Génération de données de dépenses fictives
  _generateMockExpenses() {
    const expenses = [];
    const currentDate = new Date();
    const startDate = new Date(currentDate);
    startDate.setDate(startDate.getDate() - 30); // 30 jours en arrière
    
    // Catégories de dépenses
    const categories = [
      { name: 'food_supplies', frequency: 7 }, // Hebdomadaire
      { name: 'utilities', frequency: 30 }, // Mensuel
      { name: 'rent', frequency: 30 }, // Mensuel
      { name: 'salaries', frequency: 30 }, // Mensuel
      { name: 'maintenance', frequency: 15 }, // Bi-mensuel
      { name: 'marketing', frequency: 15 } // Bi-mensuel
    ];
    
    // Générer des dépenses par catégorie
    for (const category of categories) {
      // Calculer le nombre d'occurrences dans la période
      const occurrences = Math.ceil(30 / category.frequency);
      
      for (let i = 0; i < occurrences; i++) {
        const date = new Date(startDate);
        date.setDate(date.getDate() + i * category.frequency);
        
        let amount;
        switch (category.name) {
          case 'food_supplies':
            amount = 500 + Math.random() * 300; // 500-800€
            break;
          case 'utilities':
            amount = 300 + Math.random() * 200; // 300-500€
            break;
          case 'rent':
            amount = 2000; // Fixe
            break;
          case 'salaries':
            amount = 8000 + Math.random() * 1000; // 8000-9000€
            break;
          case 'maintenance':
            amount = 200 + Math.random() * 300; // 200-500€
            break;
          case 'marketing':
            amount = 300 + Math.random() * 200; // 300-500€
            break;
          default:
            amount = 100 + Math.random() * 100; // 100-200€
        }
        
        expenses.push({
          id: `EXP-${category.name}-${i}`,
          date: new Date(date),
          category: category.name,
          amount: amount,
          description: `Dépense ${category.name}`,
          paymentMethod: 'bank_transfer',
          status: 'paid'
        });
      }
    }
    
    return expenses;
  }

  // Génération de données d'employés fictives
  _generateMockEmployees() {
    return [
      {
        id: 'EMP-001',
        name: 'Jean Dupont',
        position: 'manager',
        hourlyRate: 18,
        hoursWorked: 160,
        salary: 2880
      },
      {
        id: 'EMP-002',
        name: 'Marie Martin',
        position: 'chef',
        hourlyRate: 15,
        hoursWorked: 160,
        salary: 2400
      },
      {
        id: 'EMP-003',
        name: 'Pierre Durand',
        position: 'server',
        hourlyRate: 12,
        hoursWorked: 140,
        salary: 1680
      },
      {
        id: 'EMP-004',
        name: 'Sophie Leroy',
        position: 'server',
        hourlyRate: 12,
        hoursWorked: 120,
        salary: 1440
      }
    ];
  }

  // Méthodes pour récupérer les données
  async getTransactions(options) {
    // Filtrer par période si nécessaire
    if (options && (options.startDate || options.endDate)) {
      return this.mockData.transactions.filter(tx => {
        if (options.startDate && tx.date < options.startDate) return false;
        if (options.endDate && tx.date > options.endDate) return false;
        return true;
      });
    }
    return this.mockData.transactions;
  }

  async getInventoryValuation(options) {
    return this.mockData.inventory;
  }

  async getExpenses(options) {
    // Filtrer par période si nécessaire
    if (options && (options.startDate || options.endDate)) {
      return this.mockData.expenses.filter(exp => {
        if (options.startDate && exp.date < options.startDate) return false;
        if (options.endDate && exp.date > options.endDate) return false;
        return true;
      });
    }
    return this.mockData.expenses;
  }

  async getEmployees(options) {
    return this.mockData.employees;
  }

  async getFinancialTimeSeries(options) {
    // Simuler des séries temporelles financières
    const startDate = options.startDate || new Date(new Date().setDate(new Date().getDate() - 30));
    const endDate = options.endDate || new Date();
    const metrics = options.metrics || ['revenue', 'costs', 'margins'];
    
    const result = {};
    
    // Nombre de jours dans la période
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    
    for (const metric of metrics) {
      result[metric] = [];
      
      for (let i = 0; i < days; i++) {
        const date = new Date(startDate);
        date.setDate(date.getDate() + i);
        
        let value;
        switch (metric) {
          case 'revenue':
            // Simuler un CA entre 1000€ et 3000€
            value = 1000 + Math.random() * 2000;
            // Effet weekend (augmentation de 30%)
            if (date.getDay() === 5 || date.getDay() === 6) {
              value *= 1.3;
            }
            break;
          case 'costs':
            // Coûts entre 500€ et 1500€
            value = 500 + Math.random() * 1000;
            break;
          case 'margins':
            // Marge entre 40% et 60%
            value = 40 + Math.random() * 20;
            break;
          case 'cashflow':
            // Flux de trésorerie entre -500€ et +1500€
            value = -500 + Math.random() * 2000;
            break;
          default:
            value = Math.random() * 1000;
        }
        
        result[metric].push({
          date,
          value
        });
      }
    }
    
    return result;
  }
}

// Tests du générateur de rapports
describe('FinancialReportGenerator', function() {
  // Créer un répertoire temporaire pour les tests
  let tempDir;
  let reportGenerator;
  let mockDataCollector;
  
  before(function() {
    // Créer un répertoire temporaire pour les tests
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'report-tests-'));
    
    // Initialiser le mock collector et le générateur de rapports
    mockDataCollector = new MockDataCollector();
    
    reportGenerator = new ReportGenerator({
      templates_dir: path.join(__dirname, '../reporting/templates'),
      output_dir: tempDir,
      dataCollector: mockDataCollector,
      company_info: {
        name: 'Le Vieux Moulin',
        siret: '12345678901234',
        address: 'Camping 3 étoiles, Vensac, Gironde',
        vat_number: 'FR12345678901'
      }
    });
  });
  
  after(function() {
    // Nettoyer les fichiers temporaires
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });
  
  // Test de génération d'un rapport journalier
  describe('createDailyReport', function() {
    it('should generate a daily financial report', async function() {
      // Date pour le rapport
      const reportDate = new Date();
      reportDate.setDate(reportDate.getDate() - 1); // Hier
      
      // Générer le rapport
      const report = await reportGenerator.createReport('daily', {
        date: reportDate,
        format: 'json' // Pour faciliter les tests
      });
      
      // Vérifications
      assert.ok(report, 'Le rapport devrait être généré');
      assert.ok(report.data, 'Le rapport devrait contenir des données');
      assert.ok(report.data.transactions, 'Le rapport devrait contenir des transactions');
      assert.ok(report.data.summary, 'Le rapport devrait contenir un résumé');
      assert.equal(report.date.toDateString(), reportDate.toDateString(), 'La date du rapport devrait correspondre');
    });
  });
  
  // Test de génération d'un rapport mensuel
  describe('createMonthlyReport', function() {
    it('should generate a monthly financial report', async function() {
      // Mois et année pour le rapport
      const year = new Date().getFullYear();
      const month = new Date().getMonth();
      
      // Générer le rapport
      const report = await reportGenerator.createReport('monthly', {
        year,
        month,
        format: 'json' // Pour faciliter les tests
      });
      
      // Vérifications
      assert.ok(report, 'Le rapport devrait être généré');
      assert.ok(report.data, 'Le rapport devrait contenir des données');
      assert.ok(report.data.revenue, 'Le rapport devrait contenir des données de CA');
      assert.ok(report.data.expenses, 'Le rapport devrait contenir des données de dépenses');
      assert.ok(report.data.profitLoss, 'Le rapport devrait contenir un compte de résultat');
      assert.equal(report.year, year, 'L\'année du rapport devrait correspondre');
      assert.equal(report.month, month, 'Le mois du rapport devrait correspondre');
    });
  });
  
  // Test de génération d'un rapport personnalisé
  describe('createCustomReport', function() {
    it('should generate a custom financial report based on specified criteria', async function() {
      // Période personnalisée
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 15); // 15 jours en arrière
      const endDate = new Date();
      
      // Générer le rapport
      const report = await reportGenerator.createReport('custom', {
        startDate,
        endDate,
        metrics: ['revenue', 'costs', 'margins'],
        groupBy: 'day',
        format: 'json'
      });
      
      // Vérifications
      assert.ok(report, 'Le rapport devrait être généré');
      assert.ok(report.data, 'Le rapport devrait contenir des données');
      assert.ok(report.data.timeSeries, 'Le rapport devrait contenir des séries temporelles');
      assert.ok(report.data.timeSeries.revenue, 'Le rapport devrait contenir des données de CA');
      assert.ok(report.data.timeSeries.costs, 'Le rapport devrait contenir des données de coûts');
      assert.ok(report.data.timeSeries.margins, 'Le rapport devrait contenir des données de marges');
      assert.equal(report.startDate.toDateString(), startDate.toDateString(), 'La date de début devrait correspondre');
      assert.equal(report.endDate.toDateString(), endDate.toDateString(), 'La date de fin devrait correspondre');
    });
  });
  
  // Test d'export au format PDF
  describe('exportToPDF', function() {
    it('should export a report to PDF format', async function() {
      // Date pour le rapport
      const reportDate = new Date();
      
      // Générer le rapport
      const report = await reportGenerator.createReport('daily', {
        date: reportDate,
        format: 'pdf'
      });
      
      // Vérifications
      assert.ok(report, 'Le rapport devrait être généré');
      assert.ok(report.files, 'Le rapport devrait contenir des fichiers');
      assert.ok(report.files.pdf, 'Le rapport devrait contenir un fichier PDF');
      assert.ok(fs.existsSync(report.files.pdf), 'Le fichier PDF devrait exister');
    });
  });
  
  // Test d'export au format Excel
  describe('exportToExcel', function() {
    it('should export a report to Excel format', async function() {
      // Date pour le rapport
      const reportDate = new Date();
      
      // Générer le rapport
      const report = await reportGenerator.createReport('daily', {
        date: reportDate,
        format: 'excel'
      });
      
      // Vérifications
      assert.ok(report, 'Le rapport devrait être généré');
      assert.ok(report.files, 'Le rapport devrait contenir des fichiers');
      assert.ok(report.files.excel, 'Le rapport devrait contenir un fichier Excel');
      assert.ok(fs.existsSync(report.files.excel), 'Le fichier Excel devrait exister');
    });
  });
  
  // Test de notification par email
  describe('sendReportByEmail', function() {
    it('should send a report by email', async function() {
      // Mock du service d'email
      const emailServiceMock = {
        sendEmail: async (options) => {
          return { success: true, messageId: 'test-message-id' };
        }
      };
      
      // Remplacer temporairement le service d'email
      const originalEmailService = reportGenerator.emailService;
      reportGenerator.emailService = emailServiceMock;
      
      try {
        // Date pour le rapport
        const reportDate = new Date();
        
        // Générer et envoyer le rapport
        const report = await reportGenerator.createReport('daily', {
          date: reportDate,
          format: 'pdf'
        });
        
        const sendResult = await reportGenerator.sendReportByEmail({
          report,
          recipients: ['comptable@example.com'],
          subject: 'Rapport journalier',
          message: 'Veuillez trouver ci-joint le rapport journalier'
        });
        
        // Vérifications
        assert.ok(sendResult.success, 'L\'envoi devrait réussir');
        assert.ok(sendResult.messageId, 'Un ID de message devrait être retourné');
      } finally {
        // Restaurer le service d'email original
        reportGenerator.emailService = originalEmailService;
      }
    });
  });
  
  // Test de génération de plusieurs rapports en parallèle
  describe('generateBatchReports', function() {
    it('should generate multiple reports in batch mode', async function() {
      // Paramètres pour les rapports
      const batchConfig = [
        {
          type: 'daily',
          options: {
            date: new Date(new Date().setDate(new Date().getDate() - 1)),
            format: 'json'
          }
        },
        {
          type: 'daily',
          options: {
            date: new Date(new Date().setDate(new Date().getDate() - 2)),
            format: 'json'
          }
        },
        {
          type: 'weekly',
          options: {
            endDate: new Date(),
            format: 'json'
          }
        }
      ];
      
      // Générer les rapports en batch
      const reports = await reportGenerator.generateBatchReports(batchConfig);
      
      // Vérifications
      assert.equal(reports.length, batchConfig.length, 'Le nombre de rapports générés devrait correspondre');
      
      // Vérifier chaque rapport
      for (let i = 0; i < reports.length; i++) {
        assert.ok(reports[i], `Le rapport ${i} devrait être généré`);
        assert.ok(reports[i].data, `Le rapport ${i} devrait contenir des données`);
        assert.equal(reports[i].type, batchConfig[i].type, `Le type du rapport ${i} devrait correspondre`);
      }
    });
  });
});

// Tests unitaires pour les fonctions utilitaires
describe('Financial Reporting Utilities', function() {
  // Initialiser le mock collector
  const mockDataCollector = new MockDataCollector();
  
  describe('calculateFinancialMetrics', function() {
    it('should calculate key financial metrics from transaction data', async function() {
      // Récupérer des transactions de test
      const transactions = await mockDataCollector.getTransactions();
      
      // Calculer les métriques
      const metrics = FinancialReportGenerator.calculateFinancialMetrics(transactions);
      
      // Vérifications
      assert.ok(metrics, 'Les métriques devraient être calculées');
      assert.ok(metrics.totalRevenue !== undefined, 'Le chiffre d\'affaires total devrait être calculé');
      assert.ok(metrics.transactionCount !== undefined, 'Le nombre de transactions devrait être calculé');
      assert.ok(metrics.averageTicket !== undefined, 'Le ticket moyen devrait être calculé');
      
      // Vérifier la cohérence des calculs
      assert.equal(metrics.transactionCount, transactions.length, 'Le nombre de transactions devrait correspondre');
      assert.equal(metrics.totalRevenue, transactions.reduce((sum, tx) => sum + tx.amount, 0), 'Le CA total devrait être la somme des montants');
      assert.equal(metrics.averageTicket, metrics.totalRevenue / metrics.transactionCount, 'Le ticket moyen devrait être calculé correctement');
    });
  });
  
  describe('calculateProfitability', function() {
    it('should calculate profitability metrics from revenue and cost data', async function() {
      // Récupérer des données de test
      const revenue = 10000;
      const costs = {
        food: 3000,
        beverage: 1000,
        labor: 2500,
        overhead: 1500
      };
      
      // Calculer la rentabilité
      const profitability = FinancialReportGenerator.calculateProfitability(revenue, costs);
      
      // Vérifications
      assert.ok(profitability, 'Les métriques de rentabilité devraient être calculées');
      assert.ok(profitability.grossProfit !== undefined, 'La marge brute devrait être calculée');
      assert.ok(profitability.grossMargin !== undefined, 'Le taux de marge brute devrait être calculé');
      assert.ok(profitability.netProfit !== undefined, 'Le bénéfice net devrait être calculé');
      assert.ok(profitability.netMargin !== undefined, 'Le taux de marge nette devrait être calculé');
      
      // Vérifier la cohérence des calculs
      const totalCosts = Object.values(costs).reduce((sum, cost) => sum + cost, 0);
      const expectedGrossProfit = revenue - costs.food - costs.beverage;
      const expectedNetProfit = revenue - totalCosts;
      
      assert.equal(profitability.grossProfit, expectedGrossProfit, 'La marge brute devrait être calculée correctement');
      assert.equal(profitability.grossMargin, (expectedGrossProfit / revenue) * 100, 'Le taux de marge brute devrait être calculé correctement');
      assert.equal(profitability.netProfit, expectedNetProfit, 'Le bénéfice net devrait être calculé correctement');
      assert.equal(profitability.netMargin, (expectedNetProfit / revenue) * 100, 'Le taux de marge nette devrait être calculé correctement');
    });
  });
  
  describe('groupTransactionsByCategory', function() {
    it('should group transactions by category and calculate subtotals', async function() {
      // Récupérer des transactions de test
      const transactions = await mockDataCollector.getTransactions();
      
      // Grouper par catégorie
      const categorized = FinancialReportGenerator.groupTransactionsByCategory(transactions);
      
      // Vérifications
      assert.ok(categorized, 'Les transactions devraient être groupées');
      assert.ok(categorized.categories, 'Les catégories devraient être disponibles');
      assert.ok(categorized.totals, 'Les totaux devraient être calculés');
      
      // Vérifier que la somme des totaux par catégorie correspond au total global
      const categorySum = Object.values(categorized.categories).reduce((sum, cat) => sum + cat.total, 0);
      assert.equal(categorySum, categorized.totals.revenue, 'La somme des catégories devrait correspondre au total');
    });
  });
  
  describe('calculateTrends', function() {
    it('should calculate trends by comparing current vs previous period', async function() {
      // Données fictives pour deux périodes
      const currentPeriod = {
        revenue: 10000,
        costs: 6000,
        transactions: 500
      };
      
      const previousPeriod = {
        revenue: 9000,
        costs: 5800,
        transactions: 480
      };
      
      // Calculer les tendances
      const trends = FinancialReportGenerator.calculateTrends(currentPeriod, previousPeriod);
      
      // Vérifications
      assert.ok(trends, 'Les tendances devraient être calculées');
      assert.ok(trends.revenue !== undefined, 'La tendance du CA devrait être calculée');
      assert.ok(trends.costs !== undefined, 'La tendance des coûts devrait être calculée');
      assert.ok(trends.transactions !== undefined, 'La tendance des transactions devrait être calculée');
      
      // Vérifier la cohérence des calculs
      assert.equal(trends.revenue.absolute, currentPeriod.revenue - previousPeriod.revenue, 'La variation absolue du CA devrait être correcte');
      assert.equal(trends.revenue.percentage, ((currentPeriod.revenue - previousPeriod.revenue) / previousPeriod.revenue) * 100, 'La variation en % du CA devrait être correcte');
      
      assert.equal(trends.costs.absolute, currentPeriod.costs - previousPeriod.costs, 'La variation absolue des coûts devrait être correcte');
      assert.equal(trends.costs.percentage, ((currentPeriod.costs - previousPeriod.costs) / previousPeriod.costs) * 100, 'La variation en % des coûts devrait être correcte');
      
      assert.equal(trends.transactions.absolute, currentPeriod.transactions - previousPeriod.transactions, 'La variation absolue des transactions devrait être correcte');
      assert.equal(trends.transactions.percentage, ((currentPeriod.transactions - previousPeriod.transactions) / previousPeriod.transactions) * 100, 'La variation en % des transactions devrait être correcte');
    });
  });
});
