/**
 * Routes pour les prévisions et analyses ML
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const router = express.Router();
const forecastController = require('../controllers/forecastController');
const { authenticateJWT } = require('../middleware/authMiddleware');

// Middleware d'authentification pour toutes les routes
router.use(authenticateJWT);

// Route pour récupérer les prévisions de ventes
router.get('/sales', forecastController.getSalesForecasts);

// Route pour récupérer les prévisions de stock
router.get('/stock', forecastController.getStockForecasts);

// Route pour récupérer les insights ML
router.get('/insights', forecastController.getMlInsights);

// Route pour récupérer les informations sur le modèle ML
router.get('/model', forecastController.getModelInfo);

// Route pour détecter les anomalies dans les données
router.post('/anomalies', forecastController.detectAnomalies);

// Route pour récupérer les recommandations d'optimisation des stocks
router.get('/recommendations/stock', forecastController.getStockRecommendations);

// Route pour récupérer les recommandations de promotions
router.get('/recommendations/promotions', forecastController.getPromotionRecommendations);

// Route pour récupérer les recommandations de plats du jour
router.get('/recommendations/dishes', forecastController.getDishRecommendations);

// Route pour lancer un entraînement manuel du modèle ML
router.post('/model/train', forecastController.trainModel);

// Route pour vérifier le statut d'un entraînement
router.get('/model/training-status/:trainingId', forecastController.getTrainingStatus);

module.exports = router;
