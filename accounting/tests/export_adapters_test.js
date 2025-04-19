/**
 * Tests d'intégration pour les adaptateurs d'export comptable
 * 
 * Ce fichier contient les tests permettant de vérifier le bon fonctionnement
 * des adaptateurs d'export vers les différents logiciels comptables.
 */

'use strict';

const assert = require('assert');
const path = require('path');
const fs = require('fs');
const os = require('os');
const XLSX = require('xlsx');

const {
  AccountingSoftwareAdapter,
  SageAdapter,
  QuickBooksAdapter,
  CielComptaAdapter,
  EBPAdapter
} = require('../export/accounting_software_adapters');

const FECExporter = require('../export/fec_exporter');

// Données fictives pour les tests
const mockAccountingEntries = [
  {
    entryNumber: 'JRN-001',
    date: new Date('2025-04-01'),
    entryDate: new Date('2025-04-01'),
    documentDate: new Date('2025-03-31'),
    reference: 'FACT-2025-042',
    description: 'Vente de marchandises',
    type: 'invoice',
    journal: {
      code: 'VT',
      name: 'Journal des ventes'
    },
    validated: true,
    validationDate: new Date('2025-04-01'),
    reconciliationMark: '',
    reconciliationDate: null,
    movements: [
      {
        account: {
          number: '411000',
          name: 'Clients'
        },
        auxiliaryAccount: {
          number: 'CLI001',
          name: 'Restaurant du Port'
        },
        type: 'debit',
        amount: 1200,
        currency: 'EUR',
        currencyAmount: 1200
      },
      {
        account: {
          number: '707100',
          name: 'Ventes de produits finis'
        },
        type: 'credit',
        amount: 1000,
        currency: 'EUR',
        currencyAmount: 1000
      },
      {
        account: {
          number: '445710',
          name: 'TVA collectée'
        },
        type: 'credit',
        amount: 200,
        currency: 'EUR',
        currencyAmount: 200
      }
    ]
  },
  {
    entryNumber: 'JRN-002',
    date: new Date('2025-04-02'),
    entryDate: new Date('2025-04-02'),
    documentDate: new Date('2025-04-02'),
    reference: 'BNQ-2025-042',
    description: 'Règlement fournisseur',
    type: 'payment',
    journal: {
      code: 'BQ',
      name: 'Journal de banque'
    },
    validated: true,
    validationDate: new Date('2025-04-02'),
    reconciliationMark: 'R042',
    reconciliationDate: new Date('2025-04-10'),
    movements: [
      {
        account: {
          number: '401000',
          name: 'Fournisseurs'
        },
        auxiliaryAccount: {
          number: 'FOUR002',
          name: 'Moulin des farines'
        },
        type: 'debit',
        amount: 850,
        currency: 'EUR',
        currencyAmount: 850
      },
      {
        account: {
          number: '512000',
          name: 'Banque'
        },
        type: 'credit',
        amount: 850,
        currency: 'EUR',
        currencyAmount: 850
      }
    ]
  }
];

// Fonctions utilitaires pour les tests
function createTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'export-tests-'));
}

