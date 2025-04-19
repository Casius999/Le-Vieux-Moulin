import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Container, 
  Box, 
  Typography, 
  Button, 
  Paper 
} from '@mui/material';
import { 
  Home as HomeIcon,
} from '@mui/icons-material';

const NotFound = () => {
  const { t } = useTranslation();
  
  return (
    <Container component="main" maxWidth="md" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
      <Paper 
        elevation={3}
        sx={{
          p: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
        }}
      >
        <Typography variant="h1" color="primary" gutterBottom>
          404
        </Typography>
        <Typography variant="h4" gutterBottom>
          {t('error.pageNotFound')}
        </Typography>
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          {t('error.pageNotFoundMessage')}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            component={RouterLink}
            to="/"
            startIcon={<HomeIcon />}
          >
            {t('error.backToHome')}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default NotFound;
