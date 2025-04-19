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
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress
} from '@mui/material';
import {
  RefreshOutlined as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircleOutline as CheckIcon,
  CloudDownload as DownloadIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { fetchInventoryData } from '../../store/slices/inventorySlice';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from 'recharts';

// Composant principal pour la gestion des stocks
const InventoryManager = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { data, loading, error, lastUpdated } = useSelector((state) => state.inventory);
  
  // États locaux
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [expanded, setExpanded] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [orderDialogOpen, setOrderDialogOpen] = useState(false);
  const [orderQuantity, setOrderQuantity] = useState(0);
  
  useEffect(() => {
    dispatch(fetchInventoryData());
    
    // Mise à jour périodique toutes les 5 minutes
    const intervalId = setInterval(() => {
      dispatch(fetchInventoryData());
    }, 300000);
    
    return () => clearInterval(intervalId);
  }, [dispatch]);
  
  // Filtrer les données d'inventaire
  const filteredItems = data?.items?.filter(item => {
    const matchesCategory = category === 'all' || item.category === category;
    const matchesSearch = search === '' || 
      item.name.toLowerCase().includes(search.toLowerCase()) || 
      item.id.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  }) || [];
  
  // Pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Gestion des dialogues
  const handleOpenDialog = (item) => {
    setSelectedItem(item);
    setDialogOpen(true);
  };
  
  const handleCloseDialog = () => {
    setDialogOpen(false);
  };
  
  const handleOpenOrderDialog = (item) => {
    setSelectedItem(item);
    setOrderQuantity(item.recommendedOrderQuantity || Math.max(item.maxLevel - item.currentLevel, 0));
    setOrderDialogOpen(true);
  };
  
  const handleCloseOrderDialog = () => {
    setOrderDialogOpen(false);
  };
  
  const handleSubmitOrder = () => {
    // Logique pour soumettre une commande
    console.log(`Commande de ${orderQuantity} ${selectedItem.unit} de ${selectedItem.name}`);
    setOrderDialogOpen(false);
    // Ici, on pourrait dispatcher une action pour enregistrer la commande
  };
  
  const handleRefresh = () => {
    dispatch(fetchInventoryData());
  };
  
  // Formatage des données pour le graphique en camembert
  const getStockStatusData = () => {
    if (!data?.items) return [];
    
    const statusCount = {
      normal: 0,
      warning: 0,
      critical: 0
    };
    
    data.items.forEach(item => {
      if (item.currentLevel <= item.criticalLevel) {
        statusCount.critical++;
      } else if (item.currentLevel <= item.warningLevel) {
        statusCount.warning++;
      } else {
        statusCount.normal++;
      }
    });
    
    return [
      { name: t('inventory.statusNormal'), value: statusCount.normal, color: '#4caf50' },
      { name: t('inventory.statusWarning'), value: statusCount.warning, color: '#ff9800' },
      { name: t('inventory.statusCritical'), value: statusCount.critical, color: '#f44336' }
    ];
  };
  
  // Formatage des données pour le graphique de catégories
  const getCategoryData = () => {
    if (!data?.items) return [];
    
    const categories = {};
    data.items.forEach(item => {
      if (!categories[item.category]) {
        categories[item.category] = 0;
      }
      categories[item.category]++;
    });
    
    // Palette de couleurs pour les catégories
    const colors = ['#3f51b5', '#2196f3', '#00bcd4', '#009688', '#4caf50', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', '#ff9800'];
    
    return Object.entries(categories).map(([name, value], index) => ({
      name,
      value,
      color: colors[index % colors.length]
    }));
  };
  
  // Déterminer le statut d'un article
  const getItemStatus = (item) => {
    if (item.currentLevel <= item.criticalLevel) {
      return 'critical';
    } else if (item.currentLevel <= item.warningLevel) {
      return 'warning';
    }
    return 'normal';
  };
  
  // Icône correspondant au statut
  const getStatusIcon = (status) => {
    switch (status) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'normal':
        return <CheckIcon color="success" />;
      default:
        return null;
    }
  };
  
  // Pourcentage de remplissage
  const getStockPercentage = (item) => {
    if (item.maxLevel === 0) return 0;
    return Math.min(100, Math.round((item.currentLevel / item.maxLevel) * 100));
  };
  
  // Couleur correspondant au statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'normal':
        return 'success';
      default:
        return 'default';
    }
  };
  
  // Catégories disponibles
  const categories = data?.categories || [];
  
  // Informations pour les commandes
  const pendingOrders = data?.pendingOrders || [];
  
  return (
    <Card elevation={2}>
      <CardHeader
        title={t('inventory.title')}
        subheader={lastUpdated ? t('inventory.lastUpdate', { time: new Date(lastUpdated).toLocaleString() }) : ''}
        action={
          <Box sx={{ display: 'flex' }}>
            <Tooltip title={t('common.refresh')}>
              <IconButton onClick={handleRefresh} disabled={loading}>
                {loading ? <CircularProgress size={24} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title={t('common.export')}>
              <IconButton>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={t('common.print')}>
              <IconButton>
                <PrintIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      <Divider />
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {t('inventory.error')}: {error}
          </Alert>
        )}
        
        {/* Filtres et recherche */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel id="category-label">{t('inventory.category')}</InputLabel>
            <Select
              labelId="category-label"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              label={t('inventory.category')}
              startAdornment={
                <InputAdornment position="start">
                  <FilterIcon fontSize="small" />
                </InputAdornment>
              }
            >
              <MenuItem value="all">{t('inventory.allCategories')}</MenuItem>
              {categories.map((cat) => (
                <MenuItem key={cat} value={cat}>{t(`inventory.categories.${cat}`, { defaultValue: cat })}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            size="small"
            label={t('common.search')}
            variant="outlined"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              )
            }}
          />
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
          >
            {t('inventory.addItem')}
          </Button>
        </Box>
        
        {/* Résumé des stocks */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">{t('inventory.summary')}</Typography>
            <Button
              size="small"
              endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? t('common.collapse') : t('common.expand')}
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      {t('inventory.stockStatus')}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip 
                        icon={<CheckIcon />} 
                        label={`${data?.summary?.normalCount || 0} ${t('inventory.normal')}`} 
                        color="success" 
                        variant="outlined" 
                        size="small"
                      />
                      <Chip 
                        icon={<WarningIcon />} 
                        label={`${data?.summary?.warningCount || 0} ${t('inventory.warning')}`} 
                        color="warning" 
                        variant="outlined" 
                        size="small"
                      />
                      <Chip 
                        icon={<ErrorIcon />} 
                        label={`${data?.summary?.criticalCount || 0} ${t('inventory.critical')}`} 
                        color="error" 
                        variant="outlined" 
                        size="small"
                      />
                    </Box>
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      {t('inventory.pendingOrders')}
                    </Typography>
                    <Chip 
                      label={`${pendingOrders.length} ${t('inventory.orders')}`} 
                      color="primary" 
                      variant="outlined" 
                      size="small"
                    />
                  </Box>
                </Box>
                
                {expanded && (
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {t('inventory.stockStatusChart')}
                      </Typography>
                      <Box sx={{ height: 200 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={getStockStatusData()}
                              dataKey="value"
                              nameKey="name"
                              cx="50%"
                              cy="50%"
                              outerRadius={80}
                              innerRadius={40}
                              label={(entry) => entry.name}
                            >
                              {getStockStatusData().map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <RechartsTooltip />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {t('inventory.categoriesChart')}
                      </Typography>
                      <Box sx={{ height: 200 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={getCategoryData()}
                              dataKey="value"
                              nameKey="name"
                              cx="50%"
                              cy="50%"
                              outerRadius={80}
                              innerRadius={40}
                              label={(entry) => entry.name}
                            >
                              {getCategoryData().map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <RechartsTooltip />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      </Box>
                    </Grid>
                  </Grid>
                )}
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <Typography variant="subtitle1" gutterBottom>
                  {t('inventory.criticalItems')}
                </Typography>
                
                {data?.criticalItems?.length === 0 ? (
                  <Alert severity="success">
                    {t('inventory.noCriticalItems')}
                  </Alert>
                ) : (
                  <Box sx={{ maxHeight: expanded ? 300 : 150, overflowY: 'auto' }}>
                    {data?.criticalItems?.map((item) => (
                      <Box 
                        key={item.id} 
                        sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          p: 1,
                          borderBottom: 1,
                          borderColor: 'divider',
                          '&:last-child': {
                            borderBottom: 0
                          }
                        }}
                      >
                        <Box>
                          <Typography variant="body2">
                            {item.name}
                          </Typography>
                          <Typography variant="caption" color="error.main">
                            {item.currentLevel} {item.unit} (min: {item.criticalLevel} {item.unit})
                          </Typography>
                        </Box>
                        <Button 
                          size="small" 
                          variant="outlined" 
                          color="primary"
                          onClick={() => handleOpenOrderDialog(item)}
                        >
                          {t('inventory.order')}
                        </Button>
                      </Box>
                    ))}
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </Box>
        
        {/* Tableau d'inventaire */}
        <TableContainer component={Paper} sx={{ maxHeight: 440 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('inventory.name')}</TableCell>
                <TableCell>{t('inventory.category')}</TableCell>
                <TableCell align="right">{t('inventory.currentLevel')}</TableCell>
                <TableCell align="right">{t('inventory.status')}</TableCell>
                <TableCell>{t('inventory.stockLevel')}</TableCell>
                <TableCell align="right">{t('inventory.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && !data?.items ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : filteredItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    {t('inventory.noItemsFound')}
                  </TableCell>
                </TableRow>
              ) : (
                filteredItems
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((item) => {
                    const status = getItemStatus(item);
                    const percentage = getStockPercentage(item);
                    
                    return (
                      <TableRow 
                        key={item.id}
                        hover
                        sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                      >
                        <TableCell component="th" scope="row">
                          <Typography variant="body2" fontWeight="medium">
                            {item.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={t(`inventory.categories.${item.category}`, { defaultValue: item.category })} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {item.currentLevel} {item.unit}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('inventory.min')}: {item.criticalLevel} {item.unit}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title={t(`inventory.status${status.charAt(0).toUpperCase() + status.slice(1)}`)}>
                            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                              {getStatusIcon(status)}
                            </Box>
                          </Tooltip>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box sx={{ width: '100%', mr: 1 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={percentage} 
                                color={getStatusColor(status)}
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                            </Box>
                            <Box sx={{ minWidth: 35 }}>
                              <Typography variant="body2" color="text.secondary">
                                {percentage}%
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <Tooltip title={t('inventory.viewDetails')}>
                              <IconButton size="small" onClick={() => handleOpenDialog(item)}>
                                <ExpandMoreIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={t('inventory.edit')}>
                              <IconButton size="small">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={t('inventory.order')}>
                              <IconButton 
                                size="small" 
                                color={status === 'critical' ? 'error' : status === 'warning' ? 'warning' : 'default'}
                                onClick={() => handleOpenOrderDialog(item)}
                              >
                                <AddIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    );
                  })
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredItems.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage={t('common.rowsPerPage')}
          labelDisplayedRows={({ from, to, count }) => 
            `${from}-${to} ${t('common.of')} ${count}`
          }
        />
      </CardContent>
      
      {/* Dialogue de détails d'article */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        {selectedItem && (
          <>
            <DialogTitle>
              {selectedItem.name}
              <Chip 
                label={t(`inventory.categories.${selectedItem.category}`, { defaultValue: selectedItem.category })} 
                size="small" 
                sx={{ ml: 1 }}
              />
            </DialogTitle>
            <DialogContent dividers>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    {t('inventory.generalInfo')}
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.id')}: {selectedItem.id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.supplier')}: {selectedItem.supplier}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.location')}: {selectedItem.location}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.lastUpdated')}: {new Date(selectedItem.lastUpdated).toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Typography variant="subtitle1" gutterBottom>
                    {t('inventory.stockLevels')}
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.currentLevel')}: {selectedItem.currentLevel} {selectedItem.unit}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.warningLevel')}: {selectedItem.warningLevel} {selectedItem.unit}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.criticalLevel')}: {selectedItem.criticalLevel} {selectedItem.unit}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.maxLevel')}: {selectedItem.maxLevel} {selectedItem.unit}
                    </Typography>
                  </Box>
                  
                  <Typography variant="subtitle1" gutterBottom>
                    {t('inventory.orderInfo')}
                  </Typography>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.recommendedOrderQuantity')}: {selectedItem.recommendedOrderQuantity} {selectedItem.unit}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.orderLeadTime')}: {selectedItem.orderLeadTime} {t('inventory.days')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.unitPrice')}: {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(selectedItem.unitPrice)}
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    {t('inventory.consumptionHistory')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('inventory.averageDailyConsumption')}: {selectedItem.averageDailyConsumption} {selectedItem.unit} / {t('inventory.day')}
                  </Typography>
                  
                  {/* Ici, on pourrait ajouter un graphique d'utilisation */}
                  
                  <Typography variant="subtitle1" gutterBottom>
                    {t('inventory.pendingOrders')}
                  </Typography>
                  {selectedItem.pendingOrders && selectedItem.pendingOrders.length > 0 ? (
                    selectedItem.pendingOrders.map((order, index) => (
                      <Box 
                        key={index}
                        sx={{ 
                          p: 1,
                          mb: 1,
                          border: 1,
                          borderColor: 'divider',
                          borderRadius: 1
                        }}
                      >
                        <Typography variant="body2">
                          {order.quantity} {selectedItem.unit} - {t('inventory.orderedOn')}: {new Date(order.date).toLocaleDateString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('inventory.expectedDelivery')}: {new Date(order.expectedDelivery).toLocaleDateString()}
                        </Typography>
                      </Box>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      {t('inventory.noPendingOrders')}
                    </Typography>
                  )}
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>
                {t('common.close')}
              </Button>
              <Button 
                variant="contained" 
                color="primary"
                onClick={() => {
                  handleCloseDialog();
                  handleOpenOrderDialog(selectedItem);
                }}
              >
                {t('inventory.orderNow')}
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
      
      {/* Dialogue de commande */}
      <Dialog
        open={orderDialogOpen}
        onClose={handleCloseOrderDialog}
        maxWidth="sm"
        fullWidth
      >
        {selectedItem && (
          <>
            <DialogTitle>
              {t('inventory.orderTitle', { name: selectedItem.name })}
            </DialogTitle>
            <DialogContent dividers>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('inventory.currentLevel')}: {selectedItem.currentLevel} {selectedItem.unit}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('inventory.maxLevel')}: {selectedItem.maxLevel} {selectedItem.unit}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('inventory.recommendedOrderQuantity')}: {selectedItem.recommendedOrderQuantity || Math.max(selectedItem.maxLevel - selectedItem.currentLevel, 0)} {selectedItem.unit}
                </Typography>
              </Box>
              
              <TextField
                fullWidth
                label={t('inventory.orderQuantity')}
                type="number"
                value={orderQuantity}
                onChange={(e) => setOrderQuantity(Math.max(0, parseInt(e.target.value) || 0))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{selectedItem.unit}</InputAdornment>,
                }}
                sx={{ mb: 2 }}
              />
              
              <Typography variant="body2" gutterBottom>
                {t('inventory.estimatedTotal')}: {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(orderQuantity * selectedItem.unitPrice)}
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                {t('inventory.estimatedDelivery')}: {new Date(Date.now() + selectedItem.orderLeadTime * 24 * 60 * 60 * 1000).toLocaleDateString()}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseOrderDialog}>
                {t('common.cancel')}
              </Button>
              <Button 
                variant="contained" 
                color="primary"
                onClick={handleSubmitOrder}
                disabled={orderQuantity <= 0}
              >
                {t('inventory.placeOrder')}
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Card>
  );
};

export default InventoryManager;
