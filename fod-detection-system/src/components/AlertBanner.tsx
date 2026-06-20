import React from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Typography,
  Stack,
  Chip,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { DetectionResult } from '../types/detection';

interface AlertBannerProps {
  fodDetected: boolean;
  detections: DetectionResult[];
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  fodDetected,
  detections,
}) => {
  if (!fodDetected) {
    return (
      <Alert
        severity="success"
        sx={{
          borderRadius: 2,
          fontSize: '1.1rem',
          py: 2,
          px: 3,
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          border: '2px solid',
          borderColor: 'success.main',
        }}
        icon={<CheckCircleIcon sx={{ fontSize: 28 }} />}
      >
        <AlertTitle sx={{ fontSize: '1.2rem', fontWeight: 'bold', mb: 1 }}>
          RUNWAY CLEAR - NO FOD DETECTED
        </AlertTitle>
        <Typography variant="body2" color="inherit">
          All {detections.length} frames analyzed. No foreign object debris detected in runway area.
        </Typography>
      </Alert>
    );
  }

  const closestDetection = detections.reduce((prev, current) =>
    prev.distance_m < current.distance_m ? prev : current
  );

  return (
    <Alert
      severity="error"
      sx={{
        borderRadius: 2,
        fontSize: '1.1rem',
        py: 2,
        px: 3,
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        border: '2px solid',
        borderColor: 'error.main',
      }}
      icon={<WarningIcon sx={{ fontSize: 28 }} />}
    >
      <AlertTitle sx={{ fontSize: '1.2rem', fontWeight: 'bold', mb: 2 }}>
        ⚠️ WARNING: FOREIGN OBJECT DEBRIS DETECTED
      </AlertTitle>
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Chip
            label={`${detections.length} Object${detections.length > 1 ? 's' : ''} Detected`}
            color="error"
            variant="filled"
            size="small"
          />
          <Chip
            label={`Closest: ${closestDetection.distance_m.toFixed(1)}m away`}
            color="error"
            variant="outlined"
            size="small"
          />
        </Box>
        <Typography variant="body2" color="inherit">
          Closest detected object: <strong>{closestDetection.id}</strong> at frame{' '}
          <strong>{closestDetection.frame}</strong> ({closestDetection.timestamp}) with{' '}
          <strong>{(closestDetection.confidence * 100).toFixed(1)}%</strong> confidence.
        </Typography>
        <Typography variant="body2" color="inherit" sx={{ fontStyle: 'italic' }}>
          Immediate action required. Coordinate with airport operations to clear the runway.
        </Typography>
      </Stack>
    </Alert>
  );
};
