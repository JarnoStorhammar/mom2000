"""Unit tests for shared/utils/camera.py"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from utils.camera import CameraSource


class TestCameraSource:
    def test_webcam_device_used_when_source_webcam(self):
        cam = CameraSource(source="webcam", webcam_device=2)
        assert cam._cap_src == 2

    def test_rtsp_url_used_when_source_rtsp(self):
        cam = CameraSource(source="rtsp", rtsp_url="rtsp://cam/stream")
        assert cam._cap_src == "rtsp://cam/stream"

    @patch("utils.camera.cv2.VideoCapture")
    def test_open_raises_if_not_opened(self, MockCap):
        MockCap.return_value.isOpened.return_value = False
        cam = CameraSource()
        with pytest.raises(RuntimeError, match="Cannot open camera"):
            cam.open()

    @patch("utils.camera.cv2.VideoCapture")
    def test_open_sets_resolution(self, MockCap):
        cap_mock = MagicMock()
        cap_mock.isOpened.return_value = True
        MockCap.return_value = cap_mock
        cam = CameraSource(width=1280, height=720)
        cam.open()
        cap_mock.set.assert_any_call(3, 1280)  # CAP_PROP_FRAME_WIDTH = 3
        cap_mock.set.assert_any_call(4, 720)   # CAP_PROP_FRAME_HEIGHT = 4

    @patch("utils.camera.cv2.VideoCapture")
    def test_read_frame_returns_none_and_reconnects_on_failure(self, MockCap):
        cap_mock = MagicMock()
        cap_mock.isOpened.return_value = True
        cap_mock.read.return_value = (False, None)
        MockCap.return_value = cap_mock

        cam = CameraSource()
        cam._cap = cap_mock

        with patch.object(cam, "open") as mock_open, patch("utils.camera.time.sleep"):
            result = cam.read_frame()

        assert result is None
        mock_open.assert_called_once()

    @patch("utils.camera.cv2.VideoCapture")
    def test_close_releases_cap(self, MockCap):
        cap_mock = MagicMock()
        cap_mock.isOpened.return_value = True
        MockCap.return_value = cap_mock
        cam = CameraSource()
        cam._cap = cap_mock
        cam.close()
        cap_mock.release.assert_called_once()
