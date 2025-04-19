/**
 * Middleware de gestion des erreurs
 * Le Vieux Moulin - Système de gestion intelligente
 */

const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Gestionnaire d'erreur global pour Express
 */
module.exports = (err, req, res, next) => {
  // Log de l'erreur pour le débogage
  logger.error(`${err.name}: ${err.message}`);
  logger.error(err.stack);
  
  // Réponse par défaut
  let statusCode = err.statusCode || 500;
  let message = err.message || 'Erreur serveur';
  
  // Gestion des erreurs spécifiques
  if (err.name === 'ValidationError') {
    statusCode = 400;
    message = 'Erreur de validation des données';
  } else if (err.name === 'JsonWebTokenError') {
    statusCode = 401;
    message = 'Token invalide';
  } else if (err.name === 'TokenExpiredError') {
    statusCode = 401;
    message = 'Token expiré';
  }
  
  // Masquer les détails techniques en production
  const error = process.env.NODE_ENV === 'production' 
    ? { message } 
    : { message, stack: err.stack, details: err.details || err.errors };
  
  res.status(statusCode).json({
    success: false,
    error
  });
};
