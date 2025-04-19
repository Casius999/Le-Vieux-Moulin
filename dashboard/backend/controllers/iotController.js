/**
 * Contrôleur pour la gestion des données IoT
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { client, callApi } = require('../utils/apiClient');
const { setupLogger } = require('../utils/logger');
const socketHandler = require('../socketHandlers/iotSocketHandler');

const logger = setupLogger();

/**
 * Récupération de l'état actuel des capteurs IoT
 * @route GET /api/iot/status
 */
exports.getIotStatus = async (req, res, next) => {
  try {
    // Appel à l'API du module IoT pour récupérer les données actuelles
    const iotData = await callApi(() => 
      client.get('/iot/status')
    );
    
    res.status(200).json({
      success: true,
      data: iotData,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des données IoT: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération de l'historique des données d'un capteur
 * @route GET /api/iot/history/:sensorId
 */
exports.getSensorHistory = async (req, res, next) => {
  try {
    const { sensorId } = req.params;
    const { period = 'day' } = req.query;
    
    // Appel à l'API du module IoT pour récupérer l'historique
    const historyData = await callApi(() => 
      client.get(`/iot/sensors/${sensorId}/history`, {
        params: { period }
      })
    );
    
    res.status(200).json({
      success: true,
      data: {
        sensorId,
        data: historyData
      }
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération de l'historique du capteur: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des alertes IoT
 * @route GET /api/iot/alerts
 */
exports.getIotAlerts = async (req, res, next) => {
  try {
    // Appel à l'API du module IoT pour récupérer les alertes
    const alertsData = await callApi(() => 
      client.get('/iot/alerts')
    );
    
    res.status(200).json({
      success: true,
      data: alertsData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des alertes IoT: ${error.message}`);
    next(error);
  }
};

/**
 * Mise à jour des seuils d'alerte pour un capteur
 * @route PATCH /api/iot/thresholds/:sensorId
 */
exports.updateSensorThresholds = async (req, res, next) => {
  try {
    const { sensorId } = req.params;
    const thresholds = req.body;
    
    // Validation des données
    if (!thresholds || typeof thresholds !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Données de seuils invalides'
      });
    }
    
    // Appel à l'API du module IoT pour mettre à jour les seuils
    const updatedSensor = await callApi(() => 
      client.patch(`/iot/sensors/${sensorId}/thresholds`, thresholds)
    );
    
    res.status(200).json({
      success: true,
      data: {
        sensorId,
        thresholds: updatedSensor
      },
      message: 'Seuils mis à jour avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors de la mise à jour des seuils: ${error.message}`);
    next(error);
  }
};

/**
 * Configuration d'un capteur IoT
 * @route PATCH /api/iot/sensors/:sensorId
 */
exports.configureSensor = async (req, res, next) => {
  try {
    const { sensorId } = req.params;
    const config = req.body;
    
    // Validation des données
    if (!config || typeof config !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Données de configuration invalides'
      });
    }
    
    // Appel à l'API du module IoT pour configurer le capteur
    const updatedSensor = await callApi(() => 
      client.patch(`/iot/sensors/${sensorId}/config`, config)
    );
    
    res.status(200).json({
      success: true,
      data: updatedSensor,
      message: 'Capteur configuré avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors de la configuration du capteur: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération de la liste des capteurs disponibles
 * @route GET /api/iot/sensors
 */
exports.getSensorsList = async (req, res, next) => {
  try {
    // Appel à l'API du module IoT pour récupérer la liste des capteurs
    const sensors = await callApi(() => 
      client.get('/iot/sensors')
    );
    
    res.status(200).json({
      success: true,
      data: sensors
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération de la liste des capteurs: ${error.message}`);
    next(error);
  }
};

/**
 * Réinitialisation d'un capteur
 * @route POST /api/iot/sensors/:sensorId/reset
 */
exports.resetSensor = async (req, res, next) => {
  try {
    const { sensorId } = req.params;
    
    // Appel à l'API du module IoT pour réinitialiser le capteur
    await callApi(() => 
      client.post(`/iot/sensors/${sensorId}/reset`)
    );
    
    res.status(200).json({
      success: true,
      message: 'Capteur réinitialisé avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors de la réinitialisation du capteur: ${error.message}`);
    next(error);
  }
};

/**
 * Calibrage d'un capteur
 * @route POST /api/iot/sensors/:sensorId/calibrate
 */
exports.calibrateSensor = async (req, res, next) => {
  try {
    const { sensorId } = req.params;
    const { referenceValue } = req.body;
    
    if (referenceValue === undefined || referenceValue === null) {
      return res.status(400).json({
        success: false,
        message: 'Valeur de référence manquante'
      });
    }
    
    // Appel à l'API du module IoT pour calibrer le capteur
    const calibrationResult = await callApi(() => 
      client.post(`/iot/sensors/${sensorId}/calibrate`, { referenceValue })
    );
    
    res.status(200).json({
      success: true,
      data: calibrationResult,
      message: 'Capteur calibré avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors du calibrage du capteur: ${error.message}`);
    next(error);
  }
};

/**
 * Envoi d'une commande à un équipement IoT
 * @route POST /api/iot/devices/:deviceId/command
 */
exports.sendDeviceCommand = async (req, res, next) => {
  try {
    const { deviceId } = req.params;
    const { command, parameters } = req.body;
    
    if (!command) {
      return res.status(400).json({
        success: false,
        message: 'Commande manquante'
      });
    }
    
    // Appel à l'API du module IoT pour envoyer la commande
    const commandResult = await callApi(() => 
      client.post(`/iot/devices/${deviceId}/command`, { command, parameters })
    );
    
    res.status(200).json({
      success: true,
      data: commandResult,
      message: 'Commande envoyée avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors de l'envoi d'une commande: ${error.message}`);
    next(error);
  }
};
