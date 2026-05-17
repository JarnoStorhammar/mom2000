"""Camera input abstraction: USB webcam or RTSP stream."""
from __future__ import annotations

import logging
import time
from collections.abc import Generator
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraSource:
    def __init__(
        self,
        source: str = "webcam",
        webcam_device: int = 0,
        rtsp_url: str = "",
        width: int = 640,
        height: int = 480,
    ) -> None:
        self.source = source
        self.width = width
        self.height = height
        self._cap_src: int | str = webcam_device if source == "webcam" else rtsp_url
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        logger.info("Opening camera: %s", self._cap_src)
        self._cap = cv2.VideoCapture(self._cap_src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {self._cap_src}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def close(self) -> None:
        if self._cap and self._cap.isOpened():
            self._cap.release()

    def read_frame(self) -> np.ndarray | None:
        if self._cap is None:
            raise RuntimeError("Call open() first")
        ret, frame = self._cap.read()
        if not ret:
            logger.warning("Frame read failed – reconnecting")
            self.close()
            time.sleep(2)
            self.open()
            return None
        return frame

    def frames(self, fps_limit: int = 5) -> Generator[np.ndarray, None, None]:
        interval = 1.0 / fps_limit
        self.open()
        try:
            while True:
                t0 = time.monotonic()
                frame = self.read_frame()
                if frame is not None:
                    yield frame
                sleep = interval - (time.monotonic() - t0)
                if sleep > 0:
                    time.sleep(sleep)
        finally:
            self.close()
