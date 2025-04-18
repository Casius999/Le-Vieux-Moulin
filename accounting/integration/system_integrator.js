/**
 * Intégrateur système pour le module de comptabilité
 * Ce module gère les interactions et l'intégration avec les autres composants
 * du système de gestion du restaurant Le Vieux Moulin.
 */

'use strict';

const { EventEmitter } = require('events');
const axios = require('axios');
const { ConfigManager } = require('../common/config_manager');
const { SecurityUtils } = require('../common/security_utils');
const { AlertService } = require('../common/alert_service');

/**
 * Classe principale d'intégration système
 */
class SystemIntegrator extends EventEmitter {
  /**
   * Crée une nouvelle instance de l'intégrateur système
   * @param {Object} options - Options de configuration
   * @param {Object} options.modules - Configuration des modules externes
   * @param {Object} options.eventSubscriptions - Abonnements aux événements
   * @param {ConfigManager} options.configManager - Instance du gestionnaire de configuration
   * @param {SecurityUtils} options.securityUtils - Instance des utilitaires de sécurité
   * @param {AlertService} options.alertService - Instance du service d'alertes
   */
  constructor(options = {}) {
    super();
    
    this.modules = options.modules || {};
    this.eventSubscriptions = options.eventSubscriptions || {};
    this.configManager = options.configManager || 
      (ConfigManager.getConfigManager ? ConfigManager.getConfigManager() : null);
    this.securityUtils = options.securityUtils || new SecurityUtils();
    this.alertService = options.alertService || new AlertService();
    
    // Charger la configuration depuis le gestionnaire si disponible
    if (this.configManager) {
      const integrationConfig = this.configManager.getConfig('integration', {});
      
      if (integrationConfig.modules) {
        this.modules = { ...this.modules, ...integrationConfig.modules };
      }
      
      if (integrationConfig.eventSubscriptions) {
        this.eventSubscriptions = { ...this.eventSubscriptions, ...integrationConfig.eventSubscriptions };
      }
    }
    
    // Initialiser les connexions aux modules et les abonnements aux événements
    this._clients = {};
    this._eventHandlers = new Map();
    this._webhookHandlers = new Map();
    
    this._initializeModuleConnections();
    this._setupEventSubscriptions();
  }
  
