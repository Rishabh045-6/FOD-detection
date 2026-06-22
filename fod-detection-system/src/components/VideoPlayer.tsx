import React, { useRef, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Button,
  Slider,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import VolumeOffIcon from '@mui/icons-material/VolumeOff';

interface VideoPlayerProps {
  videoUrl: string;
  title?: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  title = 'Processed Video',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);

  const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const fullVideoUrl = videoUrl.startsWith('http')
    ? videoUrl
    : `${API_BASE_URL}${videoUrl}`;

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play()
          .catch(err => console.error("Playback failed:", err));
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleProgressChange = (value: number | number[]) => {
    if (videoRef.current) {
      const newTime = value as number;
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleVolumeChange = (value: number | number[]) => {
    const newVolume = value as number;
    setVolume(newVolume);
    
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      if (newVolume > 0 && isMuted) {
        videoRef.current.muted = false;
        setIsMuted(false);
      }
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const nextMuteState = !isMuted;
      videoRef.current.muted = nextMuteState;
      setIsMuted(nextMuteState);
    }
  };

  const formatTime = (seconds: number): string => {
    if (!seconds || isNaN(seconds)) return '00:00:00';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(
      2,
      '0'
    )}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <Card
      sx={{
        backgroundColor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <CardContent sx={{ p: 0 }}>
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6">{title}</Typography>
        </Box>

        <Box
          sx={{
            position: 'relative',
            width: '100%',
            backgroundColor: '#000',
            aspectRatio: '16 / 9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer' // UI cue indicating the frame can be clicked to play/pause
          }}
          onClick={handlePlayPause}
        >
          <video
            ref={videoRef}
            src={fullVideoUrl}
            // Removed native "controls" to let custom UI handle it exclusively
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={() => setIsPlaying(true)}   // Safely tracks native/external trigger starts
            onPause={() => setIsPlaying(false)} // Safely tracks native/external trigger stops
            onEnded={() => setIsPlaying(false)}
            onError={(e) => {
              console.error('VIDEO ERROR:', e);
              console.log('Attempted URL:', fullVideoUrl);
            }}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
            }}
          />
        </Box>

        <Box sx={{ p: 2, backgroundColor: '#0a0e27' }}>
          <Stack spacing={2}>
            <Box>
              <Slider
                value={currentTime}
                onChange={(_, value) => handleProgressChange(value)}
                max={duration || 100}
                step={0.1}
                sx={{
                  '& .MuiSlider-thumb': {
                    backgroundColor: 'primary.main',
                  },
                  '& .MuiSlider-track': {
                    backgroundColor: 'primary.main',
                  },
                }}
              />

              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  mt: 1,
                }}
              >
                <Typography variant="caption" color="textSecondary">
                  {formatTime(currentTime)}
                </Typography>

                <Typography variant="caption" color="textSecondary">
                  {formatTime(duration)}
                </Typography>
              </Box>
            </Box>

            <Stack spacing={2}>
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: 'center' }}
              >
                <Button
                  size="small"
                  variant="contained"
                  color="primary"
                  startIcon={isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
                  onClick={(e) => {
                    e.stopPropagation(); // Prevents double toggling from bubbling up to Box wrapper
                    handlePlayPause();
                  }}
                >
                  {isPlaying ? 'Pause' : 'Play'}
                </Button>

                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    ml: 'auto',
                  }}
                  onClick={(e) => e.stopPropagation()} // Prevents volume changes from triggering pause/play
                >
                  <Button
                    size="small"
                    onClick={toggleMute}
                    sx={{
                      minWidth: 'auto',
                      p: 0.5,
                    }}
                  >
                    {isMuted || volume === 0 ? <VolumeOffIcon /> : <VolumeUpIcon />}
                  </Button>

                  <Slider
                    value={isMuted ? 0 : volume}
                    onChange={(_, value) => handleVolumeChange(value)}
                    min={0}
                    max={1}
                    step={0.05}
                    sx={{ width: 100 }}
                  />
                </Box>
              </Stack>
            </Stack>
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};