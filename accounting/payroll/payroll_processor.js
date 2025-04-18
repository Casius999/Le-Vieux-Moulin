/**
 * Processeur de paie pour le restaurant "Le Vieux Moulin"
 * Gère la collecte des données de présence, le calcul des heures et variables de paie,
 * et la génération des exports pour les logiciels de paie.
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const path = require('path');
const fs = require('fs').promises;
const moment = require('moment');

// Importation des modules internes
const { SecurityUtils } = require('../common/security_utils');
const { DataValidator } = require('./data_validator');
const { AttendanceCollector } = require('./attendance_collector');
const { PayrollCalculator } = require('./payroll_calculator');
const { PayrollExporter } = require('./payroll_exporter');

/**
 * Classe principale du processeur de paie
 * @extends EventEmitter
 */
class PayrollProcessor extends EventEmitter {
  /**
   * Crée une instance du processeur de paie
   * @param {Object} options - Options de configuration
   * @param {number} options.year - Année pour le traitement de la paie
   * @param {number} options.month - Mois pour le traitement de la paie (1-12)
   * @param {boolean} [options.includeValidatedDataOnly=true] - N'inclure que les données validées
   * @param {Object} [options.rules] - Règles de paie spécifiques (remplace les règles par défaut)
   * @param {Object} [options.configManager] - Gestionnaire de configuration
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    if (!options.year || !options.month) {
      throw new Error('Les paramètres year et month sont obligatoires');
    }
    
    this.year = options.year;
    this.month = options.month;
    this.includeValidatedDataOnly = options.includeValidatedDataOnly !== undefined ? 
      options.includeValidatedDataOnly : true;
    
    this.configManager = options.configManager;
    this.logger = options.logger || console;
    
    // Calculer les dates de début et fin de la période
    this.startDate = moment({ year: this.year, month: this.month - 1, day: 1 }).startOf('day');
    this.endDate = moment(this.startDate).endOf('month');
    
    // Initialiser les règles de paie (par défaut ou personnalisées)
    this.rules = options.rules || this._getDefaultRules();
    
    // Initialiser les composants
    this._initializeComponents();
    
    this.logger.info(`Processeur de paie initialisé pour ${this.startDate.format('MMMM YYYY')}`);
  }
  
  /**
   * Initialise les composants internes du processeur
   * @private
   */
  _initializeComponents() {
    // Utilitaires de sécurité
    this.securityUtils = new SecurityUtils({
      configManager: this.configManager
    });
    
    // Validateur de données
    this.dataValidator = new DataValidator({
      rules: this.rules
    });
    
    // Collecteur de données de présence
    this.attendanceCollector = new AttendanceCollector({
      includeValidatedDataOnly: this.includeValidatedDataOnly,
      securityUtils: this.securityUtils,
      logger: this.logger
    });
    
    // Calculateur de paie
    this.payrollCalculator = new PayrollCalculator({
      rules: this.rules,
      logger: this.logger
    });
    
    // Exportateur de paie
    this.payrollExporter = new PayrollExporter({
      securityUtils: this.securityUtils,
      logger: this.logger
    });
    
    // Configuration des listeners d'événements
    this._setupEventListeners();
  }
  
  /**
   * Configure les écouteurs d'événements des sous-composants
   * @private
   */
  _setupEventListeners() {
    // Événements du collecteur de présence
    this.attendanceCollector.on('attendance:collected', (data) => {
      this.logger.info(`Données de présence collectées pour ${data.employeeCount} employés`);
    });
    
    this.attendanceCollector.on('attendance:error', (error) => {
      this.logger.error('Erreur lors de la collecte des données de présence:', error);
      this.emit('error', { type: 'attendance_collection', error });
    });
    
    // Événements du calculateur de paie
    this.payrollCalculator.on('calculation:complete', (data) => {
      this.logger.info(`Calcul de paie terminé pour ${data.employeeCount} employés`);
    });
    
    this.payrollCalculator.on('calculation:error', (error) => {
      this.logger.error('Erreur lors du calcul de paie:', error);
      this.emit('error', { type: 'payroll_calculation', error });
    });
    
    // Événements du validateur de données
    this.dataValidator.on('validation:warning', (warning) => {
      this.logger.warn('Avertissement de validation:', warning);
      this.emit('warning', { type: 'data_validation', warning });
    });
    
    this.dataValidator.on('validation:error', (error) => {
      this.logger.error('Erreur de validation:', error);
      this.emit('error', { type: 'data_validation', error });
    });
    
    // Événements de l'exportateur
    this.payrollExporter.on('export:complete', (info) => {
      this.logger.info(`Export de paie terminé: ${info.path}`);
    });
    
    this.payrollExporter.on('export:error', (error) => {
      this.logger.error('Erreur lors de l\'export de paie:', error);
      this.emit('error', { type: 'payroll_export', error });
    });
  }
  
