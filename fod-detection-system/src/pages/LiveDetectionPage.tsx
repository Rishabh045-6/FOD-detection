import { useState, useEffect, useRef } from "react";
import {
  Box,
  Grid,
  Typography,
  Card, 
  CardContent, 
  Button, 
  TextField, 
  Chip, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  LinearProgress,
  Stack
} from "@mui/material";
import {
  Videocam,
  VideocamOff,
  CompassCalibration,
  Speed,
  WarningAmber,
  CheckCircleOutlined,
} from "@mui/icons-material";
import { toast } from "react-toastify";

// Match the API structures passed via the WebSocket payload
interface Detection {
  id: string;
  distance_m: number;
  coordinates: {
    x: number;
    y: number;
  };
  confidence: number;
}

interface LiveWSMessage {
  frame: number;
  timestamp: string;
  fod_detected: boolean;
  detections: Detection[];
}

export default function LiveDetectionPage() {
  const [cameraSource, setCameraSource] = useState<string>("0");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<LiveWSMessage | null>(null);
  
  // Performance and UI tracking states
  const [fps, setFps] = useState<number>(0);
  const [closestObject, setClosestObject] = useState<Detection | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const frameCountRef = useRef<number>(0);
  const fpsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Periodic FPS calculator helper
  useEffect(() => {
    if (!isStreaming) return undefined;

    fpsIntervalRef.current = setInterval(() => {
      setFps(frameCountRef.current);
      frameCountRef.current = 0;
    }, 1000);

    return () => {
      if (fpsIntervalRef.current) {
        clearInterval(fpsIntervalRef.current);
        fpsIntervalRef.current = null;
      }
    };
  }, [isStreaming]);

  const startLiveStream = () => {
    if (wsRef.current) return;

    const wsUrl = `ws://localhost:8000/ws/live?source=${encodeURIComponent(cameraSource)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    setIsStreaming(true);
    toast.info(`Connecting to live runway stream [Source: ${cameraSource}]...`);

    ws.onmessage = (event) => {
      try {
        const data: LiveWSMessage = JSON.parse(event.data);
        setLastMessage(data);
        frameCountRef.current += 1;

        // Process telemetry to quickly determine closest risk
        if (data.detections && data.detections.length > 0) {
          const sorted = [...data.detections].sort((a, b) => a.distance_m - b.distance_m);
          setClosestObject(sorted[0]);
        } else {
          setClosestObject(null);
        }
      } catch (err) {
        console.error("Failed parsing real-time analytics packet:", err);
      }
    };

    ws.onerror = () => {
      toast.error("WebSocket connection encountered an execution failure.");
      stopLiveStream();
    };

    ws.onclose = () => {
      toast.warn("Live analytical hardware pipeline stream closed.");
      stopLiveStream();
    };
  };

  const stopLiveStream = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsStreaming(false);
    setFps(0);
    setLastMessage(null);
    setClosestObject(null);
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <Box sx={{ p: 4, maxWidth: "1600px", margin: "0 auto" }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: "bold", mb: 3 }}>
        Runway Inspection & Live FOD Stream
      </Typography>

      <Grid container spacing={3}>
        {/* Left Side: Connection Control & Live Metadata Display */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={3}>
            {/* Control Panel Card */}
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <CompassCalibration color="primary" /> Camera Interface Setup
                </Typography>
                <TextField
                  fullWidth
                  label="Target Stream Path / HW Index"
                  variant="outlined"
                  size="small"
                  value={cameraSource}
                  onChange={(e) => setCameraSource(e.target.value)}
                  disabled={isStreaming}
                  placeholder="e.g., 0, rtsp://192.168.1.50/stream"
                  sx={{ my: 2 }}
                />
                {!isStreaming ? (
                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                    startIcon={<Videocam />}
                    onClick={startLiveStream}
                  >
                    Initiate Live Inspection
                  </Button>
                ) : (
                  <Button
                    fullWidth
                    variant="contained"
                    color="error"
                    startIcon={<VideocamOff />}
                    onClick={stopLiveStream}
                  >
                    Halt Feed Processing
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Live Operational Metrics Card */}
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Speed color="secondary" /> Operational Telemetry
                </Typography>
                
                <Stack spacing={2.5} sx={{ mt: 2 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Typography color="text.secondary">System Mode:</Typography>
                    <Chip 
                      label={isStreaming ? "INSPECTION ACTIVE" : "OFFLINE"} 
                      color={isStreaming ? "success" : "default"} 
                      variant="filled"
                      size="small"
                    />
                  </Box>

                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Typography color="text.secondary">Process Frame ID:</Typography>
                    <Typography variant="body1" sx={{ fontFamily: "monospace", fontWeight: "bold" }}>
                      {lastMessage ? lastMessage.frame : "---"}
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Typography color="text.secondary">Inference Pacing:</Typography>
                    <Typography variant="body1" sx={{ fontWeight: "bold" }}>
                      {fps} FPS
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Typography color="text.secondary">FOD Runway Status:</Typography>
                    {lastMessage?.fod_detected ? (
                      <Chip icon={<WarningAmber />} label="DEBRIS DETECTED" color="error" size="small" />
                    ) : (
                      <Chip icon={<CheckCircleOutlined />} label="RUNWAY CLEAR" color="success" size="small" variant="outlined" />
                    )}
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Proximity Risk Management Card */}
            <Card elevation={3} sx={{ bgcolor: closestObject ? "error.light" : "background.paper", transition: "all 0.3s" }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: "bold", color: closestObject ? "error.dark" : "text.primary" }}>
                  🚨 Critical Vector Alert (Closest Object)
                </Typography>
                {closestObject ? (
                  <Stack spacing={1.5} sx={{ mt: 2, color: "error.dark" }}>
                    <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                      <Typography sx={{ fontWeight: "medium" }}>Target Marker:</Typography>
                      <Typography sx={{ fontWeight: "bold" }}>{closestObject.id}</Typography>
                    </Box>
                    <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                      <Typography sx={{ fontWeight: "medium" }}>Proximity Distance:</Typography>
                      <Typography sx={{ fontWeight: "bold" }}>{closestObject.distance_m} meters</Typography>
                    </Box>
                    <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                      <Typography sx={{ fontWeight: "medium" }}>Runway Position (X, Y):</Typography>
                      <Typography sx={{ fontWeight: "bold", fontFamily: "monospace" }}>
                        ({closestObject.coordinates.x}m, {closestObject.coordinates.y}m)
                      </Typography>
                    </Box>
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1, it: "italic" }}>
                    No objects tracked within scanning limits.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>

        {/* Right Side: Virtualized Camera Stream Context & Metric Inventory */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Stack spacing={3}>
            {/* Camera Frame Feed Visualization Placeholder */}
            <Card elevation={2}>
              <Box 
                sx={{ 
                  width: "100%", 
                  height: "500px", 
                  bgcolor: "black", 
                  display: "flex", 
                  flexDirection: "column",
                  alignItems: "center", 
                  justifyContent: "center",
                  color: "grey.500",
                  position: "relative",
                  borderRadius: "4px 4px 0 0"
                }}
              >
                {isStreaming ? (
                  <>
                    <Videocam sx={{ fontSize: 64, color: lastMessage?.fod_detected ? "error.main" : "success.main", mb: 2 }} />
                    <Typography variant="h6" color="grey.300">
                      Processing Stream via Hardware Matrix Channel
                    </Typography>
                    <Typography variant="body2" color="grey.500" sx={{ mt: 1, fontFamily: "monospace" }}>
                      Timestamp Context: {lastMessage?.timestamp || "Syncing..."}
                    </Typography>
                    {lastMessage?.fod_detected && (
                      <Box sx={{ position: "absolute", top: 16, right: 16, bgcolor: "error.main", color: "white", px: 2, py: 0.5, borderRadius: 1, fontWeight: "bold", animation: "pulse 1.5s infinite" }}>
                        LIVE DETECTION ALARM
                      </Box>
                    )}
                  </>
                ) : (
                  <>
                    <VideocamOff sx={{ fontSize: 64, mb: 2 }} />
                    <Typography variant="h6">Pipeline Context Disengaged</Typography>
                    <Typography variant="body2">Provide a valid stream configuration string to capture live frames.</Typography>
                  </>
                )}
              </Box>
              {isStreaming && <LinearProgress color={lastMessage?.fod_detected ? "error" : "primary"} />}
            </Card>

            {/* Detections Inventory Matrix */}
            <TableContainer component={Paper} elevation={2}>
              <Box sx={{ p: 2, borderBottom: "1px solid", borderColor: "divider" }}>
                <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                  Current Frame Detections Inventory ({lastMessage?.detections.length || 0})
                </Typography>
              </Box>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: "action.hover" }}>
                    <TableCell sx={{ fontWeight: "bold" }}>Target UUID</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Distance (m)</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Ground Coordinate X</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Ground Coordinate Y</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Confidence Scale</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {lastMessage && lastMessage.detections.length > 0 ? (
                    lastMessage.detections.map((det) => (
                      <TableRow key={det.id} hover sx={{ "&:last-child td, &:last-child th": { border: 0 } }}>
                        <TableCell component="th" scope="row" sx={{ fontWeight: "medium", color: "error.main" }}>
                          {det.id}
                        </TableCell>
                        <TableCell>{det.distance_m}m</TableCell>
                        <TableCell sx={{ fontFamily: "monospace" }}>{det.coordinates.x}m</TableCell>
                        <TableCell sx={{ fontFamily: "monospace" }}>{det.coordinates.y}m</TableCell>
                        <TableCell>
                          <Chip label={`${Math.round(det.confidence * 100)}%`} size="small" variant="outlined" color={det.confidence > 0.8 ? "success" : "warning"} />
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} align="center" sx={{ py: 3, color: "text.secondary" }}>
                        {isStreaming ? "Scanning runway... clear space confirmed." : "Initiate live link connection to monitor target matrix data."}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
}