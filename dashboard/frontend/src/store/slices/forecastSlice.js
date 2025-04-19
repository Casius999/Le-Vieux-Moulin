import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Thunk pour récupérer les prévisions de ventes
export const fetchSalesForecasts = createAsyncThunk(
  'forecast/fetchSalesForecasts',
  async ({ period = 'week', type = 'revenue' }, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/forecast/sales', {
        params: { period, type }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour récupérer les prévisions de stock
export const fetchStockForecasts = createAsyncThunk(
  'forecast/fetchStockForecasts',
  async ({ period = 'week', category = 'all' }, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/forecast/stock', {
        params: { period, category }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour récupérer les insights ML
export const fetchMlInsights = createAsyncThunk(
  'forecast/fetchMlInsights',
  async (params, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/forecast/insights');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour récupérer les informations sur le modèle ML
export const fetchModelInfo = createAsyncThunk(
  'forecast/fetchModelInfo',
  async (params, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/forecast/model');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour détecter les anomalies
export const detectAnomalies = createAsyncThunk(
  'forecast/detectAnomalies',
  async ({ data, type = 'sales' }, { rejectWithValue }) => {
    try {
      const response = await axios.post('/api/forecast/anomalies', { data, type });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// État initial
const initialState = {
  data: null,
  stockForecasts: null,
  insights: null,
  modelInfo: null,
  anomalies: [],
  loading: false,
  stockLoading: false,
  insightsLoading: false,
  modelLoading: false,
  error: null,
  lastUpdated: null
};

const forecastSlice = createSlice({
  name: 'forecast',
  initialState,
  reducers: {
    clearForecastError: (state) => {
      state.error = null;
    },
    dismissAnomaly: (state, action) => {
      const anomalyId = action.payload;
      state.anomalies = state.anomalies.filter(anomaly => anomaly.id !== anomalyId);
    }
  },
  extraReducers: (builder) => {
    builder
      // Gestion de fetchSalesForecasts
      .addCase(fetchSalesForecasts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSalesForecasts.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload.data;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchSalesForecasts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion de fetchStockForecasts
      .addCase(fetchStockForecasts.pending, (state) => {
        state.stockLoading = true;
      })
      .addCase(fetchStockForecasts.fulfilled, (state, action) => {
        state.stockLoading = false;
        state.stockForecasts = action.payload.data;
      })
      .addCase(fetchStockForecasts.rejected, (state, action) => {
        state.stockLoading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion de fetchMlInsights
      .addCase(fetchMlInsights.pending, (state) => {
        state.insightsLoading = true;
      })
      .addCase(fetchMlInsights.fulfilled, (state, action) => {
        state.insightsLoading = false;
        state.insights = action.payload.data;
      })
      .addCase(fetchMlInsights.rejected, (state, action) => {
        state.insightsLoading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion de fetchModelInfo
      .addCase(fetchModelInfo.pending, (state) => {
        state.modelLoading = true;
      })
      .addCase(fetchModelInfo.fulfilled, (state, action) => {
        state.modelLoading = false;
        state.modelInfo = action.payload.data;
      })
      .addCase(fetchModelInfo.rejected, (state, action) => {
        state.modelLoading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion de detectAnomalies
      .addCase(detectAnomalies.fulfilled, (state, action) => {
        const detectedAnomalies = action.payload.data;
        
        // Fusionner avec les anomalies existantes
        const existingIds = state.anomalies.map(anomaly => anomaly.id);
        const newAnomalies = detectedAnomalies.filter(anomaly => !existingIds.includes(anomaly.id));
        
        state.anomalies = [...state.anomalies, ...newAnomalies];
        
        // Si des anomalies ont été détectées dans les données actuelles, les ajouter au state.data
        if (state.data && detectedAnomalies.length > 0) {
          state.data.alerts = detectedAnomalies;
        }
      });
  }
});

export const { clearForecastError, dismissAnomaly } = forecastSlice.actions;

export default forecastSlice.reducer;
