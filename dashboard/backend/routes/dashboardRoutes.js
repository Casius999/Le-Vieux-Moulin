/**
 * Routes pour la vue d'ensemble du dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const dashboardController = require('../controllers/dashboardController');
const { authenticate } = require('../middleware/authMiddleware');

// Toutes ces routes sont protégées par authentification
router.use(authenticate);

// Routes dashboard
router.get('/overview', dashboardController.getOverview);
router.get('/kpi', dashboardController.getKpi);
router.get('/alerts', dashboardController.getAlerts);
router.get('/config', dashboardController.getConfig);
router.put('/config', dashboardController.updateConfig);

module.exports = router;
