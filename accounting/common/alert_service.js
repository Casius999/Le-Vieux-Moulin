/**
 * Service d'alertes pour le module de comptabilité
 * Ce service gère la détection, la génération et la distribution des alertes
 * liées aux anomalies financières et événements comptables importants.
 */

'use strict';

const { EventEmitter } = require('events');
const nodemailer = require('nodemailer');
const { ConfigManager } = require('./config_manager');

/**
 * Classe de gestion des alertes financières
 */
class AlertService extends EventEmitter {
  /**
   * Crée une nouvelle instance du service d'alertes
   * @param {Object} options - Options de configuration
   * @param {Object} options.alertLevels - Configuration des niveaux d'alerte
   * @param {Object} options.channels - Configuration des canaux de notification
   * @param {Object} options.templates - Templates de messages d'alerte
   * @param {ConfigManager} options.configManager - Instance du gestionnaire de configuration
   */
  constructor(options = {}) {
    super();
    
    this.alertLevels = options.alertLevels || {
      info: { priority: 0, color: '#3498db' },
      success: { priority: 0, color: '#2ecc71' },
      warning: { priority: 1, color: '#f39c12' },
      danger: { priority: 2, color: '#e74c3c' },
      critical: { priority: 3, color: '#c0392b' }
    };
    
    this.channels = options.channels || {};
    this.templates = options.templates || {};
    this.configManager = options.configManager || 
      (ConfigManager.getConfigManager ? ConfigManager.getConfigManager() : null);
    
    // Charger la configuration depuis le gestionnaire si disponible
    if (this.configManager) {
      const alertConfig = this.configManager.getConfig('alerts', {});
      
      if (alertConfig.levels) {
        this.alertLevels = { ...this.alertLevels, ...alertConfig.levels };
      }
      
      if (alertConfig.channels) {
        this.channels = alertConfig.channels;
      }
      
      if (alertConfig.templates) {
        this.templates = alertConfig.templates;
      }
    }
    
    // Initialiser les transporteurs d'email
    this._initializeEmailTransporters();
    
    // Historique des alertes (limité aux 100 dernières)
    this.alertHistory = [];
    this.maxHistorySize = options.maxHistorySize || 100;
  }
  
  /**
   * Initialise les transporteurs d'email pour les notifications
   * @private
   */
  _initializeEmailTransporters() {
    this.emailTransporters = {};
    
    if (this.channels && this.channels.email) {
      for (const [name, config] of Object.entries(this.channels.email)) {
        if (config.host && config.port) {
          this.emailTransporters[name] = nodemailer.createTransport({
            host: config.host,
            port: config.port,
            secure: config.secure || false,
            auth: config.auth || null,
            tls: config.tls || null
          });
        }
      }
    }
  }
  
