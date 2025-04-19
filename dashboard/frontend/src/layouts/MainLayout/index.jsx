import React, { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { 
  Box, 
  CssBaseline, 
  Drawer, 
  AppBar, 
  Toolbar, 
  List, 
  Typography, 
  Divider, 
  IconButton, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
  Badge
} from '@mui/material';
import { 
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  ShowChart as ShowChartIcon,
  Inventory as InventoryIcon,
  Campaign as CampaignIcon,
  AccountBalance as AccountBalanceIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Import des actions
import { logout } from '../../store/slices/authSlice';

// Largeur du drawer
const drawerWidth = 240;

// Composants stylisés
const StyledAppBar = styled(AppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  zIndex: theme.zIndex.drawer + 1,
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(['width', 'margin'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const StyledDrawer = styled(Drawer, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  '& .MuiDrawer-paper': {
    position: 'relative',
    whiteSpace: 'nowrap',
    width: drawerWidth,
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
    boxSizing: 'border-box',
    ...(!open && {
      overflowX: 'hidden',
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
      }),
      width: theme.spacing(7),
      [theme.breakpoints.up('sm')]: {
        width: theme.spacing(9),
      },
    }),
  },
}));

const MainLayout = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);
  
  const [open, setOpen] = useState(true);
  const [userMenu, setUserMenu] = useState(null);
  const [notificationsMenu, setNotificationsMenu] = useState(null);
  
  // Liste des notifications (simulées pour l'exemple)
  const notifications = [
    { id: 1, text: 'Niveau de stock critique pour Mozzarella', read: false },
    { id: 2, text: 'Nouvelle réservation pour ce soir', read: false },
    { id: 3, text: 'Rapport financier mensuel disponible', read: true },
  ];
  
  // Nombre de notifications non lues
  const unreadCount = notifications.filter(notif => !notif.read).length;
  
  // Navigation principale
  const mainNavigation = [
    { path: '/', label: t('navigation.dashboard'), icon: <DashboardIcon /> },
    { path: '/sales', label: t('navigation.sales'), icon: <ShowChartIcon /> },
    { path: '/stock', label: t('navigation.stock'), icon: <InventoryIcon /> },
    { path: '/marketing', label: t('navigation.marketing'), icon: <CampaignIcon /> },
    { path: '/finance', label: t('navigation.finance'), icon: <AccountBalanceIcon /> },
    { path: '/staff', label: t('navigation.staff'), icon: <PeopleIcon /> },
  ];
  
  // Navigation secondaire
  const secondaryNavigation = [
    { path: '/settings', label: t('navigation.settings'), icon: <SettingsIcon /> },
  ];
  
  const toggleDrawer = () => {
    setOpen(!open);
  };
  
  const handleUserMenuOpen = (event) => {
    setUserMenu(event.currentTarget);
  };
  
  const handleUserMenuClose = () => {
    setUserMenu(null);
  };
  
  const handleNotificationsOpen = (event) => {
    setNotificationsMenu(event.currentTarget);
  };
  
  const handleNotificationsClose = () => {
    setNotificationsMenu(null);
  };
  
  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
    handleUserMenuClose();
  };
  
  const handleNavigation = (path) => {
    navigate(path);
  };
  
  // Vérification de l'itinéraire actif
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };
  
  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* Barre d'application */}
      <StyledAppBar position="absolute" open={open}>
        <Toolbar
          sx={{
            pr: '24px',
          }}
        >
          <IconButton
            edge="start"
            color="inherit"
            aria-label="open drawer"
            onClick={toggleDrawer}
            sx={{
              marginRight: '36px',
              ...(open && { display: 'none' }),
            }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            component="h1"
            variant="h6"
            color="inherit"
            noWrap
            sx={{ flexGrow: 1 }}
          >
            {t('app.title')}
          </Typography>
          
          {/* Notifications */}
          <Tooltip title={t('common.notifications')}>
            <IconButton color="inherit" onClick={handleNotificationsOpen}>
              <Badge badgeContent={unreadCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={notificationsMenu}
            open={Boolean(notificationsMenu)}
            onClose={handleNotificationsClose}
            sx={{ mt: 2 }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            {notifications.map((notification) => (
              <MenuItem 
                key={notification.id}
                onClick={handleNotificationsClose}
                sx={{ 
                  backgroundColor: notification.read ? 'inherit' : 'action.hover',
                  fontWeight: notification.read ? 'normal' : 'bold',
                  minWidth: 240,
                }}
              >
                {notification.text}
              </MenuItem>
            ))}
          </Menu>
          
          {/* Menu utilisateur */}
          <Tooltip title={t('common.userMenu')}>
            <IconButton color="inherit" onClick={handleUserMenuOpen}>
              <Avatar
                alt={user?.name || 'User'}
                src="/static/images/avatar/1.jpg"
                sx={{ width: 32, height: 32 }}
              />
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={userMenu}
            open={Boolean(userMenu)}
            onClose={handleUserMenuClose}
            sx={{ mt: 2 }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleUserMenuClose}>
              <ListItemIcon>
                <PersonIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('user.profile')}</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('user.signOut')}</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </StyledAppBar>
      
      {/* Drawer de navigation */}
      <StyledDrawer variant="permanent" open={open}>
        <Toolbar
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            px: [1],
          }}
        >
          <IconButton onClick={toggleDrawer}>
            <ChevronLeftIcon />
          </IconButton>
        </Toolbar>
        <Divider />
        
        {/* Navigation principale */}
        <List component="nav">
          {mainNavigation.map((item) => (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={isActive(item.path)}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  minHeight: 48,
                  justifyContent: open ? 'initial' : 'center',
                  px: 2.5,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: open ? 3 : 'auto',
                    justifyContent: 'center',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.label} sx={{ opacity: open ? 1 : 0 }} />
              </ListItemButton>
            </ListItem>
          ))}
          
          <Divider sx={{ my: 1 }} />
          
          {/* Navigation secondaire */}
          {secondaryNavigation.map((item) => (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={isActive(item.path)}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  minHeight: 48,
                  justifyContent: open ? 'initial' : 'center',
                  px: 2.5,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: open ? 3 : 'auto',
                    justifyContent: 'center',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.label} sx={{ opacity: open ? 1 : 0 }} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </StyledDrawer>
      
      {/* Contenu principal */}
      <Box
        component="main"
        sx={{
          backgroundColor: (theme) => 
            theme.palette.mode === 'light'
              ? theme.palette.grey[100]
              : theme.palette.grey[900],
          flexGrow: 1,
          height: '100vh',
          overflow: 'auto',
          pt: 8, // Pour tenir compte de la barre d'application
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
