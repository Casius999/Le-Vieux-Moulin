import { apiSlice } from './apiSlice';

// Extension de l'API slice pour les endpoints de ventes
export const salesApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getSales: builder.query({
      query: ({ startDate, endDate, timeRange, product, category, limit = 100, page = 1 }) => ({
        url: '/sales',
        params: { startDate, endDate, timeRange, product, category, limit, page },
      }),
      providesTags: ['Sales'],
    }),
    
    getSalesSummary: builder.query({
      query: ({ timeRange }) => ({
        url: '/sales/summary',
        params: { timeRange },
      }),
      providesTags: ['Sales'],
    }),
    
    getSalesByProduct: builder.query({
      query: ({ startDate, endDate, timeRange, limit = 10, sort = 'total' }) => ({
        url: '/sales/products',
        params: { startDate, endDate, timeRange, limit, sort },
      }),
      providesTags: ['Sales'],
    }),
    
    getHourlySales: builder.query({
      query: ({ date, dayOfWeek, aggregateBy = 'day' }) => ({
        url: '/sales/hourly',
        params: { date, dayOfWeek, aggregateBy },
      }),
      providesTags: ['Sales'],
    }),
    
    getSalesTrends: builder.query({
      query: ({ period = 'weekly', months = 6, compareWithPrevious = true }) => ({
        url: '/sales/trends',
        params: { period, months, compareWithPrevious },
      }),
      providesTags: ['Sales'],
    }),
  }),
});

// Export des hooks générés automatiquement
export const {
  useGetSalesQuery,
  useGetSalesSummaryQuery,
  useGetSalesByProductQuery,
  useGetHourlySalesQuery,
  useGetSalesTrendsQuery,
} = salesApi;
