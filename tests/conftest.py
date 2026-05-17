"""Shared pytest fixtures and mocks."""
from __future__ import annotations
import pickle
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Ensure shared utils are importable without Docker paths
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Fixtures: fake face embeddings ───────────────────────────────────────────

@pytest.fixture()
def tmp_embeddings(tmp_path: Path) -> Path:
    """Write a minimal embeddings.pkl into a temp dir and return the dir."""
    enc1 = np.zeros(128, dtype=np.float64)
    enc2 = np.ones(128, dtype=np.float64) * 0.5
    data = {"encodings": [enc1, enc2], "names": ["Jarno", "Testi"]}
    pkl = tmp_path / "embeddings.pkl"
    with open(pkl, "wb") as f:
        pickle.dump(data, f)
    return tmp_path


@pytest.fixture()
def empty_embeddings(tmp_path: Path) -> Path:
    """Empty embeddings dir (no pkl file)."""
    return tmp_path


# ── Fixtures: camera frames ───────────────────────────────────────────────────

@pytest.fixture()
def black_frame() -> np.ndarray:
    """480x640 black BGR frame."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture()
def roi_frame() -> np.ndarray:
    """Small crop that would come from ROI extraction."""
    return np.zeros((200, 400, 3), dtype=np.uint8)


# ── Fixtures: MQTT mock ───────────────────────────────────────────────────────

@pytest.fixture()
def mock_mqtt():
    """MQTTClient with publish/subscribe mocked."""
    m = MagicMock()
    m.published: list[tuple[str, str]] = []

    def _pub(topic, payload, retain=False):
        m.published.append((topic, payload))

    m.publish.side_effect = _pub
    return m
