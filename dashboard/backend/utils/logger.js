const winston = require('winston');
const path = require('path');
const fs = require('fs');

// Création du dossier de logs s'il n'existe pas
const logDir = 'logs';
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir);
}

// Configurer les niveaux de log
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// Obtenir le niveau de log en fonction de l'environnement
const level = () => {
  const env = process.env.NODE_ENV || 'development';
  const isDevelopment = env === 'development';
  return isDevelopment ? 'debug' : 'http';
};

// Définir les couleurs des niveaux de log
winston.addColors({
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'blue',
});

// Format personnalisé pour les logs
const format = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}`
  )
);

// Format pour la console avec couleurs
const consoleFormat = winston.format.combine(
  winston.format.colorize({ all: true }),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}`
  )
);

// Définir les transports pour les logs
const transports = [
  // Console
  new winston.transports.Console({
    format: consoleFormat,
  }),
  // Fichier d'erreurs
  new winston.transports.File({
    filename: path.join(logDir, 'error.log'),
    level: 'error',
    format,
  }),
  // Fichier combiné
  new winston.transports.File({
    filename: path.join(logDir, 'combined.log'),
    format,
  }),
];

// Créer le logger
const logger = winston.createLogger({
  level: level(),
  levels,
  format,
  transports,
});

module.exports = logger;
