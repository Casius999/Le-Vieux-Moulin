/**
 * Module d'adaptateurs pour export vers logiciels comptables
 * 
 * Ce module fournit des adaptateurs spécifiques pour les principaux
 * logiciels de comptabilité utilisés par les professionnels.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const moment = require('moment');
const XLSX = require('xlsx');
const { Transform } = require('stream');

/**
 * Classe de base pour tous les adaptateurs de logiciels comptables
 */
class AccountingSoftwareAdapter {
  /**
   * Constructeur de la classe de base
   * @param {Object} options - Options de configuration
   * @param {Object} options.logger - Logger pour les traces
   */
  constructor(options = {}) {
    this.logger = options.logger || console;
  }
  
  /**
   * Convertit les données comptables au format spécifique
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de conversion
   * @returns {Promise<Buffer|string>} - Données converties
   */
  async convert(entries, options = {}) {
    throw new Error('Method not implemented: convert() must be implemented by subclasses');
  }
  
  /**
   * Enregistre les données dans un fichier
   * @param {Buffer|string} data - Données à enregistrer
   * @param {string} filePath - Chemin du fichier
   * @returns {Promise<string>} - Chemin du fichier enregistré
   */
  async saveToFile(data, filePath) {
    try {
      // Créer le répertoire si nécessaire
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      // Écrire le fichier
      fs.writeFileSync(filePath, data);
      
      return filePath;
    } catch (error) {
      this.logger.error('Erreur lors de l\'enregistrement du fichier', { error, filePath });
      throw error;
    }
  }
}

/**
 * Adaptateur pour le logiciel Sage
 */
class SageAdapter extends AccountingSoftwareAdapter {
  /**
   * Constructeur de l'adaptateur Sage
   * @param {Object} options - Options de configuration
   */
  constructor(options = {}) {
    super(options);
    
    // Configuration spécifique à Sage
    this.config = {
      dateFormat: 'DD/MM/YYYY',
      decimalSeparator: ',',
      exportVersion: options.exportVersion || '100',
      ...options.sageConfig
    };
  }
  
  /**
   * Convertit les données au format Sage
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de conversion
   * @param {string} options.company - Nom de l'entreprise
   * @param {string} options.period - Période comptable
   * @returns {Promise<Buffer>} - Fichier Excel compatible Sage
   */
  async convert(entries, options = {}) {
    try {
      this.logger.info('Conversion des données au format Sage', { entriesCount: entries.length });
      
      // Vérification des paramètres
      if (!entries || entries.length === 0) {
        throw new Error('Aucune écriture comptable à convertir');
      }
      
      // Transformation au format Sage
      const sageEntries = this._formatSageEntries(entries, options);
      
      // Création du fichier Excel
      const workbook = XLSX.utils.book_new();
      
      // Feuille des écritures
      const worksheet = XLSX.utils.json_to_sheet(sageEntries);
      
      // Ajout de la feuille au classeur
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Ecritures');
      
      // Conversion en buffer
      const excelBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      
      return excelBuffer;
    } catch (error) {
      this.logger.error('Erreur lors de la conversion au format Sage', error);
      throw error;
    }
  }
  
  /**
   * Formatage des écritures au format Sage
   * @private
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de formatage
   * @returns {Array} - Écritures au format Sage
   */
  _formatSageEntries(entries, options) {
    const sageEntries = [];
    
    // Créer un code journal unique pour le lot
    const batchId = `EXP${moment().format('YYMMDDHHmmss')}`;
    
    // Pour chaque écriture
    for (const entry of entries) {
      // Pour chaque mouvement (débit/crédit)
      for (const movement of entry.movements) {
        const sageEntry = {
          'Code Journal': entry.journal.code,
          'Numéro Pièce': entry.reference,
          'Date pièce': moment(entry.date).format(this.config.dateFormat),
          'Date écriture': moment(entry.entryDate || entry.date).format(this.config.dateFormat),
          'Compte général': movement.account.number,
          'Libellé compte': movement.account.name,
          'Compte tiers': movement.auxiliaryAccount?.number || '',
          'Libellé tiers': movement.auxiliaryAccount?.name || '',
          'Libellé écriture': entry.description,
          'Montant débit': movement.type === 'debit' ? this._formatAmount(movement.amount) : '0,00',
          'Montant crédit': movement.type === 'credit' ? this._formatAmount(movement.amount) : '0,00',
          'Code lettrage': entry.reconciliationMark || '',
          'Mode de règlement': entry.paymentMethod || '',
          'Échéance': entry.dueDate ? moment(entry.dueDate).format(this.config.dateFormat) : '',
          'Code devise': movement.currency || 'EUR',
          'Numéro lot': batchId
        };
        
        sageEntries.push(sageEntry);
      }
    }
    
    return sageEntries;
  }
  
  /**
   * Formatage des montants au format Sage
   * @private
   * @param {number} amount - Montant à formater
   * @returns {string} - Montant formaté
   */
  _formatAmount(amount) {
    return amount.toFixed(2).replace('.', this.config.decimalSeparator);
  }
}

