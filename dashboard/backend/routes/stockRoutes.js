/**
 * Routes pour la gestion des stocks
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const stockController = require('../controllers/stockController');
const { authenticate } = require('../middleware/authMiddleware');

// Toutes ces routes sont protégées par authentification
router.use(authenticate);

// Routes stocks
router.get('/', stockController.getAllStocks);
router.get('/:id', stockController.getStockById);
router.get('/categories', stockController.getStockCategories);
router.get('/alerts', stockController.getStockAlerts);

module.exports = router;
