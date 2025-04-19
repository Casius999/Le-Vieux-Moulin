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
  Tooltip,
  Fab
} from '@mui/material';
import { 
  Add as AddIcon,
  GetApp as GetAppIcon,
  Print as PrintIcon,
  FilterList as FilterListIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import des composants
import MarketingOverview from '../../components/widgets/MarketingOverview';

const MarketingView = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState('month'); // 'week', 'month', 'quarter', 'year'
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
  };
  
  const handleCreateCampaign = () => {
    // Logique de création de campagne à implémenter
    console.log('Creating new marketing campaign...');
  };
  
  const handlePrint = () => {
    window.print();
  };
  
  const handleExport = () => {
    // Logique d'export à implémenter
    console.log('Exporting marketing data...');
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* En-tête de la page */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('marketing.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <ButtonGroup variant="outlined" size="small">
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
              onClick={() => handleTimeRangeChange('quarter')}
              variant={timeRange === 'quarter' ? 'contained' : 'outlined'}
            >
              {t('timeRange.quarter')}
            </Button>
            <Button 
              onClick={() => handleTimeRangeChange('year')}
              variant={timeRange === 'year' ? 'contained' : 'outlined'}
            >
              {t('timeRange.year')}
            </Button>
          </ButtonGroup>
          <Tooltip title={t('common.filters')}>
            <IconButton size="small">
              <FilterListIcon />
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
          <Tab label={t('marketing.overview')} />
          <Tab label={t('marketing.campaigns')} />
          <Tab label={t('marketing.social')} />
          <Tab label={t('marketing.promotions')} />
          <Tab label={t('marketing.reviews')} />
        </Tabs>
      </Paper>
      
      {/* Contenu des onglets */}
      <Box sx={{ mt: 3 }}>
        {tabValue === 0 && (
          <MarketingOverview />
        )}
        {tabValue === 1 && (
          <Typography variant="body1">
            {t('marketing.campaignsTabContent')}
          </Typography>
        )}
        {tabValue === 2 && (
          <Typography variant="body1">
            {t('marketing.socialTabContent')}
          </Typography>
        )}
        {tabValue === 3 && (
          <Typography variant="body1">
            {t('marketing.promotionsTabContent')}
          </Typography>
        )}
        {tabValue === 4 && (
          <Typography variant="body1">
            {t('marketing.reviewsTabContent')}
          </Typography>
        )}
      </Box>
      
      {/* Bouton flottant pour créer une campagne */}
      <Fab 
        color="primary" 
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleCreateCampaign}
      >
        <AddIcon />
      </Fab>
    </Container>
  );
};

export default MarketingView;
