/**
 * Contrôleur pour la gestion des stocks
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { client, callApi } = require('../utils/apiClient');
const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Récupération de tous les stocks
 * @route GET /api/stocks
 */
exports.getAllStocks = async (req, res, next) => {
  try {
    // Récupération des paramètres de filtrage
    const { 
      category,
      minLevel,
      maxLevel,
      sortBy = 'name',
      sortOrder = 'asc',
      limit = 100,
      page = 1
    } = req.query;
    
    // Appel à l'API centrale
    const stocksData = await callApi(() => 
      client.get('/stocks', { 
        params: { 
          category, 
          minLevel, 
          maxLevel,
          sortBy,
          sortOrder,
          limit,
          page
        } 
      })
    );
    
    res.status(200).json({
      success: true,
      data: stocksData.data,
      pagination: stocksData.pagination,
      filters: {
        category,
        minLevel,
        maxLevel
      }
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des stocks: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération d'un stock spécifique par ID
 * @route GET /api/stocks/:id
 */
exports.getStockById = async (req, res, next) => {
  try {
    const { id } = req.params;
    
    // Appel à l'API centrale
    const stockItem = await callApi(() => 
      client.get(`/stocks/${id}`)
    );
    
    // Récupération des données historiques pour ce stock
    const history = await callApi(() => 
      client.get(`/stocks/${id}/history`)
    );
    
    // Fusion des données
    const stockData = {
      ...stockItem,
      history
    };
    
    res.status(200).json({
      success: true,
      data: stockData
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération du stock ${req.params.id}: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des catégories de stock
 * @route GET /api/stocks/categories
 */
exports.getStockCategories = async (req, res, next) => {
  try {
    // Appel à l'API centrale
    const categories = await callApi(() => 
      client.get('/stocks/categories')
    );
    
    res.status(200).json({
      success: true,
      data: categories
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des catégories de stock: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des alertes de stock
 * @route GET /api/stocks/alerts
 */
exports.getStockAlerts = async (req, res, next) => {
  try {
    // Récupération des paramètres
    const { 
      type = 'all', // 'low', 'critical', 'expiring', 'all'
      limit = 50
    } = req.query;
    
    // Appel à l'API centrale
    const alerts = await callApi(() => 
      client.get('/stocks/alerts', { 
        params: { 
          type, 
          limit 
        } 
      })
    );
    
    res.status(200).json({
      success: true,
      data: alerts,
      type
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des alertes de stock: ${error.message}`);
    next(error);
  }
};
