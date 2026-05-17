"""Text-to-speech using Piper (local, offline) via PulseAudio."""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

PIPER_BIN = os.getenv("PIPER_BIN", "/usr/local/bin/piper")
PIPER_VOICE = os.getenv("PIPER_VOICE", "fi_FI-harri-medium")
PIPER_MODELS_DIR = os.getenv("PIPER_MODELS_DIR", "/app/models/piper")
AUDIO_SINK = os.getenv("AUDIO_OUTPUT_SINK", "")


class TTSEngine:
    def __init__(self) -> None:
        self.voice = PIPER_VOICE
        self.model_path = Path(PIPER_MODELS_DIR) / f"{self.voice}.onnx"
        if not self.model_path.exists():
            logger.warning("Piper model not found: %s", self.model_path)

    def speak(self, text: str) -> None:
        logger.info("TTS: %s", text)
        try:
            self._synthesize(text)
        except Exception as e:
            logger.error("TTS failed: %s", e)

    def _synthesize(self, text: str) -> None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
        try:
            result = subprocess.run(
                [PIPER_BIN, "--model", str(self.model_path), "--output_file", wav_path],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode())
            play_cmd = ["paplay", f"--device={AUDIO_SINK}", wav_path] if AUDIO_SINK else ["paplay", wav_path]
            subprocess.run(play_cmd, check=True, timeout=30)
        finally:
            Path(wav_path).unlink(missing_ok=True)
