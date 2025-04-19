import axios from 'axios';

// Configuration de base d'Axios
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur de requête pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur de réponse pour gérer les erreurs d'authentification
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Gestion des erreurs 401 (non autorisé)
    if (error.response && error.response.status === 401) {
      // Redirection vers la page de connexion si le token est expiré
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
