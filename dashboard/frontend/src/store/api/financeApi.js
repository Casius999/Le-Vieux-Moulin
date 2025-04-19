import { apiSlice } from './apiSlice';

// Extension de l'API slice pour les endpoints financiers
export const financeApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getSummary: builder.query({
      query: ({ period }) => ({
        url: '/finance/summary',
        params: { period },
      }),
      providesTags: ['Finance'],
    }),
    
    getReports: builder.query({
      query: ({ period, type, startDate, endDate }) => ({
        url: '/finance/reports',
        params: { period, type, startDate, endDate },
      }),
      providesTags: ['Finance'],
    }),
    
    getExpenses: builder.query({
      query: ({ period, category }) => ({
        url: '/finance/expenses',
        params: { period, category },
      }),
      providesTags: ['Finance'],
    }),
    
    getRevenue: builder.query({
      query: ({ period, category }) => ({
        url: '/finance/revenue',
        params: { period, category },
      }),
      providesTags: ['Finance'],
    }),
    
    getPredictions: builder.query({
      query: ({ months = 3 }) => ({
        url: '/finance/predictions',
        params: { months },
      }),
      providesTags: ['Finance'],
    }),
  }),
});

// Export des hooks générés automatiquement
export const {
  useGetSummaryQuery,
  useGetReportsQuery,
  useGetExpensesQuery,
  useGetRevenueQuery,
  useGetPredictionsQuery,
} = financeApi;
