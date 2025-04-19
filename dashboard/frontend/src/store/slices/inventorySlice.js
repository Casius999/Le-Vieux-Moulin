import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Thunk pour récupérer les données d'inventaire
export const fetchInventoryData = createAsyncThunk(
  'inventory/fetchInventoryData',
  async (params, { rejectWithValue }) => {
    try {
      const response = await axios.get('/api/inventory');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour récupérer un élément d'inventaire spécifique
export const fetchInventoryItem = createAsyncThunk(
  'inventory/fetchInventoryItem',
  async (itemId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`/api/inventory/${itemId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour mettre à jour un élément d'inventaire
export const updateInventoryItem = createAsyncThunk(
  'inventory/updateInventoryItem',
  async ({ itemId, data }, { rejectWithValue }) => {
    try {
      const response = await axios.patch(`/api/inventory/${itemId}`, data);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour créer un élément d'inventaire
export const createInventoryItem = createAsyncThunk(
  'inventory/createInventoryItem',
  async (data, { rejectWithValue }) => {
    try {
      const response = await axios.post('/api/inventory', data);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Thunk pour commander un élément
export const orderInventoryItem = createAsyncThunk(
  'inventory/orderInventoryItem',
  async ({ itemId, quantity }, { rejectWithValue }) => {
    try {
      const response = await axios.post(`/api/inventory/${itemId}/order`, { quantity });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// État initial
const initialState = {
  data: null,
  selectedItem: null,
  loading: false,
  itemLoading: false,
  error: null,
  orderSuccess: false,
  lastUpdated: null
};

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    clearInventoryError: (state) => {
      state.error = null;
    },
    resetOrderSuccess: (state) => {
      state.orderSuccess = false;
    }
  },
  extraReducers: (builder) => {
    builder
      // Gestion de fetchInventoryData
      .addCase(fetchInventoryData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInventoryData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload.data;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchInventoryData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion de fetchInventoryItem
      .addCase(fetchInventoryItem.pending, (state) => {
        state.itemLoading = true;
      })
      .addCase(fetchInventoryItem.fulfilled, (state, action) => {
        state.itemLoading = false;
        state.selectedItem = action.payload.data;
      })
      .addCase(fetchInventoryItem.rejected, (state, action) => {
        state.itemLoading = false;
        state.error = action.payload || 'Une erreur est survenue';
      })
      
      // Gestion de updateInventoryItem
      .addCase(updateInventoryItem.fulfilled, (state, action) => {
        const updatedItem = action.payload.data;
        
        // Mise à jour de l'item dans la liste des items
        if (state.data && state.data.items) {
          const itemIndex = state.data.items.findIndex(item => item.id === updatedItem.id);
          if (itemIndex !== -1) {
            state.data.items[itemIndex] = updatedItem;
          }
        }
        
        // Mise à jour de l'item sélectionné si c'est le même
        if (state.selectedItem && state.selectedItem.id === updatedItem.id) {
          state.selectedItem = updatedItem;
        }
      })
      
      // Gestion de createInventoryItem
      .addCase(createInventoryItem.fulfilled, (state, action) => {
        const newItem = action.payload.data;
        
        // Ajout du nouvel item à la liste
        if (state.data && state.data.items) {
          state.data.items.push(newItem);
        }
      })
      
      // Gestion de orderInventoryItem
      .addCase(orderInventoryItem.pending, (state) => {
        state.orderSuccess = false;
      })
      .addCase(orderInventoryItem.fulfilled, (state, action) => {
        const { itemId, order } = action.payload.data;
        
        // Ajout de la commande à la liste des commandes en attente de l'item
        if (state.data && state.data.items) {
          const itemIndex = state.data.items.findIndex(item => item.id === itemId);
          if (itemIndex !== -1) {
            if (!state.data.items[itemIndex].pendingOrders) {
              state.data.items[itemIndex].pendingOrders = [];
            }
            state.data.items[itemIndex].pendingOrders.push(order);
          }
        }
        
        // Mise à jour de l'item sélectionné si c'est le même
        if (state.selectedItem && state.selectedItem.id === itemId) {
          if (!state.selectedItem.pendingOrders) {
            state.selectedItem.pendingOrders = [];
          }
          state.selectedItem.pendingOrders.push(order);
        }
        
        // Mise à jour des commandes en attente globales
        if (state.data && state.data.pendingOrders) {
          state.data.pendingOrders.push(order);
        }
        
        state.orderSuccess = true;
      });
  }
});

export const { clearInventoryError, resetOrderSuccess } = inventorySlice.actions;

export default inventorySlice.reducer;
