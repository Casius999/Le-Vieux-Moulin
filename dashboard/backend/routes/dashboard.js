const express = require('express');
const router = express.Router();
const dashboardController = require('../controllers/dashboard');

/**
 * @route   GET /api/dashboard/overview
 * @desc    Get dashboard overview data
 * @access  Private
 */
router.get('/overview', dashboardController.getOverview);

/**
 * @route   GET /api/dashboard/kpi
 * @desc    Get KPI data
 * @access  Private
 */
router.get('/kpi', dashboardController.getKPIs);

/**
 * @route   GET /api/dashboard/alerts
 * @desc    Get active alerts
 * @access  Private
 */
router.get('/alerts', dashboardController.getAlerts);

/**
 * @route   GET /api/dashboard/config
 * @desc    Get dashboard configuration
 * @access  Private
 */
router.get('/config', dashboardController.getConfig);

/**
 * @route   PUT /api/dashboard/config
 * @desc    Update dashboard configuration
 * @access  Private
 */
router.put('/config', dashboardController.updateConfig);

module.exports = router;
