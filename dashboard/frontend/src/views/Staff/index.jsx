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
  FilterList as FilterListIcon,
  Today as TodayIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import des composants
import StaffOverview from '../../components/widgets/StaffOverview';

const StaffView = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [view, setView] = useState('week'); // 'day', 'week', 'month'
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleViewChange = (newView) => {
    setView(newView);
  };
  
  const handleAddStaff = () => {
    // Logique d'ajout de personnel à implémenter
    console.log('Adding new staff member...');
  };
  
  const handlePrint = () => {
    window.print();
  };
  
  const handleExport = () => {
    // Logique d'export à implémenter
    console.log('Exporting staff data...');
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* En-tête de la page */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('staff.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <ButtonGroup variant="outlined" size="small">
            <Button 
              startIcon={<TodayIcon />}
              onClick={() => handleViewChange('day')}
              variant={view === 'day' ? 'contained' : 'outlined'}
            >
              {t('timeRange.day')}
            </Button>
            <Button 
              onClick={() => handleViewChange('week')}
              variant={view === 'week' ? 'contained' : 'outlined'}
            >
              {t('timeRange.week')}
            </Button>
            <Button 
              onClick={() => handleViewChange('month')}
              variant={view === 'month' ? 'contained' : 'outlined'}
            >
              {t('timeRange.month')}
            </Button>
          </ButtonGroup>
          <Tooltip title={t('common.customDateRange')}>
            <IconButton size="small">
              <DateRangeIcon />
            </IconButton>
          </Tooltip>
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
          <Tab label={t('staff.overview')} />
          <Tab label={t('staff.schedule')} />
          <Tab label={t('staff.performance')} />
          <Tab label={t('staff.hours')} />
          <Tab label={t('staff.costs')} />
        </Tabs>
      </Paper>
      
      {/* Contenu des onglets */}
      <Box sx={{ mt: 3 }}>
        {tabValue === 0 && (
          <StaffOverview />
        )}
        {tabValue === 1 && (
          <Typography variant="body1">
            {t('staff.scheduleTabContent')}
          </Typography>
        )}
        {tabValue === 2 && (
          <Typography variant="body1">
            {t('staff.performanceTabContent')}
          </Typography>
        )}
        {tabValue === 3 && (
          <Typography variant="body1">
            {t('staff.hoursTabContent')}
          </Typography>
        )}
        {tabValue === 4 && (
          <Typography variant="body1">
            {t('staff.costsTabContent')}
          </Typography>
        )}
      </Box>
      
      {/* Bouton flottant pour ajouter un membre du personnel */}
      <Fab 
        color="primary" 
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleAddStaff}
      >
        <AddIcon />
      </Fab>
    </Container>
  );
};

export default StaffView;
