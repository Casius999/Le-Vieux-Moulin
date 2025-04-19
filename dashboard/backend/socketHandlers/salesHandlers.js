/**
 * Gestionnaires WebSocket pour les ventes
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Configuration des gestionnaires d'événements pour les ventes
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {SocketIO.Socket} socket - Socket client
 */
module.exports = (io, socket) => {
  // S'abonner aux mises à jour de ventes en temps réel
  socket.on('sale:subscribe_realtime', () => {
    logger.debug(`Client ${socket.id} s'abonne aux ventes en temps réel`);
    socket.join('sales:realtime');
  });
  
  // Se désabonner des mises à jour de ventes en temps réel
  socket.on('sale:unsubscribe_realtime', () => {
    logger.debug(`Client ${socket.id} se désabonne des ventes en temps réel`);
    socket.leave('sales:realtime');
  });
  
  // S'abonner aux mises à jour de KPI
  socket.on('sale:subscribe_kpi', () => {
    logger.debug(`Client ${socket.id} s'abonne aux KPI de ventes`);
    socket.join('sales:kpi');
  });
  
  // Demande de mise à jour manuelle des KPI de vente
  socket.on('sale:request_kpi_update', async () => {
    logger.debug(`Client ${socket.id} demande une mise à jour des KPI de vente`);
    
    try {
      // Ici, vous pourriez déclencher une récupération de données fraîches
      // Pour cet exemple, nous simulons une réponse
      const kpiData = {
        dailyTotal: 1865.50,
        averageTicket: 37.31,
        customerCount: 50,
        timestamp: new Date().toISOString()
      };
      
      // Envoi des données uniquement au client qui a fait la demande
      socket.emit('sale:kpi_update', kpiData);
    } catch (error) {
      logger.error(`Erreur lors de la mise à jour des KPI de vente: ${error.message}`);
      socket.emit('error', { message: 'Erreur lors de la récupération des KPI de vente' });
    }
  });
};

/**
 * Émission d'un événement de nouvelle vente
 * Cette fonction serait appelée depuis un autre module, par exemple un listener de caisse
 * 
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {Object} data - Données de la vente
 */
exports.emitNewSale = (io, data) => {
  const { saleId, total, items, timestamp } = data;
  
  logger.debug(`Émission de nouvelle vente: ${saleId}, ${total}€`);
  
  // Émission aux clients abonnés aux ventes en temps réel
  io.to('sales:realtime').emit('sale:new', {
    saleId,
    total,
    items: items.length,
    timestamp
  });
  
  // Émission au canal de ventes
  io.of('/sales').emit('sale:new', {
    saleId,
    total,
    items: items.length,
    timestamp
  });
};

/**
 * Émission d'une mise à jour des KPI de vente
 * Cette fonction serait appelée périodiquement ou après un lot de ventes
 * 
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {Object} data - Données des KPI
 */
exports.emitSalesKpiUpdate = (io, data) => {
  const { dailyTotal, averageTicket, customerCount, timestamp } = data;
  
  logger.debug(`Émission de mise à jour KPI: Total ${dailyTotal}€, Ticket moyen ${averageTicket}€`);
  
  // Émission aux clients abonnés aux KPI
  io.to('sales:kpi').emit('sale:kpi_update', {
    dailyTotal,
    averageTicket,
    customerCount,
    timestamp
  });
  
  // Émission au canal de ventes
  io.of('/sales').emit('sale:kpi_update', {
    dailyTotal,
    averageTicket,
    customerCount,
    timestamp
  });
};
