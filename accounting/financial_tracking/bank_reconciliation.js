/**
 * Module de réconciliation bancaire pour le restaurant "Le Vieux Moulin"
 * Automatise le rapprochement entre les transactions enregistrées dans le système
 * et les opérations bancaires réelles.
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const moment = require('moment');
const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const csvParse = require('csv-parse/lib/sync');

/**
 * Classe de réconciliation bancaire automatique
 * @extends EventEmitter
 */
class BankReconciliation extends EventEmitter {
  /**
   * Crée une instance du module de réconciliation bancaire
   * @param {Object} options - Options de configuration
   * @param {Object} options.configManager - Gestionnaire de configuration
   * @param {Object} options.dataCollector - Collecteur de données
   * @param {Object} [options.securityUtils] - Utilitaires de sécurité
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    this.configManager = options.configManager;
    this.dataCollector = options.dataCollector;
    this.securityUtils = options.securityUtils;
    this.logger = options.logger || console;
    
    // Charger la configuration
    this.config = this._loadConfig();
    
    this.logger.debug('BankReconciliation initialisé');
  }
  
  /**
   * Charge la configuration pour la réconciliation bancaire
   * @returns {Object} Configuration
   * @private
   */
  _loadConfig() {
    if (this.configManager) {
      const bankConfig = this.configManager.getConfig('bank_reconciliation');
      if (bankConfig) {
        return bankConfig;
      }
    }
    
    // Configuration par défaut
    return {
      matchingThreshold: 0.85,            // Seuil de correspondance pour le matching automatique
      amountTolerance: 0.01,              // Tolérance d'arrondi pour les montants (en %)
      dateTolerance: 3,                   // Tolérance de date (en jours)
      enableFuzzyMatching: true,          // Activer la correspondance floue
      autoMatchExactAmount: true,         // Correspondance automatique pour montants exacts
      bankFormats: {
        default: {
          delimiter: ',',
          dateFormat: 'DD/MM/YYYY',
          mapping: {
            date: 0,
            description: 1,
            amount: 2,
            reference: 3
          },
          amountMultiplier: 1,            // Pour convertir en € si nécessaire
          creditIndicator: '',            // Indicateur de crédit
          debitIndicator: '-'             // Indicateur de débit
        }
      },
      archivePath: './data/bank_reconciliation/archives'
    };
  }
  
  /**
   * Importe un relevé bancaire depuis un fichier
   * @param {Object} options - Options d'import
   * @param {string} options.filePath - Chemin du fichier à importer
   * @param {string} [options.format='default'] - Format du relevé (correspond à une clé dans bankFormats)
   * @param {Date} [options.startDate] - Date de début pour l'import
   * @param {Date} [options.endDate] - Date de fin pour l'import
   * @returns {Promise<Object>} Données du relevé importé
   */
  async importBankStatement({ filePath, format = 'default', startDate, endDate }) {
    this.logger.debug(`Import du relevé bancaire depuis ${filePath} (format: ${format})`);
    
    try {
      // Vérifier que le format est supporté
      if (!this.config.bankFormats[format]) {
        throw new Error(`Format de relevé bancaire non supporté: ${format}`);
      }
      
      const formatConfig = this.config.bankFormats[format];
      
      // Lire le fichier
      const fileContent = await fs.readFile(filePath, 'utf8');
      
      // Traiter le fichier selon son format
      let bankTransactions;
      
      if (path.extname(filePath).toLowerCase() === '.csv') {
        // Analyser le CSV
        bankTransactions = this._parseCsvBankStatement(fileContent, formatConfig);
      } else {
        throw new Error(`Type de fichier non supporté: ${path.extname(filePath)}`);
      }
      
      // Filtrer par date si nécessaire
      if (startDate || endDate) {
        bankTransactions = bankTransactions.filter(transaction => {
          if (startDate && transaction.date < startDate) return false;
          if (endDate && transaction.date > endDate) return false;
          return true;
        });
      }
      
      // Générer un identifiant unique pour ce relevé
      const statementId = uuidv4();
      
      // Créer l'objet de relevé
      const bankStatement = {
        id: statementId,
        source: filePath,
        format,
        importDate: new Date(),
        periodStart: startDate || (bankTransactions.length > 0 ? 
          bankTransactions.reduce((min, t) => t.date < min ? t.date : min, bankTransactions[0].date) : 
          null),
        periodEnd: endDate || (bankTransactions.length > 0 ? 
          bankTransactions.reduce((max, t) => t.date > max ? t.date : max, bankTransactions[0].date) : 
          null),
        transactionCount: bankTransactions.length,
        totalCredit: bankTransactions.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0),
        totalDebit: bankTransactions.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0),
        transactions: bankTransactions
      };
      