  /**
   * Obtient les règles de paie par défaut
   * @returns {Object} Règles de paie par défaut
   * @private
   */
  _getDefaultRules() {
    // Si un gestionnaire de configuration est disponible, charger depuis la config
    if (this.configManager) {
      const configRules = this.configManager.getConfig('payroll.rules');
      if (configRules) {
        return configRules;
      }
    }
    
    // Règles par défaut
    return {
      workingHours: {
        regularHoursPerWeek: 35,
        maxDailyHours: 10,
        overtimeRates: [
          { threshold: 35, rate: 1.25 },
          { threshold: 43, rate: 1.50 }
        ],
        nightHours: {
          start: '22:00',
          end: '07:00',
          rate: 1.15
        }
      },
      breaks: {
        minBreakAfterHours: 6,
        breakDuration: 0.5,
        isPaid: false
      },
      serviceTips: {
        distributionMethod: 'points',
        roles: {
          'server': 10,
          'runner': 7,
          'bartender': 8,
          'kitchen': 5,
          'host': 3
        },
        includedInPayroll: true
      },
      mealAllowance: {
        value: 4.85,
        taxDeductible: true
      }
    };
  }
  
  /**
   * Collecte les données de présence pour la période spécifiée
   * @param {Object} [options] - Options supplémentaires
   * @returns {Promise<Array>} Données de présence collectées
   */
  async collectAttendanceData(options = {}) {
    this.logger.info(`Début de la collecte des données de présence pour ${this.startDate.format('MMMM YYYY')}`);
    
    try {
      // Collecter les données de pointage
      const timeClockData = await this.attendanceCollector.collectTimeClockData({
        startDate: this.startDate.toDate(),
        endDate: this.endDate.toDate()
      });
      
      // Collecter les données de planning
      const scheduleData = await this.attendanceCollector.collectScheduleData({
        startDate: this.startDate.toDate(),
        endDate: this.endDate.toDate()
      });
      
      // Collecter les données de congés et absences
      const leaveData = await this.attendanceCollector.collectLeaveData({
        startDate: this.startDate.toDate(),
        endDate: this.endDate.toDate()
      });
      
      // Fusionner les données
      this.attendanceData = this.attendanceCollector.mergeAttendanceData({
        timeClockData,
        scheduleData,
        leaveData
      });
      
      // Valider les données
      const validationResult = this.dataValidator.validateAttendanceData(this.attendanceData);
      
      // Émettre les avertissements
      if (validationResult.warnings.length > 0) {
        validationResult.warnings.forEach(warning => {
          this.emit('warning', { type: 'attendance_validation', warning });
        });
      }
      
      // Émettre les erreurs
      if (validationResult.errors.length > 0) {
        validationResult.errors.forEach(error => {
          this.emit('error', { type: 'attendance_validation', error });
        });
      }
      
      this.logger.info(`Données de présence collectées pour ${Object.keys(this.attendanceData).length} employés`);
      
      return this.attendanceData;
    } catch (error) {
      this.logger.error('Erreur lors de la collecte des données de présence:', error);
      this.emit('error', { type: 'attendance_collection', error });
      throw error;
    }
  }
  
  /**
   * Calcule les données de paie basées sur les données de présence
   * @param {Object} [options] - Options supplémentaires
   * @returns {Promise<Object>} Données de paie calculées
   */
  async calculatePayrollData(options = {}) {
    if (!this.attendanceData) {
      throw new Error('Les données de présence doivent être collectées avant de calculer la paie');
    }
    
    this.logger.info(`Début du calcul des données de paie pour ${this.startDate.format('MMMM YYYY')}`);
    
    try {
      // Collecter les données de chiffre d'affaires pour les primes
      const revenueData = await this.payrollCalculator.collectRevenueData({
        startDate: this.startDate.toDate(),
        endDate: this.endDate.toDate()
      });
      
      // Collecter les données de pourboires
      const tipsData = await this.payrollCalculator.collectTipsData({
        startDate: this.startDate.toDate(),
        endDate: this.endDate.toDate()
      });
      
      // Calculer les heures
      const hoursData = await this.payrollCalculator.calculateHours(this.attendanceData);
      
      // Calculer les primes et variables
      const variablesData = await this.payrollCalculator.calculateVariables({
        attendanceData: this.attendanceData,
        revenueData,
        tipsData
      });
      
      // Fusionner toutes les données
      this.payrollData = this.payrollCalculator.buildPayrollData({
        hoursData,
        variablesData
      });
      
      // Valider les données
      const validationResult = this.dataValidator.validatePayrollData(this.payrollData);
      
      // Émettre les avertissements
      if (validationResult.warnings.length > 0) {
        validationResult.warnings.forEach(warning => {
          this.emit('warning', { type: 'payroll_validation', warning });
        });
      }
      
      // Émettre les erreurs
      if (validationResult.errors.length > 0) {
        validationResult.errors.forEach(error => {
          this.emit('error', { type: 'payroll_validation', error });
        });
      }
      
      this.logger.info(`Calcul de paie terminé pour ${Object.keys(this.payrollData).length} employés`);
      
      return this.payrollData;
    } catch (error) {
      this.logger.error('Erreur lors du calcul des données de paie:', error);
      this.emit('error', { type: 'payroll_calculation', error });
      throw error;
    }
  }
  
