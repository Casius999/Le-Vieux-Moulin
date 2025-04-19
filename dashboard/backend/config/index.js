/**
 * Configuration du backend pour le dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

require('dotenv').config();

module.exports = {
  // Configuration du serveur
  port: process.env.PORT || 5000,
  nodeEnv: process.env.NODE_ENV || 'development',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  
  // Sécurité
  jwtSecret: process.env.JWT_SECRET || 'your_jwt_secret_key',
  jwtExpiration: process.env.JWT_EXPIRATION || '1d',
  
  // API Centrale
  centralApiUrl: process.env.CENTRAL_API_URL || 'http://localhost:8000/api',
  centralApiKey: process.env.CENTRAL_API_KEY || 'your_api_key',
  
  // Base de données (optionnel)
  mongodbUri: process.env.MONGODB_URI || 'mongodb://localhost:27017/dashboard',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  sessionSecret: process.env.SESSION_SECRET || 'your_session_secret',
  
  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',
  logFile: process.env.LOG_FILE || 'logs/app.log',
  
  // Mise à jour en temps réel
  refreshInterval: parseInt(process.env.REFRESH_INTERVAL) || 60000, // 1 minute par défaut
};