  /**
   * Génère et envoie une alerte
   * @param {string} type - Type d'alerte
   * @param {string} message - Message principal de l'alerte
   * @param {Object} data - Données associées à l'alerte
   * @param {Object} options - Options de l'alerte
   * @param {string} options.level - Niveau d'alerte (info, warning, danger, critical)
   * @param {string[]} options.channels - Canaux de notification à utiliser
   * @param {string[]} options.recipients - Destinataires de l'alerte
   * @param {boolean} options.immediate - Envoyer immédiatement sans mise en file d'attente
   * @returns {string} - Identifiant de l'alerte générée
   */
  alert(type, message, data = {}, options = {}) {
    // Valider le type d'alerte
    if (!type) {
      throw new Error('Type d\'alerte requis');
    }
    
    // Valider le message
    if (!message) {
      throw new Error('Message d\'alerte requis');
    }
    
    // Préparer les options avec valeurs par défaut
    const alertLevel = options.level || 'info';
    const levelConfig = this.alertLevels[alertLevel] || this.alertLevels.info;
    
    // Générer un identifiant unique pour l'alerte
    const alertId = `alert_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    
    // Créer l'objet d'alerte
    const alert = {
      id: alertId,
      type,
      message,
      level: alertLevel,
      data,
      timestamp: new Date(),
      status: 'pending',
      sentTo: [],
      options
    };
    
    // Ajouter à l'historique
    this._addToHistory(alert);
    
    // Émettre un événement pour l'alerte
    this.emit('alert', alert);
    this.emit(`alert:${type}`, alert);
    this.emit(`alert:level:${alertLevel}`, alert);
    
    // Traiter l'alerte selon les options
    if (options.immediate !== false) {
      this._processAlert(alert);
    }
    
    return alertId;
  }
  
  /**
   * Alerte de niveau Information
   * @param {string} type - Type d'alerte
   * @param {string} message - Message principal
   * @param {Object} data - Données associées
   * @param {Object} options - Options supplémentaires
   * @returns {string} - Identifiant de l'alerte
   */
  info(type, message, data = {}, options = {}) {
    return this.alert(type, message, data, { ...options, level: 'info' });
  }
  
  /**
   * Alerte de niveau Succès
   * @param {string} type - Type d'alerte
   * @param {string} message - Message principal
   * @param {Object} data - Données associées
   * @param {Object} options - Options supplémentaires
   * @returns {string} - Identifiant de l'alerte
   */
  success(type, message, data = {}, options = {}) {
    return this.alert(type, message, data, { ...options, level: 'success' });
  }
  
  /**
   * Alerte de niveau Avertissement
   * @param {string} type - Type d'alerte
   * @param {string} message - Message principal
   * @param {Object} data - Données associées
   * @param {Object} options - Options supplémentaires
   * @returns {string} - Identifiant de l'alerte
   */
  warning(type, message, data = {}, options = {}) {
    return this.alert(type, message, data, { ...options, level: 'warning' });
  }
  
  /**
   * Alerte de niveau Danger
   * @param {string} type - Type d'alerte
   * @param {string} message - Message principal
   * @param {Object} data - Données associées
   * @param {Object} options - Options supplémentaires
   * @returns {string} - Identifiant de l'alerte
   */
  danger(type, message, data = {}, options = {}) {
    return this.alert(type, message, data, { ...options, level: 'danger' });
  }
  
  /**
   * Alerte de niveau Critique
   * @param {string} type - Type d'alerte
   * @param {string} message - Message principal
   * @param {Object} data - Données associées
   * @param {Object} options - Options supplémentaires
   * @returns {string} - Identifiant de l'alerte
   */
  critical(type, message, data = {}, options = {}) {
    return this.alert(type, message, data, { ...options, level: 'critical' });
  }
  
  /**
   * Récupère l'historique des alertes avec filtrage optionnel
   * @param {Object} filters - Filtres à appliquer
   * @param {string} filters.type - Filtrer par type d'alerte
   * @param {string} filters.level - Filtrer par niveau d'alerte
   * @param {Date} filters.since - Filtrer depuis une date
   * @param {Date} filters.until - Filtrer jusqu'à une date
   * @param {string} filters.status - Filtrer par statut
   * @returns {Array} - Alertes filtrées
   */
  getAlertHistory(filters = {}) {
    let filteredAlerts = [...this.alertHistory];
    
    // Appliquer les filtres
    if (filters.type) {
      filteredAlerts = filteredAlerts.filter(alert => alert.type === filters.type);
    }
    
    if (filters.level) {
      filteredAlerts = filteredAlerts.filter(alert => alert.level === filters.level);
    }
    
    if (filters.since) {
      const sinceDate = new Date(filters.since);
      filteredAlerts = filteredAlerts.filter(alert => alert.timestamp >= sinceDate);
    }
    
    if (filters.until) {
      const untilDate = new Date(filters.until);
      filteredAlerts = filteredAlerts.filter(alert => alert.timestamp <= untilDate);
    }
    
    if (filters.status) {
      filteredAlerts = filteredAlerts.filter(alert => alert.status === filters.status);
    }
    
    return filteredAlerts;
  }
  
  /**
   * Marque une alerte comme résolue
   * @param {string} alertId - Identifiant de l'alerte
   * @param {Object} resolution - Informations de résolution
   * @param {string} resolution.by - Identifiant de la personne ayant résolu
   * @param {string} resolution.notes - Notes sur la résolution
   * @returns {boolean} - Succès de l'opération
   */
  resolveAlert(alertId, resolution = {}) {
    const alertIndex = this.alertHistory.findIndex(alert => alert.id === alertId);
    
    if (alertIndex === -1) {
      return false;
    }
    
    const alert = this.alertHistory[alertIndex];
    
    // Mettre à jour le statut
    alert.status = 'resolved';
    alert.resolution = {
      timestamp: new Date(),
      by: resolution.by || 'system',
      notes: resolution.notes || ''
    };
    
    // Émettre un événement
    this.emit('alert:resolved', alert);
    
    return true;
  }
  
  /**
   * Traite une alerte (envoi aux canaux configurés)
   * @param {Object} alert - Alerte à traiter
   * @private
   */
  async _processAlert(alert) {
    try {
      // Déterminer les canaux à utiliser
      const channels = alert.options.channels || this._getDefaultChannelsForLevel(alert.level);
      
      // Traiter chaque canal
      const channelPromises = channels.map(channel => this._sendToChannel(alert, channel));
      
      // Attendre que tous les envois soient terminés
      const results = await Promise.allSettled(channelPromises);
      
      // Mettre à jour le statut de l'alerte
      alert.status = 'sent';
      alert.processedAt = new Date();
      alert.deliveryResults = results.map((result, index) => ({
        channel: channels[index],
        success: result.status === 'fulfilled',
        error: result.status === 'rejected' ? result.reason.message : null
      }));
      
      // Émettre un événement
      this.emit('alert:processed', alert);
    } catch (error) {
      console.error('Erreur lors du traitement de l\'alerte:', error);
      
      alert.status = 'error';
      alert.error = error.message;
      
      // Émettre un événement d'erreur
      this.emit('alert:error', { alert, error });
    }
  }
  
  /**
   * Envoie une alerte à un canal spécifique
   * @param {Object} alert - Alerte à envoyer
   * @param {string} channelName - Nom du canal
   * @returns {Promise<boolean>} - Succès de l'envoi
   * @private
   */
  async _sendToChannel(alert, channelName) {
    // Vérifier si le canal existe
    const [channelType, channelId] = channelName.split(':');
    
    if (!this.channels[channelType]) {
      throw new Error(`Type de canal inconnu: ${channelType}`);
    }
    
    // Préparer le contenu de l'alerte
    const content = this._formatAlertForChannel(alert, channelType, channelId);
    
    // Envoyer selon le type de canal
    switch (channelType) {
      case 'email':
        return this._sendEmailAlert(alert, content, channelId);
      
      case 'sms':
        return this._sendSmsAlert(alert, content, channelId);
      
      case 'webhook':
        return this._sendWebhookAlert(alert, content, channelId);
      
      case 'notification':
        return this._sendNotificationAlert(alert, content, channelId);
      
      case 'logger':
        return this._sendLoggerAlert(alert, content, channelId);
      
      default:
        throw new Error(`Type de canal non implémenté: ${channelType}`);
    }
  }
  
  /**
   * Formate une alerte pour un canal spécifique
   * @param {Object} alert - Alerte à formater
   * @param {string} channelType - Type de canal
   * @param {string} channelId - Identifiant du canal
   * @returns {Object} - Contenu formaté
   * @private
   */
  _formatAlertForChannel(alert, channelType, channelId) {
    // Rechercher un template spécifique
    const templateKey = `${alert.type}_${channelType}` in this.templates ? 
      `${alert.type}_${channelType}` : 
      `default_${channelType}`;
    
    const template = this.templates[templateKey] || this.templates.default || {};
    
    // Format de base
    const baseContent = {
      title: template.title || `Alerte ${alert.level}: ${alert.type}`,
      body: template.body || alert.message,
      data: alert.data,
      level: alert.level,
      timestamp: alert.timestamp,
      id: alert.id
    };
    
    // Substitution des variables dans les templates
    if (typeof baseContent.title === 'string') {
      baseContent.title = this._substituteTemplateVariables(baseContent.title, alert);
    }
    
    if (typeof baseContent.body === 'string') {
      baseContent.body = this._substituteTemplateVariables(baseContent.body, alert);
    }
    
    // Formats spécifiques par canal
    switch (channelType) {
      case 'email':
        return {
          ...baseContent,
          subject: baseContent.title,
          html: this._generateHtmlEmail(baseContent, alert)
        };
      
      case 'sms':
        return {
          ...baseContent,
          text: this._generateSmsText(baseContent, alert)
        };
      
      case 'webhook':
        return {
          ...baseContent,
          payload: {
            alert_id: alert.id,
            alert_type: alert.type,
            level: alert.level,
            message: alert.message,
            timestamp: alert.timestamp,
            data: alert.data
          }
        };
      
      case 'notification':
        return {
          ...baseContent,
          clickAction: `/alerts/view/${alert.id}`
        };
      
      case 'logger':
        return {
          ...baseContent,
          logMessage: `[ALERTE ${alert.level.toUpperCase()}] ${alert.type}: ${alert.message}`
        };
      
      default:
        return baseContent;
    }
  }
  
  /**
   * Remplace les variables dans un template
   * @param {string} template - Template avec variables
   * @param {Object} alert - Données de l'alerte
   * @returns {string} - Template avec variables remplacées
   * @private
   */
  _substituteTemplateVariables(template, alert) {
    return template
      .replace(/\{id\}/g, alert.id)
      .replace(/\{type\}/g, alert.type)
      .replace(/\{level\}/g, alert.level)
      .replace(/\{message\}/g, alert.message)
      .replace(/\{timestamp\}/g, alert.timestamp.toLocaleString())
      .replace(/\{data\.([^}]+)\}/g, (match, path) => {
        return _.get(alert.data, path, '');
      });
  }
  
  /**
   * Génère le contenu HTML pour une alerte par email
   * @param {Object} content - Contenu formaté
   * @param {Object} alert - Alerte originale
   * @returns {string} - Corps HTML de l'email
   * @private
   */
  _generateHtmlEmail(content, alert) {
    const levelColor = this.alertLevels[alert.level] ? this.alertLevels[alert.level].color : '#3498db';
    
    // Template HTML de base
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .alert-container { border: 1px solid #ddd; border-radius: 4px; overflow: hidden; max-width: 600px; margin: 0 auto; }
          .alert-header { background-color: ${levelColor}; color: white; padding: 15px; font-weight: bold; }
          .alert-body { padding: 20px; }
          .alert-footer { background-color: #f8f9fa; padding: 15px; border-top: 1px solid #ddd; font-size: 12px; }
          .alert-metadata { margin-top: 20px; background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; }
          .alert-data { margin-top: 15px; }
          .alert-data table { border-collapse: collapse; width: 100%; }
          .alert-data th, .alert-data td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          .alert-data th { background-color: #f2f2f2; }
        </style>
      </head>
      <body>
        <div class="alert-container">
          <div class="alert-header">
            ${content.title}
          </div>
          <div class="alert-body">
            <p>${content.body}</p>
            
            ${this._generateDataSection(alert.data)}
            
            <div class="alert-metadata">
              <p><strong>ID:</strong> ${alert.id}</p>
              <p><strong>Type:</strong> ${alert.type}</p>
              <p><strong>Niveau:</strong> ${alert.level}</p>
              <p><strong>Date:</strong> ${alert.timestamp.toLocaleString()}</p>
            </div>
          </div>
          <div class="alert-footer">
            Cette alerte a été générée automatiquement par le système de comptabilité du restaurant Le Vieux Moulin.
          </div>
        </div>
      </body>
      </html>
    `;
  }
  
