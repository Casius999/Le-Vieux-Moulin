const logger = require('../utils/logger');

/**
 * Middleware de gestion des erreurs
 * @param {Error} err - L'erreur capturée
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 * @param {Function} next - Fonction next d'Express
 */
module.exports = (err, req, res, next) => {
  // Journaliser l'erreur
  logger.error(`${err.name}: ${err.message}`, {
    stack: err.stack,
    method: req.method,
    url: req.originalUrl,
    ip: req.ip,
  });

  // Définir le statut HTTP approprié
  const statusCode = err.statusCode || 500;

  // Structure de la réponse d'erreur
  const errorResponse = {
    error: true,
    message: process.env.NODE_ENV === 'production' ? 
      'Une erreur est survenue lors du traitement de votre requête.' : 
      err.message,
  };

  // Ajouter la stack en développement pour faciliter le débogage
  if (process.env.NODE_ENV === 'development') {
    errorResponse.stack = err.stack;
  }

  res.status(statusCode).json(errorResponse);
};
