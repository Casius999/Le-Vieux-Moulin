import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';

// Import des slices Redux
import dashboardReducer from './slices/dashboardSlice';
import salesReducer from './slices/salesSlice';
import stocksReducer from './slices/stocksSlice';
import marketingReducer from './slices/marketingSlice';
import financeReducer from './slices/financeSlice';
import staffReducer from './slices/staffSlice';
import authReducer from './slices/authSlice';

// Import des services API
import { apiSlice } from './api/apiSlice';

// Configuration du store Redux
export const store = configureStore({
  reducer: {
    dashboard: dashboardReducer,
    sales: salesReducer,
    stocks: stocksReducer,
    marketing: marketingReducer,
    finance: financeReducer,
    staff: staffReducer,
    auth: authReducer,
    [apiSlice.reducerPath]: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
});

// Configuration des listeners pour les requêtes RTK Query
setupListeners(store.dispatch);
