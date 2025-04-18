/**
 * Module de génération de rapports financiers pour Le Vieux Moulin
 * Ce module automatise la création, le formatage et la distribution des rapports comptables
 * à partir des données collectées par le système.
 */

'use strict';

const fs = require('fs').promises;
const path = require('path');
const moment = require('moment');
const _ = require('lodash');
const { EventEmitter } = require('events');

// Importation des modules internes
const { DataCollector } = require('../common/data_collector');
const { TemplateEngine } = require('./template_engine');
const { PDFFormatter } = require('./formatters/pdf_formatter');
const { ExcelFormatter } = require('./formatters/excel_formatter');
const { SageFormatter } = require('./formatters/sage_formatter');
const { EmailDistributor } = require('./distributors/email_distributor');
const { FileSystemArchiver } = require('./distributors/fs_archiver');
const { ReportValidator } = require('./validators/report_validator');
const { SecurityUtils } = require('../common/security_utils');

/**
 * Classe principale pour la génération de rapports financiers
 */
class ReportGenerator extends EventEmitter {
  /**
   * Crée une nouvelle instance du générateur de rapports
   * @param {Object} options Options de configuration
   * @param {string} options.templates_dir Répertoire des templates de rapports
   * @param {string} options.output_dir Répertoire de sortie pour les rapports générés
   * @param {Object} options.company_info Informations sur l'entreprise
   * @param {Object} options.formatters Configuration des formateurs spécifiques
   * @param {Object} options.distributors Configuration des distributeurs
   * @param {Object} options.validators Configuration des validateurs
   */
  constructor(options = {}) {
    super();
    
    this.templatesDir = options.templates_dir || path.join(__dirname, 'templates');
    this.outputDir = options.output_dir || path.join(__dirname, 'output');
    this.companyInfo = options.company_info || {};
    
    // Initialisation des composants
    this.dataCollector = new DataCollector(options.data_collector_config);
    this.templateEngine = new TemplateEngine(this.templatesDir);
    
    // Initialisation des formateurs
    this.formatters = {
      pdf: new PDFFormatter(options.formatters?.pdf || {}),
      excel: new ExcelFormatter(options.formatters?.excel || {}),
      csv: new ExcelFormatter({ ...options.formatters?.excel, format: 'csv' }),
      sage: new SageFormatter(options.formatters?.sage || {}),
      // Autres formateurs selon les besoins
    };
    
    // Initialisation des distributeurs
    this.distributors = {
      email: new EmailDistributor(options.distributors?.email || {}),
      filesystem: new FileSystemArchiver(options.distributors?.filesystem || { root_dir: this.outputDir }),
      // Autres distributeurs selon les besoins
    };
    
    // Initialisation des validateurs
    this.validator = new ReportValidator(options.validators || {});
    
    // Initialisation des répertoires
    this._initializeDirectories();
  }
  
  /**
   * Initialise les répertoires nécessaires
   * @private
   */
  async _initializeDirectories() {
    try {
      // Vérifier et créer le répertoire de sortie s'il n'existe pas
      await fs.mkdir(this.outputDir, { recursive: true });
      
      // Créer les sous-répertoires pour différents types de rapports
      const reportTypes = ['daily', 'weekly', 'monthly', 'annual', 'custom'];
      for (const type of reportTypes) {
        await fs.mkdir(path.join(this.outputDir, type), { recursive: true });
      }
    } catch (error) {
      console.error('Erreur lors de l\'initialisation des répertoires:', error);
      throw new Error(`Impossible d'initialiser les répertoires: ${error.message}`);
    }
  }
  
