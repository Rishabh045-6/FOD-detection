import React from 'react';
import type { ChipProps } from '@mui/material';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import TimerIcon from '@mui/icons-material/Timer';
import CropOriginalIcon from '@mui/icons-material/CropOriginal';

interface DetectionSummaryProps {
  totalFrames: number;
  totalFODDetected: number;
  fodDetected: boolean;
  processingTime: number;
}

export const DetectionSummary: React.FC<DetectionSummaryProps> = ({
  totalFrames,
  totalFODDetected,
  fodDetected,
  processingTime,
}) => {
  type SummaryCardColor = ChipProps['color'];

  const summaryCards: Array<{
    title: string;
    value: string;
    icon: typeof CropOriginalIcon;
    color: SummaryCardColor;
  }> = [
    {
      title: 'Total Frames Processed',
      value: totalFrames.toLocaleString(),
      icon: CropOriginalIcon,
      color: 'info',
    },
    {
      title: 'Total FOD Detected',
      value: totalFODDetected.toString(),
      icon: ErrorIcon,
      color: fodDetected ? 'error' : 'success',
    },
    {
      title: 'Detection Status',
      value: fodDetected ? 'FOD Detected' : 'No FOD',
      icon: fodDetected ? ErrorIcon : CheckCircleIcon,
      color: fodDetected ? 'error' : 'success',
    },
    {
      title: 'Processing Time',
      value: `${processingTime.toFixed(1)}s`,
      icon: TimerIcon,
      color: 'warning',
    },
  ];
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 2 }}>
      {summaryCards.map((card, index) => {
        const Icon = card.icon;
        return (
          <Card
            key={index}
            sx={{
              backgroundColor: 'background.paper',
              border: '1px solid',
              borderColor: 'divider',
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
              },
            }}
          >
            <CardContent>
              <Stack spacing={1.5} sx={{ height: '100%' }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                  }}
                >
                  <Icon
                    sx={{
                      color: `${card.color}.main`,
                      fontSize: 24,
                    }}
                  />
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ flexGrow: 1 }}
                  >
                    {card.title}
                  </Typography>
                </Box>

                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 'bold',
                    color: `${card.color}.main`,
                  }}
                >
                  {card.value}
                </Typography>

                <Chip
                  label={card.color === 'error' ? 'Critical' : 'Normal'}
                  color={card.color}
                  size="small"
                  variant="outlined"
                  sx={{ alignSelf: 'flex-start', mt: 'auto' }}
                />
              </Stack>
            </CardContent>
          </Card>
        );
      })}
    </Box>
  );
};
