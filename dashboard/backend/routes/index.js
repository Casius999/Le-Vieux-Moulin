/**
 * Configuration des routes API pour le dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();

// Import des routes spécifiques
const authRoutes = require('./authRoutes');
const stockRoutes = require('./stockRoutes');
const salesRoutes = require('./salesRoutes');
const marketingRoutes = require('./marketingRoutes');
const financeRoutes = require('./financeRoutes');
const staffRoutes = require('./staffRoutes');
const dashboardRoutes = require('./dashboardRoutes');

// Application des routes
router.use('/auth', authRoutes);
router.use('/stocks', stockRoutes);
router.use('/sales', salesRoutes);
router.use('/marketing', marketingRoutes);
router.use('/finance', financeRoutes);
router.use('/staff', staffRoutes);
router.use('/dashboard', dashboardRoutes);

// Route de base pour vérifier que l'API fonctionne
router.get('/', (req, res) => {
  res.json({ message: 'API Dashboard Le Vieux Moulin' });
});

module.exports = router;
