import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Thunk pour récupérer les données de ventes
export const fetchSales = createAsyncThunk(
  'sales/fetchSales',
  async ({ timeRange, startDate, endDate, product, category }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      const response = await axios.get(`${baseUrl}/sales`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          timeRange,
          startDate,
          endDate,
          product,
          category,
        },
      });
      
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// Thunk pour récupérer le résumé des ventes
export const fetchSalesSummary = createAsyncThunk(
  'sales/fetchSalesSummary',
  async ({ timeRange }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      const response = await axios.get(`${baseUrl}/sales/summary`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          timeRange,
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
  sales: [],
  summary: null,
  totalPages: 0,
  currentPage: 1,
  loading: false,
  error: null,
  lastUpdated: null,
};

// Création du slice
const salesSlice = createSlice({
  name: 'sales',
  initialState,
  reducers: {
    clearSalesData: (state) => {
      state.sales = [];
      state.summary = null;
      state.lastUpdated = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Cas pour fetchSales
      .addCase(fetchSales.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSales.fulfilled, (state, action) => {
        state.loading = false;
        state.sales = action.payload.data;
        state.totalPages = action.payload.pagination?.totalPages || 1;
        state.currentPage = action.payload.pagination?.currentPage || 1;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchSales.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      })
      
      // Cas pour fetchSalesSummary
      .addCase(fetchSalesSummary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSalesSummary.fulfilled, (state, action) => {
        state.loading = false;
        state.summary = action.payload.data;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchSalesSummary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      });
  },
});

// Export des actions et du reducer
export const { clearSalesData } = salesSlice.actions;
export default salesSlice.reducer;
