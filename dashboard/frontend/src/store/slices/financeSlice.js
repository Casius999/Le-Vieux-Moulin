import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Thunk pour récupérer les données financières
export const fetchFinanceData = createAsyncThunk(
  'finance/fetchData',
  async ({ period }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      // Récupération du résumé financier
      const summaryResponse = await axios.get(`${baseUrl}/finance/summary`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          period,
        },
      });
      
      // Récupération des dépenses
      const expensesResponse = await axios.get(`${baseUrl}/finance/expenses`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          period,
        },
      });
      
      // Récupération des revenus
      const revenueResponse = await axios.get(`${baseUrl}/finance/revenue`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          period,
        },
      });
      
      return {
        summary: summaryResponse.data.data,
        expenses: expensesResponse.data.data,
        revenue: revenueResponse.data.data,
      };
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// État initial
const initialState = {
  data: {
    summary: null,
    expenses: [],
    revenue: [],
    predictions: null,
  },
  loading: false,
  error: null,
  lastUpdated: null,
};

// Création du slice
const financeSlice = createSlice({
  name: 'finance',
  initialState,
  reducers: {
    clearFinanceData: (state) => {
      state.data = {
        summary: null,
        expenses: [],
        revenue: [],
        predictions: null,
      };
      state.lastUpdated = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFinanceData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFinanceData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchFinanceData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      });
  },
});

// Export des actions et du reducer
export const { clearFinanceData } = financeSlice.actions;
export default financeSlice.reducer;
