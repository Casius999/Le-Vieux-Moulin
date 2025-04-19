/**
 * Gestionnaires WebSocket pour les notifications système
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Configuration des gestionnaires d'événements pour les notifications système
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {SocketIO.Socket} socket - Socket client
 */
module.exports = (io, socket) => {
  // S'abonner aux notifications système
  socket.on('system:subscribe_notifications', (types = []) => {
    logger.debug(`Client ${socket.id} s'abonne aux notifications système: ${JSON.stringify(types)}`);
    
    if (Array.isArray(types) && types.length > 0) {
      types.forEach(type => {
        socket.join(`notification:${type}`);
      });
    } else {
      // S'abonner à toutes les notifications
      socket.join('notification:all');
    }
  });
  
  // Se désabonner des notifications système
  socket.on('system:unsubscribe_notifications', (types = []) => {
    logger.debug(`Client ${socket.id} se désabonne des notifications système: ${JSON.stringify(types)}`);
    
    if (Array.isArray(types) && types.length > 0) {
      types.forEach(type => {
        socket.leave(`notification:${type}`);
      });
    } else {
      // Se désabonner de toutes les notifications
      socket.leave('notification:all');
    }
  });
  
  // Récupérer les dernières notifications
  socket.on('system:get_recent_notifications', async () => {
    logger.debug(`Client ${socket.id} demande les dernières notifications`);
    
    try {
      // Ici, vous pourriez récupérer les notifications récentes depuis une base de données
      // Pour cet exemple, nous simulons une réponse
      const notifications = [
        {
          id: 'notif1',
          type: 'info',
          message: 'Mise à jour du système terminée',
          timestamp: new Date(Date.now() - 3600000).toISOString() // 1 heure avant
        },
        {
          id: 'notif2',
          type: 'warning',
          message: 'Stock de mozzarella en dessous du seuil d\'alerte',
          timestamp: new Date(Date.now() - 1800000).toISOString() // 30 minutes avant
        },
        {
          id: 'notif3',
          type: 'error',
          message: 'Four n°2 en panne',
          timestamp: new Date(Date.now() - 600000).toISOString() // 10 minutes avant
        }
      ];
      
      socket.emit('system:recent_notifications', notifications);
    } catch (error) {
      logger.error(`Erreur lors de la récupération des notifications récentes: ${error.message}`);
      socket.emit('error', { message: 'Erreur lors de la récupération des notifications récentes' });
    }
  });
  
  // Marquer une notification comme lue
  socket.on('system:mark_notification_read', (notificationId) => {
    logger.debug(`Client ${socket.id} marque la notification ${notificationId} comme lue`);
    
    // Ici, vous mettriez à jour l'état de la notification dans votre base de données
    
    // Confirmation au client
    socket.emit('system:notification_marked_read', { id: notificationId });
  });
};

/**
 * Émission d'une notification système
 * Cette fonction serait appelée depuis d'autres parties de l'application
 * 
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 * @param {Object} data - Données de la notification
 */
exports.emitSystemNotification = (io, data) => {
  const { id, type, message, details, timestamp } = data;
  
  logger.debug(`Émission de notification système: ${type} - ${message}`);
  
  const notification = {
    id: id || `notif_${Date.now()}`,
    type,
    message,
    details,
    timestamp: timestamp || new Date().toISOString()
  };
  
  // Émission aux clients abonnés à ce type de notification
  io.to(`notification:${type}`).emit('system:notification', notification);
  
  // Émission aux clients abonnés à toutes les notifications
  io.to('notification:all').emit('system:notification', notification);
  
  // Émission au canal d'alertes général pour les types warning et error
  if (type === 'warning' || type === 'error') {
    io.of('/alerts').to(`severity:${type === 'error' ? 'high' : 'medium'}`).emit('alert', {
      source: 'system',
      type,
      message,
      details,
      timestamp: notification.timestamp
    });
  }
};