function deleteTempDir(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

// Mock du logger pour les tests
const mockLogger = {
  info: () => {},
  warn: () => {},
  error: () => {},
  debug: () => {}
};

// Mock data collector
const mockDataCollector = {
  getAccountingEntries: async () => {
    return mockAccountingEntries;
  }
};

// Mock config manager
const mockConfigManager = {
  getConfig: () => {
    return {};
  }
};

// Tests de l'adaptateur Sage
describe('SageAdapter', function() {
  let tempDir;
  let sageAdapter;
  
  before(function() {
    tempDir = createTempDir();
    sageAdapter = new SageAdapter({
      logger: mockLogger,
      sageConfig: {
        dateFormat: 'DD/MM/YYYY',
        decimalSeparator: ','
      }
    });
  });
  
  after(function() {
    deleteTempDir(tempDir);
  });
  
  it('should convert accounting entries to Sage format', async function() {
    // Conversion des données
    const excelBuffer = await sageAdapter.convert(mockAccountingEntries, {
      company: 'Le Vieux Moulin',
      period: 'Avril 2025'
    });
    
    // Vérifier que le buffer est créé
    assert.ok(excelBuffer instanceof Buffer, 'Should return a Buffer');
    assert.ok(excelBuffer.length > 0, 'Buffer should not be empty');
    
    // Enregistrer temporairement pour vérifier le contenu
    const filePath = path.join(tempDir, 'sage_export.xlsx');
    await sageAdapter.saveToFile(excelBuffer, filePath);
    
    // Vérifier que le fichier existe
    assert.ok(fs.existsSync(filePath), 'File should exist');
    
    // Lire le fichier Excel pour vérifier son contenu
    const workbook = XLSX.readFile(filePath);
    assert.ok(workbook.SheetNames.includes('Ecritures'), 'Should have a sheet named Ecritures');
    
    const worksheet = workbook.Sheets['Ecritures'];
    const data = XLSX.utils.sheet_to_json(worksheet);
    
    // Vérifier que toutes les entrées ont été converties
    assert.equal(data.length, mockAccountingEntries.reduce((count, entry) => count + entry.movements.length, 0), 
      'Should have one row per movement');
    
    // Vérifier les colonnes essentielles
    const firstRow = data[0];
    assert.ok(firstRow['Code Journal'], 'Should have Code Journal column');
    assert.ok(firstRow['Numéro Pièce'], 'Should have Numéro Pièce column');
    assert.ok(firstRow['Date pièce'], 'Should have Date pièce column');
    assert.ok(firstRow['Compte général'], 'Should have Compte général column');
    assert.ok(firstRow['Libellé écriture'], 'Should have Libellé écriture column');
    assert.ok(firstRow['Montant débit'] !== undefined, 'Should have Montant débit column');
    assert.ok(firstRow['Montant crédit'] !== undefined, 'Should have Montant crédit column');
  });
});

// Tests de l'adaptateur QuickBooks
describe('QuickBooksAdapter', function() {
  let tempDir;
  let qbAdapter;
  
  before(function() {
    tempDir = createTempDir();
    qbAdapter = new QuickBooksAdapter({
      logger: mockLogger,
      quickBooksConfig: {
        dateFormat: 'MM/DD/YYYY',
        decimalSeparator: '.'
      }
    });
  });
  
  after(function() {
    deleteTempDir(tempDir);
  });
  
  it('should convert accounting entries to QuickBooks format', async function() {
    // Conversion des données
    const csvContent = await qbAdapter.convert(mockAccountingEntries, {
      company: 'Le Vieux Moulin',
      period: 'April 2025'
    });
    
    // Vérifier que le contenu CSV est créé
    assert.ok(typeof csvContent === 'string', 'Should return a string');
    assert.ok(csvContent.length > 0, 'Content should not be empty');
    
    // Enregistrer temporairement pour vérifier le contenu
    const filePath = path.join(tempDir, 'quickbooks_export.csv');
    await qbAdapter.saveToFile(csvContent, filePath);
    
    // Vérifier que le fichier existe
    assert.ok(fs.existsSync(filePath), 'File should exist');
    
    // Lire le fichier CSV pour vérifier son contenu
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const lines = fileContent.split('\r\n').filter(line => line.trim());
    
    // Vérifier l'en-tête et le nombre de lignes
    assert.ok(lines.length > 1, 'Should have header and data rows');
    
    // Vérifier que le nombre de lignes correspond au nombre de mouvements
    assert.equal(lines.length - 1, mockAccountingEntries.reduce((count, entry) => count + entry.movements.length, 0), 
      'Should have one row per movement plus header');
    
    // Vérifier les en-têtes essentiels
    const headers = lines[0].split(',');
    assert.ok(headers.includes('Journal No.'), 'Should have Journal No. column');
    assert.ok(headers.includes('Transaction Date'), 'Should have Transaction Date column');
    assert.ok(headers.includes('Document No.'), 'Should have Document No. column');
    assert.ok(headers.includes('Account'), 'Should have Account column');
    assert.ok(headers.includes('Description'), 'Should have Description column');
    assert.ok(headers.includes('Debit Amount'), 'Should have Debit Amount column');
    assert.ok(headers.includes('Credit Amount'), 'Should have Credit Amount column');
  });
});

// Tests de l'adaptateur Ciel Compta
describe('CielComptaAdapter', function() {
  let tempDir;
  let cielAdapter;
  
  before(function() {
    tempDir = createTempDir();
    cielAdapter = new CielComptaAdapter({
      logger: mockLogger,
      cielConfig: {
        dateFormat: 'DDMMYYYY',
        columnSeparator: ';'
      }
    });
  });
  
  after(function() {
    deleteTempDir(tempDir);
  });
  
  it('should convert accounting entries to Ciel Compta format', async function() {
    // Conversion des données
    const content = await cielAdapter.convert(mockAccountingEntries, {
      company: 'Le Vieux Moulin',
      period: 'Avril 2025'
    });
    
    // Vérifier que le contenu est créé
    assert.ok(typeof content === 'string', 'Should return a string');
    assert.ok(content.length > 0, 'Content should not be empty');
    
    // Enregistrer temporairement pour vérifier le contenu
    const filePath = path.join(tempDir, 'ciel_export.txt');
    await cielAdapter.saveToFile(content, filePath);
    
    // Vérifier que le fichier existe
    assert.ok(fs.existsSync(filePath), 'File should exist');
    
    // Lire le fichier pour vérifier son contenu
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const lines = fileContent.split('\r\n').filter(line => line.trim());
    
    // Vérifier la structure du fichier Ciel
    assert.equal(lines[0], 'IMF', 'Should start with IMF');
    assert.ok(lines[1].startsWith('DMO;'), 'Should have DMO line');
    
    // Compter les lignes d'écritures
    const ecrLines = lines.filter(line => line.startsWith('ECR;'));
    assert.equal(ecrLines.length, mockAccountingEntries.reduce((count, entry) => count + entry.movements.length, 0), 
      'Should have one ECR line per movement');
    
    // Vérifier la fin du fichier
    assert.equal(lines[lines.length - 1], 'FIN;', 'Should end with FIN;');
  });
});

// Tests de l'adaptateur EBP
describe('EBPAdapter', function() {
  let tempDir;
  let ebpAdapter;
  
  before(function() {
    tempDir = createTempDir();
    ebpAdapter = new EBPAdapter({
      logger: mockLogger,
      ebpConfig: {
        dateFormat: 'DD/MM/YYYY',
        columnSeparator: ';'
      }
    });
  });
  
  after(function() {
    deleteTempDir(tempDir);
  });
  
  it('should convert accounting entries to EBP format', async function() {
    // Conversion des données
    const csvContent = await ebpAdapter.convert(mockAccountingEntries, {
      company: 'Le Vieux Moulin',
      period: 'Avril 2025'
    });
    
    // Vérifier que le contenu CSV est créé
    assert.ok(typeof csvContent === 'string', 'Should return a string');
    assert.ok(csvContent.length > 0, 'Content should not be empty');
    
    // Enregistrer temporairement pour vérifier le contenu
    const filePath = path.join(tempDir, 'ebp_export.csv');
    await ebpAdapter.saveToFile(csvContent, filePath);
    
    // Vérifier que le fichier existe
    assert.ok(fs.existsSync(filePath), 'File should exist');
    
    // Lire le fichier CSV pour vérifier son contenu
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const lines = fileContent.split('\r\n').filter(line => line.trim());
    
    // Vérifier l'en-tête et le nombre de lignes
    assert.ok(lines.length > 1, 'Should have header and data rows');
    
    // Vérifier que le nombre de lignes correspond au nombre de mouvements
    assert.equal(lines.length - 1, mockAccountingEntries.reduce((count, entry) => count + entry.movements.length, 0), 
      'Should have one row per movement plus header');
    
    // Vérifier les en-têtes essentiels en séparant par le séparateur de colonnes
    const headers = lines[0].split(';');
    assert.ok(headers.includes('JournalCode'), 'Should have JournalCode column');
    assert.ok(headers.includes('NumPiece'), 'Should have NumPiece column');
    assert.ok(headers.includes('DatePiece'), 'Should have DatePiece column');
    assert.ok(headers.includes('CompteNum'), 'Should have CompteNum column');
    assert.ok(headers.includes('Libelle'), 'Should have Libelle column');
    assert.ok(headers.includes('Debit'), 'Should have Debit column');
    assert.ok(headers.includes('Credit'), 'Should have Credit column');
  });
});

// Tests de l'exportateur FEC
describe('FECExporter', function() {
  let tempDir;
  let fecExporter;
  
  before(function() {
    tempDir = createTempDir();
    fecExporter = new FECExporter({
      dataCollector: mockDataCollector,
      configManager: mockConfigManager,
      logger: mockLogger
    });
  });
  
  after(function() {
    deleteTempDir(tempDir);
  });
  
  it('should generate a valid FEC file', async function() {
    // Configurer la période et les informations de l'entreprise
    const options = {
      startDate: new Date('2025-04-01'),
      endDate: new Date('2025-04-30'),
      outputPath: path.join(tempDir, 'fec_export.txt'),
      companyInfo: {
        name: 'Le Vieux Moulin',
        siren: '12345678901234',
        address: 'Camping 3 étoiles, Vensac, Gironde',
        vat_number: 'FR12345678901'
      }
    };
    
    // Simuler la méthode _getAccountingEntries pour utiliser les données de test
    fecExporter._getAccountingEntries = async () => mockAccountingEntries;
    
    // Générer le fichier FEC
    const filePath = await fecExporter.generateFEC(options);
    
    // Vérifier que le fichier existe
    assert.ok(fs.existsSync(filePath), 'FEC file should exist');
    
    // Lire le fichier pour vérifier son contenu
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const lines = fileContent.split('\r\n').filter(line => line.trim());
    
    // Vérifier l'en-tête
    const headers = lines[0].split('|');
    assert.ok(headers.includes('JournalCode'), 'Should have JournalCode column');
    assert.ok(headers.includes('EcritureDate'), 'Should have EcritureDate column');
    assert.ok(headers.includes('CompteNum'), 'Should have CompteNum column');
    assert.ok(headers.includes('EcritureLib'), 'Should have EcritureLib column');
    assert.ok(headers.includes('Debit'), 'Should have Debit column');
    assert.ok(headers.includes('Credit'), 'Should have Credit column');
    
    // Vérifier le nombre de lignes (une par mouvement + en-tête)
    assert.equal(lines.length, mockAccountingEntries.reduce((count, entry) => count + entry.movements.length, 0) + 1, 
      'Should have one row per movement plus header');
    
    // Valider le fichier FEC avec la méthode de validation
    const validationResult = await fecExporter.validateFEC(filePath);
    assert.ok(validationResult.isValid, 'FEC file should be valid');
    assert.ok(validationResult.stats.headerValid, 'FEC header should be valid');
    assert.ok(validationResult.stats.balanceCheck.isBalanced, 'FEC debits and credits should be balanced');
  });
});
