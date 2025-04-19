/**
 * Routes pour les rapports financiers
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const financeController = require('../controllers/financeController');
const { authenticate } = require('../middleware/authMiddleware');

// Toutes ces routes sont protégées par authentification
router.use(authenticate);

// Routes finances
router.get('/summary', financeController.getSummary);
router.get('/reports', financeController.getReports);
router.get('/expenses', financeController.getExpenses);
router.get('/revenue', financeController.getRevenue);
router.get('/predictions', financeController.getPredictions);

module.exports = router;
