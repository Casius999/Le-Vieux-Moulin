import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Grid,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Tooltip,
  IconButton,
  CircularProgress,
  Divider,
  Alert
} from '@mui/material';
import {
  ThermostatOutlined as TempIcon,
  WaterOutlined as LiquidIcon,
  Kitchen as FridgeIcon,
  LocalFireDepartment as FireIcon,
  PowerSettingsNew as PowerIcon,
  RefreshOutlined as RefreshIcon,
  ErrorOutline as ErrorIcon,
  CheckCircleOutline as CheckIcon,
  WarningAmber as WarningIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { fetchIotData } from '../../store/slices/iotSlice';

// Composant pour afficher un capteur IoT avec son état
const SensorStatus = ({ sensor }) => {
  const { t } = useTranslation();
  
  // Déterminer la couleur en fonction du statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'normal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Déterminer l'icône en fonction du type de capteur
  const getIcon = (type) => {
    switch (type) {
      case 'temperature':
        return <TempIcon />;
      case 'liquid':
        return <LiquidIcon />;
      case 'refrigeration':
        return <FridgeIcon />;
      case 'heat':
        return <FireIcon />;
      case 'power':
        return <PowerIcon />;
      default:
        return <TempIcon />;
    }
  };
  
  return (
    <Box sx={{ p: 1, border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ mr: 1, color: `${getStatusColor(sensor.status)}.main` }}>
            {getIcon(sensor.type)}
          </Box>
          <Typography variant="body1" fontWeight="medium">
            {sensor.name}
          </Typography>
        </Box>
        <Chip 
          size="small" 
          color={getStatusColor(sensor.status)} 
          label={t(`iot.status.${sensor.status}`)}
          icon={sensor.status === 'normal' ? <CheckIcon /> : sensor.status === 'warning' ? <WarningIcon /> : <ErrorIcon />}
        />
      </Box>
      
      <Box sx={{ mb: 1 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {t('iot.currentValue')}: 
          <Box component="span" fontWeight="bold" ml={1}>
            {sensor.currentValue} {sensor.unit}
          </Box>
        </Typography>
        
        {sensor.min !== undefined && sensor.max !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box sx={{ width: '100%', mr: 1 }}>
              <LinearProgress
                variant="determinate"
                value={((sensor.currentValue - sensor.min) / (sensor.max - sensor.min)) * 100}
                color={getStatusColor(sensor.status)}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
            <Box sx={{ minWidth: 35 }}>
              <Typography variant="body2" color="text.secondary">{`${Math.round(
                ((sensor.currentValue - sensor.min) / (sensor.max - sensor.min)) * 100
              )}%`}</Typography>
            </Box>
          </Box>
        )}
      </Box>
      
      {sensor.lastUpdated && (
        <Typography variant="caption" color="text.secondary">
          {t('iot.lastUpdate')}: {new Date(sensor.lastUpdated).toLocaleTimeString()}
        </Typography>
      )}
    </Box>
  );
};

// Composant principal pour le monitoring IoT
const IotMonitoring = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { data, loading, error, lastUpdated } = useSelector((state) => state.iot);
  
  useEffect(() => {
    dispatch(fetchIotData());
    
    // Mise à jour périodique toutes les 30 secondes
    const intervalId = setInterval(() => {
      dispatch(fetchIotData());
    }, 30000);
    
    return () => clearInterval(intervalId);
  }, [dispatch]);
  
  const handleRefresh = () => {
    dispatch(fetchIotData());
  };
  
  // Regrouper les capteurs par catégorie
  const groupedSensors = data?.sensors?.reduce((acc, sensor) => {
    if (!acc[sensor.category]) {
      acc[sensor.category] = [];
    }
    acc[sensor.category].push(sensor);
    return acc;
  }, {}) || {};
  
  return (
    <Card elevation={2}>
      <CardHeader
        title={t('iot.monitoring')}
        subheader={lastUpdated ? t('iot.lastUpdateFull', { time: new Date(lastUpdated).toLocaleTimeString() }) : t('iot.noData')}
        action={
          <Tooltip title={t('common.refresh')}>
            <IconButton onClick={handleRefresh} disabled={loading}>
              {loading ? <CircularProgress size={24} /> : <RefreshIcon />}
            </IconButton>
          </Tooltip>
        }
      />
      <Divider />
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {t('iot.errorFetching')}: {error}
          </Alert>
        )}
        
        {loading && !data?.sensors && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        )}
        
        {data?.sensors?.length === 0 && !loading && (
          <Typography variant="body1" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
            {t('iot.noSensors')}
          </Typography>
        )}
        
        {Object.entries(groupedSensors).map(([category, sensors]) => (
          <Box key={category} sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t(`iot.categories.${category}`, { defaultValue: category })}
            </Typography>
            <Grid container spacing={2}>
              {sensors.map((sensor) => (
                <Grid item key={sensor.id} xs={12} md={6}>
                  <SensorStatus sensor={sensor} />
                </Grid>
              ))}
            </Grid>
          </Box>
        ))}
        
        {data?.alerts?.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              {t('iot.alerts')}
            </Typography>
            {data.alerts.map((alert) => (
              <Alert 
                key={alert.id} 
                severity={alert.severity} 
                sx={{ mb: 1 }}
                action={
                  <Tooltip title={t('iot.alertTime', { time: new Date(alert.timestamp).toLocaleString() })}>
                    <Box>
                      <Chip 
                        size="small" 
                        label={alert.equipment} 
                        variant="outlined" 
                      />
                    </Box>
                  </Tooltip>
                }
              >
                <Typography variant="body2" fontWeight="bold">
                  {alert.title}
                </Typography>
                <Typography variant="body2">
                  {alert.message}
                </Typography>
              </Alert>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default IotMonitoring;
