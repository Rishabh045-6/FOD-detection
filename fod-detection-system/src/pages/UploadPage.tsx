import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Stack,
  Paper,
} from '@mui/material';
import { VideoUploader } from '../components';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

export const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
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
          <Box sx={{ textAlign: 'center', mb: 4 }}>
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

          {/* Info Cards */}
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
                ⚡ Real-time Analysis
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Fast frame extraction and object detection
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
                📊 Detailed Results
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Coordinates, confidence scores, and distances
              </Typography>
            </Paper>
          </Stack>

          {/* Upload Section */}
          <Box>
            <VideoUploader
              onFileSelect={handleFileSelect}
              onPreviewReady={handlePreviewReady}
            />
          </Box>

          {/* Action Button */}
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
                Run Detection
              </Button>
            </Box>
          )}

          {/* Footer Info */}
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
              <strong>Important:</strong> Please ensure the video is clear and shows the runway area. The system will
              analyze every frame to detect foreign object debris. Processing time depends on video duration and server
              capacity.
            </Typography>
          </Paper>
        </Stack>
      </Container>
    </Box>
  );
};
