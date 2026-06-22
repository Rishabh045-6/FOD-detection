export interface Coordinates {
  x: number | null;
  y: number | null;
}

export interface DetectionResult {
  id: string;
  frame: number;
  timestamp: string;
  distance_m: number | null;
  coordinates: Coordinates;
  confidence: number;
}

export interface DetectionResponse {
  status: string;
  processed_video_url: string;
  total_frames: number;
  processing_time: number;
  fod_detected: boolean;
  detections: DetectionResult[];
}

export interface ProcessingState {
  status: 'idle' | 'uploading' | 'extracting' | 'detecting' | 'calculating' | 'generating' | 'complete' | 'error';
  progress: number;
  message: string;
  error?: string;
}