  /**
   * Génère un export des données de paie pour les logiciels de paie
   * @param {Object} options - Options d'export
   * @param {string} options.format - Format d'export ('csv', 'sage', 'adp', 'silae')
   * @param {string} options.outputDir - Répertoire de sortie
   * @returns {Promise<string>} Chemin du fichier généré
   */
  async generatePayrollExport(options = {}) {
    if (!this.payrollData) {
      throw new Error('Les données de paie doivent être calculées avant de générer l\'export');
    }
    
    if (!options.format) {
      throw new Error('Le format d\'export est obligatoire');
    }
    
    if (!options.outputDir) {
      throw new Error('Le répertoire de sortie est obligatoire');
    }
    
    this.logger.info(`Début de la génération de l'export de paie au format ${options.format}`);
    
    try {
      // Vérifier si le répertoire existe, le créer si nécessaire
      await fs.mkdir(options.outputDir, { recursive: true });
      
      // Générer le nom de fichier
      const filename = `payroll_${this.year}_${String(this.month).padStart(2, '0')}_${Date.now()}.${this._getFileExtension(options.format)}`;
      const outputPath = path.join(options.outputDir, filename);
      
      // Générer l'export
      await this.payrollExporter.exportPayrollData({
        data: this.payrollData,
        format: options.format,
        outputPath,
        metadata: {
          year: this.year,
          month: this.month,
          startDate: this.startDate.toDate(),
          endDate: this.endDate.toDate(),
          generatedAt: new Date()
        }
      });
      
      this.logger.info(`Export de paie généré avec succès: ${outputPath}`);
      
      return outputPath;
    } catch (error) {
      this.logger.error('Erreur lors de la génération de l\'export de paie:', error);
      this.emit('error', { type: 'payroll_export', error });
      throw error;
    }
  }
  
  /**
   * Génère un rapport de pré-validation pour le manager
   * @param {Object} options - Options du rapport
   * @param {string} options.format - Format du rapport ('pdf', 'html', 'excel')
   * @param {string} options.outputDir - Répertoire de sortie
   * @returns {Promise<string>} Chemin du fichier généré
   */
  async generateValidationReport(options = {}) {
    if (!this.payrollData) {
      throw new Error('Les données de paie doivent être calculées avant de générer le rapport');
    }
    
    if (!options.format) {
      throw new Error('Le format du rapport est obligatoire');
    }
    
    if (!options.outputDir) {
      throw new Error('Le répertoire de sortie est obligatoire');
    }
    
    this.logger.info(`Début de la génération du rapport de validation au format ${options.format}`);
    
    try {
      // Vérifier si le répertoire existe, le créer si nécessaire
      await fs.mkdir(options.outputDir, { recursive: true });
      
      // Générer le nom de fichier
      const filename = `validation_report_${this.year}_${String(this.month).padStart(2, '0')}_${Date.now()}.${options.format}`;
      const outputPath = path.join(options.outputDir, filename);
      
      // Effectuer une validation complète
      const validationResult = this.dataValidator.performFullValidation({
        attendanceData: this.attendanceData,
        payrollData: this.payrollData
      });
      
      // Générer le rapport
      await this.payrollExporter.generateValidationReport({
        validationResult,
        payrollData: this.payrollData,
        format: options.format,
        outputPath,
        metadata: {
          year: this.year,
          month: this.month,
          startDate: this.startDate.toDate(),
          endDate: this.endDate.toDate(),
          generatedAt: new Date()
        }
      });
      
      this.logger.info(`Rapport de validation généré avec succès: ${outputPath}`);
      
      return outputPath;
    } catch (error) {
      this.logger.error('Erreur lors de la génération du rapport de validation:', error);
      this.emit('error', { type: 'validation_report', error });
      throw error;
    }
  }
  
  /**
   * Obtient l'extension de fichier pour un format d'export
   * @param {string} format - Format d'export
   * @returns {string} Extension de fichier
   * @private
   */
  _getFileExtension(format) {
    const extensions = {
      'csv': 'csv',
      'excel': 'xlsx',
      'sage': 'txt',
      'adp': 'xml',
      'silae': 'csv',
      'dsn': 'xml'
    };
    
    return extensions[format.toLowerCase()] || 'dat';
  }
}

// Exports
module.exports = {
  PayrollProcessor
};
