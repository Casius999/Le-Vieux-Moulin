/**
 * Configuration des gestionnaires de WebSocket
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { setupLogger } = require('../utils/logger');
const stockHandlers = require('./stockHandlers');
const salesHandlers = require('./salesHandlers');
systemHandlers = require('./systemHandlers');

const logger = setupLogger();

/**
 * Configuration principale des WebSockets
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 */
module.exports = (io) => {
  // Middleware d'authentification pour Socket.io
  io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    
    // Vérification du token (simplifiée ici, à implémenter selon vos besoins)
    if (!token) {
      return next(new Error('Authentification requise'));
    }
    
    // Vous pouvez vérifier le token JWT ici
    // jwt.verify(token, config.jwtSecret, (err, decoded) => {...})
    
    // Pour simplifier, nous acceptons tous les tokens ici
    next();
  });
  
  // Gestion des connexions client
  io.on('connection', (socket) => {
    const clientId = socket.id;
    logger.info(`Nouvelle connexion WebSocket: ${clientId}`);
    
    // Enregistrement des gestionnaires spécifiques
    stockHandlers(io, socket);
    salesHandlers(io, socket);
    systemHandlers(io, socket);
    
    // Gestion de la déconnexion
    socket.on('disconnect', () => {
      logger.info(`Déconnexion WebSocket: ${clientId}`);
    });
    
    // Envoyer un événement de bienvenue
    socket.emit('system:welcome', {
      message: 'Connecté au serveur Le Vieux Moulin',
      timestamp: new Date().toISOString()
    });
  });
  
  // Configuration des canaux de données
  setupDataChannels(io);
  
  return io;
};

/**
 * Configuration des canaux de données pour les mises à jour en temps réel
 * @param {SocketIO.Server} io - Instance du serveur Socket.io
 */
const setupDataChannels = (io) => {
  // Canal pour les stocks
  const stocksNamespace = io.of('/stocks');
  stocksNamespace.on('connection', (socket) => {
    logger.info(`Connexion au canal stocks: ${socket.id}`);
    
    // Gestion spécifique au canal stocks
    socket.on('subscribe', (categories) => {
      if (Array.isArray(categories)) {
        categories.forEach(category => {
          socket.join(`category:${category}`);
        });
      }
    });
    
    socket.on('unsubscribe', (categories) => {
      if (Array.isArray(categories)) {
        categories.forEach(category => {
          socket.leave(`category:${category}`);
        });
      }
    });
  });
  
  // Canal pour les ventes
  const salesNamespace = io.of('/sales');
  salesNamespace.on('connection', (socket) => {
    logger.info(`Connexion au canal ventes: ${socket.id}`);
    
    // Gestion spécifique au canal ventes
    socket.on('subscribe', (types) => {
      if (Array.isArray(types)) {
        types.forEach(type => {
          socket.join(`type:${type}`);
        });
      }
    });
  });
  
  // Canal pour les alertes système
  const alertsNamespace = io.of('/alerts');
  alertsNamespace.on('connection', (socket) => {
    logger.info(`Connexion au canal alertes: ${socket.id}`);
    
    // Gestion spécifique au canal alertes
    socket.on('subscribe', (severity) => {
      if (Array.isArray(severity)) {
        severity.forEach(level => {
          socket.join(`severity:${level}`);
        });
      }
    });
  });
};
