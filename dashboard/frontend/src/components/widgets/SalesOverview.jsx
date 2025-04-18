import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  Typography, 
  Grid,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ArrowRight as ArrowRightIcon
} from '@mui/icons-material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { useTranslation } from 'react-i18next';
import { useSelector, useDispatch } from 'react-redux';
import { fetchSales } from '../../store/slices/salesSlice';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

// Couleurs pour les graphiques
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

// Composant pour afficher un KPI avec tendance
const SalesKPI = ({ title, value, unit, trend, previousValue }) => {
  const trendPercent = previousValue > 0 ? 
    Math.round((value - previousValue) / previousValue * 100) : 0;
  
  let color = 'info';
  let icon = <ArrowRightIcon />;
  
  if (trend === 'up') {
    color = 'success';
    icon = <TrendingUpIcon />;
  } else if (trend === 'down') {
    color = 'error';
    icon = <TrendingDownIcon />;
  }
  
  return (
    <Paper elevation={2} sx={{ p: 2, height: '100%' }}>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h5" component="div">
          {value}{unit}
        </Typography>
        <Chip 
          icon={icon}
          label={`${trendPercent > 0 ? '+' : ''}${trendPercent}%`}
          color={color}
          size="small"
        />
      </Box>
    </Paper>
  );
};

