import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  daily: [],
  weekly: [],
  monthly: [],
  yearly: [],
  byProduct: [],
  byCategory: [],
  comparisons: {},
  isLoading: false,
  error: null,
  lastUpdated: null,
};

const salesSlice = createSlice({
  name: 'sales',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    setDailySales: (state, action) => {
      state.daily = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setWeeklySales: (state, action) => {
      state.weekly = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setMonthlySales: (state, action) => {
      state.monthly = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setYearlySales: (state, action) => {
      state.yearly = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setSalesByProduct: (state, action) => {
      state.byProduct = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setSalesByCategory: (state, action) => {
      state.byCategory = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setSalesComparisons: (state, action) => {
      state.comparisons = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    addSale: (state, action) => {
      // Mise à jour pour une nouvelle vente en temps réel
      if (state.daily.length > 0) {
        const lastIndex = state.daily.length - 1;
        // Si la dernière période correspond à l'heure actuelle, incrémenter
        if (state.daily[lastIndex].hour === new Date().getHours()) {
          state.daily[lastIndex].value += action.payload.amount;
        } else {
          // Sinon, ajouter une nouvelle période
          state.daily.push({
            hour: new Date().getHours(),
            value: action.payload.amount,
          });
        }
      }
      state.lastUpdated = new Date().toISOString();
    },
  },
});

export const {
  setLoading,
  setError,
  setDailySales,
  setWeeklySales,
  setMonthlySales,
  setYearlySales,
  setSalesByProduct,
  setSalesByCategory,
  setSalesComparisons,
  addSale,
} = salesSlice.actions;

export default salesSlice.reducer;
