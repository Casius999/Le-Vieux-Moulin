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
  TextField,
  InputAdornment
} from '@mui/material';
import { 
  Search as SearchIcon,
  FilterList as FilterListIcon,
  GetApp as GetAppIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import des composants
import StockOverview from '../../components/widgets/StockOverview';

const StockView = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [category, setCategory] = useState('all'); // 'all', 'ingredients', 'drinks', 'supplies'
  const [searchQuery, setSearchQuery] = useState('');
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleCategoryChange = (newCategory) => {
    setCategory(newCategory);
  };
  
  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };
  
  const handlePrint = () => {
    window.print();
  };
  
  const handleExport = () => {
    // Logique d'export à implémenter
    console.log('Exporting stock data...');
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* En-tête de la page */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('stock.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            size="small"
            placeholder={t('common.search')}
            value={searchQuery}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
            sx={{ width: 200 }}
          />
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
      
      {/* Filtres de catégorie */}
      <Box sx={{ mb: 3 }}>
        <ButtonGroup variant="outlined" size="small">
          <Button 
            onClick={() => handleCategoryChange('all')}
            variant={category === 'all' ? 'contained' : 'outlined'}
          >
            {t('stock.category.all')}
          </Button>
          <Button 
            onClick={() => handleCategoryChange('ingredients')}
            variant={category === 'ingredients' ? 'contained' : 'outlined'}
          >
            {t('stock.category.ingredients')}
          </Button>
          <Button 
            onClick={() => handleCategoryChange('drinks')}
            variant={category === 'drinks' ? 'contained' : 'outlined'}
          >
            {t('stock.category.drinks')}
          </Button>
          <Button 
            onClick={() => handleCategoryChange('supplies')}
            variant={category === 'supplies' ? 'contained' : 'outlined'}
          >
            {t('stock.category.supplies')}
          </Button>
        </ButtonGroup>
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
          <Tab label={t('stock.overview')} />
          <Tab label={t('stock.inventory')} />
          <Tab label={t('stock.orders')} />
          <Tab label={t('stock.equipment')} />
          <Tab label={t('stock.history')} />
        </Tabs>
      </Paper>
      
      {/* Contenu des onglets */}
      <Box sx={{ mt: 3 }}>
        {tabValue === 0 && (
          <StockOverview />
        )}
        {tabValue === 1 && (
          <Typography variant="body1">
            {t('stock.inventoryTabContent')}
          </Typography>
        )}
        {tabValue === 2 && (
          <Typography variant="body1">
            {t('stock.ordersTabContent')}
          </Typography>
        )}
        {tabValue === 3 && (
          <Typography variant="body1">
            {t('stock.equipmentTabContent')}
          </Typography>
        )}
        {tabValue === 4 && (
          <Typography variant="body1">
            {t('stock.historyTabContent')}
          </Typography>
        )}
      </Box>
    </Container>
  );
};

export default StockView;
