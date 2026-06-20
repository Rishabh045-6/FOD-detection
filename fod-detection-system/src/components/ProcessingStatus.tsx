import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Stack,
  Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HourglassBottomIcon from '@mui/icons-material/HourglassBottom';
import type { ProcessingState } from '../types/detection';

interface ProcessingStatusProps {
  state: ProcessingState;
}

const statusSteps = [
  { key: 'uploading', label: 'Uploading Video' },
  { key: 'extracting', label: 'Extracting Frames' },
  { key: 'detecting', label: 'Running Detection' },
  { key: 'calculating', label: 'Calculating Distance' },
  { key: 'generating', label: 'Generating Results' },
  { key: 'complete', label: 'Complete' },
];

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ state }) => {
  const currentStepIndex = statusSteps.findIndex(
    (s) => s.key === state.status
  );

  const progressPercentage =
    state.status === 'idle'
      ? 0
      : state.status === 'complete'
        ? 100
        : state.status === 'error'
          ? 0
          : ((currentStepIndex + 1) / statusSteps.length) * 100;

  return (
    <Card
      sx={{
        backgroundColor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Processing Status
        </Typography>

        <Stack spacing={3}>
          {/* Overall progress */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                mb: 1,
              }}
            >
              <Typography variant="body2" color="textSecondary">
                Overall Progress
              </Typography>
              <Typography variant="body2" color="primary">
                {Math.round(progressPercentage)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressPercentage}
              sx={{
                height: 8,
                borderRadius: 4,
              }}
            />
          </Box>

          {/* Status message */}
          <Box>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Current Step
            </Typography>
            <Chip
              label={state.message || 'Preparing...'}
              color={
                state.status === 'error'
                  ? 'error'
                  : state.status === 'complete'
                    ? 'success'
                    : 'primary'
              }
              variant="filled"
              icon={
                state.status === 'error' ? undefined : state.status === 'complete' ? (
                  <CheckCircleIcon />
                ) : (
                  <HourglassBottomIcon />
                )
              }
            />
          </Box>

          {/* Steps */}
          <Box>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Processing Steps
            </Typography>
            <Stack spacing={1}>
              {statusSteps.map((step, index) => (
                <Box
                  key={step.key}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    p: 1.5,
                    borderRadius: 1,
                    backgroundColor:
                      index < currentStepIndex
                        ? 'rgba(76, 175, 80, 0.1)'
                        : index === currentStepIndex && state.status !== 'idle'
                          ? 'rgba(0, 188, 212, 0.1)'
                          : 'transparent',
                    border:
                      index === currentStepIndex && state.status !== 'idle'
                        ? '1px solid'
                        : '1px solid',
                    borderColor:
                      index < currentStepIndex
                        ? 'success.main'
                        : index === currentStepIndex && state.status !== 'idle'
                          ? 'primary.main'
                          : 'divider',
                  }}
                >
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor:
                        index < currentStepIndex
                          ? 'success.main'
                          : index === currentStepIndex && state.status !== 'idle'
                            ? 'primary.main'
                            : 'rgba(255, 255, 255, 0.1)',
                      color:
                        index < currentStepIndex || (index === currentStepIndex && state.status !== 'idle')
                          ? '#fff'
                          : 'textSecondary',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                    }}
                  >
                    {index < currentStepIndex ? '✓' : index + 1}
                  </Box>
                  <Typography
                    variant="body2"
                    sx={{
                      color:
                        index <= currentStepIndex
                          ? 'text.primary'
                          : 'text.secondary',
                    }}
                  >
                    {step.label}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>

          {/* Error message */}
          {state.error && (
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                border: '1px solid',
                borderColor: 'error.main',
              }}
            >
              <Typography variant="body2" color="error">
                {state.error}
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};
