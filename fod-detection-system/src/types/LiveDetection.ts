/**
 * Represents a single Foreign Object Debris (FOD) item 
 * identified on the ground track during live radar operations.
 */
export interface LiveDetection {
  /** A unique identification token tracking the item (e.g., "FOD-001") */
  id: string;
  /** Model predictive confidence rating scale bounded between 0.0 and 1.0 */
  confidence: number;
  /** Absolute distance to target point computed from baseline in meters */
  distance_m: number;
  /** Ground-plane runway spatial coordinates relative to vehicle/tower setup */
  coordinates: {
    /** Side lateral offset distance from scan axis baseline (Left is negative, Right is positive) */
    x: number;
    /** Direct longitudinal forward preview step range in meters */
    y: number;
  };
}