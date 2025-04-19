import { configureStore } from '@reduxjs/toolkit';
import dashboardReducer from './slices/dashboardSlice';
import salesReducer from './slices/salesSlice';
import stocksReducer from './slices/stocksSlice';
import marketingReducer from './slices/marketingSlice';
import financeReducer from './slices/financeSlice';
import staffReducer from './slices/staffSlice';
import alertsReducer from './slices/alertsSlice';

export const store = configureStore({
  reducer: {
    dashboard: dashboardReducer,
    sales: salesReducer,
    stocks: stocksReducer,
    marketing: marketingReducer,
    finance: financeReducer,
    staff: staffReducer,
    alerts: alertsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore ces actions car elles peuvent contenir des valeurs non-sérialisables
        ignoredActions: ['dashboard/setDateRange'],
      },
    }),
});
