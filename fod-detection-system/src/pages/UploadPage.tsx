import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Stack,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import { VideoUploader } from '../components';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import LiveTvIcon from '@mui/icons-material/LiveTv';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

export const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0); // 0 = File Upload, 1 = Live Camera
  const navigate = useNavigate();

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handlePreviewReady = (url: string) => {
    setPreviewUrl(url);
  };

  const handleRunDetection = () => {
    if (selectedFile) {
      navigate('/processing', { state: { file: selectedFile, previewUrl } });
    }
  };

  const handleLaunchLiveStream = () => {
    navigate('/live');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0e27 0%, #131a2e 100%)',
        pt: 4,
        pb: 4,
      }}
    >
      <Container maxWidth="lg">
        <Stack spacing={4}>
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 'bold',
                background: 'linear-gradient(135deg, #00bcd4 0%, #4dd0e1 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
              }}
            >
              ✈️ IAF FOD Detection System
            </Typography>
            <Typography variant="h6" color="textSecondary">
              Advanced runway foreign object debris detection using AI
            </Typography>
          </Box>

          {/* Operational Mode Selection Bar */}
          <Paper 
            elevation={4} 
            sx={{ 
              background: 'rgba(19, 26, 46, 0.8)', 
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: 2
            }}
          >
            <Tabs
              value={activeTab}
              onChange={(_, newValue) => setActiveTab(newValue)}
              variant="fullWidth"
              indicatorColor="primary"
              textColor="primary"
              sx={{
                '& .MuiTab-root': { py: 2, fontSize: '1rem', fontWeight: 'bold' }
              }}
            >
              <Tab icon={<CloudUploadIcon />} iconPosition="start" label="Upload Batch Video" />
              <Tab icon={<LiveTvIcon />} iconPosition="start" label="Live Camera Stream" />
            </Tabs>
          </Paper>

          {/* Mode Viewport Switcher */}
          {activeTab === 0 ? (
            /* MODE 0: Video Upload Pipeline */
            <Stack spacing={4}>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <Paper
                  sx={{
                    p: 2.5,
                    flex: 1,
                    background: 'rgba(0, 188, 212, 0.1)',
                    border: '1px solid',
                    borderColor: 'primary.main',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    📹 Supported Formats
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    MP4, AVI, MOV (Max 1GB)
                  </Typography>
                </Paper>
                <Paper
                  sx={{
                    p: 2.5,
                    flex: 1,
                    background: 'rgba(76, 175, 80, 0.1)',
                    border: '1px solid',
                    borderColor: 'success.main',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    ⚡ Batch Processing
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Automated frame analysis and artifact extraction tracking
                  </Typography>
                </Paper>
                <Paper
                  sx={{
                    p: 2.5,
                    flex: 1,
                    background: 'rgba(255, 152, 0, 0.1)',
                    border: '1px solid',
                    borderColor: 'warning.main',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    📊 Detailed Reports
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Coordinates, confidence scores, and distances
                  </Typography>
                </Paper>
              </Stack>

              <Box>
                <VideoUploader
                  onFileSelect={handleFileSelect}
                  onPreviewReady={handlePreviewReady}
                />
              </Box>

              {selectedFile && (
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    endIcon={<ArrowForwardIcon />}
                    onClick={handleRunDetection}
                    sx={{
                      px: 6,
                      py: 1.5,
                      fontSize: '1.1rem',
                      fontWeight: 'bold',
                    }}
                  >
                    Run Video Analysis
                  </Button>
                </Box>
              )}
            </Stack>
          ) : (
            /* MODE 1: Live Hardware Camera Scanning Context */
            <Stack spacing={4}>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <Paper
                  sx={{
                    p: 2.5,
                    flex: 1,
                    background: 'rgba(156, 39, 176, 0.1)',
                    border: '1px solid',
                    borderColor: 'purple.main',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    🔌 Multi-Hardware Support
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Webcams, USB Devices, RTSP Network links, and PiCams
                  </Typography>
                </Paper>
                <Paper
                  sx={{
                    p: 2.5,
                    flex: 1,
                    background: 'rgba(244, 67, 54, 0.1)',
                    border: '1px solid',
                    borderColor: 'error.main',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    🚨 Millisecond Latency
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Real-time safety alerting via dynamic WebSocket pipelines
                  </Typography>
                </Paper>
              </Stack>

              <Paper
                elevation={2}
                sx={{
                  p: 6,
                  textAlign: 'center',
                  background: 'rgba(19, 26, 46, 0.6)',
                  border: '2px dashed rgba(0, 188, 212, 0.3)',
                  borderRadius: 3,
                }}
              >
                <LiveTvIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Direct Operational Scanners
                </Typography>
                <Typography variant="body1" color="textSecondary" sx={{ mb: 4, maxWidth: '600px', mx: 'auto' }}>
                  Connect directly to local webcams or active airfield RTSP network nodes. 
                  The engine will track ground objects dynamically without disk storage requirements.
                </Typography>
                <Button
                  variant="contained"
                  color="secondary"
                  size="large"
                  startIcon={<LiveTvIcon />}
                  onClick={handleLaunchLiveStream}
                  sx={{
                    px: 6,
                    py: 1.8,
                    fontSize: '1.1rem',
                    fontWeight: 'bold',
                    boxShadow: '0 0 15px rgba(233, 30, 99, 0.3)'
                  }}
                >
                  Launch Live Control Panel
                </Button>
              </Paper>
            </Stack>
          )}

          {/* Footer Warning Info Box */}
          <Paper
            sx={{
              p: 3,
              background: 'rgba(255, 152, 0, 0.05)',
              border: '1px solid',
              borderColor: 'warning.main',
              borderRadius: 2,
            }}
          >
            <Typography variant="body2" color="textSecondary">
              <strong>Important Notification:</strong> Ensure the inspection parameters are calibrated prior to active operations. 
              Live telemetry tracking metrics depend directly on the spatial mounting context configuration matrices.
            </Typography>
          </Paper>
        </Stack>
      </Container>
    </Box>
  );
};