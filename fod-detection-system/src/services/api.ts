import axios from 'axios';
import type { AxiosProgressEvent } from 'axios';
import type { DetectionResponse } from '../types/detection';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 10 minutes for large video uploads
});

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

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
      throw new Error(error.response?.data?.message || error.message || 'Failed to upload video');
    }
    throw error;
  }
};
