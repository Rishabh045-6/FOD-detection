import cv2
import numpy as np


class CameraManager:

    def __init__(self):

        self.cap = None
        self.source_type = "unknown"
        self.source = None
        self.mock_mode = False
        self.mock_frame_counter = 0

    def open(self, source=0):

        self.release()
        self.source = source
        self.mock_mode = False
        self.mock_frame_counter = 0

        if isinstance(source, str) and source.lower() == "mock":
            self.source_type = "mock"
            self.mock_mode = True
            return True

        if isinstance(source, str) and source.isdigit():
            source = int(source)

        try:
            self.cap = cv2.VideoCapture(source)
        except Exception:
            self.cap = None
            return False

        if not self.cap or not self.cap.isOpened():
            self.release()
            return False

        self.source_type = "cv2_local" if isinstance(source, int) else "cv2_network"
        return True

    def read(self):

        if getattr(self, "mock_mode", False):
            self.mock_frame_counter += 1
            frame = 255 * np.ones((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                "MOCK VIDEO STREAM",
                (24, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Frame {self.mock_frame_counter}",
                (24, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            x = 80 + (self.mock_frame_counter % 400)
            cv2.rectangle(frame, (x, 180), (x + 120, 260), (0, 128, 255), -1)
            return True, frame

        if self.cap is None:

            return False, None

        return self.cap.read()

    def read_frame(self):
        return self.read()

    def release(self):

        if self.cap is not None:

            self.cap.release()

            self.cap = None

        self.mock_mode = False

    def close(self):

        self.release()

    def is_open(self):

        return (
            (self.cap is not None and self.cap.isOpened())
            or getattr(self, "mock_mode", False)
        )