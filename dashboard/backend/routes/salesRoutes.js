/**
 * Routes pour l'analyse des ventes
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const salesController = require('../controllers/salesController');
const { authenticate } = require('../middleware/authMiddleware');

// Toutes ces routes sont protégées par authentification
router.use(authenticate);

// Routes ventes
router.get('/', salesController.getSales);
router.get('/summary', salesController.getSalesSummary);
router.get('/products', salesController.getSalesByProduct);
router.get('/hourly', salesController.getHourlySales);
router.get('/trends', salesController.getSalesTrends);

module.exports = router;
