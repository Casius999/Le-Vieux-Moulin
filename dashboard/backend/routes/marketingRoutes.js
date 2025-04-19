/**
 * Routes pour le suivi marketing
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const marketingController = require('../controllers/marketingController');
const { authenticate } = require('../middleware/authMiddleware');

// Toutes ces routes sont protégées par authentification
router.use(authenticate);

// Routes marketing
router.get('/campaigns', marketingController.getCampaigns);
router.get('/campaigns/:id', marketingController.getCampaignById);
router.get('/social', marketingController.getSocialMetrics);
router.get('/promotions', marketingController.getPromotions);

module.exports = router;
