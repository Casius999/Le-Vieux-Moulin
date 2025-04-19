require('dotenv').config();
const app = require('./app');
const http = require('http');
const { Server } = require('socket.io');
const logger = require('./utils/logger');

// Création du serveur HTTP
const server = http.createServer(app);

// Configuration de Socket.io
const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    methods: ['GET', 'POST'],
    credentials: true,
  },
});

// Configuration des gestionnaires de Socket.io
require('./websocket/handlers')(io);

// Port d'écoute
const PORT = process.env.PORT || 5000;

// Démarrage du serveur
server.listen(PORT, () => {
  logger.info(`Serveur démarré sur le port ${PORT} en mode ${process.env.NODE_ENV}`);
});

// Gestion des erreurs non capturées
process.on('uncaughtException', (error) => {
  logger.error('Erreur non capturée:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Promesse rejetée non gérée:', reason);
});

// Export pour les tests
module.exports = server;
