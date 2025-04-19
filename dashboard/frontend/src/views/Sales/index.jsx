import React, { useState } from 'react';
import { 
  Container, 
  Grid, 
  Typography, 
  Box, 
  Tabs, 
  Tab,
  Paper,
  ButtonGroup,
  Button,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  DateRange as DateRangeIcon,
  GetApp as GetAppIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import des composants
import SalesOverview from '../../components/widgets/SalesOverview';

const SalesView = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState('week'); // 'day', 'week', 'month', 'year'
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
  };
  
  const handlePrint = () => {
    window.print();
  };
  
  const handleExport = () => {
    // Logique d'export à implémenter
    console.log('Exporting sales data...');
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* En-tête de la page */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('sales.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <ButtonGroup variant="outlined" size="small">
            <Button 
              onClick={() => handleTimeRangeChange('day')}
              variant={timeRange === 'day' ? 'contained' : 'outlined'}
            >
              {t('timeRange.day')}
            </Button>
            <Button 
              onClick={() => handleTimeRangeChange('week')}
              variant={timeRange === 'week' ? 'contained' : 'outlined'}
            >
              {t('timeRange.week')}
            </Button>
            <Button 
              onClick={() => handleTimeRangeChange('month')}
              variant={timeRange === 'month' ? 'contained' : 'outlined'}
            >
              {t('timeRange.month')}
            </Button>
            <Button 
              onClick={() => handleTimeRangeChange('year')}
              variant={timeRange === 'year' ? 'contained' : 'outlined'}
            >
              {t('timeRange.year')}
            </Button>
          </ButtonGroup>
          <Tooltip title={t('common.customDateRange')}>
            <IconButton size="small">
              <DateRangeIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('common.export')}>
            <IconButton size="small" onClick={handleExport}>
              <GetAppIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('common.print')}>
            <IconButton size="small" onClick={handlePrint}>
              <PrintIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Onglets */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label={t('sales.overview')} />
          <Tab label={t('sales.products')} />
          <Tab label={t('sales.hourly')} />
          <Tab label={t('sales.trends')} />
          <Tab label={t('sales.comparison')} />
        </Tabs>
      </Paper>
      
      {/* Contenu des onglets */}
      <Box sx={{ mt: 3 }}>
        {tabValue === 0 && (
          <SalesOverview />
        )}
        {tabValue === 1 && (
          <Typography variant="body1">
            {t('sales.productsTabContent')}
          </Typography>
        )}
        {tabValue === 2 && (
          <Typography variant="body1">
            {t('sales.hourlyTabContent')}
          </Typography>
        )}
        {tabValue === 3 && (
          <Typography variant="body1">
            {t('sales.trendsTabContent')}
          </Typography>
        )}
        {tabValue === 4 && (
          <Typography variant="body1">
            {t('sales.comparisonTabContent')}
          </Typography>
        )}
      </Box>
    </Container>
  );
};

export default SalesView;
