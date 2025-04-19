/**
 * Gestionnaires WebSocket pour les stocks
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Configuration des gestionnaires d'événements pour les stocks
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {SocketIO.Socket} socket - Socket client
 */
module.exports = (io, socket) => {
  // S'abonner aux mises à jour de stock
  socket.on('stock:subscribe', (items) => {
    logger.debug(`Client ${socket.id} s'abonne aux mises à jour de stock: ${JSON.stringify(items)}`);
    
    if (Array.isArray(items)) {
      items.forEach(itemId => {
        socket.join(`stock:${itemId}`);
      });
    }
  });
  
  // Se désabonner des mises à jour de stock
  socket.on('stock:unsubscribe', (items) => {
    logger.debug(`Client ${socket.id} se désabonne des mises à jour de stock: ${JSON.stringify(items)}`);
    
    if (Array.isArray(items)) {
      items.forEach(itemId => {
        socket.leave(`stock:${itemId}`);
      });
    }
  });
  
  // S'abonner aux alertes de stock
  socket.on('stock:subscribe_alerts', (types) => {
    logger.debug(`Client ${socket.id} s'abonne aux alertes de stock: ${JSON.stringify(types)}`);
    
    if (Array.isArray(types)) {
      types.forEach(type => {
        socket.join(`stock_alert:${type}`);
      });
    } else {
      // S'abonner à toutes les alertes
      socket.join('stock_alert:all');
    }
  });
  
  // Demande de mise à jour manuelle des données de stock
  socket.on('stock:request_update', async () => {
    logger.debug(`Client ${socket.id} demande une mise à jour des données de stock`);
    
    try {
      // Ici, vous pourriez déclencher une récupération de données fraîches 
      // auprès de l'API centrale ou des capteurs IoT
      
      // Pour cet exemple, nous simulons une réponse
      const stockData = {
        lastUpdated: new Date().toISOString(),
        items: [
          {
            id: 'item1',
            name: 'Farine',
            currentLevel: 25.5,
            unit: 'kg',
            status: 'ok'
          },
          {
            id: 'item2',
            name: 'Mozzarella',
            currentLevel: 4.2,
            unit: 'kg',
            status: 'warning'
          }
        ]
      };
      
      // Envoi des données uniquement au client qui a fait la demande
      socket.emit('stock:update', stockData);
    } catch (error) {
      logger.error(`Erreur lors de la mise à jour des données de stock: ${error.message}`);
      socket.emit('error', { message: 'Erreur lors de la récupération des données de stock' });
    }
  });
};

/**
 * Émission d'un événement de mise à jour de stock
 * Cette fonction serait appelée depuis un autre module, par exemple un listener MQTT
 * 
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {Object} data - Données de mise à jour de stock
 */
exports.emitStockUpdate = (io, data) => {
  const { itemId, currentLevel, timestamp, change, reason } = data;
  
  logger.debug(`Émission de mise à jour de stock: ${itemId}, ${currentLevel}${data.unit || ''}`);
  
  // Émission à tous les clients abonnés à cet article
  io.to(`stock:${itemId}`).emit('stock:update', {
    itemId,
    currentLevel,
    timestamp,
    change,
    reason
  });
  
  // Émission globale pour les tableaux de bord
  io.of('/stocks').emit('stock:update', {
    itemId,
    currentLevel,
    timestamp,
    change,
    reason
  });
};

/**
 * Émission d'une alerte de stock
 * Cette fonction serait appelée depuis un autre module, par exemple un service de surveillance
 * 
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {Object} data - Données de l'alerte
 */
exports.emitStockAlert = (io, data) => {
  const { itemId, alertType, level, timestamp } = data;
  
  logger.debug(`Émission d'alerte de stock: ${alertType} pour ${itemId}`);
  
  // Émission aux clients abonnés à ce type d'alerte
  io.to(`stock_alert:${alertType}`).emit('stock:alert', data);
  
  // Émission aux clients abonnés à toutes les alertes
  io.to('stock_alert:all').emit('stock:alert', data);
  
  // Émission au canal d'alertes général
  io.of('/alerts').to(`severity:${alertType === 'critical' ? 'high' : 'medium'}`).emit('alert', {
    source: 'stock',
    type: alertType,
    itemId,
    message: `Niveau de stock ${alertType} pour ${itemId}: ${level}`,
    timestamp
  });
};