  /**
   * Génère une section HTML pour les données d'alerte
   * @param {Object} data - Données à afficher
   * @returns {string} - HTML généré
   * @private
   */
  _generateDataSection(data) {
    if (!data || Object.keys(data).length === 0) {
      return '';
    }
    
    let html = '<div class="alert-data"><h3>Détails</h3><table>';
    
    // En-têtes
    html += '<tr><th>Propriété</th><th>Valeur</th></tr>';
    
    // Contenu
    for (const [key, value] of Object.entries(data)) {
      const formattedValue = typeof value === 'object' ? 
        JSON.stringify(value) : 
        String(value);
      
      html += `<tr><td>${key}</td><td>${formattedValue}</td></tr>`;
    }
    
    html += '</table></div>';
    
    return html;
  }
  
  /**
   * Génère le texte pour une alerte SMS
   * @param {Object} content - Contenu formaté
   * @param {Object} alert - Alerte originale
   * @returns {string} - Texte du SMS
   * @private
   */
  _generateSmsText(content, alert) {
    // Format simplifié pour SMS (limité en taille)
    return `${content.title}: ${content.body.substring(0, 100)}${content.body.length > 100 ? '...' : ''}`;
  }
  
  /**
   * Envoie une alerte par email
   * @param {Object} alert - Alerte à envoyer
   * @param {Object} content - Contenu formaté
   * @param {string} channelId - Identifiant du canal
   * @returns {Promise<boolean>} - Succès de l'envoi
   * @private
   */
  async _sendEmailAlert(alert, content, channelId) {
    // Récupérer la configuration du canal
    const channelConfig = this.channels.email && this.channels.email[channelId];
    
    if (!channelConfig) {
      throw new Error(`Configuration du canal email ${channelId} non trouvée`);
    }
    
    // Récupérer le transporteur
    const transporter = this.emailTransporters[channelId];
    
    if (!transporter) {
      throw new Error(`Transporteur email pour ${channelId} non initialisé`);
    }
    
    // Déterminer les destinataires
    let recipients = alert.options.recipients || channelConfig.recipients || [];
    
    // Filtrer par rôle si spécifié
    if (channelConfig.roleFilters && alert.options.roles) {
      const roleRecipients = alert.options.roles
        .filter(role => channelConfig.roleFilters[role])
        .flatMap(role => channelConfig.roleFilters[role]);
      
      recipients = [...new Set([...recipients, ...roleRecipients])];
    }
    
    if (recipients.length === 0) {
      return false;
    }
    
    // Préparer les options d'email
    const mailOptions = {
      from: channelConfig.sender || `"Système d'alertes" <alertes@levieuxmoulin.fr>`,
      to: recipients.join(', '),
      subject: content.subject,
      html: content.html,
      text: content.body
    };
    
    // Envoyer l'email
    const result = await transporter.sendMail(mailOptions);
    
    // Mettre à jour l'alerte
    alert.sentTo.push({
      channel: `email:${channelId}`,
      recipients,
      messageId: result.messageId,
      timestamp: new Date()
    });
    
    return true;
  }
  
