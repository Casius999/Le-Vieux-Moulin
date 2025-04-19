import { io } from 'socket.io-client';

// URL du serveur WebSocket
const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';

// Création d'une instance unique de Socket.io
let socket;

/**
 * Initialise la connexion WebSocket
 * @param {string} token - Token JWT pour l'authentification
 * @returns {SocketIOClient.Socket} Instance de Socket.io
 */
export const initSocket = (token) => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      auth: {
        token,
      },
      reconnectionDelay: 1000,
      reconnection: true,
      reconnectionAttempts: 10,
      transports: ['websocket'],
      agent: false,
      upgrade: false,
      rejectUnauthorized: false,
    });
    
    // Événements de connexion
    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });
    
    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
    });
    
    socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
    });
  }
  
  return socket;
};

/**
 * Déconnecte du serveur WebSocket
 */
export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

/**
 * S'abonne à un événement WebSocket
 * @param {string} event - Nom de l'événement
 * @param {Function} callback - Fonction de rappel à exécuter lors de la réception de l'événement
 */
export const subscribeToEvent = (event, callback) => {
  if (socket) {
    socket.on(event, callback);
  }
};

/**
 * Se désabonne d'un événement WebSocket
 * @param {string} event - Nom de l'événement
 * @param {Function} callback - Fonction de rappel à supprimer
 */
export const unsubscribeFromEvent = (event, callback) => {
  if (socket) {
    socket.off(event, callback);
  }
};

/**
 * Émet un événement WebSocket
 * @param {string} event - Nom de l'événement
 * @param {any} data - Données à envoyer
 */
export const emitEvent = (event, data) => {
  if (socket) {
    socket.emit(event, data);
  }
};

/**
 * Récupère l'ID de la connexion WebSocket
 * @returns {string|null} ID de la connexion ou null si non connecté
 */
export const getSocketId = () => {
  return socket ? socket.id : null;
};

export default {
  initSocket,
  disconnectSocket,
  subscribeToEvent,
  unsubscribeFromEvent,
  emitEvent,
  getSocketId,
};