  /**
   * Génère un rapport journalier
   * @param {Object} options Options de génération
   * @param {Object} options.date Date du rapport (defaults to today)
   * @param {Array<string>} options.formats Formats d'export souhaités
   * @param {boolean} options.distribute Distribuer automatiquement le rapport
   * @param {Array<Object>} options.recipients Destinataires pour la distribution
   * @returns {Promise<Object>} Informations sur le rapport généré
   */
  async createDailyReport(options = {}) {
    const date = options.date ? moment(options.date) : moment();
    const formats = options.formats || ['pdf'];
    const period = {
      type: 'daily',
      date: date.format('YYYY-MM-DD'),
      startDate: date.startOf('day').toDate(),
      endDate: date.endOf('day').toDate(),
      display: date.format('DD/MM/YYYY')
    };
    
    return this._generateReport({
      type: 'daily',
      period,
      template: options.template || 'daily_report',
      title: options.title || `Rapport journalier - ${period.display}`,
      formats,
      distribute: options.distribute,
      recipients: options.recipients,
      data: options.data,
      options
    });
  }
  
  /**
   * Génère un rapport hebdomadaire
   * @param {Object} options Options de génération
   * @param {Object} options.week Semaine du rapport (defaults to current week)
   * @param {Array<string>} options.formats Formats d'export souhaités
   * @param {boolean} options.distribute Distribuer automatiquement le rapport
   * @param {Array<Object>} options.recipients Destinataires pour la distribution
   * @returns {Promise<Object>} Informations sur le rapport généré
   */
  async createWeeklyReport(options = {}) {
    const weekDate = options.week ? moment(options.week) : moment();
    const startDate = weekDate.clone().startOf('isoWeek');
    const endDate = weekDate.clone().endOf('isoWeek');
    const formats = options.formats || ['pdf'];
    const period = {
      type: 'weekly',
      week: weekDate.format('YYYY-[W]WW'),
      year: weekDate.format('YYYY'),
      startDate: startDate.toDate(),
      endDate: endDate.toDate(),
      display: `Semaine ${weekDate.format('WW')} - ${weekDate.format('YYYY')}`
    };
    
    return this._generateReport({
      type: 'weekly',
      period,
      template: options.template || 'weekly_report',
      title: options.title || `Rapport hebdomadaire - ${period.display}`,
      formats,
      distribute: options.distribute,
      recipients: options.recipients,
      data: options.data,
      options
    });
  }
  
  /**
   * Génère un rapport mensuel
   * @param {Object} options Options de génération
   * @param {Object} options.period Période du rapport (mois, année)
   * @param {Array<string>} options.formats Formats d'export souhaités
   * @param {boolean} options.distribute Distribuer automatiquement le rapport
   * @param {Array<Object>} options.recipients Destinataires pour la distribution
   * @returns {Promise<Object>} Informations sur le rapport généré
   */
  async createMonthlyReport(options = {}) {
    const monthDate = options.period ? 
      moment(`${options.period.year}-${options.period.month}-01`) : 
      moment().startOf('month');
    
    const formats = options.formats || ['pdf', 'excel'];
    const period = {
      type: 'monthly',
      month: monthDate.format('MM'),
      year: monthDate.format('YYYY'),
      startDate: monthDate.clone().startOf('month').toDate(),
      endDate: monthDate.clone().endOf('month').toDate(),
      display: monthDate.format('MMMM YYYY')
    };
    
    return this._generateReport({
      type: 'monthly',
      period,
      template: options.template || 'monthly_report',
      title: options.title || `Rapport mensuel - ${period.display}`,
      formats,
      distribute: options.distribute,
      recipients: options.recipients,
      data: options.data,
      options
    });
  }
  
