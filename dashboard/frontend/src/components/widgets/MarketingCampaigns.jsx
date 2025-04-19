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
  Button,
  Chip,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  InputAdornment,
  FormHelperText
} from '@mui/material';
import {
  RefreshOutlined as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CampaignOutlined as CampaignIcon,
  FacebookOutlined as FacebookIcon,
  Instagram as InstagramIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  LocalOffer as OfferIcon,
  CalendarToday as CalendarIcon,
  MoreVert as MoreIcon,
  Done as DoneIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { fetchMarketingCampaigns, createCampaign, updateCampaign } from '../../store/slices/marketingSlice';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Composant pour afficher une campagne sous forme de carte
const CampaignCard = ({ campaign, onEdit, onDelete }) => {
  const { t } = useTranslation();
  
  // Format de la date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR');
  };
  
  // Déterminer l'icône selon le type de campagne
  const getCampaignIcon = (type) => {
    switch (type) {
      case 'facebook':
        return <FacebookIcon />;
      case 'instagram':
        return <InstagramIcon />;
      case 'email':
        return <EmailIcon />;
      case 'sms':
        return <SmsIcon />;
      case 'promotion':
        return <OfferIcon />;
      default:
        return <CampaignIcon />;
    }
  };
  
  // Déterminer la couleur du statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'planned':
        return 'info';
      case 'completed':
        return 'default';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Calculer le pourcentage d'avancement
  const getProgress = () => {
    if (!campaign.startDate || !campaign.endDate) return 0;
    
    const now = new Date();
    const start = new Date(campaign.startDate);
    const end = new Date(campaign.endDate);
    
    if (now < start) return 0;
    if (now > end) return 100;
    
    const total = end - start;
    const current = now - start;
    
    return Math.round((current / total) * 100);
  };
  
  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ 
            bgcolor: `${getStatusColor(campaign.status)}.lighter`,
            color: `${getStatusColor(campaign.status)}.main`,
            borderRadius: '50%',
            width: 40,
            height: 40,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            mr: 2
          }}>
            {getCampaignIcon(campaign.type)}
          </Box>
          <Box>
            <Typography variant="body1" fontWeight="bold">
              {campaign.name}
            </Typography>
            <Chip 
              size="small" 
              label={t(`marketing.status.${campaign.status}`)} 
              color={getStatusColor(campaign.status)} 
              sx={{ mt: 0.5 }}
            />
          </Box>
        </Box>
        <Box>
          <IconButton size="small" onClick={() => onEdit(campaign)}>
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" onClick={() => onDelete(campaign.id)}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, flexGrow: 1 }}>
        {campaign.description || t('marketing.noDescription')}
      </Typography>
      
      <Divider sx={{ my: 1 }} />
      
      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {t('marketing.budget')}:
          </Typography>
          <Typography variant="caption" fontWeight="medium">
            {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(campaign.budget)}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {t('marketing.spent')}:
          </Typography>
          <Typography variant="caption" fontWeight="medium">
            {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(campaign.spent)}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {t('marketing.roi')}:
          </Typography>
          <Typography 
            variant="caption" 
            fontWeight="medium"
            color={campaign.metrics.roi >= 0 ? 'success.main' : 'error.main'}
          >
            {campaign.metrics.roi.toFixed(1)}%
          </Typography>
        </Box>
      </Box>
      
      <Divider sx={{ my: 1 }} />
      
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <CalendarIcon fontSize="small" sx={{ color: 'text.secondary', mr: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            {formatDate(campaign.startDate)} - {formatDate(campaign.endDate)}
          </Typography>
        </Box>
        {campaign.status === 'active' && (
          <Chip size="small" label={`${getProgress()}%`} variant="outlined" />
        )}
      </Box>
      
      {campaign.status === 'active' && (
        <LinearProgress 
          variant="determinate" 
          value={getProgress()} 
          sx={{ height: 4, borderRadius: 2 }}
        />
      )}
    </Paper>
  );
};