  /**
   * Envoie une alerte par SMS
   * @param {Object} alert - Alerte à envoyer
   * @param {Object} content - Contenu formaté
   * @param {string} channelId - Identifiant du canal
   * @returns {Promise<boolean>} - Succès de l'envoi
   * @private
   */
  async _sendSmsAlert(alert, content, channelId) {
    // Implémentation spécifique pour SMS
    // Nécessite un service SMS externe
    
    // Simuler un succès pour l'exemple
    alert.sentTo.push({
      channel: `sms:${channelId}`,
      recipients: alert.options.recipients || [],
      timestamp: new Date()
    });
    
    return true;
  }
  
  /**
   * Envoie une alerte via webhook
   * @param {Object} alert - Alerte à envoyer
   * @param {Object} content - Contenu formaté
   * @param {string} channelId - Identifiant du canal
   * @returns {Promise<boolean>} - Succès de l'envoi
   * @private
   */
  async _sendWebhookAlert(alert, content, channelId) {
    // Récupérer la configuration du canal
    const channelConfig = this.channels.webhook && this.channels.webhook[channelId];
    
    if (!channelConfig || !channelConfig.url) {
      throw new Error(`Configuration du webhook ${channelId} non trouvée ou incomplète`);
    }
    
    // Envoyer la requête HTTP
    const response = await fetch(channelConfig.url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(channelConfig.headers || {})
      },
      body: JSON.stringify(content.payload)
    });
    
    if (!response.ok) {
      throw new Error(`Échec de l'appel webhook: ${response.status} ${response.statusText}`);
    }
    
    // Mettre à jour l'alerte
    alert.sentTo.push({
      channel: `webhook:${channelId}`,
      url: channelConfig.url,
      timestamp: new Date()
    });
    
    return true;
  }
  
  /**
   * Envoie une alerte via le système de notification interne
   * @param {Object} alert - Alerte à envoyer
   * @param {Object} content - Contenu formaté
   * @param {string} channelId - Identifiant du canal
   * @returns {Promise<boolean>} - Succès de l'envoi
   * @private
   */
  async _sendNotificationAlert(alert, content, channelId) {
    // Implémentation pour notifications internes
    // Émission d'un événement spécifique
    
    this.emit('notification', {
      id: alert.id,
      title: content.title,
      message: content.body,
      level: alert.level,
      timestamp: alert.timestamp,
      clickAction: content.clickAction,
      data: alert.data
    });
    
    // Mettre à jour l'alerte
    alert.sentTo.push({
      channel: `notification:${channelId}`,
      timestamp: new Date()
    });
    
    return true;
  }
  
  /**
   * Envoie une alerte via le système de journalisation
   * @param {Object} alert - Alerte à envoyer
   * @param {Object} content - Contenu formaté
   * @param {string} channelId - Identifiant du canal
   * @returns {Promise<boolean>} - Succès de l'envoi
   * @private
   */
  async _sendLoggerAlert(alert, content, channelId) {
    // Journalisation simple selon le niveau
    const logLevel = alert.level === 'info' || alert.level === 'success' ? 'info' :
                    alert.level === 'warning' ? 'warn' :
                    'error';
    
    console[logLevel](content.logMessage, alert.data);
    
    // Mettre à jour l'alerte
    alert.sentTo.push({
      channel: `logger:${channelId}`,
      timestamp: new Date()
    });
    
    return true;
  }
  
  /**
   * Ajoute une alerte à l'historique
   * @param {Object} alert - Alerte à ajouter
   * @private
   */
  _addToHistory(alert) {
    this.alertHistory.unshift(alert);
    
    // Limiter la taille de l'historique
    if (this.alertHistory.length > this.maxHistorySize) {
      this.alertHistory = this.alertHistory.slice(0, this.maxHistorySize);
    }
  }
  
  /**
   * Détermine les canaux par défaut pour un niveau d'alerte
   * @param {string} level - Niveau d'alerte
   * @returns {string[]} - Liste des canaux
   * @private
   */
  _getDefaultChannelsForLevel(level) {
    // Canaux par défaut selon le niveau d'alerte
    switch (level) {
      case 'info':
      case 'success':
        return ['logger:system'];
      
      case 'warning':
        return ['logger:system', 'notification:app'];
      
      case 'danger':
        return ['logger:system', 'notification:app', 'email:standard'];
      
      case 'critical':
        return ['logger:system', 'notification:app', 'email:urgent', 'sms:urgent'];
      
      default:
        return ['logger:system'];
    }
  }
}

module.exports = { AlertService };
