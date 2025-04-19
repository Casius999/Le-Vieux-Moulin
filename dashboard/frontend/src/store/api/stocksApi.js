import { apiSlice } from './apiSlice';

// Extension de l'API slice pour les endpoints de stocks
export const stocksApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getAllStocks: builder.query({
      query: ({ category, minLevel, maxLevel, sortBy = 'name', sortOrder = 'asc', limit = 100, page = 1 }) => ({
        url: '/stocks',
        params: { category, minLevel, maxLevel, sortBy, sortOrder, limit, page },
      }),
      providesTags: ['Stocks'],
    }),
    
    getStockById: builder.query({
      query: (id) => `/stocks/${id}`,
      providesTags: (result, error, id) => [{ type: 'Stocks', id }],
    }),
    
    getStockCategories: builder.query({
      query: () => '/stocks/categories',
      providesTags: ['Stocks'],
    }),
    
    getStockAlerts: builder.query({
      query: ({ type = 'all', limit = 50 }) => ({
        url: '/stocks/alerts',
        params: { type, limit },
      }),
      providesTags: ['Stocks'],
    }),
  }),
});

// Export des hooks générés automatiquement
export const {
  useGetAllStocksQuery,
  useGetStockByIdQuery,
  useGetStockCategoriesQuery,
  useGetStockAlertsQuery,
} = stocksApi;
