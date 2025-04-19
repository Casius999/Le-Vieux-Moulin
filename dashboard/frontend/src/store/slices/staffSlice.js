import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URL de base de l'API
const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Thunk pour récupérer les données du personnel
export const fetchStaffData = createAsyncThunk(
  'staff/fetchData',
  async ({ view }, { getState, rejectWithValue }) => {
    try {
      const { auth } = getState();
      
      // Définition des dates en fonction de la vue
      let startDate, endDate;
      const now = new Date();
      
      switch (view) {
        case 'day':
          startDate = new Date(now.setHours(0, 0, 0, 0)).toISOString();
          endDate = new Date(now.setHours(23, 59, 59, 999)).toISOString();
          break;
        case 'week':
          const day = now.getDay();
          const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
          startDate = new Date(now.setDate(diff)).toISOString();
          endDate = new Date(now.setDate(diff + 6)).toISOString();
          break;
        case 'month':
          startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
          endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString();
          break;
        default:
          startDate = new Date(now.setHours(0, 0, 0, 0)).toISOString();
          endDate = new Date(now.setHours(23, 59, 59, 999)).toISOString();
      }
      
      // Récupération du planning
      const scheduleResponse = await axios.get(`${baseUrl}/staff/schedule`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          startDate,
          endDate,
        },
      });
      
      // Récupération des performances
      const performanceResponse = await axios.get(`${baseUrl}/staff/performance`, {
        headers: {
          Authorization: `Bearer ${auth.token}`,
        },
        params: {
          period: view,
        },
      });
      
      return {
        schedule: scheduleResponse.data.data,
        performance: performanceResponse.data.data,
        view,
      };
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// État initial
const initialState = {
  data: {
    schedule: [],
    performance: [],
    currentView: 'week',
  },
  loading: false,
  error: null,
  lastUpdated: null,
};

// Création du slice
const staffSlice = createSlice({
  name: 'staff',
  initialState,
  reducers: {
    clearStaffData: (state) => {
      state.data = {
        schedule: [],
        performance: [],
        currentView: 'week',
      };
      state.lastUpdated = null;
    },
    setCurrentView: (state, action) => {
      state.data.currentView = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStaffData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStaffData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = {
          ...state.data,
          schedule: action.payload.schedule,
          performance: action.payload.performance,
          currentView: action.payload.view,
        };
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchStaffData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || { message: 'Une erreur est survenue' };
      });
  },
});

// Export des actions et du reducer
export const { clearStaffData, setCurrentView } = staffSlice.actions;
export default staffSlice.reducer;
