"""Face recognition using dlib via face_recognition library."""
from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import face_recognition
import numpy as np

logger = logging.getLogger(__name__)
EMBEDDINGS_FILE = "embeddings.pkl"


@dataclass
class RecognitionResult:
    name: str
    confidence: float
    location: tuple[int, int, int, int]


class FaceRecognizer:
    def __init__(self, embeddings_path: str, confidence_threshold: float = 0.55) -> None:
        self.embeddings_dir = Path(embeddings_path)
        self.threshold = confidence_threshold
        self.known_encodings: list[np.ndarray] = []
        self.known_names: list[str] = []
        self._load_embeddings()

    def _load_embeddings(self) -> None:
        pkl = self.embeddings_dir / EMBEDDINGS_FILE
        if pkl.exists():
            with open(pkl, "rb") as f:
                data = pickle.load(f)
            self.known_encodings = data.get("encodings", [])
            self.known_names = data.get("names", [])
            logger.info("Loaded %d face embeddings", len(self.known_names))
        else:
            logger.warning("No embeddings at %s – run enroll_face.py first", pkl)

    def reload(self) -> None:
        self.known_encodings = []
        self.known_names = []
        self._load_embeddings()

    def recognize(self, frame_rgb: np.ndarray) -> list[RecognitionResult]:
        if not self.known_encodings:
            return []
        locations = face_recognition.face_locations(frame_rgb, model="hog")
        if not locations:
            return []
        encodings = face_recognition.face_encodings(frame_rgb, locations)
        results: list[RecognitionResult] = []
        for encoding, location in zip(encodings, locations):
            distances = face_recognition.face_distance(self.known_encodings, encoding)
            best_idx = int(np.argmin(distances))
            confidence = 1.0 - float(distances[best_idx])
            name = self.known_names[best_idx] if confidence >= self.threshold else "unknown"
            results.append(RecognitionResult(name=name, confidence=confidence, location=location))
        return results