/**
 * Adaptateur pour le logiciel QuickBooks
 */
class QuickBooksAdapter extends AccountingSoftwareAdapter {
  /**
   * Constructeur de l'adaptateur QuickBooks
   * @param {Object} options - Options de configuration
   */
  constructor(options = {}) {
    super(options);
    
    // Configuration spécifique à QuickBooks
    this.config = {
      dateFormat: 'MM/DD/YYYY',
      decimalSeparator: '.',
      ...options.quickBooksConfig
    };
  }
  
  /**
   * Convertit les données au format QuickBooks
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de conversion
   * @returns {Promise<string>} - Contenu CSV compatible QuickBooks
   */
  async convert(entries, options = {}) {
    try {
      this.logger.info('Conversion des données au format QuickBooks', { entriesCount: entries.length });
      
      // Vérification des paramètres
      if (!entries || entries.length === 0) {
        throw new Error('Aucune écriture comptable à convertir');
      }
      
      // Transformation au format QuickBooks
      const qbEntries = this._formatQuickBooksEntries(entries, options);
      
      // Création du contenu CSV
      let csvContent = '';
      
      // En-têtes
      const headers = Object.keys(qbEntries[0]).join(',');
      csvContent += headers + '\r\n';
      
      // Lignes
      for (const entry of qbEntries) {
        const line = Object.values(entry).map(value => {
          // Échapper les virgules et les guillemets
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }).join(',');
        csvContent += line + '\r\n';
      }
      
      return csvContent;
    } catch (error) {
      this.logger.error('Erreur lors de la conversion au format QuickBooks', error);
      throw error;
    }
  }
  
  /**
   * Formatage des écritures au format QuickBooks
   * @private
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de formatage
   * @returns {Array} - Écritures au format QuickBooks
   */
  _formatQuickBooksEntries(entries, options) {
    const qbEntries = [];
    
    // Pour chaque écriture
    for (const entry of entries) {
      // Pour chaque mouvement (débit/crédit)
      for (const movement of entry.movements) {
        const qbEntry = {
          'Journal No.': entry.entryNumber,
          'Transaction Date': moment(entry.date).format(this.config.dateFormat),
          'Document No.': entry.reference,
          'Name': movement.auxiliaryAccount?.name || '',
          'Account': movement.account.number,
          'Account Description': movement.account.name,
          'Description': entry.description,
          'Debit Amount': movement.type === 'debit' ? movement.amount.toFixed(2) : '0.00',
          'Credit Amount': movement.type === 'credit' ? movement.amount.toFixed(2) : '0.00',
          'Class': entry.costCenter || '',
          'Payee': entry.payee || '',
          'Due Date': entry.dueDate ? moment(entry.dueDate).format(this.config.dateFormat) : '',
          'Transaction Type': this._mapTransactionType(entry.type)
        };
        
        qbEntries.push(qbEntry);
      }
    }
    
    return qbEntries;
  }
  
  /**
   * Mappe les types de transaction vers les types QuickBooks
   * @private
   * @param {string} type - Type de transaction
   * @returns {string} - Type de transaction QuickBooks
   */
  _mapTransactionType(type) {
    const mapping = {
      'invoice': 'INVOICE',
      'bill': 'BILL',
      'payment': 'PAYMENT',
      'expense': 'EXPENSE',
      'journal': 'JOURNAL',
      'transfer': 'TRANSFER'
    };
    
    return mapping[type] || 'JOURNAL';
  }
}

/**
 * Adaptateur pour le logiciel Ciel Compta
 */
class CielComptaAdapter extends AccountingSoftwareAdapter {
  /**
   * Constructeur de l'adaptateur Ciel Compta
   * @param {Object} options - Options de configuration
   */
  constructor(options = {}) {
    super(options);
    
    // Configuration spécifique à Ciel Compta
    this.config = {
      dateFormat: 'DDMMYYYY',
      columnSeparator: ';',
      ...options.cielConfig
    };
  }
  
  /**
   * Convertit les données au format Ciel Compta
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de conversion
   * @returns {Promise<string>} - Contenu au format Ciel Compta
   */
  async convert(entries, options = {}) {
    try {
      this.logger.info('Conversion des données au format Ciel Compta', { entriesCount: entries.length });
      
      // Vérification des paramètres
      if (!entries || entries.length === 0) {
        throw new Error('Aucune écriture comptable à convertir');
      }
      
      // Transformation au format Ciel
      const cielEntries = this._formatCielEntries(entries, options);
      
      // Création du contenu
      let content = '';
      
      // En-tête du fichier Ciel
      content += 'IMF\r\n';
      content += `DMO;${moment().format(this.config.dateFormat)};IMPORT\r\n`;
      
      // Écritures
      for (const entry of cielEntries) {
        content += 'ECR;';
        content += Object.values(entry).join(this.config.columnSeparator);
        content += '\r\n';
      }
      
      // Pied de fichier
      content += 'FIN;\r\n';
      
      return content;
    } catch (error) {
      this.logger.error('Erreur lors de la conversion au format Ciel Compta', error);
      throw error;
    }
  }
  
