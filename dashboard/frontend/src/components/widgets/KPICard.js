import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';

function KPICard({ kpi }) {
  const {
    name,
    value,
    unit,
    trend,
    status = 'info',
    icon: Icon,
  } = kpi;

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'success.main';
      case 'warning':
        return 'warning.main';
      case 'danger':
        return 'error.main';
      case 'info':
      default:
        return 'info.main';
    }
  };

  const getTrendIcon = () => {
    if (trend > 0) return <TrendingUpIcon color="success" />;
    if (trend < 0) return <TrendingDownIcon color="error" />;
    return <TrendingFlatIcon color="action" />;
  };

  const formatValue = (value, unit) => {
    if (unit === '€') return `${value.toLocaleString('fr-FR')} ${unit}`;
    if (unit === '%') return `${value}${unit}`;
    return `${value} ${unit}`;
  };

  return (
    <Card
      sx={{
        minWidth: 200,
        borderLeft: 4,
        borderColor: getStatusColor(status),
      }}
    >
      <CardContent>
        <Typography
          variant="subtitle2"
          color="text.secondary"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
        >
          {Icon && <Icon fontSize="small" />}
          {name}
        </Typography>
        <Typography variant="h5" component="div">
          {formatValue(value, unit)}
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            mt: 1,
          }}
        >
          {getTrendIcon()}
          <Typography
            variant="body2"
            color={trend > 0 ? 'success.main' : trend < 0 ? 'error.main' : 'text.secondary'}
          >
            {trend > 0 ? '+' : ''}
            {trend}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            vs période précédente
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default KPICard;
