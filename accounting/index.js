/**
 * Module principal de comptabilité pour Le Vieux Moulin
 * Ce module sert de point d'entrée pour l'ensemble des fonctionnalités comptables
 * du système de gestion du restaurant.
 */

'use strict';

// Importation des dépendances externes
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const winston = require('winston');
const cron = require('node-cron');

// Importation des modules internes
const { ConfigManager, initializeConfig } = require('./common/config_manager');
const { ConnectionPool, initializeConnectionPool } = require('./common/connection_pool');
const { SecurityUtils } = require('./common/security_utils');
const { AlertService } = require('./common/alert_service');
const { DataCollector } = require('./common/data_collector');
const { FinancialDashboard } = require('./financial_tracking/financial_dashboard');
const { ReportGenerator } = require('./reporting/report_generator');
const { InventoryCalculator } = require('./inventory_valuation/inventory_calculator');
const { TaxCalculator } = require('./tax_management/tax_calculator');
const { SystemIntegrator } = require('./integration/system_integrator');

// Importation des routes
const financialRoutes = require('./routes/financial_routes');
const reportingRoutes = require('./routes/reporting_routes');
const taxRoutes = require('./routes/tax_routes');
const inventoryRoutes = require('./routes/inventory_routes');
const exportRoutes = require('./routes/export_routes');
const adminRoutes = require('./routes/admin_routes');

/**
 * Classe principale du module de comptabilité
 */
class AccountingModule {
  /**
   * Crée une nouvelle instance du module de comptabilité
   * @param {Object} options - Options de configuration
   * @param {string} options.configPath - Chemin vers le répertoire de configuration
   * @param {string} options.environment - Environnement d'exécution (development, test, production)
   * @param {boolean} options.enableApi - Activer l'API REST
   * @param {boolean} options.enableCron - Activer les tâches planifiées
   * @param {boolean} options.enableWebhooks - Activer les webhooks
   */
  constructor(options = {}) {
    this.options = {
      configPath: options.configPath || process.env.CONFIG_PATH || './config',
      environment: options.environment || process.env.NODE_ENV || 'development',
      enableApi: options.enableApi !== undefined ? options.enableApi : true,
      enableCron: options.enableCron !== undefined ? options.enableCron : true,
      enableWebhooks: options.enableWebhooks !== undefined ? options.enableWebhooks : true
    };
    
    // Initialiser le logger
    this._initializeLogger();
    
    // Initialiser les composants
    this._initializeComponents();
    
    // Initialiser l'API si activée
    if (this.options.enableApi) {
      this._initializeApi();
    }
    
    // Initialiser les tâches planifiées si activées
    if (this.options.enableCron) {
      this._initializeCronTasks();
    }
    
    this.logger.info('Module de comptabilité initialisé');
  }
  
  /**
   * Initialise le logger
   * @private
   */
  _initializeLogger() {
    // Configurer Winston
    this.logger = winston.createLogger({
      level: this.options.environment === 'production' ? 'info' : 'debug',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      ),
      defaultMeta: { service: 'accounting-module' },
      transports: [
        // Écrire tous les logs dans le fichier
        new winston.transports.File({ filename: 'logs/accounting-error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/accounting-combined.log' })
      ]
    });
    
