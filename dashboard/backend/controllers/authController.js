/**
 * Contrôleur d'authentification
 * Le Vieux Moulin - Système de gestion intelligente
 */

const jwt = require('jsonwebtoken');
const config = require('../config');
const { client, callApi } = require('../utils/apiClient');
const { setupLogger } = require('../utils/logger');

const logger = setupLogger();

/**
 * Génération d'un token JWT
 * @param {Object} user - Informations utilisateur
 * @returns {String} Token JWT
 */
const generateToken = (user) => {
  return jwt.sign(
    {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role
    },
    config.jwtSecret,
    { expiresIn: config.jwtExpiration }
  );
};

/**
 * Connexion de l'utilisateur
 * @route POST /api/auth/login
 */
exports.login = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Veuillez fournir un email et un mot de passe'
      });
    }
    
    // Authentification via l'API centrale
    const userData = await callApi(() => 
      client.post('/auth/login', { email, password })
    );
    
    // Génération du token JWT
    const token = generateToken(userData.user);
    
    res.status(200).json({
      success: true,
      token,
      user: {
        id: userData.user.id,
        name: userData.user.name,
        email: userData.user.email,
        role: userData.user.role
      }
    });
  } catch (error) {
    logger.error(`Erreur de connexion: ${error.message}`);
    
    // Gestion spécifique des erreurs d'authentification
    if (error.statusCode === 401) {
      return res.status(401).json({
        success: false,
        message: 'Email ou mot de passe invalide'
      });
    }
    
    next(error);
  }
};

/**
 * Rafraîchissement du token JWT
 * @route POST /api/auth/refresh
 */
exports.refreshToken = async (req, res, next) => {
  try {
    const { refreshToken } = req.body;
    
    if (!refreshToken) {
      return res.status(400).json({
        success: false,
        message: 'Refresh token requis'
      });
    }
    
    // Vérification du refresh token via l'API centrale
    const tokenData = await callApi(() => 
      client.post('/auth/refresh', { refreshToken })
    );
    
    // Génération d'un nouveau token JWT
    const token = generateToken(tokenData.user);
    
    res.status(200).json({
      success: true,
      token,
      user: {
        id: tokenData.user.id,
        name: tokenData.user.name,
        email: tokenData.user.email,
        role: tokenData.user.role
      }
    });
  } catch (error) {
    logger.error(`Erreur de rafraîchissement du token: ${error.message}`);
    
    // Gestion spécifique des erreurs de refresh token
    if (error.statusCode === 401) {
      return res.status(401).json({
        success: false,
        message: 'Refresh token invalide ou expiré'
      });
    }
    
    next(error);
  }
};

/**
 * Déconnexion de l'utilisateur
 * @route POST /api/auth/logout
 */
exports.logout = async (req, res, next) => {
  try {
    // Invalidation du token via l'API centrale (optionnel)
    await callApi(() => 
      client.post('/auth/logout', { userId: req.user.id })
    );
    
    res.status(200).json({
      success: true,
      message: 'Déconnexion réussie'
    });
  } catch (error) {
    logger.error(`Erreur de déconnexion: ${error.message}`);
    next(error);
  }
};

/**
 * Récupération des informations de l'utilisateur connecté
 * @route GET /api/auth/me
 */
exports.getCurrentUser = async (req, res, next) => {
  try {
    // Récupération des informations utilisateur à jour depuis l'API centrale
    const userData = await callApi(() => 
      client.get(`/users/${req.user.id}`)
    );
    
    res.status(200).json({
      success: true,
      user: {
        id: userData.id,
        name: userData.name,
        email: userData.email,
        role: userData.role,
        // Autres informations utilisateur pertinentes
      }
    });
  } catch (error) {
    logger.error(`Erreur de récupération des données utilisateur: ${error.message}`);
    next(error);
  }
};
