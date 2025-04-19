import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Thunk pour récupérer les données du dashboard
export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchData',
  async (_, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      const response = await axios.get(`${baseUrl}/dashboard/overview`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
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
  data: null,
  loading: false,
  error: null,
  lastUpdated: null,
};

// Création du slice
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearDashboardData: (state) => {
      state.data = null;
      state.lastUpdated = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload.data;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      });
  },
});

// Export des actions et du reducer
export const { clearDashboardData } = dashboardSlice.actions;
export default dashboardSlice.reducer;