const SalesOverview = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { sales, loading, error } = useSelector((state) => state.sales);
  const [anchorEl, setAnchorEl] = useState(null);
  const [timeRange, setTimeRange] = useState('week'); // 'day', 'week', 'month', 'year'
  
  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  
  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
    handleMenuClose();
  };
  
  const handleRefresh = () => {
    dispatch(fetchSales({ timeRange }));
  };
  
  useEffect(() => {
    dispatch(fetchSales({ timeRange }));
    
    // Mise à jour périodique des données
    const interval = setInterval(() => {
      dispatch(fetchSales({ timeRange }));
    }, 300000); // 5 minutes
    
    return () => clearInterval(interval);
  }, [dispatch, timeRange]);
  
  // Données de vente simulées pour l'exemple
  const salesData = [
    { date: '2025-04-11', total: 1250, customers: 45 },
    { date: '2025-04-12', total: 1850, customers: 62 },
    { date: '2025-04-13', total: 2200, customers: 78 },
    { date: '2025-04-14', total: 1100, customers: 40 },
    { date: '2025-04-15', total: 1500, customers: 55 },
    { date: '2025-04-16', total: 1750, customers: 60 },
    { date: '2025-04-17', total: 1950, customers: 70 }
  ];
  
  // Calculer les KPI
  const currentTotal = salesData.reduce((sum, day) => sum + day.total, 0);
  
  // Supposons que ce sont les données de la semaine précédente pour la comparaison
  const previousSalesData = [
    { date: '2025-04-04', total: 1150, customers: 40 },
    { date: '2025-04-05', total: 1650, customers: 58 },
    { date: '2025-04-06', total: 2000, customers: 72 },
    { date: '2025-04-07', total: 1000, customers: 35 },
    { date: '2025-04-08', total: 1400, customers: 50 },
    { date: '2025-04-09', total: 1600, customers: 55 },
    { date: '2025-04-10', total: 1800, customers: 65 }
  ];
  
  const previousTotal = previousSalesData.reduce((sum, day) => sum + day.total, 0);
  
  const currentCustomers = salesData.reduce((sum, day) => sum + day.customers, 0);
  const previousCustomers = previousSalesData.reduce((sum, day) => sum + day.customers, 0);
  
  const averageTicket = currentTotal / currentCustomers;
  const previousAverageTicket = previousTotal / previousCustomers;
  
  // Données pour le graphique camembert des ventes par catégorie
  const salesByCategory = [
    { name: 'Pizzas', value: 7500 },
    { name: 'Salades', value: 2500 },
    { name: 'Boissons', value: 3000 },
    { name: 'Desserts', value: 1800 },
    { name: 'Autres', value: 900 }
  ];
  
  // Top produits
  const topProducts = [
    { id: 1, name: 'Pizza Margherita', quantity: 120, total: 1560 },
    { id: 2, name: 'Pizza Reine', quantity: 85, total: 1190 },
    { id: 3, name: 'Pizza 4 Fromages', quantity: 75, total: 1125 },
    { id: 4, name: 'Tiramisu', quantity: 68, total: 476 },
    { id: 5, name: 'Salade César', quantity: 65, total: 715 }
  ];
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, 'EEE dd/MM', { locale: fr });
  };
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={t('sales.overview.title')}
        action={
          <>
            <Tooltip title={t('common.refresh')}>
              <IconButton onClick={handleRefresh} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <IconButton 
              aria-label={t('common.more')}
              aria-controls="sales-menu"
              aria-haspopup="true"
              onClick={handleMenuClick}
              size="small"
            >
              <MoreVertIcon />
            </IconButton>
            <Menu
              id="sales-menu"
              anchorEl={anchorEl}
              keepMounted
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={() => handleTimeRangeChange('day')}>{t('timeRange.day')}</MenuItem>
              <MenuItem onClick={() => handleTimeRangeChange('week')}>{t('timeRange.week')}</MenuItem>
              <MenuItem onClick={() => handleTimeRangeChange('month')}>{t('timeRange.month')}</MenuItem>
              <MenuItem onClick={() => handleTimeRangeChange('year')}>{t('timeRange.year')}</MenuItem>
              <MenuItem onClick={handleMenuClose}>{t('sales.seeAll')}</MenuItem>
            </Menu>
          </>
        }
      />
      <CardContent>
        <Grid container spacing={3}>
          {/* KPIs */}
          <Grid item xs={12} sm={4}>
            <SalesKPI 
              title={t('sales.kpi.totalSales')}
              value={currentTotal}
              unit="€"
              trend={currentTotal > previousTotal ? 'up' : currentTotal < previousTotal ? 'down' : 'neutral'}
              previousValue={previousTotal}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <SalesKPI 
              title={t('sales.kpi.customers')}
              value={currentCustomers}
              unit=""
              trend={currentCustomers > previousCustomers ? 'up' : currentCustomers < previousCustomers ? 'down' : 'neutral'}
              previousValue={previousCustomers}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <SalesKPI 
              title={t('sales.kpi.averageTicket')}
              value={averageTicket.toFixed(2)}
              unit="€"
              trend={averageTicket > previousAverageTicket ? 'up' : averageTicket < previousAverageTicket ? 'down' : 'neutral'}
              previousValue={previousAverageTicket}
            />
          </Grid>
          
          {/* Graphique d'évolution des ventes */}
          <Grid item xs={12} md={8}>
            <Typography variant="subtitle1" gutterBottom>
              {t('sales.evolution')}
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={salesData}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatDate}
                  />
                  <YAxis />
                  <RechartsTooltip 
                    formatter={(value, name) => {
                      if (name === 'total') return [`${value} €`, t('sales.revenue')];
                      if (name === 'customers') return [value, t('sales.customers')];
                      return [value, name];
                    }}
                    labelFormatter={(label) => formatDate(label)}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="total" 
                    stroke="#8884d8" 
                    activeDot={{ r: 8 }} 
                    name="total"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="customers" 
                    stroke="#82ca9d" 
                    name="customers"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          
          {/* Répartition des ventes par catégorie */}
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle1" gutterBottom>
              {t('sales.byCategory')}
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={salesByCategory}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {salesByCategory.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          
          {/* Top produits */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              {t('sales.topProducts')}
            </Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('products.name')}</TableCell>
                    <TableCell align="right">{t('products.quantity')}</TableCell>
                    <TableCell align="right">{t('products.total')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topProducts.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell component="th" scope="row">
                        {product.name}
                      </TableCell>
                      <TableCell align="right">{product.quantity}</TableCell>
                      <TableCell align="right">{product.total} €</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SalesOverview;
