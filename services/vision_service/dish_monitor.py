"""Dish monitoring: YOLOv8n with ROI, per-object timers, and MQTT alerts."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)

TRACKED_CLASSES = {
    "cup", "bowl", "plate", "fork", "knife", "spoon", "bottle", "wine glass",
}


@dataclass
class TrackedObject:
    class_name: str
    first_seen: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)

    def minutes_present(self) -> float:
        return (time.monotonic() - self.first_seen) / 60.0


class DishMonitor:
    def __init__(
        self,
        model_path: str,
        roi: tuple[float, float, float, float],
        timeout_minutes: float,
        cooldown_minutes: float,
        quiet_start: int,
        quiet_end: int,
        confidence_threshold: float = 0.45,
    ) -> None:
        logger.info("Loading YOLO model: %s", model_path)
        self.model = YOLO(model_path)
        self.roi = roi
        self.timeout_minutes = timeout_minutes
        self.cooldown_minutes = cooldown_minutes
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end
        self.conf_threshold = confidence_threshold
        self._tracked: dict[str, TrackedObject] = {}
        self._last_alert_time: float = 0.0

    def _is_quiet_hours(self) -> bool:
        hour = datetime.now().hour
        if self.quiet_start > self.quiet_end:
            return hour >= self.quiet_start or hour < self.quiet_end
        return self.quiet_start <= hour < self.quiet_end

    def _roi_px(self, frame: np.ndarray) -> tuple[int, int, int, int]:
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = self.roi
        return int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)

    def process_frame(self, frame: np.ndarray) -> dict | None:
        rx1, ry1, rx2, ry2 = self._roi_px(frame)
        roi_frame = frame[ry1:ry2, rx1:rx2]
        results = self.model(roi_frame, conf=self.conf_threshold, verbose=False)

        detected: set[str] = set()
        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls)]
                if cls_name in TRACKED_CLASSES:
                    detected.add(cls_name)

        now = time.monotonic()
        for cls in detected:
            if cls in self._tracked:
                self._tracked[cls].last_seen = now
            else:
                self._tracked[cls] = TrackedObject(class_name=cls)

        gone = [k for k, v in self._tracked.items() if now - v.last_seen > 10.0]
        for k in gone:
            del self._tracked[k]

        if not self._tracked:
            return None

        max_minutes = max(v.minutes_present() for v in self._tracked.values())
        if max_minutes < self.timeout_minutes:
            return None
        if self._is_quiet_hours():
            return None
        if now - self._last_alert_time < self.cooldown_minutes * 60:
            return None

        self._last_alert_time = now
        return {
            "items": list(self._tracked.keys()),
            "minutes": round(max_minutes, 1),
            "timestamp": datetime.now().isoformat(),
        }

    def get_status(self) -> dict[str, float]:
        return {cls: round(obj.minutes_present(), 1) for cls, obj in self._tracked.items()}