// Composant principal pour les campagnes marketing
const MarketingCampaigns = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { campaigns, loading, error, lastUpdated } = useSelector((state) => state.marketing);
  
  // États locaux
  const [tabValue, setTabValue] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'email',
    description: '',
    startDate: '',
    endDate: '',
    budget: 0,
    content: {
      title: '',
      description: ''
    }
  });
  const [formErrors, setFormErrors] = useState({});
  
  useEffect(() => {
    dispatch(fetchMarketingCampaigns());
  }, [dispatch]);
  
  // Gérer le changement d'onglet
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Ouvrir le dialogue de création/édition
  const handleOpenDialog = (campaign = null) => {
    if (campaign) {
      setSelectedCampaign(campaign);
      setFormData({
        name: campaign.name,
        type: campaign.type,
        description: campaign.description || '',
        startDate: new Date(campaign.startDate).toISOString().split('T')[0],
        endDate: new Date(campaign.endDate).toISOString().split('T')[0],
        budget: campaign.budget,
        content: {
          title: campaign.content?.title || '',
          description: campaign.content?.description || ''
        }
      });
    } else {
      setSelectedCampaign(null);
      setFormData({
        name: '',
        type: 'email',
        description: '',
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date(new Date().setDate(new Date().getDate() + 30)).toISOString().split('T')[0],
        budget: 0,
        content: {
          title: '',
          description: ''
        }
      });
    }
    setFormErrors({});
    setDialogOpen(true);
  };
  
  // Fermer le dialogue
  const handleCloseDialog = () => {
    setDialogOpen(false);
  };
  
  // Gérer le changement dans le formulaire
  const handleFormChange = (event) => {
    const { name, value } = event.target;
    
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setFormData({
        ...formData,
        [parent]: {
          ...formData[parent],
          [child]: value
        }
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
    
    // Effacer l'erreur si le champ est rempli
    if (formErrors[name] && value) {
      setFormErrors({
        ...formErrors,
        [name]: ''
      });
    }
  };
  
  // Valider le formulaire
  const validateForm = () => {
    const errors = {};
    
    if (!formData.name) errors.name = t('marketing.errors.nameRequired');
    if (!formData.startDate) errors.startDate = t('marketing.errors.startDateRequired');
    if (!formData.endDate) errors.endDate = t('marketing.errors.endDateRequired');
    if (formData.budget < 0) errors.budget = t('marketing.errors.invalidBudget');
    
    if (new Date(formData.startDate) > new Date(formData.endDate)) {
      errors.endDate = t('marketing.errors.endDateBeforeStart');
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // Soumettre le formulaire
  const handleSubmit = () => {
    if (!validateForm()) return;
    
    const campaignData = {
      ...formData,
      spent: selectedCampaign?.spent || 0,
      status: new Date(formData.startDate) > new Date() ? 'planned' : 'active',
      metrics: selectedCampaign?.metrics || {
        impressions: 0,
        clicks: 0,
        conversions: 0,
        roi: 0
      }
    };
    
    if (selectedCampaign) {
      dispatch(updateCampaign({
        id: selectedCampaign.id,
        data: campaignData
      }));
    } else {
      dispatch(createCampaign(campaignData));
    }
    
    handleCloseDialog();
  };
  
  // Gérer la suppression d'une campagne
  const handleDeleteCampaign = (id) => {
    // Ici, vous pourriez ajouter une confirmation avant suppression
    console.log(`Suppression de la campagne ${id}`);
  };
  
  // Obtenir les statistiques de campagnes par statut
  const getCampaignStatsByStatus = () => {
    if (!campaigns) return [];
    
    const stats = [
      { name: t('marketing.status.active'), value: 0, color: '#4caf50' },
      { name: t('marketing.status.planned'), value: 0, color: '#2196f3' },
      { name: t('marketing.status.completed'), value: 0, color: '#9e9e9e' },
      { name: t('marketing.status.cancelled'), value: 0, color: '#f44336' }
    ];
    
    campaigns.forEach(campaign => {
      const statusIndex = stats.findIndex(s => s.name === t(`marketing.status.${campaign.status}`));
      if (statusIndex !== -1) {
        stats[statusIndex].value += 1;
      }
    });
    
    return stats.filter(s => s.value > 0);
  };
  
  // Obtenir les statistiques de campagnes par type
  const getCampaignStatsByType = () => {
    if (!campaigns) return [];
    
    const stats = {};
    
    campaigns.forEach(campaign => {
      const typeName = t(`marketing.type.${campaign.type}`);
      if (!stats[typeName]) {
        stats[typeName] = {
          impressions: 0,
          clicks: 0,
          conversions: 0,
          budget: 0,
          spent: 0
        };
      }
      
      stats[typeName].impressions += campaign.metrics?.impressions || 0;
      stats[typeName].clicks += campaign.metrics?.clicks || 0;
      stats[typeName].conversions += campaign.metrics?.conversions || 0;
      stats[typeName].budget += campaign.budget || 0;
      stats[typeName].spent += campaign.spent || 0;
    });
    
    return Object.entries(stats).map(([type, metrics]) => ({
      type,
      ...metrics,
      ctr: metrics.impressions > 0 ? (metrics.clicks / metrics.impressions) * 100 : 0,
      cvr: metrics.clicks > 0 ? (metrics.conversions / metrics.clicks) * 100 : 0
    }));
  };
  
  // Filtrer les campagnes selon l'onglet actif
  const getFilteredCampaigns = () => {
    if (!campaigns) return [];
    
    switch (tabValue) {
      case 1: // Actives
        return campaigns.filter(campaign => campaign.status === 'active');
      case 2: // Planifiées
        return campaigns.filter(campaign => campaign.status === 'planned');
      case 3: // Terminées
        return campaigns.filter(campaign => campaign.status === 'completed');
      default: // Toutes
        return campaigns;
    }
  };
  
  // Constantes pour les graphiques
  const campaignStatsByStatus = getCampaignStatsByStatus();
  const campaignStatsByType = getCampaignStatsByType();
  const filteredCampaigns = getFilteredCampaigns();
  
  // Rafraîchir les données
  const handleRefresh = () => {
    dispatch(fetchMarketingCampaigns());
  };
  
  return (
    <Card elevation={2}>
      <CardHeader
        title={t('marketing.campaigns')}
        subheader={lastUpdated ? t('marketing.lastUpdate', { time: new Date(lastUpdated).toLocaleString() }) : ''}
        action={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              size="small"
              onClick={() => handleOpenDialog()}
              sx={{ mr: 1 }}
            >
              {t('marketing.newCampaign')}
            </Button>
            <Tooltip title={t('common.refresh')}>
              <IconButton onClick={handleRefresh} disabled={loading}>
                {loading ? <CircularProgress size={24} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      
      <Tabs
        value={tabValue}
        onChange={handleTabChange}
        variant="fullWidth"
        indicatorColor="primary"
        textColor="primary"
        aria-label="campaign tabs"
      >
        <Tab label={t('marketing.allCampaigns')} />
        <Tab label={t('marketing.activeCampaigns')} />
        <Tab label={t('marketing.plannedCampaigns')} />
        <Tab label={t('marketing.completedCampaigns')} />
      </Tabs>
      
      <Divider />
      
      <CardContent>
        {error && (
          <Box sx={{ mb: 3 }}>
            <Typography color="error" variant="body2">
              {t('marketing.error')}: {error}
            </Typography>
          </Box>
        )}
        
        {/* Afficher le tableau de bord des statistiques dans l'onglet "Toutes" */}
        {tabValue === 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              {t('marketing.overview')}
            </Typography>
            
            <Grid container spacing={3}>
              {/* Graphiques et statistiques */}
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {t('marketing.campaignsByStatus')}
                  </Typography>
                  <Box sx={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={campaignStatsByStatus}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          fill="#8884d8"
                          label
                        >
                          {campaignStatsByStatus.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <RechartsTooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={8}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {t('marketing.performanceByType')}
                  </Typography>
                  <Box sx={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={campaignStatsByType}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="type" />
                        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                        <RechartsTooltip />
                        <Legend />
                        <Bar yAxisId="left" dataKey="impressions" name={t('marketing.impressions')} fill="#8884d8" />
                        <Bar yAxisId="left" dataKey="clicks" name={t('marketing.clicks')} fill="#82ca9d" />
                        <Bar yAxisId="right" dataKey="conversions" name={t('marketing.conversions')} fill="#ffc658" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </Paper>
              </Grid>
              
              <Grid item xs={12}>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('marketing.type')}</TableCell>
                        <TableCell align="right">{t('marketing.budget')}</TableCell>
                        <TableCell align="right">{t('marketing.spent')}</TableCell>
                        <TableCell align="right">{t('marketing.ctr')}</TableCell>
                        <TableCell align="right">{t('marketing.cvr')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {campaignStatsByType.map((type, index) => (
                        <TableRow key={index}>
                          <TableCell component="th" scope="row">
                            {type.type}
                          </TableCell>
                          <TableCell align="right">
                            {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(type.budget)}
                          </TableCell>
                          <TableCell align="right">
                            {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(type.spent)}
                          </TableCell>
                          <TableCell align="right">
                            {type.ctr.toFixed(2)}%
                          </TableCell>
                          <TableCell align="right">
                            {type.cvr.toFixed(2)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </Box>
        )}
        
        {/* Liste des campagnes */}
        <Box>
          {filteredCampaigns.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                {t('marketing.noCampaigns')}
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
                sx={{ mt: 2 }}
              >
                {t('marketing.createFirst')}
              </Button>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {filteredCampaigns.map((campaign) => (
                <Grid item key={campaign.id} xs={12} sm={6} lg={4}>
                  <CampaignCard
                    campaign={campaign}
                    onEdit={handleOpenDialog}
                    onDelete={handleDeleteCampaign}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      </CardContent>
      
      {/* Dialogue de création/édition de campagne */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedCampaign ? t('marketing.editCampaign') : t('marketing.newCampaign')}
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('marketing.campaignName')}
                name="name"
                value={formData.name}
                onChange={handleFormChange}
                required
                error={!!formErrors.name}
                helperText={formErrors.name}
                sx={{ mb: 3 }}
              />
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel id="campaign-type-label">{t('marketing.campaignType')}</InputLabel>
                <Select
                  labelId="campaign-type-label"
                  name="type"
                  value={formData.type}
                  onChange={handleFormChange}
                  label={t('marketing.campaignType')}
                >
                  <MenuItem value="email">{t('marketing.type.email')}</MenuItem>
                  <MenuItem value="facebook">{t('marketing.type.facebook')}</MenuItem>
                  <MenuItem value="instagram">{t('marketing.type.instagram')}</MenuItem>
                  <MenuItem value="sms">{t('marketing.type.sms')}</MenuItem>
                  <MenuItem value="promotion">{t('marketing.type.promotion')}</MenuItem>
                  <MenuItem value="other">{t('marketing.type.other')}</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label={t('marketing.campaignDescription')}
                name="description"
                value={formData.description}
                onChange={handleFormChange}
                multiline
                rows={4}
                sx={{ mb: 3 }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('marketing.startDate')}
                name="startDate"
                type="date"
                value={formData.startDate}
                onChange={handleFormChange}
                required
                error={!!formErrors.startDate}
                helperText={formErrors.startDate}
                InputLabelProps={{ shrink: true }}
                sx={{ mb: 3 }}
              />
              
              <TextField
                fullWidth
                label={t('marketing.endDate')}
                name="endDate"
                type="date"
                value={formData.endDate}
                onChange={handleFormChange}
                required
                error={!!formErrors.endDate}
                helperText={formErrors.endDate}
                InputLabelProps={{ shrink: true }}
                sx={{ mb: 3 }}
              />
              
              <TextField
                fullWidth
                label={t('marketing.budget')}
                name="budget"
                type="number"
                value={formData.budget}
                onChange={handleFormChange}
                required
                error={!!formErrors.budget}
                helperText={formErrors.budget}
                InputProps={{
                  startAdornment: <InputAdornment position="start">€</InputAdornment>,
                }}
                sx={{ mb: 3 }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                {t('marketing.campaignContent')}
              </Typography>
              
              <TextField
                fullWidth
                label={t('marketing.contentTitle')}
                name="content.title"
                value={formData.content.title}
                onChange={handleFormChange}
                sx={{ mb: 3 }}
              />
              
              <TextField
                fullWidth
                label={t('marketing.contentDescription')}
                name="content.description"
                value={formData.content.description}
                onChange={handleFormChange}
                multiline
                rows={4}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>
            {t('common.cancel')}
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            color="primary"
          >
            {selectedCampaign ? t('common.save') : t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default MarketingCampaigns;
