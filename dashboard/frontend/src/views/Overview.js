import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Grid, Typography, Paper, Box, CircularProgress } from '@mui/material';

import KPICard from '../components/widgets/KPICard';
import RecentAlerts from '../components/widgets/RecentAlerts';
import DailySalesChart from '../components/charts/DailySalesChart';
import StockStatusOverview from '../components/widgets/StockStatusOverview';

import { loadDashboardData } from '../store/actions/dashboardActions';
import { loadStockAlerts } from '../store/actions/stocksActions';
import { loadTodaySales } from '../store/actions/salesActions';

function Overview() {
  const dispatch = useDispatch();
  const { kpis, isLoading } = useSelector((state) => state.dashboard);
  const { daily: dailySales } = useSelector((state) => state.sales);

  useEffect(() => {
    // Charger les données du dashboard
    dispatch(loadDashboardData());
    dispatch(loadStockAlerts());
    dispatch(loadTodaySales());

    // Configuration du rafraîchissement automatique
    const interval = setInterval(() => {
      dispatch(loadDashboardData());
      dispatch(loadTodaySales());
    }, 60000); // Mise à jour toutes les minutes

    return () => clearInterval(interval);
  }, [dispatch]);

  if (isLoading && kpis.length === 0) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="60vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Vue d'ensemble
      </Typography>

      {/* KPI Cards */}
      <Grid container spacing={3} mb={4}>
        {kpis.map((kpi) => (
          <Grid item xs={12} sm={6} md={3} key={kpi.id}>
            <KPICard kpi={kpi} />
          </Grid>
        ))}
      </Grid>

      {/* Charts and Widgets */}
      <Grid container spacing={3}>
        {/* Daily Sales Chart */}
        <Grid item xs={12} md={8}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 300,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Ventes d'aujourd'hui
            </Typography>
            <DailySalesChart data={dailySales} />
          </Paper>
        </Grid>

        {/* Recent Alerts */}
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 300,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Alertes récentes
            </Typography>
            <RecentAlerts />
          </Paper>
        </Grid>

        {/* Stock Status Overview */}
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Typography variant="h6" gutterBottom>
              État des stocks
            </Typography>
            <StockStatusOverview />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Overview;
