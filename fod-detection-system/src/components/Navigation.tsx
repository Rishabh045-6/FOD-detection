import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
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
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  CloudUpload as UploadIcon,
  LiveTv as LiveIcon,
} from '@mui/icons-material';

const DRAWER_WIDTH = 260;

interface NavigationProps {
  children: React.ReactNode;
}

export const Navigation: React.FC<NavigationProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  
  // Handles breakpoint adaptive scaling for tablets/phones
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const navItems = [
    { text: 'Upload Video', icon: <UploadIcon />, path: '/' },
    { text: 'Live Detection', icon: <LiveIcon />, path: '/live' },
  ];

  const drawerContent = (
    <Box sx={{ height: '100%', bgcolor: '#0d1224', color: 'white' }}>
      <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2 }}>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold', tracking: '0.5px' }}>
          🛡️ IAF FOD NAV
        </Typography>
      </Toolbar>
      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />
      <List sx={{ px: 1.5, py: 2 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => {
                  navigate(item.path);
                  if (isMobile) setMobileOpen(false);
                }}
                sx={{
                  borderRadius: 1.5,
                  py: 1.2,
                  px: 2,
                  bgcolor: isActive ? 'rgba(0, 188, 212, 0.12)' : 'transparent',
                  border: '1px solid',
                  borderColor: isActive ? 'rgba(0, 188, 212, 0.3)' : 'transparent',
                  color: isActive ? '#00bcd4' : 'grey.400',
                  '&:hover': {
                    bgcolor: isActive ? 'rgba(0, 188, 212, 0.18)' : 'rgba(255, 255, 255, 0.03)',
                    color: isActive ? '#00bcd4' : 'white',
                    '& .MuiListItemIcon-root': { color: isActive ? '#00bcd4' : 'white' }
                  },
                  transition: 'all 0.2s'
                }}
              >
                <ListItemIcon sx={{ color: isActive ? '#00bcd4' : 'grey.500', minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  sx={{
                    '.MuiTypography-root': {
                      fontSize: '0.95rem',
                      fontWeight: isActive ? 'bold' : '500',
                    },
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', background: 'linear-gradient(135deg, #0a0e27 0%, #131a2e 100%)' }}>
      {/* Top Header Appbar (Hidden on desktop sidebar layouts) */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          display: { md: 'none' },
          bgcolor: 'rgba(10, 14, 39, 0.85)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          boxShadow: 'none',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
            IAF FOD Detection System
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Responsive Navigation Side Drawer Layout containers */}
      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        {/* Mobile View Drawer Component */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }} // Optimizes mobile rendering performance
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, borderRight: 'none' },
          }}
        >
          {drawerContent}
        </Drawer>
        
        {/* Permanent Desktop View Sidebar Component */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: DRAWER_WIDTH, 
              borderRight: '1px solid rgba(255, 255, 255, 0.05)' 
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Main Content Render Viewport Frame */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: { xs: 7, md: 0 }, // Offsets main content top-padding for mobile appbars
        }}
      >
        {children}
      </Box>
    </Box>
  );
};