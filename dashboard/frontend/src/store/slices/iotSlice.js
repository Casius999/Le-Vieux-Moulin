import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Thunk pour récupérer les données IoT
export const fetchIotData = createAsyncThunk(
  'iot/fetchIotData',
  async (params, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/iot/status');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour récupérer l'historique IoT
export const fetchIotHistory = createAsyncThunk(
  'iot/fetchIotHistory',
  async ({ sensorId, period = 'day' }, { rejectWithValue }) => {
    try {
      const response = await axios.get(`/api/iot/history/${sensorId}`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour mettre à jour les seuils d'alerte
export const updateIotThresholds = createAsyncThunk(
  'iot/updateIotThresholds',
  async ({ sensorId, thresholds }, { rejectWithValue }) => {
    try {
      const response = await axios.patch(`/api/iot/thresholds/${sensorId}`, thresholds);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour récupérer les alertes IoT
export const fetchIotAlerts = createAsyncThunk(
  'iot/fetchIotAlerts',
  async (params, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/iot/alerts');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

const initialState = {
  data: null,
  sensorHistory: {},
  alerts: [],
  loading: false,
  historyLoading: false,
  error: null,
  lastUpdated: null
};

const iotSlice = createSlice({
  name: 'iot',
  initialState,
  reducers: {
    clearIotError: (state) => {
      state.error = null;
    },
    acknowledgeAlert: (state, action) => {
      const alertId = action.payload;
      state.alerts = state.alerts.filter(alert => alert.id !== alertId);
    }
  },
  extraReducers: (builder) => {
    builder
      // Gestion du fetchIotData
      .addCase(fetchIotData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchIotData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload.data;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchIotData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion du fetchIotHistory
      .addCase(fetchIotHistory.pending, (state) => {
        state.historyLoading = true;
      })
      .addCase(fetchIotHistory.fulfilled, (state, action) => {
        state.historyLoading = false;
        const { sensorId, data } = action.payload;
        state.sensorHistory[sensorId] = data;
      })
      .addCase(fetchIotHistory.rejected, (state, action) => {
        state.historyLoading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion du updateIotThresholds
      .addCase(updateIotThresholds.fulfilled, (state, action) => {
        const { sensorId, thresholds } = action.payload;
        
        if (state.data && state.data.sensors) {
          const sensorIndex = state.data.sensors.findIndex(sensor => sensor.id === sensorId);
          if (sensorIndex !== -1) {
            state.data.sensors[sensorIndex] = {
              ...state.data.sensors[sensorIndex],
              ...thresholds
            };
          }
        }
      })
      
      // Gestion du fetchIotAlerts
      .addCase(fetchIotAlerts.fulfilled, (state, action) => {
        state.alerts = action.payload.data;
      });
  }
});

export const { clearIotError, acknowledgeAlert } = iotSlice.actions;

export default iotSlice.reducer;