    // Ajouter la sortie console en développement
    if (this.options.environment !== 'production') {
      this.logger.add(new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          winston.format.simple()
        )
      }));
    }
  }
  
  /**
   * Initialise les composants du module
   * @private
   */
  _initializeComponents() {
    try {
      // Initialiser le gestionnaire de configuration
      this.configManager = initializeConfig({
        configPath: this.options.configPath,
        environment: this.options.environment
      });
      
      // Récupérer la configuration globale
      const config = this.configManager.getConfig();
      
      // Initialiser le pool de connexions
      this.connectionPool = initializeConnectionPool(config.database);
      
      // Initialiser les utilitaires de sécurité
      this.securityUtils = new SecurityUtils({
        configManager: this.configManager
      });
      
      // Initialiser le service d'alertes
      this.alertService = new AlertService({
        configManager: this.configManager
      });
      
      // Initialiser le collecteur de données
      this.dataCollector = new DataCollector({
        configManager: this.configManager,
        dbConfig: config.database
      });
      
      // Initialiser le tableau de bord financier
      this.financialDashboard = new FinancialDashboard({
        configManager: this.configManager,
        dataCollector: this.dataCollector,
        alertService: this.alertService
      });
      
      // Initialiser le générateur de rapports
      this.reportGenerator = new ReportGenerator({
        configManager: this.configManager,
        dataCollector: this.dataCollector
      });
      
      // Initialiser le calculateur d'inventaire
      this.inventoryCalculator = new InventoryCalculator({
        configManager: this.configManager,
        dataCollector: this.dataCollector,
        valuationMethod: config.inventory?.valuationMethod || 'weighted_average'
      });
      
      // Initialiser le calculateur de taxes
      this.taxCalculator = new TaxCalculator({
        configManager: this.configManager,
        dataCollector: this.dataCollector
      });
      
      // Initialiser l'intégrateur système
      this.systemIntegrator = new SystemIntegrator({
        configManager: this.configManager,
        securityUtils: this.securityUtils,
        alertService: this.alertService
      });
      
      // S'abonner aux événements importants
      this._setupEventListeners();
      
      this.logger.info('Composants initialisés avec succès');
    } catch (error) {
      this.logger.error('Erreur lors de l\'initialisation des composants:', error);
      throw error;
    }
  }
  
  /**
   * Configure les écouteurs d'événements
   * @private
   */
  _setupEventListeners() {
    // Événements de l'intégrateur système
    this.systemIntegrator.on('event:error', (data) => {
      this.logger.error('Erreur d\'intégration:', data);
    });
    
    this.systemIntegrator.on('webhook:error', (data) => {
      this.logger.error('Erreur de webhook:', data);
    });
    
    // Événements du service d'alertes
    this.alertService.on('alert', (alert) => {
      this.logger.info(`Alerte générée: ${alert.type} - ${alert.message}`);
    });
    
    this.alertService.on('alert:critical', (alert) => {
      this.logger.error(`Alerte CRITIQUE: ${alert.type} - ${alert.message}`);
    });
    
    // Événements du tableau de bord financier
    this.financialDashboard.on('dashboard:updated', ({ dashboardId }) => {
      this.logger.debug(`Tableau de bord mis à jour: ${dashboardId}`);
    });
  }
  
  /**
   * Initialise l'API REST
   * @private
   */
  _initializeApi() {
    try {
      // Créer l'application Express
      this.app = express();
      
      // Middleware de base
      this.app.use(helmet()); // Sécurité
      this.app.use(cors()); // CORS
      this.app.use(bodyParser.json()); // Parsing JSON
      this.app.use(bodyParser.urlencoded({ extended: true }));
      
      // Logging
      this.app.use(morgan('combined', {
        stream: {
          write: (message) => this.logger.info(message.trim())
        }
      }));
      
      // Routes
      this.app.use('/api/financial', financialRoutes(this));
      this.app.use('/api/reporting', reportingRoutes(this));
      this.app.use('/api/tax', taxRoutes(this));
      this.app.use('/api/inventory', inventoryRoutes(this));
      this.app.use('/api/export', exportRoutes(this));
      this.app.use('/api/admin', adminRoutes(this));
      
      // Route racine
      this.app.get('/api', (req, res) => {
        res.json({
          name: 'Module de comptabilité - Le Vieux Moulin',
          version: '1.0.0',
          status: 'running',
          environment: this.options.environment
        });
      });
      
      // Middleware d'erreur
      this.app.use((err, req, res, next) => {
        this.logger.error('Erreur API:', err);
        
        res.status(err.status || 500).json({
          error: {
            message: err.message,
            code: err.code || 'internal_error'
          }
        });
      });
      
      // Démarrer le serveur si port configuré
      const port = this.configManager.get('api.port');
      if (port) {
        this.server = this.app.listen(port, () => {
          this.logger.info(`API comptabilité démarrée sur le port ${port}`);
        });
      }
      
      this.logger.info('API REST initialisée avec succès');
    } catch (error) {
      this.logger.error('Erreur lors de l\'initialisation de l\'API:', error);
      throw error;
    }
  }
  
  /**
   * Initialise les tâches planifiées
   * @private
   */
  _initializeCronTasks() {
    try {
      const cronConfig = this.configManager.getConfig('cron', {});
      
      // Tâche de mise à jour des tableaux de bord
      if (cronConfig.dashboardUpdate) {
        cron.schedule(cronConfig.dashboardUpdate, async () => {
          try {
            this.logger.info('Exécution de la mise à jour planifiée des tableaux de bord');
            
            // Mettre à jour les dashboards financiers
            const dashboards = this.financialDashboard.getDashboardList();
            
            for (const dashboardId of dashboards) {
              await this.financialDashboard.refreshDashboard(dashboardId);
              this.logger.debug(`Tableau de bord ${dashboardId} mis à jour`);
            }
            
            this.logger.info('Mise à jour des tableaux de bord terminée');
          } catch (error) {
            this.logger.error('Erreur lors de la mise à jour des tableaux de bord:', error);
            
            // Créer une alerte
            this.alertService.danger('cron_dashboard_update_error',
              'Erreur lors de la mise à jour planifiée des tableaux de bord',
              { error: error.message }
            );
          }
        });
      }
      
      // Tâche de génération de rapports quotidiens
      if (cronConfig.dailyReports) {
        cron.schedule(cronConfig.dailyReports, async () => {
          try {
            this.logger.info('Exécution de la génération planifiée des rapports quotidiens');
            
            // Générer les rapports configurés
            const reportsConfig = this.configManager.getConfig('reports.daily', []);
            
            for (const reportConfig of reportsConfig) {
              await this.reportGenerator.generateReport(reportConfig.type, reportConfig.options);
              this.logger.debug(`Rapport ${reportConfig.type} généré`);
            }
            
            this.logger.info('Génération des rapports quotidiens terminée');
          } catch (error) {
            this.logger.error('Erreur lors de la génération des rapports quotidiens:', error);
            
            // Créer une alerte
            this.alertService.danger('cron_daily_reports_error',
              'Erreur lors de la génération planifiée des rapports quotidiens',
              { error: error.message }
            );
          }
        });
      }
      
      // Tâche de calcul de TVA mensuel
      if (cronConfig.monthlyVatReport) {
        cron.schedule(cronConfig.monthlyVatReport, async () => {
          try {
            this.logger.info('Exécution du calcul mensuel de TVA');
            
            // Calculer pour le mois précédent
            const today = new Date();
            const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const lastDayOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
            
            const vatReport = await this.taxCalculator.generateVATReport({
              startDate: lastMonth,
              endDate: lastDayOfLastMonth,
              includeDetails: true
            });
            
            // Générer les écritures comptables
            const vatEntries = this.taxCalculator.generateVATEntries(vatReport);
            
            // Sauvegarder le rapport
            // TODO: Implémenter la sauvegarde
            
            this.logger.info('Calcul mensuel de TVA terminé');
            
            // Créer une alerte informative
            this.alertService.info('vat_report_generated',
              `Rapport de TVA généré pour la période du ${lastMonth.toLocaleDateString()} au ${lastDayOfLastMonth.toLocaleDateString()}`,
              {
                period: {
                  start: lastMonth,
                  end: lastDayOfLastMonth
                },
                balanceDue: vatReport.balance.balanceDue,
                declarationDate: vatReport.dates.declaration
              }
            );
          } catch (error) {
            this.logger.error('Erreur lors du calcul mensuel de TVA:', error);
            
            // Créer une alerte
            this.alertService.danger('cron_vat_calculation_error',
              'Erreur lors du calcul mensuel de TVA',
              { error: error.message }
            );
          }
        });
      }
      
      // Tâche de valorisation de stock
      if (cronConfig.inventoryValuation) {
        cron.schedule(cronConfig.inventoryValuation, async () => {
          try {
            this.logger.info('Exécution de la valorisation planifiée des stocks');
            
            const inventoryValue = await this.inventoryCalculator.calculateInventoryValue();
            
            // Sauvegarder les résultats
            // TODO: Implémenter la sauvegarde
            
            this.logger.info(`Valorisation des stocks terminée. Valeur totale: ${inventoryValue.totalValue}€`);
          } catch (error) {
            this.logger.error('Erreur lors de la valorisation des stocks:', error);
            
            // Créer une alerte
            this.alertService.danger('cron_inventory_valuation_error',
              'Erreur lors de la valorisation planifiée des stocks',
              { error: error.message }
            );
          }
        });
      }
      
      this.logger.info('Tâches planifiées initialisées avec succès');
    } catch (error) {
      this.logger.error('Erreur lors de l\'initialisation des tâches planifiées:', error);
      throw error;
    }
  }
  
  /**
   * Démarre le module de comptabilité
   * @returns {Promise<void>}
   */
  async start() {
    this.logger.info('Démarrage du module de comptabilité...');
    
    try {
      // Initialiser la connexion à la base de données
      if (this.connectionPool) {
        // Vérifier les connexions
        const pools = this.connectionPool.getAvailablePools();
        
        for (const pool of pools) {
          const healthCheck = await this.connectionPool.checkPoolHealth(pool);
          
          if (healthCheck.status !== 'healthy') {
            this.logger.error(`Pool de connexion ${pool} en mauvais état:`, healthCheck);
            this.alertService.warning('database_connection_issue',
              `Problème avec le pool de connexion ${pool}`,
              healthCheck
            );
          } else {
            this.logger.debug(`Pool de connexion ${pool} en bon état`);
          }
        }
      }
      
      // Vérifier les intégrations
      if (this.systemIntegrator) {
        const integrationStatus = await this.systemIntegrator.checkConnectionStatus();
        
        for (const [module, status] of Object.entries(integrationStatus)) {
          if (!status.connected) {
            this.logger.error(`Module d'intégration ${module} non connecté:`, status);
            this.alertService.warning('integration_connection_issue',
              `Problème de connexion avec le module ${module}`,
              status
            );
          } else {
            this.logger.debug(`Module d'intégration ${module} connecté`);
          }
        }
      }
      
      // Initialiser le tableau de bord financier
      if (this.financialDashboard) {
        await this.financialDashboard.initialize();
      }
      
      this.logger.info('Module de comptabilité démarré avec succès');
      
      return true;
    } catch (error) {
      this.logger.error('Erreur lors du démarrage du module de comptabilité:', error);
      
      // Notifier d'une erreur critique
      this.alertService.critical('module_start_error',
        'Erreur critique lors du démarrage du module de comptabilité',
        { error: error.message, stack: error.stack }
      );
      
      throw error;
    }
  }
  
  /**
   * Arrête le module de comptabilité
   * @returns {Promise<void>}
   */
  async stop() {
    this.logger.info('Arrêt du module de comptabilité...');
    
    try {
      // Fermer le serveur HTTP
      if (this.server) {
        await new Promise((resolve, reject) => {
          this.server.close((err) => {
            if (err) reject(err);
            else resolve();
          });
        });
      }
      
      // Fermer l'intégrateur système
      if (this.systemIntegrator) {
        this.systemIntegrator.close();
      }
      
      // Fermer les connexions à la base de données
      if (this.connectionPool) {
        await this.connectionPool.close();
      }
      
      this.logger.info('Module de comptabilité arrêté avec succès');
      
      return true;
    } catch (error) {
      this.logger.error('Erreur lors de l\'arrêt du module de comptabilité:', error);
      throw error;
    }
  }
  
  /**
   * Point d'entrée pour l'exécution directe du module
   * @static
   */
  static async main() {
    try {
      // Créer et démarrer le module
      const accounting = new AccountingModule();
      await accounting.start();
      
      // Gérer les signaux d'arrêt
      process.on('SIGINT', async () => {
        console.log('Arrêt demandé (SIGINT)...');
        await accounting.stop();
        process.exit(0);
      });
      
      process.on('SIGTERM', async () => {
        console.log('Arrêt demandé (SIGTERM)...');
        await accounting.stop();
        process.exit(0);
      });
      
      console.log('Module de comptabilité en cours d\'exécution. Appuyez sur Ctrl+C pour arrêter.');
    } catch (error) {
      console.error('Erreur fatale:', error);
      process.exit(1);
    }
  }
}

// Exportation
module.exports = {
  AccountingModule,
  // Exportation de tous les composants pour utilisation individuelle
  ConfigManager,
  ConnectionPool,
  SecurityUtils,
  AlertService,
  DataCollector,
  FinancialDashboard,
  ReportGenerator,
  InventoryCalculator,
  TaxCalculator,
  SystemIntegrator
};

// Exécution directe si appelé en tant que script
if (require.main === module) {
  AccountingModule.main().catch(console.error);
}
