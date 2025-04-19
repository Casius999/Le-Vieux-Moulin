import { io } from 'socket.io-client';
import { store } from '../store';
import { updateStockItem, updateEquipment } from '../store/slices/stocksSlice';
import { addSale } from '../store/slices/salesSlice';

let socket = null;

/**
 * Initialise la connexion WebSocket pour les mises à jour en temps réel
 * @returns {Function} Fonction de nettoyage pour déconnecter le socket
 */
export const initializeWebSocket = () => {
  const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';
  
  // Créer une connexion socket
  socket = io(SOCKET_URL, {
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
  });

  // Gérer les événements de connexion
  socket.on('connect', () => {
    console.log('WebSocket connecté');
  });

  socket.on('disconnect', () => {
    console.log('WebSocket déconnecté');
  });

  socket.on('connect_error', (error) => {
    console.error('Erreur de connexion WebSocket:', error);
  });

  // Gestion des mises à jour en temps réel
  setupEventListeners();

  // Fonction de nettoyage
  return () => {
    if (socket) {
      socket.disconnect();
    }
  };
};

/**
 * Configure les écouteurs d'événements pour les données en temps réel
 */
const setupEventListeners = () => {
  // Mises à jour des stocks
  socket.on('stock:update', (data) => {
    store.dispatch(updateStockItem(data));
  });

  // Alertes de stock
  socket.on('stock:alert', (data) => {
    // Gérer l'alerte stock (pourrait être ajouté à un tableau d'alertes)
    console.log('Alerte stock:', data);
  });

  // Mises à jour des équipements
  socket.on('equipment:status', (data) => {
    store.dispatch(updateEquipment(data));
  });

  // Nouvelles ventes
  socket.on('sale:new', (data) => {
    store.dispatch(addSale(data));
  });

  // Notifications système
  socket.on('system:notification', (data) => {
    console.log('Notification système:', data);
    // Afficher une notification ou mise à jour d'état
  });
};

/**
 * Émet un événement via le WebSocket
 * @param {string} event - Nom de l'événement
 * @param {*} data - Données à envoyer
 */
export const emitEvent = (event, data) => {
  if (socket && socket.connected) {
    socket.emit(event, data);
  } else {
    console.error('Impossible d\'émettre un événement: WebSocket non connecté');
  }
};

export default {
  initializeWebSocket,
  emitEvent,
};
