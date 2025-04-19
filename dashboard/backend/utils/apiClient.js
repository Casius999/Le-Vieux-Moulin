/**
 * Client API pour communiquer avec les autres modules
 * Le Vieux Moulin - Système de gestion intelligente
 */

const axios = require('axios');
const config = require('../config');
const { setupLogger } = require('./logger');

const logger = setupLogger();

// Création d'une instance axios avec configuration de base
const apiClient = axios.create({
  baseURL: config.centralApiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': config.centralApiKey
  }
});

// Intercepteur pour les requêtes
apiClient.interceptors.request.use(
  (config) => {
    logger.debug(`Requête API: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    logger.error(`Erreur de requête API: ${error.message}`);
    return Promise.reject(error);
  }
);

// Intercepteur pour les réponses
apiClient.interceptors.response.use(
  (response) => {
    logger.debug(`Réponse API: ${response.status} ${response.statusText}`);
    return response;
  },
  (error) => {
    if (error.response) {
      logger.error(`Erreur de réponse API: ${error.response.status} ${error.response.statusText}`);
      logger.error(`Détails: ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      logger.error(`Erreur de réponse API: Pas de réponse reçue`);
      logger.error(`Requête: ${JSON.stringify(error.request)}`);
    } else {
      logger.error(`Erreur de configuration API: ${error.message}`);
    }
    return Promise.reject(error);
  }
);

/**
 * Fonction pour appeler l'API et gérer les erreurs de manière standardisée
 * @param {Function} apiCall - Fonction qui effectue l'appel API
 * @returns {Promise} Promesse résolue avec les données ou rejetée avec une erreur formattée
 */
const callApi = async (apiCall) => {
  try {
    const response = await apiCall();
    return response.data;
  } catch (error) {
    // Formater l'erreur de manière standardisée
    const formattedError = new Error(
      error.response?.data?.message || 
      error.message || 
      'Une erreur est survenue lors de la communication avec l\'API'
    );
    
    // Ajouter des informations supplémentaires à l'erreur
    formattedError.statusCode = error.response?.status || 500;
    formattedError.details = error.response?.data;
    
    throw formattedError;
  }
};

module.exports = {
  client: apiClient,
  callApi
};