  /**
   * Génère un rapport annuel
   * @param {Object} options Options de génération
   * @param {number} options.year Année du rapport (defaults to current year)
   * @param {Array<string>} options.formats Formats d'export souhaités
   * @param {boolean} options.distribute Distribuer automatiquement le rapport
   * @param {Array<Object>} options.recipients Destinataires pour la distribution
   * @returns {Promise<Object>} Informations sur le rapport généré
   */
  async createAnnualReport(options = {}) {
    const year = options.year || moment().year();
    const startDate = moment(`${year}-01-01`).startOf('day');
    const endDate = moment(`${year}-12-31`).endOf('day');
    const formats = options.formats || ['pdf', 'excel'];
    const period = {
      type: 'annual',
      year,
      startDate: startDate.toDate(),
      endDate: endDate.toDate(),
      display: `Année ${year}`
    };
    
    return this._generateReport({
      type: 'annual',
      period,
      template: options.template || 'annual_report',
      title: options.title || `Rapport annuel - ${period.display}`,
      formats,
      distribute: options.distribute,
      recipients: options.recipients,
      data: options.data,
      options
    });
  }
  
  /**
   * Génère un rapport personnalisé
   * @param {Object} options Options de génération
   * @param {Object} options.period Période personnalisée du rapport
   * @param {string} options.template Template à utiliser
   * @param {Array<string>} options.formats Formats d'export souhaités
   * @param {boolean} options.distribute Distribuer automatiquement le rapport
   * @returns {Promise<Object>} Informations sur le rapport généré
   */
  async createCustomReport(options = {}) {
    if (!options.period || !options.period.startDate || !options.period.endDate) {
      throw new Error('Les dates de début et de fin sont requises pour un rapport personnalisé');
    }
    
    const startDate = moment(options.period.startDate);
    const endDate = moment(options.period.endDate);
    const formats = options.formats || ['pdf'];
    const period = {
      type: 'custom',
      startDate: startDate.toDate(),
      endDate: endDate.toDate(),
      display: `${startDate.format('DD/MM/YYYY')} - ${endDate.format('DD/MM/YYYY')}`
    };
    
    return this._generateReport({
      type: 'custom',
      period,
      template: options.template || 'custom_report',
      title: options.title || `Rapport personnalisé - ${period.display}`,
      formats,
      distribute: options.distribute,
      recipients: options.recipients,
      data: options.data,
      options
    });
  }
  
  /**
   * Procédure interne de génération de rapport
   * @param {Object} config Configuration du rapport à générer
   * @returns {Promise<Object>} Informations sur le rapport généré
   * @private
   */
  async _generateReport(config) {
    try {
      // Récupération des données si non fournies
      const reportData = config.data || await this._collectReportData(config.type, config.period, config.options);
      
      // Validation des données
      await this.validator.validateReportData(reportData, config.type);
      
      // Préparation du contexte pour le template
      const templateContext = {
        report: {
          type: config.type,
          title: config.title,
          period: config.period,
          generated_at: new Date()
        },
        company: this.companyInfo,
        data: reportData
      };
      
      // Génération du contenu du rapport via le moteur de template
      const reportContent = await this.templateEngine.render(config.template, templateContext);
      
      // Génération des fichiers dans les formats demandés
      const files = await this._exportToFormats(reportContent, templateContext, config.formats, config);
      
      // Distribution du rapport si demandé
      if (config.distribute) {
        await this._distributeReport(files, config);
      }
      
      // Événement de rapport généré
      this.emit('report:generated', {
        type: config.type,
        period: config.period,
        formats: config.formats,
        files
      });
      
      return {
        type: config.type,
        title: config.title,
        period: config.period,
        generated_at: templateContext.report.generated_at,
        files
      };
    } catch (error) {
      console.error(`Erreur lors de la génération du rapport ${config.type}:`, error);
      
      // Événement d'erreur
      this.emit('report:error', {
        type: config.type,
        period: config.period,
        error: error.message
      });
      
      throw error;
    }
  }
  
