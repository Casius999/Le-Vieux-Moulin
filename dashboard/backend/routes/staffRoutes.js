/**
 * Routes pour la gestion du personnel
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const staffController = require('../controllers/staffController');
const { authenticate } = require('../middleware/authMiddleware');

// Toutes ces routes sont protégées par authentification
router.use(authenticate);

// Routes personnel
router.get('/schedule', staffController.getSchedule);
router.get('/performance', staffController.getPerformance);
router.get('/hours', staffController.getHours);
router.get('/costs', staffController.getCosts);

module.exports = router;
