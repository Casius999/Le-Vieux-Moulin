const logger = require('../utils/logger');

/**
 * Configuration des gestionnaires de WebSocket
 * @param {Object} io - Instance Socket.io
 */
module.exports = (io) => {
  // Middleware pour la journalisation des connexions
  io.use((socket, next) => {
    logger.info(`Nouvelle connexion WebSocket: ${socket.id}`);
    next();
  });

  // Gestionnaire de connexion
  io.on('connection', (socket) => {
    // Événement de déconnexion
    socket.on('disconnect', () => {
      logger.info(`Déconnexion WebSocket: ${socket.id}`);
    });

    // Événement d'erreur
    socket.on('error', (error) => {
      logger.error(`Erreur WebSocket (${socket.id}):`, error);
    });

    // Abonnement aux canaux
    socket.on('subscribe', (channels) => {
      if (Array.isArray(channels)) {
        channels.forEach((channel) => {
          socket.join(channel);
          logger.debug(`Socket ${socket.id} abonné au canal: ${channel}`);
        });
      } else if (typeof channels === 'string') {
        socket.join(channels);
        logger.debug(`Socket ${socket.id} abonné au canal: ${channels}`);
      }
    });

    // Désabonnement des canaux
    socket.on('unsubscribe', (channels) => {
      if (Array.isArray(channels)) {
        channels.forEach((channel) => {
          socket.leave(channel);
          logger.debug(`Socket ${socket.id} désabonné du canal: ${channel}`);
        });
      } else if (typeof channels === 'string') {
        socket.leave(channels);
        logger.debug(`Socket ${socket.id} désabonné du canal: ${channels}`);
      }
    });

    // Exemple d'événement personnalisé
    socket.on('client:action', (data) => {
      // Traitement de l'action client
      logger.debug(`Action reçue du client ${socket.id}:`, data);
      
      // Réponse au client
      socket.emit('server:response', {
        status: 'success',
        message: 'Action traitée avec succès',
        data: { ...data, processed: true }
      });
    });
  });

  // Fonction pour émettre des mises à jour en temps réel
  const emitUpdate = (channel, event, data) => {
    io.to(channel).emit(event, data);
    logger.debug(`Émission sur ${channel}:${event}`, data);
  };

  // Expose la fonction emitUpdate pour être utilisée par d'autres modules
  io.emitUpdate = emitUpdate;

  return io;
};
