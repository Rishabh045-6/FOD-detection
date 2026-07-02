import React from "react";
import { Box, Typography, CircularProgress } from "@mui/material";
import VideocamOffIcon from "@mui/icons-material/VideocamOff";

interface LiveVideoProps {
  /** Indicates whether the live camera processing thread loop is active */
  isStreaming: boolean;
  /** Expects the sequential Base64 encoded JPEG target frame string string ("data:image/jpeg;base64,...") */
  frameData: string | null;
  /** Binary assertion flag to trigger HUD critical visual hazard alerts */
  fodDetected: boolean;
}

export const LiveVideo: React.FC<LiveVideoProps> = ({ 
  isStreaming, 
  frameData, 
  fodDetected 
}) => {
  return (
    <Box
      sx={{
        width: "100%",
        height: "500px",
        bgcolor: "#090d1a",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "grey.500",
        position: "relative",
        borderRadius: 2,
        overflow: "hidden",
        border: "2px solid",
        borderColor: isStreaming ? (fodDetected ? "error.main" : "success.main") : "rgba(255, 255, 255, 0.05)",
        transition: "border-color 0.2s ease-in-out",
        boxShadow: isStreaming && fodDetected ? "0 0 20px rgba(244, 67, 54, 0.25)" : "none"
      }}
    >
      {isStreaming ? (
        frameData ? (
          /* Live Stream Viewport Viewport */
          <Box sx={{ width: "100%", height: "100%", position: "relative" }}>
            <img
              src={frameData}
              alt="Live Runway Analytical Stream"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                display: "block"
              }}
            />
            
            {/* Status Overlays HUD */}
            <Box 
              sx={{ 
                position: "absolute", 
                top: 16, 
                left: 16, 
                bgcolor: "rgba(10, 14, 39, 0.75)", 
                backdropFilter: "blur(4px)",
                color: "white", 
                px: 1.5, 
                py: 0.5, 
                borderRadius: 1, 
                display: "flex",
                alignItems: "center",
                gap: 1,
                fontSize: "0.8rem",
                fontWeight: "bold",
                border: "1px solid rgba(255, 255, 255, 0.1)"
              }}
            >
              <Box 
                sx={{ 
                  width: 8, 
                  height: 8, 
                  bgcolor: "error.main", 
                  borderRadius: "50%",
                  animation: "live-pulse 1.5s infinite" 
                }} 
              />
              LIVE BROADCAST
            </Box>

            {fodDetected && (
              <Box 
                sx={{ 
                  position: "absolute", 
                  top: 16, 
                  right: 16, 
                  bgcolor: "error.main", 
                  color: "white", 
                  px: 2, 
                  py: 0.5, 
                  borderRadius: 1, 
                  fontWeight: "bold",
                  fontSize: "0.85rem",
                  boxShadow: 3,
                  letterSpacing: "0.5px",
                  animation: "alert-flash 1s infinite"
                }}
              >
                RUNWAY ALARM: DEBRIS DETECTED
              </Box>
            )}
          </Box>
        ) : (
          /* Connecting State */
          <Box sx={{ textAlign: "center" }}>
            <CircularProgress color="primary" size={40} sx={{ mb: 2 }} />
            <Typography variant="body1" color="textSecondary">
              Buffering video stream lines...
            </Typography>
          </Box>
        )
      ) : (
        /* Dormant State */
        <Box sx={{ textAlign: "center", p: 3 }}>
          <VideocamOffIcon sx={{ fontSize: 64, color: "rgba(255, 255, 255, 0.15)", mb: 2 }} />
          <Typography variant="h6" color="textPrimary" sx={{ fontWeight: "bold", mb: 0.5 }}>
            Camera Stream Inactive
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ maxWidth: "340px", mx: "auto" }}>
            Provide a physical device index or airfield RTSP pipeline string link to launch automated checking matrices.
          </Typography>
        </Box>
      )}

      {/* Embedded Operational Keyframe Keyframe Animations */}
      <style>{`
        @keyframes live-pulse {
          0% { transform: scale(0.9); opacity: 0.4; }
          50% { transform: scale(1.1); opacity: 1; }
          100% { transform: scale(0.9); opacity: 0.4; }
        }
        @keyframes alert-flash {
          0% { background-color: #f44336; box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4); }
          50% { background-color: #d32f2f; box-shadow: 0 0 0 10px rgba(244, 67, 54, 0); }
          100% { background-color: #f44336; box-shadow: 0 0 0 0 rgba(244, 67, 54, 0); }
        }
      `}</style>
    </Box>
  );
};