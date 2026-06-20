import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Container, Box, Stack, Alert, Typography } from '@mui/material';
import { toast } from 'react-toastify';
import { ProcessingStatus } from '../components';
import { uploadVideoForDetection } from '../services/api';
import type { UploadProgress } from '../services/api';
import type { ProcessingState } from '../types/detection';

interface LocationState {
  file: File;
  previewUrl: string;
}

export const ProcessingPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [processingState, setProcessingState] = useState<ProcessingState>({
    status: 'uploading',
    progress: 0,
    message: 'Preparing to upload video...',
  });

  const file = (location.state as LocationState)?.file;

  useEffect(() => {
    if (!file) {
      navigate('/');
      return;
    }

    const processVideo = async () => {
      try {
        setProcessingState({
          status: 'uploading',
          progress: 0,
          message: 'Uploading Video',
        });

        const response = await uploadVideoForDetection(
          file,
          (progress: UploadProgress) => {
            const progressPercent = progress.percent;
            setProcessingState((prev) => ({
              ...prev,
              progress: progressPercent,
              message: `Uploading Video - ${progressPercent}%`,
            }));
          }
        );

        // Simulate processing steps for better UX
        const steps: Array<{ status: ProcessingState['status']; message: string }> = [
          { status: 'extracting', message: 'Extracting Frames' },
          { status: 'detecting', message: 'Running Detection' },
          { status: 'calculating', message: 'Calculating Distance' },
          { status: 'generating', message: 'Generating Results' },
        ];

        for (const step of steps) {
          await new Promise((resolve) => {
            setTimeout(() => {
              setProcessingState({
                status: step.status,
                progress: Math.min(
                  100,
                  20 + (steps.indexOf(step) + 1) * (70 / steps.length)
                ),
                message: step.message,
              });
              resolve(null);
            }, 1500);
          });
        }

        setProcessingState({
          status: 'complete',
          progress: 100,
          message: 'Processing Complete',
        });

        toast.success('Video processing completed successfully!');

        // Navigate to results after a short delay
        setTimeout(() => {
          navigate('/results', { state: { data: response } });
        }, 1000);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        setProcessingState({
          status: 'error',
          progress: 0,
          message: 'Processing Failed',
          error: errorMessage,
        });

        toast.error(`Error: ${errorMessage}`);

        // Navigate back to upload after delay
        setTimeout(() => {
          navigate('/');
        }, 3000);
      }
    };

    processVideo();
  }, [file, navigate]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0e27 0%, #131a2e 100%)',
        pt: 4,
        pb: 4,
      }}
    >
      <Container maxWidth="md">
        <Stack spacing={4}>
          {/* Header */}
          <Box sx={{ textAlign: 'center' }}>
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
              Processing Your Video
            </Typography>
          </Box>

          {/* File Info */}
          {file && (
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              <Typography variant="body2">
                <strong>File:</strong> {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </Typography>
            </Alert>
          )}

          {/* Processing Status */}
          <ProcessingStatus state={processingState} />

          {/* Disclaimer */}
          <Alert severity="warning" sx={{ borderRadius: 2 }}>
            <Typography variant="body2">
              Please do not refresh or navigate away from this page during processing. The system will automatically
              proceed to results once complete.
            </Typography>
          </Alert>
        </Stack>
      </Container>
    </Box>
  );
};