      // Émettre un événement d'import réussi
      this.emit('import:success', {
        statementId,
        transactionCount: bankTransactions.length,
        source: filePath
      });
      
      return bankStatement;
    } catch (error) {
      this.logger.error(`Erreur lors de l'import du relevé bancaire depuis ${filePath}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('import:error', {
        source: filePath,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Récupère les transactions du système pour la réconciliation
   * @param {Object} options - Options de récupération
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Array>} Transactions du système
   */
  async getSystemTransactions({ startDate, endDate }) {
    this.logger.debug(`Récupération des transactions du système du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Utiliser le collecteur de données pour récupérer les transactions
      const transactions = await this.dataCollector.getTransactions({
        startDate,
        endDate,
        includePaymentDetails: true
      });
      
      // Filtrer et formater les transactions pour la réconciliation
      const systemTransactions = transactions
        .filter(transaction => {
          // Ne garder que les transactions avec un paiement électronique (CB, virement)
          return transaction.paymentMethod && 
                ['credit_card', 'bank_transfer', 'check'].includes(transaction.paymentMethod.type);
        })
        .map(transaction => ({
          id: transaction.id,
          date: new Date(transaction.date),
          amount: transaction.paymentMethod.type === 'credit_card' ? 
            transaction.total : // Pour les CB, le montant est positif (crédit pour le restaurant)
            -transaction.total, // Pour les virements sortants et chèques, le montant est négatif (débit)
          description: transaction.description || `Ticket #${transaction.id}`,
          reference: transaction.paymentMethod.reference || null,
          paymentMethod: transaction.paymentMethod.type,
          reconciled: false,
          reconciledWith: null
        }));
      
      return systemTransactions;
    } catch (error) {
      this.logger.error('Erreur lors de la récupération des transactions du système:', error);
      throw error;
    }
  }
  
  /**
   * Effectue la réconciliation entre les transactions bancaires et les transactions du système
   * @param {Object} options - Options de réconciliation
   * @param {Object} options.bankStatement - Relevé bancaire
   * @param {Array} options.systemTransactions - Transactions du système
   * @param {Object} [options.settings] - Paramètres de réconciliation (remplace ceux par défaut)
   * @returns {Promise<Object>} Résultats de la réconciliation
   */
  async reconcile({ bankStatement, systemTransactions, settings = {} }) {
    this.logger.debug(`Début de la réconciliation pour le relevé ${bankStatement.id}`);
    
    try {
      // Fusionner les paramètres avec ceux par défaut
      const reconcileSettings = {
        ...this.config,
        ...settings
      };
      
      // Préparer les variables pour les résultats
      const matches = [];
      const unmatchedBank = [];
      const unmatchedSystem = [];
      
      // Copier les transactions pour éviter de modifier les originaux
      const bankTransactions = [...bankStatement.transactions];
      const sysTransactions = [...systemTransactions];
      
      // Phase 1: Correspondance exacte sur montant, date et référence
      if (reconcileSettings.autoMatchExactAmount) {
        this._doExactMatching(bankTransactions, sysTransactions, matches, reconcileSettings);
      }
      
      // Phase 2: Correspondance floue sur le reste
      if (reconcileSettings.enableFuzzyMatching) {
        this._doFuzzyMatching(bankTransactions, sysTransactions, matches, reconcileSettings);
      }
      
      // Les transactions restantes sont non réconciliées
      bankTransactions.forEach(transaction => unmatchedBank.push(transaction));
      sysTransactions.forEach(transaction => unmatchedSystem.push(transaction));
      
      // Construire le résultat de la réconciliation
      const reconciliationResult = {
        statementId: bankStatement.id,
        date: new Date(),
        periodStart: bankStatement.periodStart,
        periodEnd: bankStatement.periodEnd,
        matches,
        unmatchedBank,
        unmatchedSystem,
        summary: {
          totalTransactions: bankStatement.transactionCount + systemTransactions.length,
          matchedTransactions: matches.length * 2,
          unmatchedBankTransactions: unmatchedBank.length,
          unmatchedSystemTransactions: unmatchedSystem.length,
          matchPercentage: (matches.length * 2) / (bankStatement.transactionCount + systemTransactions.length) * 100
        }
      };
      
      // Émettre un événement de réconciliation terminée
      this.emit('reconciliation:complete', {
        statementId: bankStatement.id,
        matchCount: matches.length,
        unmatchedBankCount: unmatchedBank.length,
        unmatchedSystemCount: unmatchedSystem.length,
        matchPercentage: reconciliationResult.summary.matchPercentage
      });
      
      return reconciliationResult;
    } catch (error) {
      this.logger.error(`Erreur lors de la réconciliation pour le relevé ${bankStatement.id}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('reconciliation:error', {
        statementId: bankStatement.id,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Génère un rapport de réconciliation
   * @param {Object} options - Options de rapport
   * @param {Object} options.reconciliationResult - Résultat de réconciliation
   * @param {string} options.format - Format du rapport ('csv', 'excel', 'pdf', 'json')
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<string>} Chemin du fichier généré
   */
  async generateReconciliationReport({ reconciliationResult, format, outputPath }) {
    this.logger.debug(`Génération du rapport de réconciliation au format ${format}`);
    
    try {
      // Sélectionner la méthode d'export en fonction du format
      let exportFunction;
      
      switch (format.toLowerCase()) {
        case 'csv':
          exportFunction = this._exportReportToCSV;
          break;
        case 'excel':
          exportFunction = this._exportReportToExcel;
          break;
        case 'pdf':
          exportFunction = this._exportReportToPDF;
          break;
        case 'json':
          exportFunction = this._exportReportToJSON;
          break;
        default:
          throw new Error(`Format de rapport non pris en charge: ${format}`);
      }
      
      // Effectuer l'export
      await exportFunction.call(this, { reconciliationResult, outputPath });
      
      // Émettre un événement de génération terminée
      this.emit('report:complete', {
        statementId: reconciliationResult.statementId,
        format,
        path: outputPath
      });
      
      return outputPath;
    } catch (error) {
      this.logger.error(`Erreur lors de la génération du rapport de réconciliation au format ${format}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('report:error', {
        statementId: reconciliationResult.statementId,
        format,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Valide et finalise une réconciliation
   * @param {Object} options - Options de finalisation
   * @param {Object} options.reconciliationResult - Résultat de réconciliation
   * @param {boolean} [options.autoApprove=false] - Approuver automatiquement les correspondances
   * @param {Array} [options.manualMatches=[]] - Correspondances manuelles à ajouter
   * @returns {Promise<Object>} Résultat finalisé
   */
  async finalizeReconciliation({ reconciliationResult, autoApprove = false, manualMatches = [] }) {
    this.logger.debug(`Finalisation de la réconciliation pour le relevé ${reconciliationResult.statementId}`);
    
    try {
      // Copier le résultat pour éviter de modifier l'original
      const finalResult = { ...reconciliationResult };
      finalResult.matches = [...reconciliationResult.matches];
      finalResult.unmatchedBank = [...reconciliationResult.unmatchedBank];
      finalResult.unmatchedSystem = [...reconciliationResult.unmatchedSystem];
      
      // Traiter les correspondances manuelles
      for (const match of manualMatches) {
        // Vérifier que les transactions existent
        const bankTransaction = finalResult.unmatchedBank.find(t => t.id === match.bankTransactionId);
        const systemTransaction = finalResult.unmatchedSystem.find(t => t.id === match.systemTransactionId);
        
        if (!bankTransaction || !systemTransaction) {
          this.logger.warn(`Correspondance manuelle impossible: transaction non trouvée (bank: ${match.bankTransactionId}, system: ${match.systemTransactionId})`);
          continue;
        }
        
        // Ajouter la correspondance
        finalResult.matches.push({
          bankTransaction,
          systemTransaction,
          matchType: 'manual',
          confidence: 1.0,
          approved: true
        });
        
        // Supprimer des listes non réconciliées
        finalResult.unmatchedBank = finalResult.unmatchedBank.filter(t => t.id !== match.bankTransactionId);
        finalResult.unmatchedSystem = finalResult.unmatchedSystem.filter(t => t.id !== match.systemTransactionId);
      }
      
      // Approuver automatiquement les correspondances si demandé
      if (autoApprove) {
        finalResult.matches = finalResult.matches.map(match => ({
          ...match,
          approved: true
        }));
      }
      
      // Mettre à jour les statistiques
      finalResult.summary = {
        totalTransactions: finalResult.matches.length * 2 + finalResult.unmatchedBank.length + finalResult.unmatchedSystem.length,
        matchedTransactions: finalResult.matches.length * 2,
        unmatchedBankTransactions: finalResult.unmatchedBank.length,
        unmatchedSystemTransactions: finalResult.unmatchedSystem.length,
        matchPercentage: (finalResult.matches.length * 2) / 
          (finalResult.matches.length * 2 + finalResult.unmatchedBank.length + finalResult.unmatchedSystem.length) * 100,
        approvedMatches: finalResult.matches.filter(m => m.approved).length,
        pendingMatches: finalResult.matches.filter(m => !m.approved).length
      };
      
      // Ajouter la date de finalisation
      finalResult.finalized = {
        date: new Date(),
        autoApproved: autoApprove,
        manualMatchesAdded: manualMatches.length
      };
      
      // Émettre un événement de finalisation
      this.emit('reconciliation:finalized', {
        statementId: finalResult.statementId,
        matchCount: finalResult.matches.length,
        approvedMatchCount: finalResult.summary.approvedMatches,
        unmatchedBankCount: finalResult.unmatchedBank.length,
        unmatchedSystemCount: finalResult.unmatchedSystem.length
      });
      
      // Archiver le résultat si un chemin d'archive est configuré
      if (this.config.archivePath) {
        await this._archiveReconciliationResult(finalResult);
      }
      
      return finalResult;
    } catch (error) {
      this.logger.error(`Erreur lors de la finalisation de la réconciliation pour le relevé ${reconciliationResult.statementId}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('reconciliation:error', {
        statementId: reconciliationResult.statementId,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Parse un relevé bancaire au format CSV
   * @param {string} fileContent - Contenu du fichier CSV
   * @param {Object} formatConfig - Configuration du format
   * @returns {Array} Transactions bancaires
   * @private
   */
  _parseCsvBankStatement(fileContent, formatConfig) {
    // Analyser le CSV
    const records = csvParse(fileContent, {
      delimiter: formatConfig.delimiter,
      skip_empty_lines: true,
      columns: false, // Pas d'en-tête automatique
      trim: true
    });
    
    // Ignorer la ligne d'en-tête si elle existe
    const dataRecords = records.length > 1 && isNaN(parseFloat(records[0][formatConfig.mapping.amount])) ? 
      records.slice(1) : records;
    
    // Transformer les enregistrements en transactions
    return dataRecords.map((record, index) => {
      // Extraire les données selon le mapping
      const dateStr = record[formatConfig.mapping.date];
      const description = record[formatConfig.mapping.description];
      let amountStr = record[formatConfig.mapping.amount];
      const reference = formatConfig.mapping.reference !== undefined ? 
        record[formatConfig.mapping.reference] : null;
      
      // Traiter le montant
      let amount;
      
      // Si le débit et crédit sont dans des colonnes séparées
      if (formatConfig.mapping.creditAmount !== undefined && formatConfig.mapping.debitAmount !== undefined) {
        const creditAmount = record[formatConfig.mapping.creditAmount].trim();
        const debitAmount = record[formatConfig.mapping.debitAmount].trim();
        
        if (creditAmount && creditAmount !== '0' && creditAmount !== '0.00') {
          amount = parseFloat(creditAmount.replace(',', '.'));
        } else if (debitAmount && debitAmount !== '0' && debitAmount !== '0.00') {
          amount = -parseFloat(debitAmount.replace(',', '.'));
        } else {
          amount = 0;
        }
      } else {
        // Nettoyage du montant
        amountStr = amountStr.replace(/\s/g, '').replace(',', '.');
        
        // Déterminer si c'est un crédit ou un débit
        if (formatConfig.creditIndicator && amountStr.includes(formatConfig.creditIndicator)) {
          amountStr = amountStr.replace(formatConfig.creditIndicator, '');
          amount = parseFloat(amountStr);
        } else if (formatConfig.debitIndicator && amountStr.includes(formatConfig.debitIndicator)) {
          amountStr = amountStr.replace(formatConfig.debitIndicator, '');
          amount = -parseFloat(amountStr);
        } else {
          // Si pas d'indicateur explicite, considérer que c'est un débit par défaut
          amount = parseFloat(amountStr);
        }
      }
      
      // Appliquer le multiplicateur de montant
      amount = amount * (formatConfig.amountMultiplier || 1);
      
      // Parser la date
      let date;
      try {
        date = moment(dateStr, formatConfig.dateFormat).toDate();
      } catch (e) {
        this.logger.warn(`Impossible de parser la date "${dateStr}" pour l'enregistrement ${index + 1}`);
        date = new Date(); // Date par défaut
      }
      
      return {
        id: `bank_${index}`, // Identifiant temporaire, sera remplacé par un UUID
        date,
        amount,
        description: description.trim(),
        reference: reference ? reference.trim() : null,
        reconciled: false,
        reconciledWith: null
      };
    }).filter(transaction => !isNaN(transaction.amount)); // Filtrer les transactions sans montant valide
  }
  
  /**
   * Effectue une correspondance exacte entre les transactions
   * @param {Array} bankTransactions - Transactions bancaires
   * @param {Array} sysTransactions - Transactions système
   * @param {Array} matches - Tableau à remplir avec les correspondances
   * @param {Object} settings - Paramètres de réconciliation
   * @private
   */
  _doExactMatching(bankTransactions, sysTransactions, matches, settings) {
    // Fonction pour calculer la différence de jours
    const daysDiff = (date1, date2) => Math.abs(moment(date1).diff(moment(date2), 'days'));
    
    // Fonction pour vérifier si les montants sont égaux (avec tolérance)
    const amountsEqual = (amount1, amount2) => {
      const tolerance = Math.abs(amount1 * settings.amountTolerance);
      return Math.abs(amount1 - amount2) <= tolerance;
    };
    
    // Indexer pour une recherche plus rapide
    const sysTransactionsByAmount = {};
    
    sysTransactions.forEach((transaction, index) => {
      const key = transaction.amount.toFixed(2);
      if (!sysTransactionsByAmount[key]) {
        sysTransactionsByAmount[key] = [];
      }
      sysTransactionsByAmount[key].push({ transaction, index });
    });
    
    // Pour chaque transaction bancaire, chercher une correspondance exacte
    for (let i = 0; i < bankTransactions.length; i++) {
      const bankTx = bankTransactions[i];
      const amountKey = bankTx.amount.toFixed(2);
      
      // Chercher des transactions système avec le même montant
      const candidates = sysTransactionsByAmount[amountKey] || [];
      
      for (let j = 0; j < candidates.length; j++) {
        const { transaction: sysTx, index: sysIndex } = candidates[j];
        
        // Vérifier si les montants correspondent exactement
        if (amountsEqual(bankTx.amount, sysTx.amount)) {
          // Vérifier si les dates sont proches
          if (daysDiff(bankTx.date, sysTx.date) <= settings.dateTolerance) {
            // Vérifier si les références correspondent (si disponibles)
            if ((!bankTx.reference && !sysTx.reference) || 
                (bankTx.reference && sysTx.reference && 
                 bankTx.reference.toLowerCase() === sysTx.reference.toLowerCase())) {
              
              // C'est une correspondance exacte
              matches.push({
                bankTransaction: bankTx,
                systemTransaction: sysTx,
                matchType: 'exact',
                confidence: 1.0,
                approved: false // Nécessite une validation manuelle par défaut
              });
              
              // Supprimer les transactions des listes d'origine
              bankTransactions.splice(i, 1);
              sysTransactions.splice(sysIndex, 1);
              
              // Mettre à jour les index pour l'itération
              i--;
              
              // Mettre à jour l'index des transactions système
              sysTransactionsByAmount[amountKey].splice(j, 1);
              
              // Sortir de la boucle interne
              break;
            }
          }
        }
      }
    }
  }
  
  /**
   * Effectue une correspondance floue entre les transactions
   * @param {Array} bankTransactions - Transactions bancaires
   * @param {Array} sysTransactions - Transactions système
   * @param {Array} matches - Tableau à remplir avec les correspondances
   * @param {Object} settings - Paramètres de réconciliation
   * @private
   */
  _doFuzzyMatching(bankTransactions, sysTransactions, matches, settings) {
    // Fonction pour calculer la différence de jours
    const daysDiff = (date1, date2) => Math.abs(moment(date1).diff(moment(date2), 'days'));
    
    // Fonction pour vérifier si les montants sont proches
    const amountSimilarity = (amount1, amount2) => {
      const tolerance = Math.abs(amount1 * settings.amountTolerance);
      const diff = Math.abs(amount1 - amount2);
      if (diff <= tolerance) return 1.0;
      if (diff <= tolerance * 2) return 0.8;
      if (diff <= tolerance * 5) return 0.5;
      return 0;
    };
    
    // Fonction pour calculer la similarité des descriptions
    const descriptionSimilarity = (desc1, desc2) => {
      if (!desc1 || !desc2) return 0;
      
      // Normaliser et nettoyer les descriptions
      const normalize = text => text.toLowerCase()
        .replace(/[^\w\s]/g, '') // Supprimer la ponctuation
        .replace(/\s+/g, ' ')    // Normaliser les espaces
        .trim();
      
      const normDesc1 = normalize(desc1);
      const normDesc2 = normalize(desc2);
      
      // Calculer la similarité
      if (normDesc1 === normDesc2) return 1.0;
      
      // Vérifier si une description est une sous-chaîne de l'autre
      if (normDesc1.includes(normDesc2) || normDesc2.includes(normDesc1)) {
        return 0.8;
      }
      
      // Diviser en mots et compter les mots communs
      const words1 = normDesc1.split(' ');
      const words2 = normDesc2.split(' ');
      
      let commonWords = 0;
      for (const word of words1) {
        if (words2.includes(word)) commonWords++;
      }
      
      const totalWords = new Set([...words1, ...words2]).size;
      return commonWords / totalWords;
    };
    
    // Pour chaque transaction bancaire, chercher la meilleure correspondance
    for (let i = 0; i < bankTransactions.length; i++) {
      const bankTx = bankTransactions[i];
      let bestMatch = null;
      let bestScore = settings.matchingThreshold; // Seuil minimum pour considérer une correspondance
      let bestSysIndex = -1;
      
      for (let j = 0; j < sysTransactions.length; j++) {
        const sysTx = sysTransactions[j];
        
        // Calculer les scores de similarité
        const amountScore = amountSimilarity(bankTx.amount, sysTx.amount);
        const descScore = descriptionSimilarity(bankTx.description, sysTx.description);
        
        // Pénalité pour les dates éloignées
        const dateDiff = daysDiff(bankTx.date, sysTx.date);
        const dateScore = dateDiff <= settings.dateTolerance ? 
          1.0 - (dateDiff / settings.dateTolerance) * 0.5 : 0;
        
        // Score global (moyenne pondérée)
        const score = (amountScore * 0.5) + (descScore * 0.3) + (dateScore * 0.2);
        
        if (score > bestScore) {
          bestScore = score;
          bestMatch = sysTx;
          bestSysIndex = j;
        }
      }
      
      // Si une correspondance a été trouvée
      if (bestMatch) {
        matches.push({
          bankTransaction: bankTx,
          systemTransaction: bestMatch,
          matchType: 'fuzzy',
          confidence: bestScore,
          approved: false // Nécessite une validation manuelle
        });
        
        // Supprimer les transactions des listes d'origine
        bankTransactions.splice(i, 1);
        sysTransactions.splice(bestSysIndex, 1);
        
        // Mettre à jour l'index pour l'itération
        i--;
      }
    }
  }
  
  /**
   * Exporte un rapport de réconciliation au format CSV
   * @param {Object} options - Options d'export
   * @param {Object} options.reconciliationResult - Résultat de réconciliation
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToCSV({ reconciliationResult, outputPath }) {
    // Préparer les lignes du CSV
    const csvLines = [];
    
    // En-tête avec informations générales
    csvLines.push(`# Rapport de réconciliation bancaire - Le Vieux Moulin`);
    csvLines.push(`# ID du relevé: ${reconciliationResult.statementId}`);
    csvLines.push(`# Période: ${moment(reconciliationResult.periodStart).format('DD/MM/YYYY')} - ${moment(reconciliationResult.periodEnd).format('DD/MM/YYYY')}`);
    csvLines.push(`# Généré le: ${moment().format('DD/MM/YYYY HH:mm:ss')}`);
    csvLines.push(`# Résumé: ${reconciliationResult.summary.matchedTransactions} transactions réconciliées (${reconciliationResult.summary.matchPercentage.toFixed(2)}%)`);
    csvLines.push(`#         ${reconciliationResult.summary.unmatchedBankTransactions} transactions bancaires non réconciliées`);
    csvLines.push(`#         ${reconciliationResult.summary.unmatchedSystemTransactions} transactions système non réconciliées`);
    csvLines.push('#');
    
    // En-tête des correspondances
    csvLines.push('## CORRESPONDANCES');
    csvLines.push('type,confiance,approuvé,date_banque,montant_banque,description_banque,référence_banque,date_système,montant_système,description_système,référence_système');
    
    // Données des correspondances
    reconciliationResult.matches.forEach(match => {
      const bankTx = match.bankTransaction;
      const sysTx = match.systemTransaction;
      
      const line = [
        match.matchType,
        match.confidence.toFixed(2),
        match.approved ? 'Oui' : 'Non',
        moment(bankTx.date).format('DD/MM/YYYY'),
        bankTx.amount.toFixed(2),
        `"${bankTx.description.replace(/"/g, '""')}"`,
        bankTx.reference ? `"${bankTx.reference.replace(/"/g, '""')}"` : '',
        moment(sysTx.date).format('DD/MM/YYYY'),
        sysTx.amount.toFixed(2),
        `"${sysTx.description.replace(/"/g, '""')}"`,
        sysTx.reference ? `"${sysTx.reference.replace(/"/g, '""')}"` : ''
      ].join(',');
      
      csvLines.push(line);
    });
    
    csvLines.push('#');
    
    // En-tête des transactions bancaires non réconciliées
    csvLines.push('## TRANSACTIONS BANCAIRES NON RÉCONCILIÉES');
    csvLines.push('date,montant,description,référence');
    
    // Données des transactions bancaires non réconciliées
    reconciliationResult.unmatchedBank.forEach(transaction => {
      const line = [
        moment(transaction.date).format('DD/MM/YYYY'),
        transaction.amount.toFixed(2),
        `"${transaction.description.replace(/"/g, '""')}"`,
        transaction.reference ? `"${transaction.reference.replace(/"/g, '""')}"` : ''
      ].join(',');
      
      csvLines.push(line);
    });
    
    csvLines.push('#');
    
    // En-tête des transactions système non réconciliées
    csvLines.push('## TRANSACTIONS SYSTÈME NON RÉCONCILIÉES');
    csvLines.push('date,montant,description,référence,méthode_paiement');
    
    // Données des transactions système non réconciliées
    reconciliationResult.unmatchedSystem.forEach(transaction => {
      const line = [
        moment(transaction.date).format('DD/MM/YYYY'),
        transaction.amount.toFixed(2),
        `"${transaction.description.replace(/"/g, '""')}"`,
        transaction.reference ? `"${transaction.reference.replace(/"/g, '""')}"` : '',
        transaction.paymentMethod || ''
      ].join(',');
      
      csvLines.push(line);
    });
    
    // Écrire le fichier
    await fs.writeFile(outputPath, csvLines.join('\n'), 'utf8');
  }
  
  /**
   * Exporte un rapport de réconciliation au format Excel
   * @param {Object} options - Options d'export
   * @param {Object} options.reconciliationResult - Résultat de réconciliation
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToExcel({ reconciliationResult, outputPath }) {
    // Dans une implémentation réelle, utiliser une bibliothèque comme ExcelJS
    // Ici, on utilise une approche simplifiée pour l'exemple
    await this._exportReportToCSV({ reconciliationResult, outputPath: outputPath.replace(/\.xlsx$/, '.csv') });
    
    this.logger.warn('Export Excel non implémenté. Un fichier CSV a été généré à la place.');
  }
  
  /**
   * Exporte un rapport de réconciliation au format PDF
   * @param {Object} options - Options d'export
   * @param {Object} options.reconciliationResult - Résultat de réconciliation
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToPDF({ reconciliationResult, outputPath }) {
    // Dans une implémentation réelle, utiliser une bibliothèque comme PDFKit
    // Ici, on utilise une approche simplifiée pour l'exemple
    await this._exportReportToCSV({ reconciliationResult, outputPath: outputPath.replace(/\.pdf$/, '.csv') });
    
    this.logger.warn('Export PDF non implémenté. Un fichier CSV a été généré à la place.');
  }
  
  /**
   * Exporte un rapport de réconciliation au format JSON
   * @param {Object} options - Options d'export
   * @param {Object} options.reconciliationResult - Résultat de réconciliation
   * @param {string} options.outputPath - Chemin de sortie
   * @returns {Promise<void>}
   * @private
   */
  async _exportReportToJSON({ reconciliationResult, outputPath }) {
    await fs.writeFile(outputPath, JSON.stringify(reconciliationResult, null, 2), 'utf8');
  }
  
  /**
   * Archive un résultat de réconciliation
   * @param {Object} reconciliationResult - Résultat de réconciliation
   * @returns {Promise<void>}
   * @private
   */
  async _archiveReconciliationResult(reconciliationResult) {
    try {
      // Créer le répertoire d'archive si nécessaire
      await fs.mkdir(this.config.archivePath, { recursive: true });
      
      // Chemin du fichier d'archive
      const fileName = `reconciliation_${reconciliationResult.statementId}_${moment().format('YYYYMMDD-HHmmss')}.json`;
      const filePath = path.join(this.config.archivePath, fileName);
      
      // Écrire le fichier
      await fs.writeFile(filePath, JSON.stringify(reconciliationResult, null, 2), 'utf8');
      
      this.logger.debug(`Résultat de réconciliation archivé: ${filePath}`);
    } catch (error) {
      this.logger.error(`Erreur lors de l'archivage du résultat de réconciliation:`, error);
    }
  }
}

// Exports
module.exports = {
  BankReconciliation
};
