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
  Button,
  ButtonGroup,
  Tooltip,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Skeleton,
  Chip,
  Alert
} from '@mui/material';
import {
  RefreshOutlined as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Info as InfoIcon,
  CalendarToday as CalendarIcon,
  FileDownload as DownloadIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { fetchSalesForecasts } from '../../store/slices/forecastSlice';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ComposedChart,
  Scatter
} from 'recharts';

// Composant principal pour les prévisions de ventes
const SalesForecast = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { data, loading, error, lastUpdated } = useSelector((state) => state.forecast);
  
  // États locaux
  const [forecastPeriod, setForecastPeriod] = useState('week'); // 'day', 'week', 'month'
  const [forecastType, setForecastType] = useState('revenue'); // 'revenue', 'volume', 'items'
  const [chartType, setChartType] = useState('line'); // 'line', 'bar', 'area'
  const [selectedTab, setSelectedTab] = useState(0);
  const [productCategory, setProductCategory] = useState('all');
  
  useEffect(() => {
    dispatch(fetchSalesForecasts({ period: forecastPeriod, type: forecastType }));
  }, [dispatch, forecastPeriod, forecastType]);
  
  const handleRefresh = () => {
    dispatch(fetchSalesForecasts({ period: forecastPeriod, type: forecastType }));
  };
  
  const handlePeriodChange = (newPeriod) => {
    setForecastPeriod(newPeriod);
  };
  
  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };
  
  // Formatage des données pour les graphiques
  const formatChartData = () => {
    if (!data?.forecasts) return [];
    
    // Pour les données quotidiennes, on formate différemment
    if (forecastPeriod === 'day') {
      return data.forecasts.map(item => ({
        ...item,
        hour: new Date(item.timestamp).getHours() + 'h',
        actualLabel: item.actual !== undefined ? t('forecast.actual') : null,
        forecastLabel: t('forecast.forecast'),
        lowerBoundLabel: t('forecast.lowerBound'),
        upperBoundLabel: t('forecast.upperBound')
      }));
    }
    
    // Pour les données hebdomadaires ou mensuelles
    return data.forecasts.map(item => ({
      ...item,
      date: forecastPeriod === 'week'
        ? new Intl.DateTimeFormat('fr-FR', { weekday: 'short' }).format(new Date(item.timestamp))
        : new Date(item.timestamp).getDate(),
      actualLabel: item.actual !== undefined ? t('forecast.actual') : null,
      forecastLabel: t('forecast.forecast'),
      lowerBoundLabel: t('forecast.lowerBound'),
      upperBoundLabel: t('forecast.upperBound')
    }));
  };
  
  // Données pour le graphique
  const chartData = formatChartData();
  
  // Configuration pour les différents graphiques
  const getChartConfig = () => {
    // Couleurs pour les différentes séries
    const colors = {
      actual: '#1976d2',
      forecast: '#ff9800',
      lowerBound: '#e0e0e0',
      upperBound: '#e0e0e0'
    };
    
    // Formatage des valeurs selon le type de prévision
    const valueFormatter = (value) => {
      if (forecastType === 'revenue') {
        return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
      } else if (forecastType === 'volume') {
        return value.toLocaleString('fr-FR');
      }
      return value;
    };
    
    // Clé de données pour l'axe X selon la période
    const xAxisKey = forecastPeriod === 'day' ? 'hour' : 'date';
    
    return {
      colors,
      valueFormatter,
      xAxisKey
    };
  };
  
  // Configuration du graphique
  const chartConfig = getChartConfig();
  
  // Rendu du graphique selon le type choisi
  const renderChart = () => {
    if (loading && !data?.forecasts) {
      return (
        <Box sx={{ width: '100%', height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <CircularProgress />
        </Box>
      );
    }
    
    if (!chartData.length) {
      return (
        <Box sx={{ width: '100%', height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            {t('forecast.noData')}
          </Typography>
        </Box>
      );
    }
    
    // Graphique en ligne
    if (chartType === 'line') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey={chartConfig.xAxisKey}
              axisLine={{ stroke: '#E0E0E0' }}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tickFormatter={chartConfig.valueFormatter}
            />
            <RechartsTooltip 
              formatter={chartConfig.valueFormatter}
              labelFormatter={(label) => t(`forecast.${forecastPeriod === 'day' ? 'hour' : 'date'}`, { value: label })}
            />
            <Legend />
            
            {/* Zone de confiance */}
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="none"
              fill={chartConfig.colors.lowerBound}
              fillOpacity={0.2}
              name={t('forecast.confidenceInterval')}
              activeDot={false}
              legendType="none"
            />
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill={chartConfig.colors.upperBound}
              fillOpacity={0}
              legendType="none"
              activeDot={false}
            />
            
            {/* Données réelles et prévisions */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke={chartConfig.colors.actual}
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6, strokeWidth: 1 }}
              name={t('forecast.actual')}
            />
            <Line
              type="monotone"
              dataKey="forecast"
              stroke={chartConfig.colors.forecast}
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 4 }}
              activeDot={{ r: 6, strokeWidth: 1 }}
              name={t('forecast.forecast')}
            />
          </LineChart>
        </ResponsiveContainer>
      );
    }
    
    // Graphique en barres
    if (chartType === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey={chartConfig.xAxisKey}
              axisLine={{ stroke: '#E0E0E0' }}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tickFormatter={chartConfig.valueFormatter}
            />
            <RechartsTooltip 
              formatter={chartConfig.valueFormatter}
              labelFormatter={(label) => t(`forecast.${forecastPeriod === 'day' ? 'hour' : 'date'}`, { value: label })}
            />
            <Legend />
            
            {/* Barres pour les valeurs réelles */}
            <Bar
              dataKey="actual"
              fill={chartConfig.colors.actual}
              name={t('forecast.actual')}
              barSize={20}
            />
            
            {/* Ligne pour les prévisions */}
            <Line
              type="monotone"
              dataKey="forecast"
              stroke={chartConfig.colors.forecast}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6, strokeWidth: 1 }}
              name={t('forecast.forecast')}
            />
            
            {/* Points pour les limites de confiance */}
            <Scatter
              dataKey="lowerBound"
              fill={chartConfig.colors.lowerBound}
              name={t('forecast.lowerBound')}
              line={{ stroke: chartConfig.colors.lowerBound, strokeDasharray: '3 3' }}
              shape="cross"
              legendType="none"
            />
            <Scatter
              dataKey="upperBound"
              fill={chartConfig.colors.upperBound}
              name={t('forecast.upperBound')}
              line={{ stroke: chartConfig.colors.upperBound, strokeDasharray: '3 3' }}
              shape="cross"
              legendType="none"
            />
          </ComposedChart>
        </ResponsiveContainer>
      );
    }
    
    // Graphique en aire
    return (
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey={chartConfig.xAxisKey}
            axisLine={{ stroke: '#E0E0E0' }}
            tickLine={false}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tickFormatter={chartConfig.valueFormatter}
          />
          <RechartsTooltip 
            formatter={chartConfig.valueFormatter}
            labelFormatter={(label) => t(`forecast.${forecastPeriod === 'day' ? 'hour' : 'date'}`, { value: label })}
          />
          <Legend />
          
          {/* Zone de confiance */}
          <Area
            type="monotone"
            dataKey="lowerBound"
            stackId="1"
            stroke="none"
            fill={chartConfig.colors.lowerBound}
            fillOpacity={0.1}
            legendType="none"
          />
          <Area
            type="monotone"
            dataKey="upperBound"
            stackId="1"
            stroke="none"
            fill={chartConfig.colors.upperBound}
            fillOpacity={0.1}
            name={t('forecast.confidenceInterval')}
          />
          
          {/* Données réelles et prévisions */}
          <Area
            type="monotone"
            dataKey="actual"
            stroke={chartConfig.colors.actual}
            fill={chartConfig.colors.actual}
            fillOpacity={0.4}
            name={t('forecast.actual')}
          />
          <Area
            type="monotone"
            dataKey="forecast"
            stroke={chartConfig.colors.forecast}
            fill={chartConfig.colors.forecast}
            fillOpacity={0.4}
            strokeDasharray="5 5"
            name={t('forecast.forecast')}
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  };
  
  // Rendu des statistiques
  const renderStats = () => {
    if (!data?.summary) {
      return (
        <Box sx={{ p: 2 }}>
          <Skeleton variant="rectangular" height={100} />
        </Box>
      );
    }
    
    const { summary } = data;
    
    return (
      <Grid container spacing={2} sx={{ p: 1 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('forecast.totalForecast')}
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {forecastType === 'revenue'
                ? new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(summary.totalForecast)
                : summary.totalForecast.toLocaleString('fr-FR')}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <TrendingUpIcon 
                fontSize="small" 
                color={summary.changePercent >= 0 ? 'success' : 'error'}
                sx={{ mr: 0.5 }}
              />
              <Typography 
                variant="body2" 
                color={summary.changePercent >= 0 ? 'success.main' : 'error.main'}
              >
                {summary.changePercent >= 0 ? '+' : ''}{summary.changePercent.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                {t('forecast.vsPrevious')}
              </Typography>
            </Box>
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('forecast.peakValue')}
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {forecastType === 'revenue'
                ? new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(summary.peakValue)
                : summary.peakValue.toLocaleString('fr-FR')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {t('forecast.expectedOn')} {new Date(summary.peakDate).toLocaleDateString('fr-FR')}
            </Typography>
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('forecast.accuracy')}
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {summary.accuracy.toFixed(1)}%
            </Typography>
            <Tooltip title={t('forecast.accuracyInfo')}>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <InfoIcon fontSize="small" color="info" sx={{ mr: 0.5 }} />
                <Typography variant="body2" color="text.secondary">
                  {t('forecast.basedOnHistory')}
                </Typography>
              </Box>
            </Tooltip>
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('forecast.anomalyScore')}
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {summary.anomalyScore.toFixed(1)}
            </Typography>
            <Chip 
              size="small"
              label={t(`forecast.anomalyLevel.${summary.anomalyScore < 30 ? 'low' : summary.anomalyScore < 70 ? 'medium' : 'high'}`)}
              color={summary.anomalyScore < 30 ? 'success' : summary.anomalyScore < 70 ? 'warning' : 'error'}
              sx={{ mt: 1 }}
            />
          </Box>
        </Grid>
      </Grid>
    );
  };
  
  // Rendu de l'onglet "Tendances"
  const renderTrendsTab = () => {
    if (!data?.trends) {
      return (
        <Box sx={{ p: 2 }}>
          <Skeleton variant="rectangular" height={200} />
        </Box>
      );
    }
    
    return (
      <Box sx={{ p: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              {t('forecast.topSellingItems')}
            </Typography>
            {data.trends.topSellingItems.map((item, index) => (
              <Box 
                key={index}
                sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 1,
                  borderBottom: index < data.trends.topSellingItems.length - 1 ? 1 : 0,
                  borderColor: 'divider'
                }}
              >
                <Typography variant="body2">
                  {index + 1}. {item.name}
                </Typography>
                <Chip 
                  size="small" 
                  label={forecastType === 'revenue' 
                    ? new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(item.value)
                    : item.value.toLocaleString('fr-FR')}
                />
              </Box>
            ))}
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              {t('forecast.growthByCategory')}
            </Typography>
            {data.trends.growthByCategory.map((item, index) => (
              <Box 
                key={index}
                sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 1,
                  borderBottom: index < data.trends.growthByCategory.length - 1 ? 1 : 0,
                  borderColor: 'divider'
                }}
              >
                <Typography variant="body2">
                  {item.name}
                </Typography>
                <Chip 
                  size="small" 
                  label={`${item.growthPercent >= 0 ? '+' : ''}${item.growthPercent.toFixed(1)}%`}
                  color={item.growthPercent >= 0 ? 'success' : 'error'}
                />
              </Box>
            ))}
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Box>
          <Typography variant="subtitle1" gutterBottom>
            {t('forecast.insights')}
          </Typography>
          {data.trends.insights.map((insight, index) => (
            <Alert 
              key={index} 
              severity={insight.type} 
              sx={{ mb: 1 }}
              icon={insight.type === 'info' ? <InfoIcon /> : undefined}
            >
              <Typography variant="body2">
                {insight.message}
              </Typography>
            </Alert>
          ))}
        </Box>
      </Box>
    );
  };
  
  // Rendu de l'onglet "ML Model"
  const renderModelTab = () => {
    if (!data?.model) {
      return (
        <Box sx={{ p: 2 }}>
          <Skeleton variant="rectangular" height={200} />
        </Box>
      );
    }
    
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          {t('forecast.modelInfo')}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('forecast.modelName')}
              </Typography>
              <Typography variant="body1">
                {data.model.name}
              </Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('forecast.lastTrained')}
              </Typography>
              <Typography variant="body1">
                {new Date(data.model.lastTrained).toLocaleString('fr-FR')}
              </Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('forecast.dataPoints')}
              </Typography>
              <Typography variant="body1">
                {data.model.dataPoints.toLocaleString('fr-FR')}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('forecast.features')}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {data.model.features.map((feature, index) => (
                  <Chip key={index} label={feature} size="small" />
                ))}
              </Box>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('forecast.trainAccuracy')}
              </Typography>
              <Typography variant="body1">
                {data.model.trainAccuracy.toFixed(1)}%
              </Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('forecast.validationAccuracy')}
              </Typography>
              <Typography variant="body1">
                {data.model.validationAccuracy.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>
    );
  };
  
  // Rendu du contenu de l'onglet actif
  const renderTabContent = () => {
    switch (selectedTab) {
      case 1:
        return renderTrendsTab();
      case 2:
        return renderModelTab();
      default:
        return (
          <Box>
            {renderStats()}
            <Box sx={{ p: 2 }}>
              {renderChart()}
            </Box>
          </Box>
        );
    }
  };
  
  return (
    <Card elevation={2}>
      <CardHeader
        title={t('forecast.title')}
        subheader={lastUpdated ? t('forecast.lastUpdate', { time: new Date(lastUpdated).toLocaleString() }) : ''}
        action={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', gap: 1, mr: 1 }}>
              <ButtonGroup size="small">
                <Button 
                  variant={chartType === 'line' ? 'contained' : 'outlined'} 
                  onClick={() => setChartType('line')}
                >
                  {t('forecast.line')}
                </Button>
                <Button 
                  variant={chartType === 'bar' ? 'contained' : 'outlined'} 
                  onClick={() => setChartType('bar')}
                >
                  {t('forecast.bar')}
                </Button>
                <Button 
                  variant={chartType === 'area' ? 'contained' : 'outlined'} 
                  onClick={() => setChartType('area')}
                >
                  {t('forecast.area')}
                </Button>
              </ButtonGroup>
            </Box>
            
            <Tooltip title={t('common.refresh')}>
              <IconButton onClick={handleRefresh} disabled={loading}>
                {loading ? <CircularProgress size={24} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title={t('common.settings')}>
              <IconButton>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={t('common.export')}>
              <IconButton>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      
      <Divider />
      
      <Box sx={{ p: 2, backgroundColor: 'background.paper' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <ButtonGroup size="small">
              <Button 
                variant={forecastPeriod === 'day' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('day')}
              >
                {t('forecast.day')}
              </Button>
              <Button 
                variant={forecastPeriod === 'week' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('week')}
              >
                {t('forecast.week')}
              </Button>
              <Button 
                variant={forecastPeriod === 'month' ? 'contained' : 'outlined'} 
                onClick={() => handlePeriodChange('month')}
              >
                {t('forecast.month')}
              </Button>
            </ButtonGroup>
          </Grid>
          
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="forecast-type-label">{t('forecast.type')}</InputLabel>
              <Select
                labelId="forecast-type-label"
                value={forecastType}
                onChange={(e) => setForecastType(e.target.value)}
                label={t('forecast.type')}
              >
                <MenuItem value="revenue">{t('forecast.revenue')}</MenuItem>
                <MenuItem value="volume">{t('forecast.volume')}</MenuItem>
                <MenuItem value="items">{t('forecast.items')}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {forecastType === 'items' && (
            <Grid item>
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel id="product-category-label">{t('forecast.category')}</InputLabel>
                <Select
                  labelId="product-category-label"
                  value={productCategory}
                  onChange={(e) => setProductCategory(e.target.value)}
                  label={t('forecast.category')}
                >
                  <MenuItem value="all">{t('forecast.allCategories')}</MenuItem>
                  {data?.categories?.map((category) => (
                    <MenuItem key={category} value={category}>
                      {t(`forecast.categories.${category}`, { defaultValue: category })}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
          
          <Grid item xs />
          
          {data?.alerts && data.alerts.length > 0 && (
            <Grid item>
              <Alert severity="warning" icon={<WarningIcon />} sx={{ py: 0 }}>
                {t('forecast.anomalyDetected')}
              </Alert>
            </Grid>
          )}
        </Grid>
      </Box>
      
      <Box>
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          variant="fullWidth"
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label={t('forecast.forecasts')} />
          <Tab label={t('forecast.trends')} />
          <Tab label={t('forecast.mlModel')} />
        </Tabs>
      </Box>
      
      <Divider />
      
      <CardContent sx={{ p: 0 }}>
        {error ? (
          <Alert severity="error" sx={{ m: 2 }}>
            {t('forecast.error')}: {error}
          </Alert>
        ) : (
          renderTabContent()
        )}
      </CardContent>
    </Card>
  );
};

export default SalesForecast;