  /**
   * Collecte les données nécessaires pour un type de rapport
   * @param {string} reportType Type de rapport
   * @param {Object} period Période du rapport
   * @param {Object} options Options supplémentaires
   * @returns {Promise<Object>} Données collectées pour le rapport
   * @private
   */
  async _collectReportData(reportType, period, options = {}) {
    // Déterminer les sources de données selon le type de rapport
    const dataSources = [];
    
    switch (reportType) {
      case 'daily':
        dataSources.push(
          this.dataCollector.getSalesData({ date: period.date, detailed: true }),
          this.dataCollector.getExpensesData({ date: period.date }),
          this.dataCollector.getInventoryMovements({ date: period.date })
        );
        
        if (options.includeComparison) {
          // Ajouter données de comparaison (jour précédent, même jour semaine précédente)
          const previousDay = moment(period.startDate).subtract(1, 'day');
          const sameWeekDayLastWeek = moment(period.startDate).subtract(7, 'days');
          
          dataSources.push(
            this.dataCollector.getSalesData({ date: previousDay.format('YYYY-MM-DD'), summary: true })
              .then(data => ({ previousDay: data })),
            this.dataCollector.getSalesData({ date: sameWeekDayLastWeek.format('YYYY-MM-DD'), summary: true })
              .then(data => ({ sameWeekDayLastWeek: data }))
          );
        }
        break;
        
      case 'weekly':
        dataSources.push(
          this.dataCollector.getSalesData({ 
            startDate: period.startDate, 
            endDate: period.endDate,
            groupBy: 'day'
          }),
          this.dataCollector.getExpensesData({ 
            startDate: period.startDate, 
            endDate: period.endDate,
            groupBy: 'category'
          }),
          this.dataCollector.getLabourCosts({
            startDate: period.startDate,
            endDate: period.endDate,
            groupBy: 'day'
          })
        );
        
        if (options.includeComparison) {
          // Ajouter données de comparaison (semaine précédente)
          const previousWeekStart = moment(period.startDate).subtract(1, 'week');
          const previousWeekEnd = moment(period.endDate).subtract(1, 'week');
          
          dataSources.push(
            this.dataCollector.getSalesData({ 
              startDate: previousWeekStart.toDate(), 
              endDate: previousWeekEnd.toDate(),
              summary: true
            }).then(data => ({ previousWeek: data }))
          );
        }
        break;
        
      case 'monthly':
        dataSources.push(
          this.dataCollector.getSalesData({ 
            startDate: period.startDate, 
            endDate: period.endDate,
            groupBy: 'day'
          }),
          this.dataCollector.getExpensesData({ 
            startDate: period.startDate, 
            endDate: period.endDate,
            groupBy: 'category'
          }),
          this.dataCollector.getLabourCosts({
            startDate: period.startDate,
            endDate: period.endDate,
            groupBy: 'week'
          }),
          this.dataCollector.getInventoryValuation({
            date: period.endDate
          }),
          this.dataCollector.getVatReport({
            startDate: period.startDate,
            endDate: period.endDate
          })
        );
        
        if (options.includeComparison) {
          // Ajouter données de comparaison (mois précédent, même mois année précédente)
          const previousMonth = moment(period.startDate).subtract(1, 'month');
          const sameMonthLastYear = moment(period.startDate).subtract(1, 'year');
          
          dataSources.push(
            this.dataCollector.getSalesData({ 
              startDate: previousMonth.clone().startOf('month').toDate(), 
              endDate: previousMonth.clone().endOf('month').toDate(),
              summary: true
            }).then(data => ({ previousMonth: data })),
            
            this.dataCollector.getSalesData({ 
              startDate: sameMonthLastYear.clone().startOf('month').toDate(), 
              endDate: sameMonthLastYear.clone().endOf('month').toDate(),
              summary: true
            }).then(data => ({ sameMonthLastYear: data }))
          );
        }
        break;
        
      case 'annual':
        dataSources.push(
          this.dataCollector.getSalesData({ 
            startDate: period.startDate, 
            endDate: period.endDate,
            groupBy: 'month'
          }),
          this.dataCollector.getExpensesData({ 
            startDate: period.startDate, 
            endDate: period.endDate,
            groupBy: 'month'
          }),
          this.dataCollector.getLabourCosts({
            startDate: period.startDate,
            endDate: period.endDate,
            groupBy: 'month'
          }),
          this.dataCollector.getFinancialStatements({
            year: period.year
          }),
          this.dataCollector.getVatReport({
            startDate: period.startDate,
            endDate: period.endDate,
            groupBy: 'quarter'
          })
        );
        
        if (options.includeComparison) {
          // Ajouter données de comparaison (année précédente)
          const previousYear = period.year - 1;
          const previousYearStart = moment(`${previousYear}-01-01`).startOf('day').toDate();
          const previousYearEnd = moment(`${previousYear}-12-31`).endOf('day').toDate();
          
          dataSources.push(
            this.dataCollector.getSalesData({ 
              startDate: previousYearStart, 
              endDate: previousYearEnd,
              groupBy: 'month'
            }).then(data => ({ previousYear: data }))
          );
        }
        break;
        
      case 'custom':
        // Pour les rapports personnalisés, collecter en fonction des options fournies
        if (options.includeSales !== false) {
          dataSources.push(
            this.dataCollector.getSalesData({ 
              startDate: period.startDate, 
              endDate: period.endDate,
              groupBy: options.groupBy || 'day'
            })
          );
        }
        
        if (options.includeExpenses !== false) {
          dataSources.push(
            this.dataCollector.getExpensesData({ 
              startDate: period.startDate, 
              endDate: period.endDate,
              groupBy: options.expensesGroupBy || 'category'
            })
          );
        }
        
        if (options.includeLabour) {
          dataSources.push(
            this.dataCollector.getLabourCosts({
              startDate: period.startDate,
              endDate: period.endDate,
              groupBy: options.labourGroupBy || 'day'
            })
          );
        }
        
        if (options.includeInventory) {
          dataSources.push(
            this.dataCollector.getInventoryValuation({
              date: options.inventoryDate || period.endDate
            })
          );
        }
        
        if (options.includeVat) {
          dataSources.push(
            this.dataCollector.getVatReport({
              startDate: period.startDate,
              endDate: period.endDate
            })
          );
        }
        break;
        
      default:
        throw new Error(`Type de rapport non pris en charge: ${reportType}`);
    }
    
    // Collecter toutes les données
    try {
      const results = await Promise.all(dataSources);
      
      // Fusionner les résultats dans un objet structuré
      const reportData = {};
      
      results.forEach(result => {
        if (result && typeof result === 'object') {
          // Si c'est un objet avec une seule clé (comparaison), l'intégrer au niveau racine
          const keys = Object.keys(result);
          if (keys.length === 1 && (
              keys[0] === 'previousDay' || 
              keys[0] === 'sameWeekDayLastWeek' || 
              keys[0] === 'previousWeek' || 
              keys[0] === 'previousMonth' || 
              keys[0] === 'sameMonthLastYear' || 
              keys[0] === 'previousYear')) {
            reportData[keys[0]] = result[keys[0]];
          } else {
            // Sinon, fusion intelligente des propriétés
            Object.assign(reportData, result);
          }
        }
      });
      
      // Ajouter les méta-données du rapport
      reportData.metadata = {
        reportType,
        period,
        generatedAt: new Date(),
        dataVersion: '1.0'
      };
      
      return reportData;
    } catch (error) {
      console.error(`Erreur lors de la collecte des données pour le rapport ${reportType}:`, error);
      throw new Error(`Impossible de collecter les données du rapport: ${error.message}`);
    }
  }
  
