"""Unit tests for services/face_service/recognizer.py"""
from __future__ import annotations
import pickle
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "face_service"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from recognizer import FaceRecognizer, RecognitionResult


class TestFaceRecognizerInit:
    def test_loads_embeddings(self, tmp_embeddings):
        rec = FaceRecognizer(str(tmp_embeddings), threshold=0.55)
        assert len(rec.encodings) == 2
        assert rec.names == ["Jarno", "Testi"]

    def test_no_embeddings_file(self, empty_embeddings):
        rec = FaceRecognizer(str(empty_embeddings))
        assert rec.encodings == []
        assert rec.names == []

    def test_threshold_stored(self, tmp_embeddings):
        rec = FaceRecognizer(str(tmp_embeddings), threshold=0.7)
        assert rec.threshold == 0.7

    def test_reload_refreshes_data(self, tmp_embeddings):
        rec = FaceRecognizer(str(tmp_embeddings))
        assert len(rec.encodings) == 2
        # add a third embedding to the file
        with open(tmp_embeddings / "embeddings.pkl", "rb") as f:
            data = pickle.load(f)
        data["encodings"].append(np.zeros(128))
        data["names"].append("Extra")
        with open(tmp_embeddings / "embeddings.pkl", "wb") as f:
            pickle.dump(data, f)
        rec.reload()
        assert len(rec.encodings) == 3


class TestFaceRecognizerRecognize:
    def test_returns_empty_when_no_embeddings(self, empty_embeddings, black_frame):
        import cv2
        rec = FaceRecognizer(str(empty_embeddings))
        frame_rgb = cv2.cvtColor(black_frame, cv2.COLOR_BGR2RGB)
        assert rec.recognize(frame_rgb) == []

    @patch("recognizer.face_recognition.face_locations", return_value=[])
    def test_returns_empty_when_no_faces(self, mock_locs, tmp_embeddings):
        import cv2
        rec = FaceRecognizer(str(tmp_embeddings))
        frame_rgb = np.zeros((480, 640, 3), dtype=np.uint8)
        result = rec.recognize(frame_rgb)
        assert result == []
        mock_locs.assert_called_once()

    @patch("recognizer.face_recognition.face_encodings")
    @patch("recognizer.face_recognition.face_locations")
    def test_known_person_above_threshold(self, mock_locs, mock_encs, tmp_embeddings):
        mock_locs.return_value = [(10, 100, 90, 20)]
        # encoding very close to known[0] (all zeros) → distance ~0 → confidence ~1
        mock_encs.return_value = [np.zeros(128)]

        rec = FaceRecognizer(str(tmp_embeddings), threshold=0.55)
        results = rec.recognize(np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(results) == 1
        assert results[0].name == "Jarno"
        assert results[0].confidence >= 0.55

    @patch("recognizer.face_recognition.face_encodings")
    @patch("recognizer.face_recognition.face_locations")
    def test_unknown_below_threshold(self, mock_locs, mock_encs, tmp_embeddings):
        mock_locs.return_value = [(10, 100, 90, 20)]
        # encoding far from all known → high distance → low confidence
        mock_encs.return_value = [np.ones(128) * 999.0]

        rec = FaceRecognizer(str(tmp_embeddings), threshold=0.55)
        results = rec.recognize(np.zeros((480, 640, 3), dtype=np.uint8))

        assert results[0].name == "unknown"

    @patch("recognizer.face_recognition.face_encodings")
    @patch("recognizer.face_recognition.face_locations")
    def test_multiple_faces(self, mock_locs, mock_encs, tmp_embeddings):
        mock_locs.return_value = [(10, 100, 90, 20), (10, 300, 90, 220)]
        mock_encs.return_value = [np.zeros(128), np.ones(128) * 999.0]

        rec = FaceRecognizer(str(tmp_embeddings), threshold=0.55)
        results = rec.recognize(np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(results) == 2
        names = {r.name for r in results}
        assert "Jarno" in names
        assert "unknown" in names

    @patch("recognizer.face_recognition.face_encodings")
    @patch("recognizer.face_recognition.face_locations")
    def test_result_has_confidence_and_location(self, mock_locs, mock_encs, tmp_embeddings):
        loc = (10, 100, 90, 20)
        mock_locs.return_value = [loc]
        mock_encs.return_value = [np.zeros(128)]

        rec = FaceRecognizer(str(tmp_embeddings))
        results = rec.recognize(np.zeros((480, 640, 3), dtype=np.uint8))

        r = results[0]
        assert isinstance(r, RecognitionResult)
        assert 0.0 <= r.confidence <= 1.0
        assert r.location == loc
