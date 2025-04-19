import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Grid,
  Typography,
  Box,
  IconButton,
  CircularProgress,
  Divider,
  Paper,
  Tooltip,
  ButtonGroup,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Skeleton
} from '@mui/material';
import {
  RefreshOutlined as RefreshIcon,
  TrendingUp as IncreaseIcon,
  TrendingDown as DecreaseIcon,
  TrendingFlat as StableIcon,
  CalendarToday as CalendarIcon,
  FileDownload as DownloadIcon,
  MoreVert as MoreIcon,
  Print as PrintIcon,
  Share as ShareIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFinancialData } from '../../store/slices/financeSlice';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

// Composant pour afficher un KPI avec son évolution
const KPICard = ({ title, value, unit, previousValue, format, icon, color = 'primary' }) => {
  const { t } = useTranslation();
  
  // Calculer le pourcentage d'évolution
  const getPercentChange = () => {
    if (!previousValue || previousValue === 0) return 0;
    return ((value - previousValue) / Math.abs(previousValue)) * 100;
  };
  
  // Déterminer la tendance (hausse, baisse, stable)
  const getTrend = () => {
    const percentChange = getPercentChange();
    if (Math.abs(percentChange) < 1) return 'stable';
    return percentChange > 0 ? 'increase' : 'decrease';
  };
  
  // Formater la valeur selon le type
  const formatValue = (val) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(val);
    } else if (format === 'percent') {
      return `${val.toFixed(1)}%`;
    } else if (format === 'number') {
      return new Intl.NumberFormat('fr-FR').format(val);
    }
    return val;
  };
  
  // Afficher l'icône de tendance
  const renderTrendIcon = () => {
    const trend = getTrend();
    if (trend === 'increase') {
      return <IncreaseIcon color="success" />;
    } else if (trend === 'decrease') {
      return <DecreaseIcon color="error" />;
    }
    return <StableIcon color="action" />;
  };
  
  return (
    <Paper 
      elevation={0}
      sx={{ 
        p: 2, 
        height: '100%',
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between'
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          bgcolor: `${color}.lighter`,
          color: `${color}.main`,
          borderRadius: '50%',
          width: 36,
          height: 36
        }}>
          {icon}
        </Box>
      </Box>
      
      <Typography variant="h4" component="div" fontWeight="bold" gutterBottom>
        {formatValue(value)}
        {unit && !format && <Typography component="span" variant="body2" color="text.secondary" ml={0.5}>{unit}</Typography>}
      </Typography>
      
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {renderTrendIcon()}
        <Typography variant="body2" color={getTrend() === 'stable' ? 'text.secondary' : getTrend() === 'increase' ? 'success.main' : 'error.main'} sx={{ ml: 0.5 }}>
          {Math.abs(getPercentChange()).toFixed(1)}%
          <Typography component="span" variant="body2" color="text.secondary" ml={0.5}>
            {getPercentChange() >= 0 ? t('finance.vsLastPeriodUp') : t('finance.vsLastPeriodDown')}
          </Typography>
        </Typography>
      </Box>
    </Paper>
  );
};

