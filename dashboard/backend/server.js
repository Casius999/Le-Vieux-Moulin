/**
 * Point d'entrée du serveur backend pour le dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { httpServer } = require('./app');
const config = require('./config');
const { setupLogger } = require('./utils/logger');

// Configuration du logger
const logger = setupLogger();

// Démarrage du serveur
const PORT = config.port || 5000;

httpServer.listen(PORT, () => {
  logger.info(`Server running in ${process.env.NODE_ENV} mode on port ${PORT}`);
});

// Gestion des erreurs non capturées
process.on('uncaughtException', (err) => {
  logger.error('UNCAUGHT EXCEPTION! 💥 Shutting down...');
  logger.error(`${err.name}: ${err.message}`);
  logger.error(err.stack);
  process.exit(1);
});

process.on('unhandledRejection', (err) => {
  logger.error('UNHANDLED REJECTION! 💥 Shutting down...');
  logger.error(`${err.name}: ${err.message}`);
  logger.error(err.stack);
  httpServer.close(() => {
    process.exit(1);
  });
});
