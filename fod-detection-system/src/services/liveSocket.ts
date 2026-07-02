import type { LiveFrame } from "../types/LiveFrame";

interface LiveSocketOptions {
  /** The server target string (e.g., '0' or 'rtsp://...') */
  source: string;
  /** Fired instantly when a complete telemetry frame packet arrives */
  onFrameReceived: (data: LiveFrame) => void;
  /** Triggered when connection state mutations happen */
  onStatusChange: (status: "connecting" | "connected" | "disconnected" | "reconnecting") => void;
  /** Optional custom base backend websocket URL override */
  baseUrl?: string;
}

export class LiveSocketService {
  private ws: WebSocket | null = null;
  private options: LiveSocketOptions;
  private isIntentionallyClosed: boolean = false;
  
  // Connection recovery variables
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private baseReconnectDelayMs: number = 1000;

  constructor(options: LiveSocketOptions) {
    this.options = options;
  }

  /**
   * Establishes a persistent full-duplex socket pipe to the backend.
   */
  public connect(): void {
    this.cleanUpTimers();
    this.isIntentionallyClosed = false;
    
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";
    const defaultHostUrl = apiBaseUrl.startsWith("https://")
      ? apiBaseUrl.replace(/^https:/, "wss:")
      : apiBaseUrl.replace(/^http:/, "ws:");

    const hostUrl = this.options.baseUrl || import.meta.env.VITE_WS_BASE_URL || defaultHostUrl;
    const encodedSource = encodeURIComponent(this.options.source);
    const fullUrl = `${hostUrl}/ws/live?source=${encodedSource}`;

    this.options.onStatusChange(this.reconnectAttempts > 0 ? "reconnecting" : "connecting");
    
    try {
      this.ws = new WebSocket(fullUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error("[LiveSocket] Failed to instantiate raw WebSocket protocol:", error);
      this.handleDisconnection();
    }
  }

  /**
   * Gracefully tears down connections and clears automated fallback intervals.
   */
  public disconnect(): void {
    this.isIntentionallyClosed = true;
    this.cleanUpTimers();
    
    if (this.ws) {
      // 1000 indicates a normal termination context drop
      this.ws.close(1000, "User terminated live tracking section session");
      this.ws = null;
    }
    
    this.options.onStatusChange("disconnected");
  }

  /**
   * Binds data parsing hooks to the underlying network layer.
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log("[LiveSocket] Analytical stream channel fully operational.");
      this.reconnectAttempts = 0;
      this.options.onStatusChange("connected");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const payload: LiveFrame = JSON.parse(event.data);
        this.options.onFrameReceived(payload);
      } catch (err) {
        console.error("[LiveSocket] Error parsing real-time message payload data frame:", err);
      }
    };

    this.ws.onerror = (error: Event) => {
      console.error("[LiveSocket] Connection boundary error event encountered:", error);
    };

    this.ws.onclose = (event: CloseEvent) => {
      console.log(`[LiveSocket] Data pipe disconnected cleanly. Code: ${event.code}`);
      this.handleDisconnection();
    };
  }

  /**
   * Deduce disconnect driver source to safely schedule recovery loops.
   */
  private handleDisconnection(): void {
    if (this.isIntentionallyClosed) return;

    this.options.onStatusChange("disconnected");

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      // Compute exponential retry delay backoff curve (1s, 2s, 4s, 8s...)
      const delay = this.baseReconnectDelayMs * Math.pow(2, this.reconnectAttempts - 1);
      console.warn(`[LiveSocket] Pipeline lost. Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms...`);
      
      this.reconnectTimeoutId = setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error("[LiveSocket] Maximum reconnection exhaustion limit hit. Halting retry threads.");
    }
  }

  private cleanUpTimers(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
  }
}