// Composant principal pour les KPIs financiers
const FinancialKPI = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { data, loading, error, lastUpdated } = useSelector((state) => state.finance);
  const [period, setPeriod] = useState('day'); // 'day', 'week', 'month', 'year'
  const [chartData, setChartData] = useState([]);
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  
  useEffect(() => {
    dispatch(fetchFinancialData({ period }));
  }, [dispatch, period]);
  
  // Préparer les données pour le graphique
  useEffect(() => {
    if (data?.revenueOverTime) {
      setChartData(data.revenueOverTime);
    }
  }, [data]);
  
  const handleRefresh = () => {
    dispatch(fetchFinancialData({ period }));
  };
  
  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod);
  };
  
  const handleMenuOpen = (event) => {
    setMenuAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };
  
  // Format des dates sur l'axe X en fonction de la période
  const formatXAxis = (tickItem) => {
    const date = new Date(tickItem);
    switch (period) {
      case 'day':
        return date.getHours() + 'h';
      case 'week':
        return new Intl.DateTimeFormat('fr-FR', { weekday: 'short' }).format(date);
      case 'month':
        return date.getDate();
      case 'year':
        return new Intl.DateTimeFormat('fr-FR', { month: 'short' }).format(date);
      default:
        return tickItem;
    }
  };
  
  // Obtenir le titre de la période pour l'en-tête
  const getPeriodTitle = () => {
    switch (period) {
      case 'day':
        return t('finance.today');
      case 'week':
        return t('finance.thisWeek');
      case 'month':
        return t('finance.thisMonth');
      case 'year':
        return t('finance.thisYear');
      default:
        return '';
    }
  };
  
  return (
    <Card elevation={2}>
      <CardHeader
        title={t('finance.performance')}
        subheader={getPeriodTitle()}
        action={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ButtonGroup size="small" sx={{ mr: 1 }}>
              <Button 
                variant={period === 'day' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('day')}
              >
                {t('finance.day')}
              </Button>
              <Button 
                variant={period === 'week' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('week')}
              >
                {t('finance.week')}
              </Button>
              <Button 
                variant={period === 'month' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('month')}
              >
                {t('finance.month')}
              </Button>
              <Button 
                variant={period === 'year' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('year')}
              >
                {t('finance.year')}
              </Button>
            </ButtonGroup>
            
            <Tooltip title={t('common.refresh')}>
              <IconButton onClick={handleRefresh} disabled={loading}>
                {loading ? <CircularProgress size={24} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title={t('common.moreOptions')}>
              <IconButton onClick={handleMenuOpen}>
                <MoreIcon />
              </IconButton>
            </Tooltip>
            
            <Menu
              anchorEl={menuAnchorEl}
              open={Boolean(menuAnchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleMenuClose}>
                <ListItemIcon>
                  <DownloadIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('common.exportData')}</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleMenuClose}>
                <ListItemIcon>
                  <PrintIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('common.print')}</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleMenuClose}>
                <ListItemIcon>
                  <ShareIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('common.share')}</ListItemText>
              </MenuItem>
            </Menu>
          </Box>
        }
      />
      <Divider />
      <CardContent>
        {/* KPI Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            {loading && !data ? (
              <Skeleton variant="rectangular" height={120} />
            ) : (
              <KPICard 
                title={t('finance.revenue')} 
                value={data?.kpi?.revenue || 0} 
                previousValue={data?.kpi?.previousRevenue || 0} 
                format="currency"
                icon={<EuroIcon />}
                color="primary"
              />
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {loading && !data ? (
              <Skeleton variant="rectangular" height={120} />
            ) : (
              <KPICard 
                title={t('finance.averageTicket')} 
                value={data?.kpi?.averageTicket || 0} 
                previousValue={data?.kpi?.previousAverageTicket || 0} 
                format="currency"
                icon={<ReceiptIcon />}
                color="info"
              />
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {loading && !data ? (
              <Skeleton variant="rectangular" height={120} />
            ) : (
              <KPICard 
                title={t('finance.customerCount')} 
                value={data?.kpi?.customerCount || 0} 
                previousValue={data?.kpi?.previousCustomerCount || 0} 
                format="number"
                icon={<PeopleIcon />}
                color="success"
              />
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {loading && !data ? (
              <Skeleton variant="rectangular" height={120} />
            ) : (
              <KPICard 
                title={t('finance.profitMargin')} 
                value={data?.kpi?.profitMargin || 0} 
                previousValue={data?.kpi?.previousProfitMargin || 0} 
                format="percent"
                icon={<TrendingUpIcon />}
                color="warning"
              />
            )}
          </Grid>
        </Grid>
        
        {/* Revenue Chart */}
        <Box sx={{ height: 300, mt: 3 }}>
          {loading && !chartData.length ? (
            <Skeleton variant="rectangular" height="100%" />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatXAxis}
                  axisLine={{ stroke: '#E0E0E0' }}
                  tickLine={false}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value) => 
                    new Intl.NumberFormat('fr-FR', { 
                      style: 'currency', 
                      currency: 'EUR',
                      notation: 'compact',
                      maximumFractionDigits: 1 
                    }).format(value)
                  }
                />
                <RechartsTooltip
                  formatter={(value) => 
                    new Intl.NumberFormat('fr-FR', { 
                      style: 'currency', 
                      currency: 'EUR' 
                    }).format(value)
                  }
                  labelFormatter={(label) => new Date(label).toLocaleString('fr-FR')}
                />
                <Line 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#1976d2" 
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5, strokeWidth: 1 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

// Icônes manquantes
const EuroIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M15 18.5C12.49 18.5 10.32 17.08 9.24 15H15V13H8.58C8.53 12.67 8.5 12.34 8.5 12C8.5 11.66 8.53 11.33 8.58 11H15V9H9.24C10.32 6.92 12.5 5.5 15 5.5C16.61 5.5 18.09 6.09 19.23 7.07L21 5.3C19.41 3.87 17.3 3 15 3C11.08 3 7.76 5.51 6.52 9H3V11H6.06C6.02 11.33 6 11.66 6 12C6 12.34 6.02 12.67 6.06 13H3V15H6.52C7.76 18.49 11.08 21 15 21C17.31 21 19.41 20.13 21 18.7L19.22 16.93C18.09 17.91 16.62 18.5 15 18.5Z" fill="currentColor"/>
  </svg>
);

const ReceiptIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M19.5 3.5L18 2L16.5 3.5L15 2L13.5 3.5L12 2L10.5 3.5L9 2L7.5 3.5L6 2V22L7.5 20.5L9 22L10.5 20.5L12 22L13.5 20.5L15 22L16.5 20.5L18 22L19.5 20.5L21 22V2L19.5 3.5ZM19 19.09H5V4.91H19V19.09ZM7 15H17V17H7V15ZM7 11H17V13H7V11ZM7 7H17V9H7V7Z" fill="currentColor"/>
  </svg>
);

const PeopleIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M16 11C17.66 11 18.99 9.66 18.99 8C18.99 6.34 17.66 5 16 5C14.34 5 13 6.34 13 8C13 9.66 14.34 11 16 11ZM8 11C9.66 11 10.99 9.66 10.99 8C10.99 6.34 9.66 5 8 5C6.34 5 5 6.34 5 8C5 9.66 6.34 11 8 11ZM8 13C5.67 13 1 14.17 1 16.5V19H15V16.5C15 14.17 10.33 13 8 13ZM16 13C15.71 13 15.38 13.02 15.03 13.05C16.19 13.89 17 15.02 17 16.5V19H23V16.5C23 14.17 18.33 13 16 13Z" fill="currentColor"/>
  </svg>
);

const TrendingUpIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M16 6L18.29 8.29L13.41 13.17L9.41 9.17L2 16.59L3.41 18L9.41 12L13.41 16L19.71 9.71L22 12V6H16Z" fill="currentColor"/>
  </svg>
);

export default FinancialKPI;
