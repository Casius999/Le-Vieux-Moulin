const { getIoTData } = require('../services/iotService');
const { getSalesData } = require('../services/salesService');
const { getMarketingData } = require('../services/marketingService');
const { getFinanceData } = require('../services/financeService');
const logger = require('../utils/logger');

/**
 * Récupère les données de vue d'ensemble pour le dashboard
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getOverview = async (req, res) => {
  try {
    // Récupérer les données essentielles des différents services
    const [iotData, salesData, marketingData, financeData] = await Promise.all([
      getIoTData(),
      getSalesData(),
      getMarketingData(),
      getFinanceData()
    ]);

    // Construire la réponse
    const overviewData = {
      stockStatus: iotData.stockSummary,
      equipmentStatus: iotData.equipmentSummary,
      salesSummary: salesData.summary,
      marketingCampaigns: marketingData.activeCampaigns,
      financialState: financeData.summary
    };

    res.json(overviewData);
  } catch (error) {
    logger.error('Error in getOverview:', error);
    res.status(500).json({ error: 'Erreur lors de la récupération des données de vue d\'ensemble' });
  }
};

/**
 * Récupère les KPIs pour le dashboard
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getKPIs = async (req, res) => {
  try {
    // Récupérer la période depuis les query params
    const { start, end } = req.query;

    // Récupérer les données de vente et financières pour calculer les KPIs
    const [salesData, financeData] = await Promise.all([
      getSalesData({ start, end }),
      getFinanceData({ start, end })
    ]);

    // Construire les KPIs
    const kpis = [
      {
        id: 'revenue',
        name: "Chiffre d'affaires du jour",
        value: salesData.summary.dailyRevenue,
        unit: '€',
        trend: salesData.summary.revenueTrend,
        status: salesData.summary.revenueTrend >= 0 ? 'success' : 'warning'
      },
      {
        id: 'tickets',
        name: "Nombre de tickets",
        value: salesData.summary.ticketCount,
        unit: '',
        trend: salesData.summary.ticketCountTrend,
        status: 'info'
      },
      {
        id: 'average_ticket',
        name: "Ticket moyen",
        value: salesData.summary.averageTicket,
        unit: '€',
        trend: salesData.summary.averageTicketTrend,
        status: salesData.summary.averageTicketTrend >= 0 ? 'success' : 'warning'
      },
      {
        id: 'margin',
        name: "Marge brute",
        value: financeData.summary.grossMargin,
        unit: '%',
        trend: financeData.summary.grossMarginTrend,
        status: financeData.summary.grossMargin >= 65 ? 'success' : 
                financeData.summary.grossMargin >= 60 ? 'warning' : 'danger'
      }
    ];

    res.json(kpis);
  } catch (error) {
    logger.error('Error in getKPIs:', error);
    res.status(500).json({ error: 'Erreur lors de la récupération des KPIs' });
  }
};

/**
 * Récupère les alertes actives
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getAlerts = async (req, res) => {
  try {
    // Récupérer les alertes des différents systèmes
    const [iotAlerts, salesAlerts, marketingAlerts, financeAlerts] = await Promise.all([
      getIoTData().then(data => data.alerts || []),
      getSalesData().then(data => data.alerts || []),
      getMarketingData().then(data => data.alerts || []),
      getFinanceData().then(data => data.alerts || [])
    ]);

    // Combiner toutes les alertes
    const allAlerts = [
      ...iotAlerts,
      ...salesAlerts,
      ...marketingAlerts,
      ...financeAlerts
    ];

    // Trier par importance et date
    const sortedAlerts = allAlerts.sort((a, b) => {
      // D'abord par niveau de sévérité
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
      
      if (severityDiff !== 0) return severityDiff;
      
      // Ensuite par date (plus récente d'abord)
      return new Date(b.timestamp) - new Date(a.timestamp);
    });

    res.json(sortedAlerts);
  } catch (error) {
    logger.error('Error in getAlerts:', error);
    res.status(500).json({ error: 'Erreur lors de la récupération des alertes' });
  }
};

/**
 * Récupère la configuration du dashboard
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getConfig = (req, res) => {
  // Cette fonction devrait récupérer la configuration depuis la base de données
  // Pour l'instant, on retourne une configuration statique
  const config = {
    refreshInterval: 60000, // 1 minute
    defaultDateRange: 'today',
    defaultView: 'overview',
    widgets: {
      overview: ['kpi', 'sales', 'alerts', 'stock'],
      iot: ['stockLevels', 'equipment', 'consumption', 'predictions'],
      sales: ['dailySales', 'topProducts', 'salesByCategory', 'hourlyDistribution'],
      marketing: ['campaigns', 'socialMedia', 'promotions', 'customerFeedback'],
      finance: ['summary', 'revenue', 'expenses', 'profitability'],
      staff: ['schedule', 'performance', 'costs', 'optimization']
    },
    alerts: {
      thresholds: {
        stock: {
          low: 30, // pourcentage
          critical: 10 // pourcentage
        },
        finance: {
          margin: 60 // pourcentage en dessous duquel une alerte est émise
        }
      }
    }
  };

  res.json(config);
};

/**
 * Met à jour la configuration du dashboard
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.updateConfig = (req, res) => {
  const newConfig = req.body;

  // Cette fonction devrait sauvegarder la configuration dans la base de données
  // Pour l'instant, on simule une mise à jour réussie
  logger.info('Configuration du dashboard mise à jour', { config: newConfig });

  res.json({ success: true, message: 'Configuration mise à jour avec succès' });
};
