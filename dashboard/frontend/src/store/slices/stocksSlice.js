import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  items: [],
  equipment: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  alertThresholds: {
    low: 30, // Pourcentage en-dessous duquel un stock est considéré bas
    critical: 10, // Pourcentage en-dessous duquel un stock est critique
  },
};

const stocksSlice = createSlice({
  name: 'stocks',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    setStockItems: (state, action) => {
      state.items = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    updateStockItem: (state, action) => {
      const { id, ...updates } = action.payload;
      const index = state.items.findIndex(item => item.id === id);
      if (index !== -1) {
        state.items[index] = { ...state.items[index], ...updates };
        state.lastUpdated = new Date().toISOString();
      }
    },
    setEquipment: (state, action) => {
      state.equipment = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    updateEquipment: (state, action) => {
      const { id, ...updates } = action.payload;
      const index = state.equipment.findIndex(item => item.id === id);
      if (index !== -1) {
        state.equipment[index] = { ...state.equipment[index], ...updates };
        state.lastUpdated = new Date().toISOString();
      }
    },
    setAlertThresholds: (state, action) => {
      state.alertThresholds = action.payload;
    },
  },
});

export const {
  setLoading,
  setError,
  setStockItems,
  updateStockItem,
  setEquipment,
  updateEquipment,
  setAlertThresholds,
} = stocksSlice.actions;

export default stocksSlice.reducer;
