import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Container,
  Box,
  Stack,
  Button,
  Paper,
  Typography,
  Divider,
} from '@mui/material';
import { toast } from 'react-toastify';
import {
  VideoPlayer,
  DetectionSummary,
  FODTable,
  AlertBanner,
} from '../components';
import type { DetectionResponse } from '../types/detection';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

interface LocationState {
  data: DetectionResponse;
}

export const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const data = (location.state as LocationState)?.data;

  React.useEffect(() => {
    if (!data) {
      navigate('/');
      return;
    }
  }, [data, navigate]);

  if (!data) {
    return null;
  }

  const handleDownloadResults = () => {
    try {
      const resultsData = {
        timestamp: new Date().toISOString(),
        summary: {
          totalFrames: data.total_frames,
          totalFODDetected: data.detections.length,
          fodDetected: data.fod_detected,
          processingTime: data.processing_time,
        },
        detections: data.detections,
        processedVideoUrl: data.processed_video_url,
      };

      const element = document.createElement('a');
      element.setAttribute(
        'href',
        'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(resultsData, null, 2))
      );
      element.setAttribute('download', `fod-detection-results-${Date.now()}.json`);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);

      toast.success('Results downloaded successfully!');
    } catch (err) {
      console.error('Download results failed:', err);
      toast.error('Failed to download results');
    }
  };

  const handleAnalyzeAnotherVideo = () => {
    navigate('/');
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
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 2,
            }}
          >
            <Box>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 'bold',
                  background: 'linear-gradient(135deg, #00bcd4 0%, #4dd0e1 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Detection Results
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Analysis completed at {new Date().toLocaleString()}
              </Typography>
            </Box>

            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                startIcon={<ArrowBackIcon />}
                onClick={handleAnalyzeAnotherVideo}
              >
                Analyze Another Video
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<FileDownloadIcon />}
                onClick={handleDownloadResults}
              >
                Download Results
              </Button>
            </Stack>
          </Box>

          {/* Alert Banner */}
          <AlertBanner
            fodDetected={data.fod_detected}
            detections={data.detections}
          />

          {/* Video Section */}
          <Box>
            <VideoPlayer videoUrl={data.processed_video_url} />
          </Box>

          <Divider sx={{ borderColor: 'divider' }} />

          {/* Summary Cards */}
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              📊 Summary
            </Typography>
            <DetectionSummary
              totalFrames={data.total_frames}
              totalFODDetected={data.detections.length}
              fodDetected={data.fod_detected}
              processingTime={data.processing_time}
            />
          </Box>

          <Divider sx={{ borderColor: 'divider' }} />

          {/* Detections Table */}
          <Box>
            {data.detections.length > 0 ? (
              <FODTable detections={data.detections} />
            ) : (
              <Paper
                sx={{
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'background.paper',
                  border: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Typography color="textSecondary">
                  No FOD detections to display
                </Typography>
              </Paper>
            )}
          </Box>

          {/* Info Section */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
            <Paper
              sx={{
                p: 3,
                background: 'rgba(76, 175, 80, 0.1)',
                border: '1px solid',
                borderColor: 'success.main',
                borderRadius: 2,
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                ✅ Analysis Complete
              </Typography>
              <Typography variant="body2" color="textSecondary">
                All frames have been processed. Review the results above and take appropriate action if any FOD is
                detected.
              </Typography>
            </Paper>
            <Paper
              sx={{
                p: 3,
                background: 'rgba(0, 188, 212, 0.1)',
                border: '1px solid',
                borderColor: 'primary.main',
                borderRadius: 2,
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                📥 Export Data
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Download the full detection results in JSON format for further analysis or archival purposes.
              </Typography>
            </Paper>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
};
