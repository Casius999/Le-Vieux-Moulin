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
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import { 
  DateRange as DateRangeIcon,
  GetApp as GetAppIcon,
  Print as PrintIcon,
  FilterList as FilterListIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as CsvIcon,
  Image as ImageIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import des composants
import FinanceOverview from '../../components/widgets/FinanceOverview';

const FinanceView = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [period, setPeriod] = useState('month'); // 'month', 'quarter', 'year'
  const [exportMenu, setExportMenu] = useState(null);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod);
  };
  
  const handleExportClick = (event) => {
    setExportMenu(event.currentTarget);
  };
  
  const handleExportClose = () => {
    setExportMenu(null);
  };
  
  const handleExport = (format) => {
    // Logique d'export à implémenter
    console.log(`Exporting financial data as ${format}...`);
    handleExportClose();
  };
  
  const handlePrint = () => {
    window.print();
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* En-tête de la page */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('finance.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <ButtonGroup variant="outlined" size="small">
            <Button 
              onClick={() => handlePeriodChange('month')}
              variant={period === 'month' ? 'contained' : 'outlined'}
            >
              {t('timeRange.month')}
            </Button>
            <Button 
              onClick={() => handlePeriodChange('quarter')}
              variant={period === 'quarter' ? 'contained' : 'outlined'}
            >
              {t('timeRange.quarter')}
            </Button>
            <Button 
              onClick={() => handlePeriodChange('year')}
              variant={period === 'year' ? 'contained' : 'outlined'}
            >
              {t('timeRange.year')}
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
            <IconButton size="small" onClick={handleExportClick}>
              <GetAppIcon />
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={exportMenu}
            open={Boolean(exportMenu)}
            onClose={handleExportClose}
          >
            <MenuItem onClick={() => handleExport('pdf')}>
              <ListItemIcon>
                <PdfIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>PDF</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleExport('csv')}>
              <ListItemIcon>
                <CsvIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>CSV</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleExport('excel')}>
              <ListItemIcon>
                <TableChartIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Excel</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleExport('image')}>
              <ListItemIcon>
                <ImageIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Image</ListItemText>
            </MenuItem>
          </Menu>
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
          <Tab label={t('finance.overview')} />
          <Tab label={t('finance.revenue')} />
          <Tab label={t('finance.expenses')} />
          <Tab label={t('finance.profit')} />
          <Tab label={t('finance.reports')} />
        </Tabs>
      </Paper>
      
      {/* Contenu des onglets */}
      <Box sx={{ mt: 3 }}>
        {tabValue === 0 && (
          <FinanceOverview />
        )}
        {tabValue === 1 && (
          <Typography variant="body1">
            {t('finance.revenueTabContent')}
          </Typography>
        )}
        {tabValue === 2 && (
          <Typography variant="body1">
            {t('finance.expensesTabContent')}
          </Typography>
        )}
        {tabValue === 3 && (
          <Typography variant="body1">
            {t('finance.profitTabContent')}
          </Typography>
        )}
        {tabValue === 4 && (
          <Typography variant="body1">
            {t('finance.reportsTabContent')}
          </Typography>
        )}
      </Box>
    </Container>
  );
};

export default FinanceView;
