import { apiSlice } from './apiSlice';

// Extension de l'API slice pour les endpoints du personnel
export const staffApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getSchedule: builder.query({
      query: ({ startDate, endDate, staff }) => ({
        url: '/staff/schedule',
        params: { startDate, endDate, staff },
      }),
      providesTags: ['Staff'],
    }),
    
    getPerformance: builder.query({
      query: ({ period, staff }) => ({
        url: '/staff/performance',
        params: { period, staff },
      }),
      providesTags: ['Staff'],
    }),
    
    getHours: builder.query({
      query: ({ period, staff }) => ({
        url: '/staff/hours',
        params: { period, staff },
      }),
      providesTags: ['Staff'],
    }),
    
    getCosts: builder.query({
      query: ({ period, category }) => ({
        url: '/staff/costs',
        params: { period, category },
      }),
      providesTags: ['Staff'],
    }),
    
    updateSchedule: builder.mutation({
      query: ({ id, ...shift }) => ({
        url: `/staff/schedule/${id}`,
        method: 'PUT',
        body: shift,
      }),
      invalidatesTags: ['Staff'],
    }),
  }),
});

// Export des hooks générés automatiquement
export const {
  useGetScheduleQuery,
  useGetPerformanceQuery,
  useGetHoursQuery,
  useGetCostsQuery,
  useUpdateScheduleMutation,
} = staffApi;