  /**
   * Exporte le rapport dans les formats demandés
   * @param {string} content Contenu du rapport
   * @param {Object} context Contexte du rapport
   * @param {Array<string>} formats Formats d'export demandés
   * @param {Object} config Configuration du rapport
   * @returns {Promise<Object>} Fichiers générés par format
   * @private
   */
  async _exportToFormats(content, context, formats, config) {
    const files = {};
    const baseName = this._generateReportFilename(config);
    
    // Générer les fichiers pour chaque format demandé
    await Promise.all(formats.map(async format => {
      try {
        const formatter = this.formatters[format.toLowerCase()];
        if (!formatter) {
          throw new Error(`Format non pris en charge: ${format}`);
        }
        
        const fileName = `${baseName}.${formatter.getFileExtension()}`;
        const filePath = path.join(this.outputDir, config.type, fileName);
        
        // Générer le fichier
        await formatter.format(content, context, filePath);
        
        files[format] = {
          format,
          path: filePath,
          fileName,
          size: await this._getFileSize(filePath)
        };
      } catch (error) {
        console.error(`Erreur lors de l'export au format ${format}:`, error);
        throw error;
      }
    }));
    
    return files;
  }
  
  /**
   * Génère un nom de fichier pour le rapport
   * @param {Object} config Configuration du rapport
   * @returns {string} Nom de fichier généré
   * @private
   */
  _generateReportFilename(config) {
    const timestamp = moment().format('YYYYMMDDHHmmss');
    let periodStr = '';
    
    switch (config.type) {
      case 'daily':
        periodStr = moment(config.period.date).format('YYYYMMDD');
        break;
      case 'weekly':
        periodStr = `${config.period.year}W${moment(config.period.startDate).format('WW')}`;
        break;
      case 'monthly':
        periodStr = `${config.period.year}${config.period.month}`;
        break;
      case 'annual':
        periodStr = `${config.period.year}`;
        break;
      case 'custom':
        periodStr = `${moment(config.period.startDate).format('YYYYMMDD')}-${moment(config.period.endDate).format('YYYYMMDD')}`;
        break;
    }
    
    // Générer un nom sécurisé (sans caractères spéciaux)
    const safeTitle = (config.title || '')
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '_')
      .replace(/_+/g, '_')
      .substring(0, 50);
    
