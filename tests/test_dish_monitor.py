"""Unit tests for services/vision_service/dish_monitor.py"""
from __future__ import annotations
import sys, time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "vision_service"))

# Patch ultralytics before import so no model is loaded during tests
import unittest.mock as mock
sys.modules.setdefault("ultralytics", mock.MagicMock())

from dish_monitor import DishMonitor, Obj, TRACKED


def _make_monitor(**kwargs):
    defaults = dict(
        model_path="fake.pt",
        roi=(0.0, 0.0, 1.0, 1.0),
        timeout_m=15.0,
        cooldown_m=30.0,
        q_start=22,
        q_end=7,
        conf=0.45,
    )
    defaults.update(kwargs)
    mon = DishMonitor.__new__(DishMonitor)
    mon.roi       = defaults["roi"]
    mon.timeout_m = defaults["timeout_m"]
    mon.cooldown_m= defaults["cooldown_m"]
    mon.q_start   = defaults["q_start"]
    mon.q_end     = defaults["q_end"]
    mon.conf      = defaults["conf"]
    mon._tr       = {}
    mon._last_alert = 0.0
    # Mock YOLO model
    mon.model = MagicMock()
    return mon


class TestDishMonitorQuietHours:
    def test_quiet_wraps_midnight(self):
        mon = _make_monitor(q_start=22, q_end=7)
        with patch("dish_monitor.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 23
            assert mon._quiet() is True
            mock_dt.now.return_value.hour = 3
            assert mon._quiet() is True
            mock_dt.now.return_value.hour = 10
            assert mon._quiet() is False

    def test_quiet_normal_range(self):
        mon = _make_monitor(q_start=14, q_end=16)
        with patch("dish_monitor.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 15
            assert mon._quiet() is True
            mock_dt.now.return_value.hour = 17
            assert mon._quiet() is False


class TestDishMonitorROI:
    def test_roi_pixels_full_frame(self):
        mon = _make_monitor(roi=(0.0, 0.0, 1.0, 1.0))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        assert mon._roi_px(frame) == (0, 0, 640, 480)

    def test_roi_pixels_partial(self):
        mon = _make_monitor(roi=(0.25, 0.25, 0.75, 0.75))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x1, y1, x2, y2 = mon._roi_px(frame)
        assert x1 == 160 and y1 == 120
        assert x2 == 480 and y2 == 360


class TestDishMonitorTracking:
    def _detection_result(self, class_names: list[str]):
        """Build a fake YOLO result object."""
        result = MagicMock()
        result.names = {i: n for i, n in enumerate(class_names)}
        boxes = []
        for i in range(len(class_names)):
            b = MagicMock()
            b.cls = MagicMock()
            b.cls.__int__ = lambda self, i=i: i
            boxes.append(b)
        result.boxes = boxes
        return [result]

    def test_no_detection_returns_none(self):
        mon = _make_monitor()
        mon.model.return_value = self._detection_result([])
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        assert mon.process_frame(frame) is None

    def test_detected_object_added_to_tracking(self):
        mon = _make_monitor()
        mon.model.return_value = self._detection_result(["cup"])
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mon.process_frame(frame)
        assert "cup" in mon._tr

    def test_non_tracked_class_ignored(self):
        mon = _make_monitor()
        mon.model.return_value = self._detection_result(["laptop"])
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mon.process_frame(frame)
        assert "laptop" not in mon._tr

    def test_object_removed_after_gone_10s(self):
        mon = _make_monitor()
        mon._tr["cup"] = Obj(cls="cup")
        # Simulate last_seen 15s ago
        mon._tr["cup"].last = time.monotonic() - 15.0
        mon.model.return_value = self._detection_result([])
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mon.process_frame(frame)
        assert "cup" not in mon._tr

    def test_no_alert_before_timeout(self):
        mon = _make_monitor(timeout_m=15.0)
        obj = Obj(cls="plate")
        obj.first = time.monotonic() - 5 * 60  # 5 min ago
        mon._tr["plate"] = obj
        mon.model.return_value = self._detection_result(["plate"])
        with patch("dish_monitor.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 12
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = mon.process_frame(frame)
        assert result is None

    def test_alert_fires_after_timeout(self):
        mon = _make_monitor(timeout_m=15.0, cooldown_m=0.0)
        obj = Obj(cls="plate")
        obj.first = time.monotonic() - 20 * 60  # 20 min ago
        mon._tr["plate"] = obj
        mon.model.return_value = self._detection_result(["plate"])
        with patch("dish_monitor.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 12
            mock_dt.now.return_value.isoformat.return_value = "2026-05-17T12:00:00"
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = mon.process_frame(frame)
        assert result is not None
        assert "plate" in result["items"]
        assert result["minutes"] >= 19.9

    def test_alert_respects_cooldown(self):
        mon = _make_monitor(timeout_m=1.0, cooldown_m=30.0)
        obj = Obj(cls="cup")
        obj.first = time.monotonic() - 10 * 60
        mon._tr["cup"] = obj
        mon._last_alert = time.monotonic() - 60  # alert fired 1 min ago
        mon.model.return_value = self._detection_result(["cup"])
        with patch("dish_monitor.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 12
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = mon.process_frame(frame)
        assert result is None

    def test_alert_suppressed_during_quiet_hours(self):
        mon = _make_monitor(timeout_m=1.0, cooldown_m=0.0, q_start=22, q_end=7)
        obj = Obj(cls="bowl")
        obj.first = time.monotonic() - 10 * 60
        mon._tr["bowl"] = obj
        mon.model.return_value = self._detection_result(["bowl"])
        with patch("dish_monitor.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 23  # quiet hours
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = mon.process_frame(frame)
        assert result is None

    def test_get_status_returns_minutes(self):
        mon = _make_monitor()
        obj = Obj(cls="fork")
        obj.first = time.monotonic() - 3 * 60
        mon._tr["fork"] = obj
        status = mon.get_status()
        assert "fork" in status
        assert 2.9 <= status["fork"] <= 3.1
