/**
 * Configuration de l'application Express pour le backend du dashboard
 * Le Vieux Moulin - Système de gestion intelligente
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const path = require('path');
const { createServer } = require('http');
const { Server } = require('socket.io');
const config = require('./config');
const routes = require('./routes');
const socketHandlers = require('./socketHandlers');
const errorMiddleware = require('./middleware/errorMiddleware');
const { setupLogger } = require('./utils/logger');

// Configuration du logger
const logger = setupLogger();

// Initialisation de l'application Express
const app = express();
const httpServer = createServer(app);

// Configuration du serveur Socket.io
const io = new Server(httpServer, {
  cors: {
    origin: config.corsOrigin,
    methods: ['GET', 'POST'],
    credentials: true
  }
});

// Middleware
app.use(helmet()); // Sécurisation des en-têtes HTTP
app.use(cors({ origin: config.corsOrigin, credentials: true }));
app.use(express.json()); // Parsing JSON
app.use(express.urlencoded({ extended: true }));
app.use(compression()); // Compression des réponses
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Routes API
app.use('/api', routes);

// Servir les fichiers statiques du frontend en production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../frontend/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/build/index.html'));
  });
}

// Middleware de gestion d'erreurs
app.use(errorMiddleware);

// Configuration des gestionnaires de Socket.io
socketHandlers(io);

// Export du serveur HTTP pour server.js
module.exports = { httpServer, app, io };
