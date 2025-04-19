import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Thunk pour récupérer les données de stocks
export const fetchStocks = createAsyncThunk(
  'stocks/fetchStocks',
  async ({ category, minLevel, maxLevel, sortBy, sortOrder }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      const response = await axios.get(`${baseUrl}/stocks`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          category,
          minLevel,
          maxLevel,
          sortBy,
          sortOrder,
        },
      });
      
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// Thunk pour récupérer les alertes de stock
export const fetchStockAlerts = createAsyncThunk(
  'stocks/fetchAlerts',
  async ({ type = 'all', limit = 50 }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      const response = await axios.get(`${baseUrl}/stocks/alerts`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          type,
          limit,
        },
      });
      
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// État initial
const initialState = {
  stocks: [],
  categories: [],
  alerts: [],
  totalPages: 0,
  currentPage: 1,
  loading: false,
  error: null,
  lastUpdated: null,
};

// Création du slice
const stocksSlice = createSlice({
  name: 'stocks',
  initialState,
  reducers: {
    clearStocksData: (state) => {
      state.stocks = [];
      state.alerts = [];
      state.lastUpdated = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Cas pour fetchStocks
      .addCase(fetchStocks.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStocks.fulfilled, (state, action) => {
        state.loading = false;
        state.stocks = action.payload.data;
        state.categories = action.payload.categories || state.categories;
        state.totalPages = action.payload.pagination?.totalPages || 1;
        state.currentPage = action.payload.pagination?.currentPage || 1;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchStocks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      })
      
      // Cas pour fetchStockAlerts
      .addCase(fetchStockAlerts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStockAlerts.fulfilled, (state, action) => {
        state.loading = false;
        state.alerts = action.payload.data;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchStockAlerts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      });
  },
});

// Export des actions et du reducer
export const { clearStocksData } = stocksSlice.actions;
export default stocksSlice.reducer;
