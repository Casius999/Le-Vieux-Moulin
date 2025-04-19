/**
 * Module d'exportation au format FEC (Fichier des Écritures Comptables)
 * 
 * Ce module permet l'exportation des données comptables au format FEC
 * tel que requis par l'administration fiscale française.
 * 
 * Documentation de référence: 
 * https://www.economie.gouv.fr/dgfip/controle-fiscal-fichier-des-ecritures-comptables-fec
 */

'use strict';

const fs = require('fs');
const path = require('path');
const moment = require('moment');
const { Transform } = require('stream');
const { createObjectCsvWriter } = require('csv-writer');

/**
 * Classe pour l'exportation au format FEC
 */
class FECExporter {
  /**
   * Crée une nouvelle instance de l'exportateur FEC
   * @param {Object} options - Options de configuration
   * @param {Object} options.dataCollector - Instance du collecteur de données
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.logger - Logger pour tracer les opérations
   */
  constructor(options = {}) {
    this.dataCollector = options.dataCollector;
    this.configManager = options.configManager;
    this.logger = options.logger || console;
    
    // Charger la configuration spécifique au FEC
    this.config = this.configManager ? 
      this.configManager.getConfig('export.fec', {}) : 
      {};
    
    // Configuration par défaut
    this.defaultConfig = {
      headerFormat: 'JournalCode|JournalLib|EcritureNum|EcritureDate|CompteNum|CompteLib|CompAuxNum|CompAuxLib|PieceRef|PieceDate|EcritureLib|Debit|Credit|EcritureLet|DateLet|ValidDate|Montantdevise|Idevise',
      dateFormat: 'YYYYMMDD',
      decimalSeparator: '.',
      encoding: 'UTF-8',
      lineSeparator: '\r\n',
      columnSeparator: '|'
    };
    
    // Fusionner avec la configuration par défaut
    this.config = { ...this.defaultConfig, ...this.config };
  }
  
  /**
   * Génère un fichier FEC pour une période donnée
   * @param {Object} options - Options d'exportation
   * @param {Date} options.startDate - Date de début de la période
   * @param {Date} options.endDate - Date de fin de la période
   * @param {string} options.outputPath - Chemin du fichier de sortie
   * @param {Object} options.companyInfo - Informations sur l'entreprise
   * @param {string} options.companyInfo.siren - Numéro SIREN de l'entreprise
   * @param {string} options.companyInfo.name - Raison sociale
   * @returns {Promise<string>} - Chemin du fichier généré
   */
  async generateFEC(options) {
    try {
      this.logger.info('Début de génération du fichier FEC', options);
      
      const { startDate, endDate, outputPath, companyInfo } = options;
      
      // Validation des paramètres obligatoires
      if (!startDate || !endDate) {
        throw new Error('Les dates de début et de fin sont obligatoires');
      }
      
      if (!companyInfo || !companyInfo.siren) {
        throw new Error('Les informations de l\'entreprise sont obligatoires');
      }
      
      // Formatage du nom de fichier si non spécifié
      const finalOutputPath = outputPath || this._generateDefaultFilename(startDate, endDate, companyInfo);
      
      // Récupérer les écritures comptables
      const entries = await this._getAccountingEntries(startDate, endDate);
      
      if (!entries || entries.length === 0) {
        this.logger.warn('Aucune écriture comptable trouvée pour la période', { startDate, endDate });
        throw new Error('Aucune écriture comptable trouvée pour la période spécifiée');
      }
      
      // Transforme les écritures au format FEC
      const fecEntries = this._transformToFEC(entries, companyInfo);
      
      // Écrire le fichier
      await this._writeToFile(fecEntries, finalOutputPath);
      
      this.logger.info('Fichier FEC généré avec succès', { path: finalOutputPath, entryCount: fecEntries.length });
      
      return finalOutputPath;
    } catch (error) {
      this.logger.error('Erreur lors de la génération du fichier FEC', error);
      throw error;
    }
  }
  
