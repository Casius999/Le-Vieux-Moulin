/**
 * Routes pour les données IoT
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const iotController = require('../controllers/iotController');
const { authenticateJWT } = require('../middleware/authMiddleware');

// Middleware d'authentification pour toutes les routes
router.use(authenticateJWT);

// Route pour récupérer l'état actuel des capteurs IoT
router.get('/status', iotController.getIotStatus);

// Route pour récupérer l'historique d'un capteur
router.get('/history/:sensorId', iotController.getSensorHistory);

// Route pour récupérer les alertes IoT
router.get('/alerts', iotController.getIotAlerts);

// Route pour mettre à jour les seuils d'alerte d'un capteur
router.patch('/thresholds/:sensorId', iotController.updateSensorThresholds);

// Route pour configurer un capteur
router.patch('/sensors/:sensorId', iotController.configureSensor);

// Route pour récupérer la liste des capteurs
router.get('/sensors', iotController.getSensorsList);

// Route pour réinitialiser un capteur
router.post('/sensors/:sensorId/reset', iotController.resetSensor);

// Route pour calibrer un capteur
router.post('/sensors/:sensorId/calibrate', iotController.calibrateSensor);

// Route pour envoyer une commande à un équipement
router.post('/devices/:deviceId/command', iotController.sendDeviceCommand);

module.exports = router;
