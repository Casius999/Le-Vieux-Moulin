import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isLoading: false,
  error: null,
  kpis: [],
  dateRange: {
    start: new Date(new Date().setHours(0, 0, 0, 0)),
    end: new Date(),
  },
  refreshInterval: parseInt(process.env.REACT_APP_REFRESH_INTERVAL) || 60000,
  lastUpdated: null,
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    setKPIs: (state, action) => {
      state.kpis = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    setDateRange: (state, action) => {
      state.dateRange = action.payload;
    },
    setRefreshInterval: (state, action) => {
      state.refreshInterval = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setLoading,
  setError,
  setKPIs,
  setDateRange,
  setRefreshInterval,
  clearError,
} = dashboardSlice.actions;

export default dashboardSlice.reducer;
