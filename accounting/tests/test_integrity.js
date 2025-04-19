/**
 * Tests d'intégrité des données financières
 * Ce script vérifie l'intégrité et la cohérence des données pour les rapports financiers
 */

'use strict';

const { expect } = require('chai');
const sinon = require('sinon');
const { DataCollector } = require('../common/data_collector');
const { FinancialIntegrityChecker } = require('../common/financial_integrity_checker');
const { ReportGenerator } = require('../reporting/financial_report_generator');

describe('Financial Integrity Tests', () => {
  let dataCollector;
  let integrityChecker;
  let reportGenerator;
  
  beforeEach(() => {
    // Initialiser avec des mocks
    dataCollector = new DataCollector({
      configManager: {
        getConfig: () => ({
          database: { connectionString: 'mock-connection-string' }
        })
      }
    });
    
    integrityChecker = new FinancialIntegrityChecker();
    reportGenerator = new ReportGenerator({
      dataCollector,
      integrityChecker
    });
    
    // Stubs pour simuler les données de test
    sinon.stub(dataCollector, 'getTransactions').resolves([
      {
        id: 'tx1',
        date: '2025-04-15',
        total: 152.50,
        taxTotal: 15.25,
        items: [
          { id: 'item1', name: 'Pizza Margherita', quantity: 2, price: 12.5, total: 25.0, taxRate: 10 },
          { id: 'item2', name: 'Tiramisu', quantity: 1, price: 6.5, total: 6.5, taxRate: 10 },
          { id: 'item3', name: 'Vin rouge (verre)', quantity: 3, price: 4.0, total: 12.0, taxRate: 20 }
        ],
        payments: [
          { method: 'CARD', amount: 152.50 }
        ]
      },
      {
        id: 'tx2',
        date: '2025-04-15',
        total: 86.00,
        taxTotal: 8.60,
        items: [
          { id: 'item4', name: 'Salade César', quantity: 1, price: 9.5, total: 9.5, taxRate: 10 },
          { id: 'item5', name: 'Entrecôte', quantity: 1, price: 22.5, total: 22.5, taxRate: 10 }
        ],
        payments: [
          { method: 'CASH', amount: 90.00 },
          { method: 'CASH', amount: -4.00, type: 'CHANGE' }
        ]
      }
    ]);
    
    sinon.stub(dataCollector, 'getInventoryMovements').resolves([
      { date: '2025-04-15', type: 'CONSUMPTION', productId: 'prod1', quantity: 0.4, cost: 6.0 },
      { date: '2025-04-15', type: 'CONSUMPTION', productId: 'prod2', quantity: 0.2, cost: 3.0 },
      { date: '2025-04-15', type: 'CONSUMPTION', productId: 'prod3', quantity: 0.5, cost: 7.5 }
    ]);
  });
  
  afterEach(() => {
    sinon.restore();
  });
  
  describe('Data Reconciliation', () => {
    it('should reconcile sales with payments', async () => {
      // Arrange
      const period = {
        startDate: new Date('2025-04-15T00:00:00Z'),
        endDate: new Date('2025-04-15T23:59:59Z')
      };
      
      // Act
      const reconciliation = await integrityChecker.reconcileSalesAndPayments(
        await dataCollector.getTransactions(period),
        period
      );
      
      // Assert
      expect(reconciliation.status).to.equal('RECONCILED');
      expect(reconciliation.totalSales).to.equal(238.50);
      expect(reconciliation.totalPayments).to.equal(238.50);
      expect(reconciliation.discrepancy).to.equal(0);
    });
    
    it('should detect discrepancies in tax calculations', async () => {
      // Arrange
      const transactions = await dataCollector.getTransactions({
        startDate: new Date('2025-04-15'),
        endDate: new Date('2025-04-15')
      });
      
      // Modifions une transaction pour créer une discordance
      transactions[0].taxTotal = 16.00; // Valeur incorrecte, devrait être 15.25
      
      // Act
      const validation = await integrityChecker.validateTaxCalculations(transactions);
      
      // Assert
      expect(validation.valid).to.be.false;
      expect(validation.discrepancies.length).to.equal(1);
      expect(validation.discrepancies[0].transaction).to.equal('tx1');
      expect(validation.discrepancies[0].calculatedTax).to.not.equal(validation.discrepancies[0].recordedTax);
    });
    
    it('should verify inventory movements against sales', async () => {
      // Arrange
      const period = {
        startDate: new Date('2025-04-15'),
        endDate: new Date('2025-04-15')
      };
      
      const sales = await dataCollector.getTransactions(period);
      const inventoryMovements = await dataCollector.getInventoryMovements(period);
      
      // Act
      const verification = await integrityChecker.verifyInventoryMovementsAgainstSales(
        sales,
        inventoryMovements,
        period
      );
      
      // Assert
      expect(verification.status).to.equal('VALID');
      expect(verification.totalSalesCost).to.be.greaterThan(0);
      expect(verification.totalInventoryConsumption).to.be.greaterThan(0);
    });
  });
  
  describe('Report Validation', () => {
    it('should validate financial report accuracy', async () => {
      // Arrange
      const period = {
        startDate: new Date('2025-04-15'),
        endDate: new Date('2025-04-15')
      };
      
      // Act
      const report = await reportGenerator.generateDailyReport(period);
      const validation = integrityChecker.validateReportAccuracy(report);
      
      // Assert
      expect(validation.valid).to.be.true;
      expect(validation.checksPassed).to.be.an('array');
      expect(validation.checksPassed.length).to.be.greaterThan(0);
    });
    
    it('should detect balance discrepancies in reports', async () => {
      // Arrange
      const period = {
        startDate: new Date('2025-04-15'),
        endDate: new Date('2025-04-15')
      };
      
      // Act
      const report = await reportGenerator.generateDailyReport(period);
      
      // Introduire une discordance artificielle
      report.totalRevenue = report.totalRevenue + 10;
      
      const validation = integrityChecker.validateReportAccuracy(report);
      
      // Assert
      expect(validation.valid).to.be.false;
      expect(validation.errors).to.be.an('array');
      expect(validation.errors.length).to.be.greaterThan(0);
    });
  });
});
