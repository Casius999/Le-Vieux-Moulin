/**
 * Configuration du logger
 * Le Vieux Moulin - Système de gestion intelligente
 */

const winston = require('winston');
const fs = require('fs');
const path = require('path');
const config = require('../config');

/**
 * Configuration et initialisation du logger Winston
 */
exports.setupLogger = () => {
  // Création du dossier de logs s'il n'existe pas
  const logDir = path.dirname(config.logFile);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  // Format personnalisé pour les logs
  const customFormat = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ level, message, timestamp, stack }) => {
      return `${timestamp} ${level.toUpperCase()}: ${message}${stack ? `\n${stack}` : ''}`;
    })
  );
  
  // Configuration des transports (destinations des logs)
  const transports = [
    // Logs dans un fichier avec rotation
    new winston.transports.File({
      filename: config.logFile,
      maxsize: 5242880, // 5MB
      maxFiles: 5,
      format: customFormat
    })
  ];
  
  // Ajouter les logs console en développement
  if (process.env.NODE_ENV !== 'production') {
    transports.push(
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          customFormat
        )
      })
    );
  }
  
  // Création du logger
  return winston.createLogger({
    level: config.logLevel,
    levels: winston.config.npm.levels,
    transports,
    exitOnError: false
  });
};
