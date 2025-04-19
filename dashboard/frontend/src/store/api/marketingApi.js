import { apiSlice } from './apiSlice';

// Extension de l'API slice pour les endpoints de marketing
export const marketingApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getCampaigns: builder.query({
      query: () => '/marketing/campaigns',
      providesTags: ['Marketing'],
    }),
    
    getCampaignById: builder.query({
      query: (id) => `/marketing/campaigns/${id}`,
      providesTags: (result, error, id) => [{ type: 'Marketing', id }],
    }),
    
    getSocialMetrics: builder.query({
      query: ({ platform, period }) => ({
        url: '/marketing/social',
        params: { platform, period },
      }),
      providesTags: ['Marketing'],
    }),
    
    getPromotions: builder.query({
      query: ({ status, future = true }) => ({
        url: '/marketing/promotions',
        params: { status, future },
      }),
      providesTags: ['Marketing'],
    }),
    
    createCampaign: builder.mutation({
      query: (campaign) => ({
        url: '/marketing/campaigns',
        method: 'POST',
        body: campaign,
      }),
      invalidatesTags: ['Marketing'],
    }),
    
    updateCampaign: builder.mutation({
      query: ({ id, ...campaign }) => ({
        url: `/marketing/campaigns/${id}`,
        method: 'PUT',
        body: campaign,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Marketing', id },
        'Marketing',
      ],
    }),
  }),
});

// Export des hooks générés automatiquement
export const {
  useGetCampaignsQuery,
  useGetCampaignByIdQuery,
  useGetSocialMetricsQuery,
  useGetPromotionsQuery,
  useCreateCampaignMutation,
  useUpdateCampaignMutation,
} = marketingApi;
