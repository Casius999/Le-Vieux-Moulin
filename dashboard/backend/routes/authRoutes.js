/**
 * Routes d'authentification pour le dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const { authenticate } = require('../middleware/authMiddleware');

// Routes publiques
router.post('/login', authController.login);
router.post('/refresh', authController.refreshToken);

// Routes protégées
router.post('/logout', authenticate, authController.logout);
router.get('/me', authenticate, authController.getCurrentUser);

module.exports = router;
