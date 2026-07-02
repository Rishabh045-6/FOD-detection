/**
 * Telemetry layout mapping hardware stream sources and type contexts.
 */
export interface CameraSource {
  /** The driver abstraction flag loaded by backend (e.g., "cv2_local", "cv2_network", "rpi_native") */
  hardware_type: string;
  /** The target runtime endpoint path assigned (e.g., "0" or "rtsp://...") */
  target_source: string;
}