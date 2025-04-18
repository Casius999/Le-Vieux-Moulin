import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Grid, 
  Typography, 
  Paper, 
  Box, 
  Divider,
  IconButton,
  Stack,
  Chip,
  Badge,
  Alert,
  AlertTitle,
  Card,
  CardContent
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  RestaurantMenu as RestaurantMenuIcon
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

// Import des composants widgets
import StockOverview from '../../components/widgets/StockOverview';
import SalesOverview from '../../components/widgets/SalesOverview';

// Import des actions 
import { fetchDashboardData } from '../../store/slices/dashboardSlice';

const DashboardOverview = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { data, loading, error, lastUpdated } = useSelector((state) => state.dashboard);
  const [alertsOpen, setAlertsOpen] = useState({});
  
  useEffect(() => {
    // Chargement initial des données du dashboard
    dispatch(fetchDashboardData());
    
    // Rafraîchissement automatique toutes les 5 minutes
    const intervalId = setInterval(() => {
      dispatch(fetchDashboardData());
    }, 300000);
    
    return () => clearInterval(intervalId);
  }, [dispatch]);
  
  // Gestion des alertes
  const handleAlertClose = (alertId) => {
    setAlertsOpen(prev => ({ ...prev, [alertId]: false }));
  };
  
  // Format de la date
  const formattedDate = format(new Date(), 'EEEE d MMMM yyyy', { locale: fr });
  const lastUpdateTime = lastUpdated ? format(new Date(lastUpdated), 'HH:mm:ss') : '--:--:--';
  
  // Alertes simulées pour l'exemple
  const alerts = [
    { id: 1, type: 'warning', title: 'Stock faible', message: 'Le niveau de Mozzarella est en dessous du seuil critique (5kg restant)' },
    { id: 2, type: 'error', title: 'Équipement en panne', message: 'La sonde de température du four à pizza #2 ne répond plus' },
    { id: 3, type: 'info', title: 'Campagne marketing', message: 'La promotion "Pizza du mois" sera lancée automatiquement demain' }
  ];
  
  // Suggestions du jour (plat du jour, etc.) provenant du module ML
  const suggestions = [
    { id: 1, title: 'Pizza Spéciale du Jour', description: 'Pizza Forestière avec champignons frais (promotion des ingrédients en stock)', profit: 68 },
    { id: 2, title: 'Dessert à mettre en avant', description: 'Tiramisu aux fraises (utilisation optimale des fraises avant péremption)', profit: 72 }
  ];
  
  // Données de réservation pour le jour
  const reservations = [
    { id: 1, time: '12:30', guests: 4, name: 'Dubois', note: 'Anniversaire' },
    { id: 2, time: '13:00', guests: 2, name: 'Martin', note: '' },
    { id: 3, time: '19:30', guests: 6, name: 'Petit', note: 'Table extérieure' },
    { id: 4, time: '20:00', guests: 8, name: 'Leroy', note: 'Réservation VIP' },
    { id: 5, time: '20:30', guests: 4, name: 'Bernard', note: '' }
  ];
  
  const totalReservations = reservations.reduce((sum, res) => sum + res.guests, 0);
  
  // Fonction pour effectuer un rafraîchissement manuel
  const handleRefresh = () => {
    dispatch(fetchDashboardData());
  };
  
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* En-tête du dashboard */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            {t('dashboard.welcome')}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {formattedDate}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Chip 
            label={`${t('dashboard.lastUpdate')}: ${lastUpdateTime}`} 
            variant="outlined" 
            size="small"
          />
          <IconButton onClick={handleRefresh} title={t('common.refresh')}>
            <RefreshIcon />
          </IconButton>
          <IconButton title={t('dashboard.notifications')}>
            <Badge badgeContent={alerts.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          <IconButton title={t('dashboard.settings')}>
            <SettingsIcon />
          </IconButton>
        </Stack>
      </Box>
      
      {/* Alertes */}
      {alerts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {t('dashboard.alerts')}
          </Typography>
          <Stack spacing={2}>
            {alerts.map(alert => (
              <Alert 
                key={alert.id} 
                severity={alert.type}
                onClose={() => handleAlertClose(alert.id)}
                sx={{ display: alertsOpen[alert.id] === false ? 'none' : 'flex' }}
              >
                <AlertTitle>{alert.title}</AlertTitle>
                {alert.message}
              </Alert>
            ))}
          </Stack>
        </Box>
      )}
      
      {/* Grille principale */}
      <Grid container spacing={3}>
        {/* Résumé des stocks */}
        <Grid item xs={12} lg={6}>
          <StockOverview />
        </Grid>
        
        {/* Résumé des ventes */}
        <Grid item xs={12} lg={6}>
          <SalesOverview />
        </Grid>
        
        {/* Réservations du jour */}
        <Grid item xs={12} md={6} lg={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  {t('reservations.today')}
                </Typography>
                <Chip 
                  label={`${totalReservations} ${t('reservations.guests')}`} 
                  color="primary" 
                  size="small"
                />
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
                {reservations.map(reservation => (
                  <Box 
                    key={reservation.id}
                    sx={{ 
                      py: 1, 
                      px: 2, 
                      mb: 1, 
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {reservation.time} - {reservation.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {reservation.guests} {t('reservations.people')}
                        {reservation.note && ` - ${reservation.note}`}
                      </Typography>
                    </Box>
                    <Chip 
                      label={reservation.time} 
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Suggestions du jour (ML) */}
        <Grid item xs={12} md={6} lg={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  {t('suggestions.title')}
                </Typography>
                <RestaurantMenuIcon color="primary" />
              </Box>
              <Divider sx={{ mb: 2 }} />
              {suggestions.map(suggestion => (
                <Paper 
                  key={suggestion.id}
                  sx={{ 
                    p: 2, 
                    mb: 2, 
                    backgroundColor: 'background.default',
                    border: '1px solid',
                    borderLeft: 5,
                    borderColor: 'primary.main',
                    borderRadius: 1
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {suggestion.title}
                    </Typography>
                    <Chip 
                      label={`${suggestion.profit}% ${t('suggestions.profitMargin')}`} 
                      color="success" 
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2">
                    {suggestion.description}
                  </Typography>
                </Paper>
              ))}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Autres widgets */}
        <Grid item xs={12} md={6} lg={4}>
          {/* Placeholder pour des widgets supplémentaires */}
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('dashboard.quickActions')}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Paper 
                    sx={{ 
                      p: 2, 
                      display: 'flex', 
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <Typography variant="body1" gutterBottom>
                      {t('actions.inventory')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('actions.inventoryDesc')}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper 
                    sx={{ 
                      p: 2, 
                      display: 'flex', 
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <Typography variant="body1" gutterBottom>
                      {t('actions.orders')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('actions.ordersDesc')}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper 
                    sx={{ 
                      p: 2, 
                      display: 'flex', 
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <Typography variant="body1" gutterBottom>
                      {t('actions.marketing')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('actions.marketingDesc')}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper 
                    sx={{ 
                      p: 2, 
                      display: 'flex', 
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <Typography variant="body1" gutterBottom>
                      {t('actions.reports')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('actions.reportsDesc')}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DashboardOverview;
