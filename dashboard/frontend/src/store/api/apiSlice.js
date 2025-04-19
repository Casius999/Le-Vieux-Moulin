import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Configuration de la requête de base avec authentification
const baseQuery = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers, { getState }) => {
    // Récupération du token depuis le state Redux
    const token = getState().auth.token;
    
    // Ajout du token si présent
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    return headers;
  },
});

// Création de l'API slice avec RTK Query
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery,
  tagTypes: ['Sales', 'Stocks', 'Marketing', 'Finance', 'Staff', 'Dashboard'],
  endpoints: (builder) => ({}),
});
