import axios from 'axios';
import type { AxiosProgressEvent } from 'axios';
import type { DetectionResponse } from '../types/detection';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 10 minutes for large video uploads
});

// --- Structural Model Declarations matching the FastAPI Layer ---

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

export interface LiveStatusResponse {
  is_active: boolean;
  current_source: string | null;
  hardware_type: string;
}

export interface LiveActionResponse {
  status: string;
  message: string;
}

// --- Video Batch Processing API ---

export const uploadVideoForDetection = async (
  file: File,
  onProgressChange?: (progress: UploadProgress) => void
): Promise<DetectionResponse> => {
  const formData = new FormData();
  formData.append('video', file);

  try {
    const response = await apiClient.post<DetectionResponse>(
      '/api/detect',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgressChange && progressEvent.total) {
            onProgressChange({
              loaded: progressEvent.loaded,
              total: progressEvent.total,
              percent: Math.round((progressEvent.loaded / progressEvent.total) * 100),
            });
          }
        },
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to upload video',
        { cause: error }
      );
    }
    throw error;
  }
};

// --- Live Control Plane Operations APIs ---

/**
 * Commands the backend engine to initialize a communication channel 
 * onto a physical index or an remote network RTSP address path.
 */
export const startLiveCamera = async (source: string = '0'): Promise<LiveActionResponse> => {
  try {
    const response = await apiClient.post<LiveActionResponse>('/api/live/start', {
      source: source.trim()
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        error.response?.data?.detail || 'Failed to initialize target hardware stream.',
        { cause: error }
      );
    }
    throw error;
  }
};

/**
 * Commands the backend to drop active hardware frames buffers 
 * and disconnect the camera pipeline safely.
 */
export const stopLiveCamera = async (): Promise<LiveActionResponse> => {
  try {
    const response = await apiClient.post<LiveActionResponse>('/api/live/stop');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        error.response?.data?.detail || 'Failed to cleanly terminate camera capture.',
        { cause: error }
      );
    }
    throw error;
  }
};

/**
 * Interrogates the server interface regarding active connection channels 
 * and operational stream health profiles.
 */
export const getLiveCameraStatus = async (): Promise<LiveStatusResponse> => {
  try {
    const response = await apiClient.get<LiveStatusResponse>('/api/live/status');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        error.response?.data?.detail || 'Failed to fetch hardware runtime status registries.',
        { cause: error }
      );
    }
    throw error;
  }
};