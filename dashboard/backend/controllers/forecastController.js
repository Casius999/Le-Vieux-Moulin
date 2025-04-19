/**
 * Contrôleur pour les prévisions et analyses ML
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { client, callApi } = require('../utils/apiClient');
const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Récupération des prévisions de ventes
 * @route GET /api/forecast/sales
 */
exports.getSalesForecasts = async (req, res, next) => {
  try {
    const { period = 'week', type = 'revenue' } = req.query;
    
    // Appel à l'API du module ML pour récupérer les prévisions
    const forecastData = await callApi(() => 
      client.get('/ml/forecast/sales', {
        params: { period, type }
      })
    );
    
    res.status(200).json({
      success: true,
      data: forecastData,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des prévisions de ventes: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des prévisions de stock
 * @route GET /api/forecast/stock
 */
exports.getStockForecasts = async (req, res, next) => {
  try {
    const { period = 'week', category = 'all' } = req.query;
    
    // Appel à l'API du module ML pour récupérer les prévisions de stock
    const forecastData = await callApi(() => 
      client.get('/ml/forecast/stock', {
        params: { period, category }
      })
    );
    
    res.status(200).json({
      success: true,
      data: forecastData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des prévisions de stock: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des insights ML
 * @route GET /api/forecast/insights
 */
exports.getMlInsights = async (req, res, next) => {
  try {
    // Appel à l'API du module ML pour récupérer les insights
    const insightsData = await callApi(() => 
      client.get('/ml/insights')
    );
    
    res.status(200).json({
      success: true,
      data: insightsData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des insights ML: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des informations sur le modèle ML
 * @route GET /api/forecast/model
 */
exports.getModelInfo = async (req, res, next) => {
  try {
    // Appel à l'API du module ML pour récupérer les informations sur le modèle
    const modelData = await callApi(() => 
      client.get('/ml/model/info')
    );
    
    res.status(200).json({
      success: true,
      data: modelData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des informations sur le modèle: ${error.message}`);
    next(error);
  }
};

/**
 * Détection d'anomalies dans les données
 * @route POST /api/forecast/anomalies
 */
exports.detectAnomalies = async (req, res, next) => {
  try {
    const { data, type = 'sales' } = req.body;
    
    if (!data || !Array.isArray(data)) {
      return res.status(400).json({
        success: false,
        message: 'Données invalides pour la détection d\'anomalies'
      });
    }
    
    // Appel à l'API du module ML pour détecter les anomalies
    const anomaliesData = await callApi(() => 
      client.post('/ml/anomalies/detect', { data, type })
    );
    
    res.status(200).json({
      success: true,
      data: anomaliesData
    });
  } catch (error) {
    logger.error(`Erreur lors de la détection d'anomalies: ${error.message}`);
    next(error);
  }
};

/**
 * Génération de recommandations pour l'optimisation des stocks
 * @route GET /api/forecast/recommendations/stock
 */
exports.getStockRecommendations = async (req, res, next) => {
  try {
    const { category = 'all' } = req.query;
    
    // Appel à l'API du module ML pour récupérer les recommandations
    const recommendationsData = await callApi(() => 
      client.get('/ml/recommendations/stock', {
        params: { category }
      })
    );
    
    res.status(200).json({
      success: true,
      data: recommendationsData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des recommandations de stock: ${error.message}`);
    next(error);
  }
};

/**
 * Génération de recommandations pour les promotions
 * @route GET /api/forecast/recommendations/promotions
 */
exports.getPromotionRecommendations = async (req, res, next) => {
  try {
    // Appel à l'API du module ML pour récupérer les recommandations de promotions
    const recommendationsData = await callApi(() => 
      client.get('/ml/recommendations/promotions')
    );
    
    res.status(200).json({
      success: true,
      data: recommendationsData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des recommandations de promotions: ${error.message}`);
    next(error);
  }
};

/**
 * Génération de recommandations pour les plats du jour
 * @route GET /api/forecast/recommendations/dishes
 */
exports.getDishRecommendations = async (req, res, next) => {
  try {
    const { date } = req.query;
    
    // Appel à l'API du module ML pour récupérer les recommandations de plats
    const params = date ? { date } : {};
    const recommendationsData = await callApi(() => 
      client.get('/ml/recommendations/dishes', { params })
    );
    
    res.status(200).json({
      success: true,
      data: recommendationsData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des recommandations de plats: ${error.message}`);
    next(error);
  }
};

/**
 * Entraînement manuel du modèle ML
 * @route POST /api/forecast/model/train
 */
exports.trainModel = async (req, res, next) => {
  try {
    const { modelType, parameters } = req.body;
    
    if (!modelType) {
      return res.status(400).json({
        success: false,
        message: 'Type de modèle manquant'
      });
    }
    
    // Appel à l'API du module ML pour entraîner le modèle
    const trainingResponse = await callApi(() => 
      client.post('/ml/model/train', { modelType, parameters })
    );
    
    res.status(200).json({
      success: true,
      data: trainingResponse,
      message: 'Entraînement du modèle lancé avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors de l'entraînement du modèle: ${error.message}`);
    next(error);
  }
};

/**
 * Vérification du statut d'un entraînement de modèle
 * @route GET /api/forecast/model/training-status/:trainingId
 */
exports.getTrainingStatus = async (req, res, next) => {
  try {
    const { trainingId } = req.params;
    
    // Appel à l'API du module ML pour vérifier le statut de l'entraînement
    const statusData = await callApi(() => 
      client.get(`/ml/model/training-status/${trainingId}`)
    );
    
    res.status(200).json({
      success: true,
      data: statusData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération du statut d'entraînement: ${error.message}`);
    next(error);
  }
};
