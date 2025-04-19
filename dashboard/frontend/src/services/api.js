import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Création d'une instance axios avec configuration de base
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification si disponible
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Services API pour les différentes sections du dashboard
export const dashboardApi = {
  getOverview: () => api.get('/dashboard/overview'),
  getKPIs: (dateRange) => api.get('/dashboard/kpi', { params: dateRange }),
  getAlerts: () => api.get('/dashboard/alerts'),
};

export const stocksApi = {
  getItems: () => api.get('/stocks'),
  getItemDetails: (itemId) => api.get(`/stocks/${itemId}`),
  getCategories: () => api.get('/stocks/categories'),
  getAlerts: () => api.get('/stocks/alerts'),
  getEquipment: () => api.get('/stocks/equipment'),
};

export const salesApi = {
  getSalesSummary: (params) => api.get('/sales/summary', { params }),
  getDailySales: (date) => api.get('/sales/daily', { params: { date } }),
  getWeeklySales: (week) => api.get('/sales/weekly', { params: { week } }),
  getMonthlySales: (month) => api.get('/sales/monthly', { params: { month } }),
  getYearlySales: (year) => api.get('/sales/yearly', { params: { year } }),
  getSalesByProduct: (params) => api.get('/sales/products', { params }),
  getSalesByCategory: (params) => api.get('/sales/categories', { params }),
  getHourlySales: (date) => api.get('/sales/hourly', { params: { date } }),
};

export const marketingApi = {
  getCampaigns: () => api.get('/marketing/campaigns'),
  getCampaignDetails: (id) => api.get(`/marketing/campaigns/${id}`),
  getSocialMediaMetrics: () => api.get('/marketing/social'),
  getPromotions: () => api.get('/marketing/promotions'),
};

export const financeApi = {
  getSummary: (period) => api.get('/finance/summary', { params: { period } }),
  getReports: (period) => api.get('/finance/reports', { params: { period } }),
  getExpenses: (params) => api.get('/finance/expenses', { params }),
  getRevenue: (params) => api.get('/finance/revenue', { params }),
  getPredictions: () => api.get('/finance/predictions'),
};

export const staffApi = {
  getSchedule: (date) => api.get('/staff/schedule', { params: { date } }),
  getPerformance: (params) => api.get('/staff/performance', { params }),
  getHours: (params) => api.get('/staff/hours', { params }),
  getCosts: (params) => api.get('/staff/costs', { params }),
};

export default api;
