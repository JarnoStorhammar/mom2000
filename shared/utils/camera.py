"""Camera abstraction: USB webcam or RTSP."""
from __future__ import annotations
import logging, time
from typing import Generator, Optional
import cv2, numpy as np

logger = logging.getLogger(__name__)

class CameraSource:
    def __init__(self, source="webcam", webcam_device=0, rtsp_url="", width=640, height=480):
        self._src = webcam_device if source == "webcam" else rtsp_url
        self.width, self.height = width, height
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self):
        self._cap = cv2.VideoCapture(self._src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open: {self._src}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def close(self):
        if self._cap and self._cap.isOpened(): self._cap.release()

    def read_frame(self) -> Optional[np.ndarray]:
        ret, frame = self._cap.read()
        if not ret:
            logger.warning("Frame read failed, reconnecting")
            self.close(); time.sleep(2); self.open(); return None
        return frame

    def frames(self, fps_limit=5) -> Generator[np.ndarray, None, None]:
        interval = 1.0 / fps_limit
        self.open()
        try:
            while True:
                t0 = time.monotonic()
                f = self.read_frame()
                if f is not None: yield f
                s = interval - (time.monotonic() - t0)
                if s > 0: time.sleep(s)
        finally:
            self.close()