  /**
   * Formatage des écritures au format Ciel Compta
   * @private
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de formatage
   * @returns {Array} - Écritures au format Ciel
   */
  _formatCielEntries(entries, options) {
    const cielEntries = [];
    
    // Pour chaque écriture
    for (const entry of entries) {
      // Pour chaque mouvement (débit/crédit)
      for (const movement of entry.movements) {
        const cielEntry = {
          'journal': entry.journal.code,
          'date': moment(entry.date).format(this.config.dateFormat),
          'compte': movement.account.number,
          'piece': entry.reference,
          'libelle': entry.description,
          'sensdc': movement.type === 'debit' ? 'D' : 'C',
          'montant': movement.amount.toFixed(2).replace('.', ','),
          'pointage': entry.reconciliationMark || '',
          'contrepart': '',
          'echeance': entry.dueDate ? moment(entry.dueDate).format(this.config.dateFormat) : '',
          'devise': movement.currency || 'EUR',
          'quantite': '',
          'codejournal2': '',
          'numero_facture': entry.invoiceNumber || ''
        };
        
        cielEntries.push(cielEntry);
      }
    }
    
    return cielEntries;
  }
}

/**
 * Adaptateur pour le logiciel EBP
 */
class EBPAdapter extends AccountingSoftwareAdapter {
  /**
   * Constructeur de l'adaptateur EBP
   * @param {Object} options - Options de configuration
   */
  constructor(options = {}) {
    super(options);
    
    // Configuration spécifique à EBP
    this.config = {
      dateFormat: 'DD/MM/YYYY',
      columnSeparator: ';',
      ...options.ebpConfig
    };
  }
  
  /**
   * Convertit les données au format EBP
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de conversion
   * @returns {Promise<string>} - Contenu CSV compatible EBP
   */
  async convert(entries, options = {}) {
    try {
      this.logger.info('Conversion des données au format EBP', { entriesCount: entries.length });
      
      // Vérification des paramètres
      if (!entries || entries.length === 0) {
        throw new Error('Aucune écriture comptable à convertir');
      }
      
      // Transformation au format EBP
      const ebpEntries = this._formatEBPEntries(entries, options);
      
      // Création du contenu CSV
      let csvContent = '';
      
      // En-têtes
      const headers = Object.keys(ebpEntries[0]).join(this.config.columnSeparator);
      csvContent += headers + '\r\n';
      
      // Lignes
      for (const entry of ebpEntries) {
        const line = Object.values(entry).map(value => {
          if (typeof value === 'string' && value.includes(this.config.columnSeparator)) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }).join(this.config.columnSeparator);
        csvContent += line + '\r\n';
      }
      
      return csvContent;
    } catch (error) {
      this.logger.error('Erreur lors de la conversion au format EBP', error);
      throw error;
    }
  }
  
  /**
   * Formatage des écritures au format EBP
   * @private
   * @param {Array} entries - Écritures comptables
   * @param {Object} options - Options de formatage
   * @returns {Array} - Écritures au format EBP
   */
  _formatEBPEntries(entries, options) {
    const ebpEntries = [];
    
    // Pour chaque écriture
    for (const entry of entries) {
      // Pour chaque mouvement (débit/crédit)
      for (const movement of entry.movements) {
        const ebpEntry = {
          'JournalCode': entry.journal.code,
          'JournalLib': entry.journal.name,
          'NumPiece': entry.reference,
          'DatePiece': moment(entry.date).format(this.config.dateFormat),
          'CompteNum': movement.account.number,
          'CompteLib': movement.account.name,
          'CompteAuxNum': movement.auxiliaryAccount?.number || '',
          'CompteAuxLib': movement.auxiliaryAccount?.name || '',
          'Libelle': entry.description,
          'Debit': movement.type === 'debit' ? movement.amount.toFixed(2).replace('.', ',') : '0,00',
          'Credit': movement.type === 'credit' ? movement.amount.toFixed(2).replace('.', ',') : '0,00',
          'CodeLettrage': entry.reconciliationMark || '',
          'DateEcheance': entry.dueDate ? moment(entry.dueDate).format(this.config.dateFormat) : '',
          'CodeDevise': movement.currency || 'EUR',
          'MontantDevise': movement.currencyAmount ? movement.currencyAmount.toFixed(2).replace('.', ',') : '',
          'Analytique': entry.costCenter || '',
          'Validee': entry.validated ? 'Oui' : 'Non'
        };
        
        ebpEntries.push(ebpEntry);
      }
    }
    
    return ebpEntries;
  }
}

// Exporter les classes
module.exports = {
  AccountingSoftwareAdapter,
  SageAdapter,
  QuickBooksAdapter,
  CielComptaAdapter,
  EBPAdapter
};