  /**
   * Initialise les connexions aux modules externes
   * @private
   */
  _initializeModuleConnections() {
    for (const [moduleName, config] of Object.entries(this.modules)) {
      // Créer un client HTTP pour chaque module
      this._clients[moduleName] = axios.create({
        baseURL: config.baseUrl,
        timeout: config.timeout || 30000,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(config.headers || {})
        }
      });
      
      // Configurer l'authentification si nécessaire
      if (config.auth) {
        if (config.auth.type === 'bearer') {
          this._clients[moduleName].interceptors.request.use(request => {
            request.headers.Authorization = `Bearer ${config.auth.token}`;
            return request;
          });
        } else if (config.auth.type === 'basic') {
          this._clients[moduleName].interceptors.request.use(request => {
            const credentials = Buffer.from(`${config.auth.username}:${config.auth.password}`).toString('base64');
            request.headers.Authorization = `Basic ${credentials}`;
            return request;
          });
        }
      }
      
      console.log(`Module ${moduleName} initialisé avec URL de base: ${config.baseUrl}`);
    }
  }
  
  /**
   * Configure les abonnements aux événements
   * @private
   */
  _setupEventSubscriptions() {
    for (const [eventSource, events] of Object.entries(this.eventSubscriptions)) {
      for (const [eventName, handler] of Object.entries(events)) {
        const fullEventName = `${eventSource}:${eventName}`;
        
        // Créer un handler pour l'événement
        const eventHandler = async (eventData) => {
          try {
            // Exécuter le handler configuré
            if (typeof handler === 'function') {
              await handler.call(this, eventData);
            } else if (typeof handler === 'object') {
              // Handler sous forme de configuration
              if (handler.action === 'forward') {
                // Transférer l'événement à un module spécifique
                await this.forwardEvent(handler.target, eventName, eventData, handler.options);
              } else if (handler.action === 'transform') {
                // Transformer et transférer l'événement
                const transformedData = this._transformEventData(eventData, handler.transformation);
                await this.forwardEvent(handler.target, handler.targetEvent || eventName, transformedData, handler.options);
              } else if (handler.action === 'aggregate') {
                // Agréger l'événement avec d'autres données
                await this._handleAggregateEvent(eventName, eventData, handler);
              } else if (handler.action === 'alert') {
                // Créer une alerte
                await this._handleAlertEvent(eventName, eventData, handler);
              }
            }
            
            // Émettre un événement de succès
            this.emit('event:processed', { source: eventSource, name: eventName, success: true });
          } catch (error) {
            console.error(`Erreur lors du traitement de l'événement ${fullEventName}:`, error);
            
            // Émettre un événement d'erreur
            this.emit('event:error', { 
              source: eventSource, 
              name: eventName, 
              error: error.message,
              data: eventData
            });
            
            // Créer une alerte si configuré
            if (handler.alertOnError) {
              this.alertService.danger('event_processing_error', 
                `Erreur lors du traitement de l'événement ${fullEventName}: ${error.message}`,
                { eventSource, eventName, eventData, error: error.message }
              );
            }
          }
        };
        
        // Stocker le handler pour le nettoyage
        this._eventHandlers.set(fullEventName, eventHandler);
        
        // S'abonner à l'événement
        this.on(fullEventName, eventHandler);
        
        console.log(`Abonné à l'événement ${fullEventName}`);
      }
    }
  }
  
  /**
   * Transforme les données d'un événement selon une configuration
   * @param {Object} data - Données d'origine
   * @param {Object|Function} transformation - Configuration de transformation
   * @returns {Object} - Données transformées
   * @private
   */
  _transformEventData(data, transformation) {
    if (typeof transformation === 'function') {
      return transformation(data);
    } else if (typeof transformation === 'object') {
      // Transformation déclarative
      const result = {};
      
      for (const [targetField, sourceField] of Object.entries(transformation)) {
        if (typeof sourceField === 'string') {
          // Mapping simple
          const parts = sourceField.split('.');
          let value = data;
          
          for (const part of parts) {
            value = value && value[part];
          }
          
          result[targetField] = value;
        } else if (typeof sourceField === 'object' && sourceField.type === 'template') {
          // Template avec substitution de variables
          result[targetField] = this._processTemplate(sourceField.template, data);
        } else if (typeof sourceField === 'object' && sourceField.type === 'function') {
          // Fonction de transformation
          const func = new Function('data', sourceField.body);
          result[targetField] = func(data);
        }
      }
      
      return result;
    }
    
    // Par défaut, retourner les données inchangées
    return data;
  }
  
  /**
   * Traite un template avec substitution de variables
   * @param {string} template - Template avec variables
   * @param {Object} data - Données pour substitution
   * @returns {string} - Template avec variables substituées
   * @private
   */
  _processTemplate(template, data) {
    return template.replace(/\{([^}]+)\}/g, (match, path) => {
      const parts = path.split('.');
      let value = data;
      
      for (const part of parts) {
        value = value && value[part];
      }
      
      return value !== undefined ? value : match;
    });
  }
  
  /**
   * Gère un événement de type agrégation
   * @param {string} eventName - Nom de l'événement
   * @param {Object} eventData - Données de l'événement
   * @param {Object} config - Configuration de l'agrégation
   * @returns {Promise<void>}
   * @private
   */
  async _handleAggregateEvent(eventName, eventData, config) {
    // Cette méthode dépend de l'implémentation spécifique
    // Elle peut agréger plusieurs événements ou enrichir avec des données externes
    
    // Exemple simplifié
    const aggregatedData = {
      ...eventData,
      timestamp: new Date(),
      aggregationType: config.type || 'default'
    };
    
    // Enrichir avec des données externes si configuré
    if (config.enrichWith) {
      for (const [fieldName, enrichConfig] of Object.entries(config.enrichWith)) {
        try {
          const enrichData = await this._fetchEnrichmentData(enrichConfig, eventData);
          aggregatedData[fieldName] = enrichData;
        } catch (error) {
          console.error(`Erreur lors de l'enrichissement du champ ${fieldName}:`, error);
          aggregatedData[fieldName] = { error: error.message };
        }
      }
    }
    
    // Transférer l'événement agrégé
    if (config.target) {
      await this.forwardEvent(config.target, config.targetEvent || eventName, aggregatedData, config.options);
    }
    
    // Émettre localement
    this.emit(`aggregated:${eventName}`, aggregatedData);
  }
  
  /**
   * Récupère des données d'enrichissement
   * @param {Object} config - Configuration de l'enrichissement
   * @param {Object} sourceData - Données source
   * @returns {Promise<Object>} - Données d'enrichissement
   * @private
   */
  async _fetchEnrichmentData(config, sourceData) {
    if (!config.source || !this._clients[config.source]) {
      throw new Error(`Source d'enrichissement non configurée: ${config.source}`);
    }
    
    // Préparer le chemin avec substitution de variables
    const path = this._processTemplate(config.path, sourceData);
    
    // Effectuer la requête
    const response = await this._clients[config.source].get(path);
    
    // Traitement spécifique si nécessaire
    if (config.transform) {
      return this._transformEventData(response.data, config.transform);
    }
    
    return response.data;
  }
  
  /**
   * Gère un événement de type alerte
   * @param {string} eventName - Nom de l'événement
   * @param {Object} eventData - Données de l'événement
   * @param {Object} config - Configuration de l'alerte
   * @returns {Promise<void>}
   * @private
   */
  async _handleAlertEvent(eventName, eventData, config) {
    if (!this.alertService) {
      throw new Error('AlertService non initialisé');
    }
    
    // Préparer le message de l'alerte
    const message = config.messageTemplate ? 
      this._processTemplate(config.messageTemplate, eventData) : 
      `Événement ${eventName} déclenché`;
    
    // Déterminer le niveau d'alerte
    const level = config.level || 'info';
    
    // Créer l'alerte
    this.alertService.alert(
      config.alertType || 'event_triggered',
      message,
      eventData,
      {
        level,
        channels: config.channels,
        recipients: config.recipients
      }
    );
  }
  
  /**
   * Transfère un événement à un module externe
   * @param {string} target - Module cible
   * @param {string} eventName - Nom de l'événement
   * @param {Object} data - Données de l'événement
   * @param {Object} options - Options de transfert
   * @returns {Promise<Object>} - Réponse du module cible
   */
  async forwardEvent(target, eventName, data, options = {}) {
    // Vérifier que le module cible existe
    if (!this._clients[target]) {
      throw new Error(`Module cible non configuré: ${target}`);
    }
    
    // Récupérer la configuration du module
    const moduleConfig = this.modules[target];
    
    if (!moduleConfig) {
      throw new Error(`Configuration du module ${target} non trouvée`);
    }
    
    // Déterminer le point d'API
    let endpoint = options.endpoint || moduleConfig.endpoints?.[eventName];
    
    if (!endpoint) {
      // Point d'API par défaut basé sur le nom de l'événement
      endpoint = `/events/${eventName}`;
    }
    
    // Préparer les données à envoyer
    const payload = {
      event: eventName,
      data,
      timestamp: new Date(),
      source: 'accounting_module',
      ...options.additionalData
    };
    
    // Ajouter une signature si nécessaire
    if (options.sign || moduleConfig.signEvents) {
      payload.signature = this.securityUtils.signData(
        JSON.stringify(payload),
        moduleConfig.signingKey || process.env.INTEGRATION_SIGNING_KEY
      );
    }
    
    try {
      // Effectuer la requête
      const response = await this._clients[target].post(endpoint, payload, {
        headers: options.headers
      });
      
      // Émettre un événement de succès
      this.emit('event:forwarded', { 
        target, 
        eventName, 
        success: true,
        responseStatus: response.status
      });
      
      return response.data;
    } catch (error) {
      console.error(`Erreur lors du transfert de l'événement ${eventName} vers ${target}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('event:forward_error', {
        target,
        eventName,
        error: error.message,
        data
      });
      
      // Créer une alerte si configuré
      if (options.alertOnError || moduleConfig.alertOnError) {
        this.alertService.danger('event_forward_error',
          `Erreur lors du transfert de l'événement ${eventName} vers ${target}: ${error.message}`,
          { target, eventName, data, error: error.message }
        );
      }
      
      throw error;
    }
  }
  
  /**
   * Enregistre un gestionnaire de webhook
   * @param {string} path - Chemin du webhook
   * @param {Function} handler - Fonction de traitement
   */
  registerWebhookHandler(path, handler) {
    this._webhookHandlers.set(path, handler);
    console.log(`Gestionnaire de webhook enregistré pour le chemin: ${path}`);
  }
  
  /**
   * Traite une requête webhook entrante
   * @param {string} path - Chemin du webhook
   * @param {Object} payload - Données de la requête
   * @param {Object} headers - En-têtes de la requête
   * @returns {Promise<Object>} - Résultat du traitement
   */
  async handleWebhook(path, payload, headers = {}) {
    // Rechercher le gestionnaire pour ce chemin
    const handler = this._webhookHandlers.get(path);
    
    if (!handler) {
      throw new Error(`Aucun gestionnaire trouvé pour le webhook: ${path}`);
    }
    
    try {
      // Vérifier l'authenticité de la requête si nécessaire
      if (headers['x-signature'] && this.modules.webhook?.verifySignature) {
        const isValid = this.securityUtils.verifySignature(
          JSON.stringify(payload),
          headers['x-signature'],
          this.modules.webhook.publicKey || process.env.WEBHOOK_VERIFICATION_KEY
        );
        
        if (!isValid) {
          throw new Error('Signature du webhook invalide');
        }
      }
      
      // Exécuter le handler
      const result = await handler.call(this, payload, headers);
      
      // Émettre un événement de succès
      this.emit('webhook:processed', { 
        path, 
        success: true,
        timestamp: new Date()
      });
      
      return result;
    } catch (error) {
      console.error(`Erreur lors du traitement du webhook ${path}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('webhook:error', {
        path,
        error: error.message,
        payload,
        timestamp: new Date()
      });
      
      // Créer une alerte
      this.alertService.warning('webhook_processing_error',
        `Erreur lors du traitement du webhook ${path}: ${error.message}`,
        { path, payload, error: error.message }
      );
      
      throw error;
    }
  }
  
  /**
   * Appelle une méthode d'API d'un module externe
   * @param {string} module - Nom du module
   * @param {string} endpoint - Point d'API
   * @param {Object} data - Données de la requête
   * @param {Object} options - Options de la requête
   * @returns {Promise<Object>} - Réponse du module
   */
  async callModuleApi(module, endpoint, data = null, options = {}) {
    // Vérifier que le module existe
    if (!this._clients[module]) {
      throw new Error(`Module non configuré: ${module}`);
    }
    
    try {
      let response;
      
      // Déterminer la méthode HTTP
      const method = options.method || (data ? 'post' : 'get');
      
      switch (method.toLowerCase()) {
        case 'get':
          response = await this._clients[module].get(endpoint, {
            params: data,
            headers: options.headers
          });
          break;
        
        case 'post':
          response = await this._clients[module].post(endpoint, data, {
            headers: options.headers
          });
          break;
        
        case 'put':
          response = await this._clients[module].put(endpoint, data, {
            headers: options.headers
          });
          break;
        
        case 'delete':
          response = await this._clients[module].delete(endpoint, {
            params: data,
            headers: options.headers
          });
          break;
        
        default:
          throw new Error(`Méthode HTTP non supportée: ${method}`);
      }
      
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de l'appel à l'API ${endpoint} du module ${module}:`, error);
      
      // Créer une alerte si configuré
      if (options.alertOnError) {
        this.alertService.danger('api_call_error',
          `Erreur lors de l'appel à l'API ${endpoint} du module ${module}: ${error.message}`,
          { module, endpoint, data, error: error.message }
        );
      }
      
      throw error;
    }
  }
  
  /**
   * Vérifie l'état des connexions aux modules externes
   * @returns {Promise<Object>} - État des connexions
   */
  async checkConnectionStatus() {
    const status = {};
    
    for (const [moduleName, client] of Object.entries(this._clients)) {
      try {
        // Récupérer la configuration du module
        const moduleConfig = this.modules[moduleName];
        const healthEndpoint = moduleConfig.healthEndpoint || '/health';
        
        // Vérifier la connexion
        const response = await client.get(healthEndpoint, { timeout: 5000 });
        
        status[moduleName] = {
          connected: response.status >= 200 && response.status < 300,
          status: response.status,
          responseTime: response.headers['x-response-time'],
          lastChecked: new Date()
        };
      } catch (error) {
        status[moduleName] = {
          connected: false,
          error: error.message,
          lastChecked: new Date()
        };
      }
    }
    
    return status;
  }
  
  /**
   * Ferme toutes les connexions et nettoie les ressources
   */
  close() {
    // Supprimer tous les abonnements aux événements
    for (const [eventName, handler] of this._eventHandlers.entries()) {
      this.removeListener(eventName, handler);
    }
    
    // Vider les collections
    this._eventHandlers.clear();
    this._webhookHandlers.clear();
    
    console.log('Intégrateur système fermé, connexions et abonnements nettoyés');
  }
}

module.exports = { SystemIntegrator };
