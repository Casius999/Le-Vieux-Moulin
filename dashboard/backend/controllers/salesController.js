/**
 * Contrôleur pour l'analyse des ventes
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { client, callApi } = require('../utils/apiClient');
const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Récupération des données de vente
 * @route GET /api/sales
 */
exports.getSales = async (req, res, next) => {
  try {
    // Récupération des paramètres de filtrage
    const { 
      startDate, 
      endDate, 
      timeRange = 'week', // 'day', 'week', 'month', 'year'
      product,
      category,
      limit = 100,
      page = 1
    } = req.query;
    
    // Appel à l'API centrale pour récupérer les données de vente
    const salesData = await callApi(() => 
      client.get('/sales', { 
        params: { 
          startDate, 
          endDate, 
          timeRange,
          product,
          category,
          limit,
          page
        } 
      })
    );
    
    res.status(200).json({
      success: true,
      data: salesData.data,
      pagination: salesData.pagination,
      filters: {
        startDate,
        endDate,
        timeRange,
        product,
        category
      }
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des données de vente: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération du résumé des ventes
 * @route GET /api/sales/summary
 */
exports.getSalesSummary = async (req, res, next) => {
  try {
    // Récupération des paramètres
    const { timeRange = 'week' } = req.query;
    
    // Appel à l'API centrale
    const summary = await callApi(() => 
      client.get('/sales/summary', { params: { timeRange } })
    );
    
    res.status(200).json({
      success: true,
      data: summary,
      timeRange
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération du résumé des ventes: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des ventes par produit
 * @route GET /api/sales/products
 */
exports.getSalesByProduct = async (req, res, next) => {
  try {
    // Récupération des paramètres
    const { 
      startDate, 
      endDate, 
      timeRange = 'week',
      limit = 10, // Top N produits
      sort = 'total' // 'total', 'quantity', 'profit'
    } = req.query;
    
    // Appel à l'API centrale
    const productSales = await callApi(() => 
      client.get('/sales/products', { 
        params: { 
          startDate, 
          endDate, 
          timeRange,
          limit,
          sort
        } 
      })
    );
    
    res.status(200).json({
      success: true,
      data: productSales,
      timeRange
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des ventes par produit: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des ventes par heure
 * @route GET /api/sales/hourly
 */
exports.getHourlySales = async (req, res, next) => {
  try {
    // Récupération des paramètres
    const { 
      date, // date spécifique ou aujourd'hui par défaut
      dayOfWeek, // 0-6 (dimanche-samedi)
      aggregateBy = 'day' // 'day', 'weekday'
    } = req.query;
    
    // Appel à l'API centrale
    const hourlySales = await callApi(() => 
      client.get('/sales/hourly', { 
        params: { 
          date, 
          dayOfWeek, 
          aggregateBy 
        } 
      })
    );
    
    res.status(200).json({
      success: true,
      data: hourlySales,
      filters: {
        date,
        dayOfWeek,
        aggregateBy
      }
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des ventes horaires: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des tendances de vente
 * @route GET /api/sales/trends
 */
exports.getSalesTrends = async (req, res, next) => {
  try {
    // Récupération des paramètres
    const { 
      period = 'weekly', // 'daily', 'weekly', 'monthly'
      months = 6, // nombre de mois à analyser
      compareWithPrevious = true // comparer avec la période précédente
    } = req.query;
    
    // Appel à l'API centrale
    const trends = await callApi(() => 
      client.get('/sales/trends', { 
        params: { 
          period, 
          months, 
          compareWithPrevious 
        } 
      })
    );
    
    res.status(200).json({
      success: true,
      data: trends,
      period,
      months,
      compareWithPrevious
    });
  } catch (error) {
    logger.error(`Erreur lors de la récupération des tendances de vente: ${error.message}`);
    next(error);
  }
};