  /**
   * Génère un nom de fichier par défaut selon les normes FEC
   * @private
   * @param {Date} startDate - Date de début
   * @param {Date} endDate - Date de fin
   * @param {Object} companyInfo - Informations de l'entreprise
   * @returns {string} - Nom de fichier FEC
   */
  _generateDefaultFilename(startDate, endDate, companyInfo) {
    const siren = companyInfo.siren.replace(/\s/g, '');
    const startYear = moment(startDate).format('YYYY');
    const endYear = moment(endDate).format('YYYY');
    
    // Format: SIREN_FEC_YYYYMMDD_YYYYMMDD.txt
    return path.join(
      this.config.outputDir || './export',
      `${siren}_FEC_${moment(startDate).format('YYYYMMDD')}_${moment(endDate).format('YYYYMMDD')}.txt`
    );
  }
  
  /**
   * Récupère les écritures comptables de la période
   * @private
   * @param {Date} startDate - Date de début
   * @param {Date} endDate - Date de fin
   * @returns {Promise<Array>} - Écritures comptables
   */
  async _getAccountingEntries(startDate, endDate) {
    try {
      // Utiliser le collecteur de données pour récupérer les écritures
      const entries = await this.dataCollector.getAccountingEntries({
        startDate,
        endDate,
        includeDetails: true,
        status: 'validated' // Ne prendre que les écritures validées
      });
      
      return entries;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des écritures comptables', error);
      throw error;
    }
  }
  
  /**
   * Transforme les écritures comptables au format FEC
   * @private
   * @param {Array} entries - Écritures comptables
   * @param {Object} companyInfo - Informations de l'entreprise
   * @returns {Array} - Écritures au format FEC
   */
  _transformToFEC(entries, companyInfo) {
    try {
      const fecEntries = [];
      
      // Formatage des écritures
      for (const entry of entries) {
        // Pour chaque mouvement (débit/crédit)
        for (const movement of entry.movements) {
          const fecEntry = {
            JournalCode: entry.journal.code,
            JournalLib: entry.journal.name,
            EcritureNum: entry.entryNumber,
            EcritureDate: moment(entry.date).format(this.config.dateFormat),
            CompteNum: movement.account.number,
            CompteLib: movement.account.name,
            CompAuxNum: movement.auxiliaryAccount?.number || '',
            CompAuxLib: movement.auxiliaryAccount?.name || '',
            PieceRef: entry.reference,
            PieceDate: moment(entry.documentDate || entry.date).format(this.config.dateFormat),
            EcritureLib: entry.description,
            Debit: movement.type === 'debit' ? this._formatAmount(movement.amount) : '0.00',
            Credit: movement.type === 'credit' ? this._formatAmount(movement.amount) : '0.00',
            EcritureLet: entry.reconciliationMark || '',
            DateLet: entry.reconciliationDate ? moment(entry.reconciliationDate).format(this.config.dateFormat) : '',
            ValidDate: moment(entry.validationDate || entry.date).format(this.config.dateFormat),
            Montantdevise: movement.currencyAmount ? this._formatAmount(movement.currencyAmount) : '',
            Idevise: movement.currency || ''
          };
          
          fecEntries.push(fecEntry);
        }
      }
      
      return fecEntries;
    } catch (error) {
      this.logger.error('Erreur lors de la transformation des écritures au format FEC', error);
      throw error;
    }
  }
  
  /**
   * Formate un montant selon les règles FEC
   * @private
   * @param {number} amount - Montant à formater
   * @returns {string} - Montant formaté
   */
  _formatAmount(amount) {
    // FEC attend un nombre avec 2 décimales et un point comme séparateur
    return amount.toFixed(2).replace(',', this.config.decimalSeparator);
  }
  
  /**
   * Écrit les données au format FEC dans un fichier
   * @private
   * @param {Array} entries - Écritures au format FEC
   * @param {string} filePath - Chemin du fichier de sortie
   * @returns {Promise<void>}
   */
  async _writeToFile(entries, filePath) {
    try {
      // Créer le répertoire s'il n'existe pas
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      // Configuration du writer CSV
      const csvWriter = createObjectCsvWriter({
        path: filePath,
        header: this.config.headerFormat.split('|').map(id => ({ id, title: id })),
        fieldDelimiter: this.config.columnSeparator,
        recordDelimiter: this.config.lineSeparator,
        encoding: this.config.encoding
      });
      
      // Écrire les données
      await csvWriter.writeRecords(entries);
      
      // Vérification du fichier
      if (!fs.existsSync(filePath)) {
        throw new Error(`Le fichier FEC n'a pas été créé: ${filePath}`);
      }
      
      return filePath;
    } catch (error) {
      this.logger.error('Erreur lors de l\'écriture du fichier FEC', error);
      throw error;
    }
  }
  