    return `${config.type}_report_${periodStr}_${safeTitle}_${timestamp}`;
  }
  
  /**
   * Retourne la taille d'un fichier
   * @param {string} filePath Chemin du fichier
   * @returns {Promise<number>} Taille en octets
   * @private
   */
  async _getFileSize(filePath) {
    try {
      const stats = await fs.stat(filePath);
      return stats.size;
    } catch (error) {
      console.error(`Erreur lors de la récupération de la taille du fichier ${filePath}:`, error);
      return 0;
    }
  }
  
  /**
   * Distribue le rapport aux destinataires configurés
   * @param {Object} files Fichiers générés par format
   * @param {Object} config Configuration du rapport
   * @returns {Promise<void>}
   * @private
   */
  async _distributeReport(files, config) {
    // Archiver sur le système de fichiers
    try {
      await this.distributors.filesystem.distribute({
        files: Object.values(files),
        metadata: {
          type: config.type,
          period: config.period,
          title: config.title,
          generatedAt: new Date()
        }
      });
    } catch (error) {
      console.error('Erreur lors de l\'archivage du rapport:', error);
      // Continuer malgré l'erreur d'archivage
    }
    
    // Envoyer par email si des destinataires sont configurés
    const recipients = config.recipients || [];
    if (recipients.length > 0) {
      try {
        await this.distributors.email.distribute({
          files: Object.values(files),
          recipients,
          subject: `Rapport financier - ${config.title}`,
          body: `Veuillez trouver ci-joint le rapport "${config.title}" généré le ${moment().format('DD/MM/YYYY à HH:mm')}.`,
          metadata: {
            type: config.type,
            period: config.period
          }
        });
      } catch (error) {
        console.error('Erreur lors de l\'envoi du rapport par email:', error);
        throw new Error(`Impossible d'envoyer le rapport par email: ${error.message}`);
      }
    }
  }
}

module.exports = {
  ReportGenerator
};