/**
 * Contrôleur pour la vue d'ensemble du dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { client, callApi } = require('../utils/apiClient');
const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Récupération des données pour la vue d'ensemble du dashboard
 * @route GET /api/dashboard/overview
 */
exports.getOverview = async (req, res, next) => {
  try {
    // Appel à l'API centrale pour agréger les données pertinentes
    const overview = await callApi(() => 
      client.get('/dashboard/overview')
    );
    
    // Si l'API centrale ne fournit pas ces données, nous pouvons les agréger ici
    // en appelant d'autres endpoints et en combinant les résultats
    
    res.status(200).json({
      success: true,
      data: overview,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des données du dashboard: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des indicateurs clés de performance (KPI)
 * @route GET /api/dashboard/kpi
 */
exports.getKpi = async (req, res, next) => {
  try {
    // Récupération des paramètres de la requête
    const { period = 'day' } = req.query; // 'day', 'week', 'month', 'year'
    
    // Appel à l'API centrale pour obtenir les KPI
    const kpiData = await callApi(() => 
      client.get('/dashboard/kpi', { params: { period } })
    );
    
    res.status(200).json({
      success: true,
      data: kpiData,
      period,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des KPI: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des alertes pour le dashboard
 * @route GET /api/dashboard/alerts
 */
exports.getAlerts = async (req, res, next) => {
  try {
    // Appel à l'API centrale pour obtenir les alertes
    const alerts = await callApi(() => 
      client.get('/dashboard/alerts')
    );
    
    res.status(200).json({
      success: true,
      data: alerts,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des alertes: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération de la configuration personnalisée du dashboard
 * @route GET /api/dashboard/config
 */
exports.getConfig = async (req, res, next) => {
  try {
    // Récupération de la configuration spécifique à l'utilisateur
    const userId = req.user.id;
    
    // Appel à l'API centrale ou à la base de données locale
    const userConfig = await callApi(() => 
      client.get(`/users/${userId}/dashboard-config`)
    );
    
    res.status(200).json({
      success: true,
      data: userConfig
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération de la configuration: ${error.message}`);
    next(error);
  }
};

/**
 * Mise à jour de la configuration personnalisée du dashboard
 * @route PUT /api/dashboard/config
 */
exports.updateConfig = async (req, res, next) => {
  try {
    const userId = req.user.id;
    const config = req.body;
    
    // Validation des données de configuration
    if (!config || typeof config !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Configuration invalide'
      });
    }
    
    // Mise à jour de la configuration via l'API centrale
    const updatedConfig = await callApi(() => 
      client.put(`/users/${userId}/dashboard-config`, config)
    );
    
    res.status(200).json({
      success: true,
      data: updatedConfig,
      message: 'Configuration mise à jour avec succès'
    });
  } catch (error) {
    logger.error(`Erreur lors de la mise à jour de la configuration: ${error.message}`);
    next(error);
  }
};