  /**
   * Valide un fichier FEC selon les règles de l'administration fiscale
   * @param {string} filePath - Chemin du fichier FEC à valider
   * @returns {Promise<Object>} - Résultats de la validation
   */
  async validateFEC(filePath) {
    try {
      this.logger.info('Validation du fichier FEC', { filePath });
      
      if (!fs.existsSync(filePath)) {
        throw new Error(`Le fichier FEC n'existe pas: ${filePath}`);
      }
      
      // Lecture du fichier
      const fileContent = fs.readFileSync(filePath, this.config.encoding);
      const lines = fileContent.split(this.config.lineSeparator);
      
      // Vérifications de base
      const validationResults = {
        isValid: true,
        errors: [],
        warnings: [],
        stats: {
          totalLines: lines.length,
          headerValid: false,
          balanceCheck: {
            totalDebit: 0,
            totalCredit: 0,
            isBalanced: false
          }
        }
      };
      
      // Vérifier l'en-tête
      const expectedHeader = this.config.headerFormat;
      const actualHeader = lines[0].trim();
      
      if (actualHeader !== expectedHeader) {
        validationResults.isValid = false;
        validationResults.errors.push({
          type: 'header_mismatch',
          message: 'L\'en-tête du fichier ne correspond pas au format attendu',
          expected: expectedHeader,
          actual: actualHeader
        });
      } else {
        validationResults.stats.headerValid = true;
      }
      
      // Vérifier la balance débit/crédit
      let totalDebit = 0;
      let totalCredit = 0;
      
      for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;
        
        const columns = lines[i].split(this.config.columnSeparator);
        
        // Vérifier le nombre de colonnes
        if (columns.length !== expectedHeader.split(this.config.columnSeparator).length) {
          validationResults.isValid = false;
          validationResults.errors.push({
            type: 'column_count_mismatch',
            message: `Ligne ${i+1}: Le nombre de colonnes ne correspond pas à l'en-tête`,
            expected: expectedHeader.split(this.config.columnSeparator).length,
            actual: columns.length
          });
          continue;
        }
        
        // Vérifier le débit et crédit
        const debitIndex = expectedHeader.split(this.config.columnSeparator).indexOf('Debit');
        const creditIndex = expectedHeader.split(this.config.columnSeparator).indexOf('Credit');
        
        const debit = parseFloat(columns[debitIndex].replace(this.config.decimalSeparator, '.'));
        const credit = parseFloat(columns[creditIndex].replace(this.config.decimalSeparator, '.'));
        
        if (isNaN(debit)) {
          validationResults.warnings.push({
            type: 'invalid_debit',
            message: `Ligne ${i+1}: Valeur débit non numérique`,
            value: columns[debitIndex]
          });
        } else {
          totalDebit += debit;
        }
        
        if (isNaN(credit)) {
          validationResults.warnings.push({
            type: 'invalid_credit',
            message: `Ligne ${i+1}: Valeur crédit non numérique`,
            value: columns[creditIndex]
          });
        } else {
          totalCredit += credit;
        }
      }
      
      // Arrondir à 2 décimales pour éviter les problèmes de précision
      totalDebit = Math.round(totalDebit * 100) / 100;
      totalCredit = Math.round(totalCredit * 100) / 100;
      
      validationResults.stats.balanceCheck.totalDebit = totalDebit;
      validationResults.stats.balanceCheck.totalCredit = totalCredit;
      
      // Vérifier l'équilibre débit/crédit
      if (totalDebit !== totalCredit) {
        validationResults.isValid = false;
        validationResults.errors.push({
          type: 'unbalanced_debits_credits',
          message: 'Le total des débits et crédits ne sont pas équilibrés',
          totalDebit,
          totalCredit,
          difference: Math.abs(totalDebit - totalCredit)
        });
      } else {
        validationResults.stats.balanceCheck.isBalanced = true;
      }
      
      this.logger.info('Validation du fichier FEC terminée', validationResults);
      
      return validationResults;
    } catch (error) {
      this.logger.error('Erreur lors de la validation du fichier FEC', error);
      throw error;
    }
  }
}

module.exports = FECExporter;
