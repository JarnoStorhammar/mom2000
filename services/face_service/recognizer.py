from __future__ import annotations
import logging, pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import face_recognition, numpy as np

logger = logging.getLogger(__name__)

@dataclass
class RecognitionResult:
    name: str; confidence: float; location: tuple

class FaceRecognizer:
    def __init__(self, embeddings_path: str, threshold: float = 0.55):
        self.dir = Path(embeddings_path)
        self.threshold = threshold
        self.encodings: list = []; self.names: list[str] = []
        self._load()

    def _load(self):
        pkl = self.dir / "embeddings.pkl"
        if pkl.exists():
            with open(pkl,"rb") as f: d = pickle.load(f)
            self.encodings = d.get("encodings",[]); self.names = d.get("names",[])
            logger.info("Loaded %d embeddings: %s", len(self.names), sorted(set(self.names)))
        else:
            logger.warning("No embeddings at %s – run enroll_face.py", pkl)

    def reload(self): self.encodings=[]; self.names=[]; self._load()

    def recognize(self, frame_rgb) -> list[RecognitionResult]:
        if not self.encodings: return []
        locs = face_recognition.face_locations(frame_rgb, model="hog")
        if not locs: return []
        encs = face_recognition.face_encodings(frame_rgb, locs)
        out = []
        for enc, loc in zip(encs, locs):
            dists = face_recognition.face_distance(self.encodings, enc)
            i = int(np.argmin(dists)); conf = float(1.0 - dists[i])
            name = self.names[i] if conf >= self.threshold else "unknown"
            out.append(RecognitionResult(name=name, confidence=conf, location=loc))
        return out
