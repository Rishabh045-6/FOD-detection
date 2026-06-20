import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Chip,
  Alert,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface VideoUploaderProps {
  onFileSelect: (file: File) => void;
  onPreviewReady?: (url: string) => void;
  disabled?: boolean;
}

export const VideoUploader: React.FC<VideoUploaderProps> = ({
  onFileSelect,
  onPreviewReady,
  disabled = false,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ACCEPTED_FORMATS = ['video/mp4', 'video/x-msvideo', 'video/quicktime'];
  const MAX_FILE_SIZE = 1024 * 1024 * 1024; // 1GB

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_FORMATS.includes(file.type)) {
      return 'Unsupported file format. Accepted formats: MP4, AVI, MOV';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 1GB limit';
    }
    return null;
  };

  const handleFile = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setSelectedFile(file);
    onFileSelect(file);

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    if (onPreviewReady) {
      onPreviewReady(url);
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getVideoDuration = (file: File): Promise<number> => {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      video.onloadedmetadata = () => {
        resolve(video.duration);
      };
      video.onerror = reject;
      video.src = URL.createObjectURL(file);
    });
  };

  React.useEffect(() => {
    if (selectedFile) {
      getVideoDuration(selectedFile).catch(console.error);
    }
  }, [selectedFile]);

  return (
    <Stack spacing={3} sx={{ width: '100%' }}>
      <Paper
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          border: '2px dashed',
          borderColor: dragActive ? 'primary.main' : 'divider',
          backgroundColor: dragActive ? 'rgba(0, 188, 212, 0.05)' : 'background.paper',
          transition: 'all 0.3s ease',
          opacity: disabled ? 0.6 : 1,
          ...(
            !disabled && {
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'rgba(0, 188, 212, 0.05)',
              },
            }
          ),
        }}
      >
        <input
          type="file"
          id="video-input"
          hidden
          accept=".mp4,.avi,.mov,video/mp4,video/x-msvideo,video/quicktime"
          onChange={handleFileInput}
          disabled={disabled}
        />
        <label
          htmlFor="video-input"
          style={{
            cursor: disabled ? 'not-allowed' : 'pointer',
            display: 'block',
          }}
        >
          <CloudUploadIcon
            sx={{ fontSize: 60, color: 'primary.main', mb: 2 }}
          />
          <Typography variant="h5" gutterBottom>
            Drag and drop your video here
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
            or click to select (MP4, AVI, MOV - Max 1GB)
          </Typography>
          <Button
            variant="contained"
            color="primary"
            disabled={disabled}
            onClick={() => document.getElementById('video-input')?.click()}
          >
            Select Video
          </Button>
        </label>
      </Paper>

      {error && (
        <Alert severity="error">{error}</Alert>
      )}

      {selectedFile && !error && (
        <Box sx={{ p: 3, backgroundColor: 'background.paper', borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Selected File
          </Typography>
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip
                label={`File: ${selectedFile.name}`}
                variant="outlined"
                color="primary"
              />
              <Chip
                label={`Size: ${formatFileSize(selectedFile.size)}`}
                variant="outlined"
                color="primary"
              />
            </Box>

            {previewUrl && (
              <Box
                sx={{
                  mt: 2,
                  borderRadius: 2,
                  overflow: 'hidden',
                  backgroundColor: '#000',
                  maxHeight: '400px',
                }}
              >
                <video
                  src={previewUrl}
                  style={{
                    width: '100%',
                    height: 'auto',
                    maxHeight: '400px',
                  }}
                  controls
                />
              </Box>
            )}
          </Stack>
        </Box>
      )}
    </Stack>
  );
};
