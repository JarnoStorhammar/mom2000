"""Speech-to-text: faster-whisper, local, offline, Finnish."""
from __future__ import annotations

import logging
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.5
MAX_DURATION = 10.0


class STTEngine:
    def __init__(self, model_size: str = "small", language: str = "fi") -> None:
        logger.info("Loading Whisper model: %s", model_size)
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.language = language
        logger.info("Whisper ready")

    def transcribe_audio(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(audio, language=self.language, beam_size=5, vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip()

    def listen_once(self, timeout: float = 15.0) -> str | None:
        """Record one utterance and return transcribed text, or None on timeout."""
        audio_chunks: list[np.ndarray] = []
        silence_start: float | None = None
        recording_start = time.monotonic()

        def callback(indata, frames, time_info, status):
            if status:
                logger.debug("Audio status: %s", status)
            audio_chunks.append(indata.copy())

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=int(SAMPLE_RATE * CHUNK_DURATION),
            callback=callback,
        ):
            while True:
                time.sleep(CHUNK_DURATION)
                elapsed = time.monotonic() - recording_start
                if not audio_chunks:
                    if elapsed > timeout:
                        return None
                    continue
                rms = float(np.sqrt(np.mean(audio_chunks[-1].flatten() ** 2)) * 32768)
                if rms < SILENCE_THRESHOLD:
                    if silence_start is None:
                        silence_start = time.monotonic()
                    elif time.monotonic() - silence_start > SILENCE_DURATION:
                        break
                else:
                    silence_start = None
                if elapsed > MAX_DURATION:
                    break

        if not audio_chunks:
            return None
        audio = np.concatenate(audio_chunks).flatten()
        return self.transcribe_audio(audio)
