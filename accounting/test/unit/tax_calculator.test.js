/**
 * Tests unitaires pour le module TaxCalculator
 */

const { TaxCalculator } = require('../../tax_management/tax_calculator');
const { ConfigManager } = require('../../common/config_manager');
const moment = require('moment');

// Mock des dépendances
jest.mock('../../common/config_manager', () => ({
  ConfigManager: {
    getConfigManager: jest.fn().mockReturnValue({
      getConfig: jest.fn().mockReturnValue({})
    })
  }
}));

jest.mock('../../common/data_collector', () => ({
  DataCollector: jest.fn().mockImplementation(() => ({
    getSalesData: jest.fn(),
    getExpensesData: jest.fn()
  }))
}));

describe('TaxCalculator', () => {
  let taxCalculator;
  let mockDataCollector;
  
  beforeEach(() => {
    // Réinitialiser les mocks
    jest.clearAllMocks();
    
    // Créer un mock du DataCollector
    mockDataCollector = {
      getSalesData: jest.fn(),
      getExpensesData: jest.fn()
    };
    
    // Créer une instance du TaxCalculator avec la configuration de test
    taxCalculator = new TaxCalculator({
      vatRates: {
        standard: 20.0,
        intermediate: 10.0,
        reduced: 5.5,
        superReduced: 2.1,
        zero: 0.0
      },
      declarationPeriods: {
        type: 'monthly',
        deadline: 15,
        paymentDeadline: 20
      },
      dataCollector: mockDataCollector
    });
  });
  
  describe('constructor', () => {
    it('should initialize with default values when no options are provided', () => {
      const defaultCalculator = new TaxCalculator();
      expect(defaultCalculator).toBeInstanceOf(TaxCalculator);
      expect(defaultCalculator.vatRates.standard).toBe(20.0);
      expect(defaultCalculator.vatRates.intermediate).toBe(10.0);
      expect(defaultCalculator.declarationPeriods.type).toBe('monthly');
    });
    
    it('should initialize with provided options', () => {
      expect(taxCalculator.vatRates.standard).toBe(20.0);
      expect(taxCalculator.declarationPeriods.deadline).toBe(15);
      expect(taxCalculator.dataCollector).toBe(mockDataCollector);
    });
  });
  
  describe('calculateTransactionVAT', () => {
    it('should calculate VAT correctly for a transaction with multiple items', () => {
      // Créer une transaction de test
      const transaction = {
        id: 'tx1',
        date: '2025-04-15',
        type: 'onsite', // Sur place
        items: [
          { id: 'item1', name: 'Pizza Margherita', quantity: 2, unitPrice: 12.00, category: 'food' },
          { id: 'item2', name: 'Bière', quantity: 3, unitPrice: 5.00, category: 'alcoholic_beverages' },
          { id: 'item3', name: 'Eau minérale', quantity: 1, unitPrice: 3.00, category: 'non_alcoholic_beverages' },
          { id: 'item4', name: 'Dessert à emporter', quantity: 1, unitPrice: 6.00, category: 'food', taxCategory: 'reduced' }
        ]
      };
      
      // Calculer la TVA
      const result = taxCalculator.calculateTransactionVAT(transaction);
      
      // Vérifier le montant total avec TVA
      expect(result.totalAmountWithTax).toBeCloseTo(12 * 2 + 5 * 3 + 3 * 1 + 6 * 1, 2);
      
      // Vérifier la répartition de la TVA
      expect(Object.keys(result.vatBreakdown).length).toBe(3); // 3 taux différents
      
      // Vérifier que chaque item a les informations de TVA correctes
      expect(result.items.length).toBe(4);
      
      // Vérifier le premier item (nourriture sur place - 10%)
      expect(result.items[0].vatRate).toBe(10.0);
      expect(result.items[0].amountWithTax).toBe(24.00);
      expect(result.items[0].amountWithoutTax).toBeCloseTo(21.82, 2);
      expect(result.items[0].vatAmount).toBeCloseTo(2.18, 2);
      
      // Vérifier le deuxième item (alcool - 20%)
      expect(result.items[1].vatRate).toBe(20.0);
      expect(result.items[1].amountWithTax).toBe(15.00);
      expect(result.items[1].amountWithoutTax).toBeCloseTo(12.50, 2);
      expect(result.items[1].vatAmount).toBeCloseTo(2.50, 2);
      
      // Vérifier le troisième item (boisson non alcoolisée sur place - 10%)
      expect(result.items[2].vatRate).toBe(10.0);
      expect(result.items[2].amountWithTax).toBe(3.00);
      expect(result.items[2].amountWithoutTax).toBeCloseTo(2.73, 2);
      expect(result.items[2].vatAmount).toBeCloseTo(0.27, 2);
      
      // Vérifier le quatrième item (dessert à emporter - 5.5%)
      expect(result.items[3].vatRate).toBe(5.5);
      expect(result.items[3].amountWithTax).toBe(6.00);
      expect(result.items[3].amountWithoutTax).toBeCloseTo(5.69, 2);
      expect(result.items[3].vatAmount).toBeCloseTo(0.31, 2);
      
      // Vérifier les totaux
      expect(result.totalAmountWithTax).toBe(48.00);
      expect(result.totalAmountWithoutTax).toBeCloseTo(42.74, 2);
      expect(result.totalVatAmount).toBeCloseTo(5.26, 2);
    });
    
    it('should handle transaction with explicit VAT rates', () => {
      // Créer une transaction avec des taux explicites
      const transaction = {
        id: 'tx2',
        date: '2025-04-15',
        items: [
          { id: 'item1', name: 'Produit taux standard', quantity: 1, unitPrice: 100.00, vatRate: 20.0 },
          { id: 'item2', name: 'Produit taux réduit', quantity: 1, unitPrice: 100.00, vatRate: 5.5 }
        ]
      };
      
      // Calculer la TVA
      const result = taxCalculator.calculateTransactionVAT(transaction);
      
      // Vérifier les résultats
      expect(result.totalAmountWithTax).toBe(200.00);
      expect(result.totalAmountWithoutTax).toBeCloseTo(176.30, 2);
      expect(result.totalVatAmount).toBeCloseTo(23.70, 2);
      
      // Vérifier les détails par taux
      expect(Object.keys(result.vatBreakdown).length).toBe(2);
      
      // Taux standard (20%)
      expect(result.vatBreakdown.standard.rate).toBe(20.0);
      expect(result.vatBreakdown.standard.baseAmount).toBeCloseTo(83.33, 2);
      expect(result.vatBreakdown.standard.vatAmount).toBeCloseTo(16.67, 2);
      
      // Taux réduit (5.5%)
      expect(result.vatBreakdown.reduced.rate).toBe(5.5);
      expect(result.vatBreakdown.reduced.baseAmount).toBeCloseTo(94.79, 2);
      expect(result.vatBreakdown.reduced.vatAmount).toBeCloseTo(5.21, 2);
    });
    
    it('should throw an error for invalid transaction', () => {
      // Différents cas invalides
      expect(() => taxCalculator.calculateTransactionVAT(null)).toThrow('Transaction invalide');
      expect(() => taxCalculator.calculateTransactionVAT({})).toThrow('Transaction invalide');
      expect(() => taxCalculator.calculateTransactionVAT({ id: 'tx3' })).toThrow('Transaction invalide');
      expect(() => taxCalculator.calculateTransactionVAT({ id: 'tx3', items: null })).toThrow('Transaction invalide');
    });
  });
  
  describe('generateVATReport', () => {
    it('should generate a complete VAT report for a period', async () => {
      // Configurer les mocks de données
      const salesData = {
        transactions: [
          {
            id: 'tx1',
            date: '2025-04-10',
            items: [
              { id: 'item1', quantity: 10, unitPrice: 10.00, vatRate: 20.0 },
              { id: 'item2', quantity: 5, unitPrice: 20.00, vatRate: 10.0 }
            ]
          },
          {
            id: 'tx2',
            date: '2025-04-15',
            items: [
              { id: 'item3', quantity: 3, unitPrice: 30.00, vatRate: 5.5 }
            ]
          }
        ]
      };
      
      const purchasesData = {
        purchases: [
          {
            id: 'pur1',
            invoice_date: '2025-04-05',
            supplier: 'Fournisseur 1',
            type: 'goods',
            items: [
              { id: 'pitem1', amount: 100.00, vatRate: 20.0 },
              { id: 'pitem2', amount: 50.00, vatRate: 5.5 }
            ]
          },
          {
            id: 'pur2',
            invoice_date: '2025-04-12',
            supplier: 'Fournisseur 2',
            type: 'services',
            items: [
              { id: 'pitem3', amount: 120.00, vatRate: 20.0 }
            ]
          }
        ]
      };
      
      // Configurer les mocks des fonctions
      mockDataCollector.getSalesData.mockResolvedValue(salesData);
      mockDataCollector.getExpensesData.mockResolvedValue(purchasesData);
      
      // Appeler la méthode
      const report = await taxCalculator.generateVATReport({
        startDate: '2025-04-01',
        endDate: '2025-04-30'
      });
      
      // Vérifier que les fonctions ont été appelées avec les bons paramètres
      expect(mockDataCollector.getSalesData).toHaveBeenCalledWith(expect.objectContaining({
        startDate: expect.any(Date),
        endDate: expect.any(Date)
      }));
      
      expect(mockDataCollector.getExpensesData).toHaveBeenCalledWith(expect.objectContaining({
        startDate: expect.any(Date),
        endDate: expect.any(Date)
      }));
      
      // Vérifier la structure du rapport
      expect(report).toHaveProperty('period');
      expect(report).toHaveProperty('collected');
      expect(report).toHaveProperty('deductible');
      expect(report).toHaveProperty('balance');
      expect(report).toHaveProperty('dates');
      
      // Vérifier les détails du rapport
      expect(report.period.type).toBe('month');
      expect(report.collected.totalVatAmount).toBeGreaterThan(0);
      expect(report.deductible.totalVatAmount).toBeGreaterThan(0);
      expect(report.balance.balanceDue).toBe(report.collected.totalVatAmount - report.deductible.totalVatAmount);
      
      // Vérifier les dates de déclaration
      expect(report.dates.declaration).toBeInstanceOf(Date);
      expect(report.dates.payment).toBeInstanceOf(Date);
    });
    
    it('should handle invalid date ranges', async () => {
      // Cas où la date de fin est avant la date de début
      await expect(taxCalculator.generateVATReport({
        startDate: '2025-04-30',
        endDate: '2025-04-01'
      })).rejects.toThrow('La date de fin doit être postérieure à la date de début');
    });
  });
  
  describe('_getVatRateForItem', () => {
    it('should determine correct VAT rate based on item properties', () => {
      // Tester différents cas
      
      // Item avec taux explicite
      expect(taxCalculator._getVatRateForItem({ vatRate: 15.0 })).toBe(15.0);
      
      // Item avec catégorie fiscale
      expect(taxCalculator._getVatRateForItem({ taxCategory: 'standard' })).toBe(20.0);
      expect(taxCalculator._getVatRateForItem({ taxCategory: 'reduced' })).toBe(5.5);
      
      // Item avec catégorie de produit
      expect(taxCalculator._getVatRateForItem({ category: 'food' }, 'onsite')).toBe(10.0);
      expect(taxCalculator._getVatRateForItem({ category: 'food' }, 'takeaway')).toBe(5.5);
      
      // Item avec attribut isAlcoholic
      expect(taxCalculator._getVatRateForItem({ isAlcoholic: true })).toBe(20.0);
      
      // Valeur par défaut selon le type de transaction
      expect(taxCalculator._getVatRateForItem({}, 'onsite')).toBe(10.0);
      expect(taxCalculator._getVatRateForItem({}, 'takeaway')).toBe(5.5);
    });
  });
  
  describe('checkVATConsistency', () => {
    it('should detect inconsistencies in VAT reports', () => {
      // Créer un rapport avec des incohérences
      const invalidReport = {
        collected: {
          totalVatAmount: 100.00,
          byRate: {
            standard: { vatAmount: 50.00 },
            intermediate: { vatAmount: 30.00 }
            // Total = 80.00, différence de 20.00
          }
        },
        deductible: {
          totalVatAmount: 60.00,
          byType: {
            goods: { vatAmount: 40.00 },
            services: { vatAmount: 30.00 }
            // Total = 70.00, différence de -10.00
          }
        },
        balance: {
          balanceDue: 30.00 // Devrait être 100.00 - 60.00 = 40.00
        }
      };
      
      const result = taxCalculator.checkVATConsistency(invalidReport);
      
      // Vérifier que les incohérences sont détectées
      expect(result.isConsistent).toBe(false);
      expect(result.issues.length).toBe(3);
      
      // Vérifier les détails des problèmes
      expect(result.issues[0].type).toBe('total_mismatch');
      expect(result.issues[0].entity).toBe('collected');
      expect(result.issues[0].difference).toBeCloseTo(20.00, 2);
      
      expect(result.issues[1].type).toBe('total_mismatch');
      expect(result.issues[1].entity).toBe('deductible');
      expect(result.issues[1].difference).toBeCloseTo(-10.00, 2);
      
      expect(result.issues[2].type).toBe('balance_mismatch');
      expect(result.issues[2].difference).toBeCloseTo(10.00, 2);
    });
    
    it('should validate consistent VAT reports', () => {
      // Créer un rapport cohérent
      const validReport = {
        collected: {
          totalVatAmount: 100.00,
          byRate: {
            standard: { vatAmount: 70.00 },
            intermediate: { vatAmount: 30.00 }
          }
        },
        deductible: {
          totalVatAmount: 60.00,
          byType: {
            goods: { vatAmount: 40.00 },
            services: { vatAmount: 20.00 }
          }
        },
        balance: {
          balanceDue: 40.00
        }
      };
      
      const result = taxCalculator.checkVATConsistency(validReport);
      
      // Vérifier que le rapport est validé
      expect(result.isConsistent).toBe(true);
      expect(result.issues.length).toBe(0);
    });
  });
  
  describe('_getPeriodType', () => {
    it('should correctly identify period types', () => {
      // Un mois complet
      expect(taxCalculator._getPeriodType(
        moment('2025-04-01'),
        moment('2025-04-30')
      )).toBe('month');
      
      // Un trimestre complet
      expect(taxCalculator._getPeriodType(
        moment('2025-01-01'),
        moment('2025-03-31')
      )).toBe('quarter');
      
      // Une année complète
      expect(taxCalculator._getPeriodType(
        moment('2025-01-01'),
        moment('2025-12-31')
      )).toBe('year');
      
      // Une période personnalisée
      expect(taxCalculator._getPeriodType(
        moment('2025-04-15'),
        moment('2025-05-15')
      )).toBe('custom');
    });
  });
});
