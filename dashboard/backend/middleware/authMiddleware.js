/**
 * Middleware d'authentification
 * Le Vieux Moulin - Système de gestion intelligente
 */

const jwt = require('jsonwebtoken');
const config = require('../config');
const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Middleware de vérification du token JWT
 */
exports.authenticate = (req, res, next) => {
  try {
    // Récupération du token depuis les headers
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ message: 'Accès non autorisé. Token manquant.' });
    }
    
    const token = authHeader.split(' ')[1];
    
    // Vérification du token
    const decoded = jwt.verify(token, config.jwtSecret);
    
    // Ajouter les informations utilisateur à la requête
    req.user = decoded;
    
    next();
  } catch (error) {
    logger.error(`Erreur d'authentification: ${error.message}`);
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ message: 'Token expiré.' });
    }
    
    return res.status(401).json({ message: 'Accès non autorisé. Token invalide.' });
  }
};

/**
 * Middleware de vérification des rôles
 * @param {Array} roles - Tableau des rôles autorisés
 */
exports.authorize = (roles = []) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ message: 'Accès non autorisé. Utilisateur non authentifié.' });
    }
    
    if (roles.length && !roles.includes(req.user.role)) {
      return res.status(403).json({ message: 'Accès interdit. Privilèges insuffisants.' });
    }
    
    next();
  };
};
