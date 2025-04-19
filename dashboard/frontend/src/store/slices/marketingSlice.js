import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Thunk pour récupérer les données marketing
export const fetchMarketingData = createAsyncThunk(
  'marketing/fetchData',
  async ({ timeRange }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      const response = await axios.get(`${baseUrl}/marketing/campaigns`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          timeRange,
        },
      });
      
      // Récupération des métriques sociales
      const socialResponse = await axios.get(`${baseUrl}/marketing/social`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          timeRange,
        },
      });
      
      return {
        campaigns: response.data.data,
        social: socialResponse.data.data,
      };
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// État initial
const initialState = {
  data: {
    campaigns: [],
    social: null,
  },
  loading: false,
  error: null,
  lastUpdated: null,
};

// Création du slice
const marketingSlice = createSlice({
  name: 'marketing',
  initialState,
  reducers: {
    clearMarketingData: (state) => {
      state.data = {
        campaigns: [],
        social: null,
      };
      state.lastUpdated = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMarketingData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMarketingData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchMarketingData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      });
  },
});

// Export des actions et du reducer
export const { clearMarketingData } = marketingSlice.actions;
export default marketingSlice.reducer;
