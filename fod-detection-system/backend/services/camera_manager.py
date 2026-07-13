import cv2
import numpy as np
from pathlib import Path

class CameraManager:

    def __init__(self):

        self.cap = None
        self.source_type = "unknown"
        self.source = None

        self.mock_mode = False
        self.mock_video = None

        self.sample_video = (
            Path(__file__).resolve().parent.parent
            / "sample_videos"
            / "fod_16sep01.mp4"
        )

    def open(self, source=0):

        self.release()
        self.source = source
        self.mock_mode = False
        self.mock_frame_counter = 0

        if isinstance(source, str) and source.lower() == "mock":

            print("Opening MOCK source...")

            self.source_type = "mock"
            self.mock_mode = True

            print("Video path:", self.sample_video)
            print("Exists:", self.sample_video.exists())

            self.mock_video = cv2.VideoCapture(str(self.sample_video))

            print("Opened:", self.mock_video.isOpened())

            if not self.mock_video.isOpened():
                self.mock_mode = False
                return False

            return True

        if isinstance(source, str) and source.isdigit():
            source = int(source)

        try:
            if isinstance(source, str):

                self.cap = cv2.VideoCapture(
                    source,
                    cv2.CAP_FFMPEG
                )

            else:

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

        if self.mock_mode:

            if self.mock_video is None:
                return False, None

            ret, frame = self.mock_video.read()

            # Restart automatically when the video ends
            if not ret:

                self.mock_video.set(cv2.CAP_PROP_POS_FRAMES, 0)

                ret, frame = self.mock_video.read()

            return ret, frame
        if self.cap is None:

            return False, None

        ret, frame = self.cap.read()

        print("----------------------------")
        print("RET:", ret)

        if frame is not None:
            print("Shape:", frame.shape)
        else:
            print("Frame is None")

        return ret, frame

    def read_frame(self):
        return self.read()

    def release(self):

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        if self.mock_video is not None:
            self.mock_video.release()
            self.mock_video = None

        self.mock_mode = False

    def close(self):

        self.release()

    def is_open(self):

        return (
            (self.cap is not None and self.cap.isOpened())
            or getattr(self, "mock_mode", False)
        )