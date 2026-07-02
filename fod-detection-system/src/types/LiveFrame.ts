import type { LiveDetection } from "./LiveDetection";
import type { CameraSource } from "./CameraSource";

/**
 * Structural schema for streaming analysis data packets 
 * pushed down the active WebSocket pipe every frame event loop.
 */
export interface LiveFrame {
  /** Sequentially increments on every captured source image matrix frame index */
  frame: number;
  /** Standard ISO runtime stamp code structured matching "HH:MM:SS" */
  timestamp: string;
  /** Dynamic network lifecycle context report flag ("active", "reconnecting", "error") */
  status: "active" | "reconnecting" | "error";
  /** Current performance metrics frame evaluation scale tracking engine speed */
  fps: number;
  /** Fast assertion binary state checker to trigger control tower strobe highlights */
  fod_detected: boolean;
  /** Live array collection tracking all active target risk items across current frame context */
  detections: LiveDetection[];
  /** Continuous Base64 JPEG data URI stream package ("data:image/jpeg;base64,...") */
  image: string;
  /** Context description detailing configuration origins mapping to backend devices */
  camera_info: CameraSource;
}