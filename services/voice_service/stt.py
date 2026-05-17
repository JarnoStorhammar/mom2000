from __future__ import annotations
import logging, time
from typing import Optional
import numpy as np, sounddevice as sd
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)
SR=16000; CHUNK=0.5; SIL_RMS=500; SIL_DUR=1.5; MAX_DUR=10.0

class STTEngine:
    def __init__(self, model_size="small", language="fi"):
        logger.info("Loading Whisper %s", model_size)
        self.m = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.lang = language; logger.info("Whisper ready")

    def transcribe(self, audio: np.ndarray) -> str:
        segs,_ = self.m.transcribe(audio, language=self.lang, beam_size=5, vad_filter=True)
        return " ".join(s.text.strip() for s in segs).strip()

    def listen_once(self, timeout=15.0) -> Optional[str]:
        chunks=[]; sil_t=None; t0=time.monotonic()
        def cb(d,f,ti,st): chunks.append(d.copy())
        with sd.InputStream(samplerate=SR,channels=1,dtype="float32",
                            blocksize=int(SR*CHUNK),callback=cb):
            while True:
                time.sleep(CHUNK); e=time.monotonic()-t0
                if not chunks:
                    if e>timeout: return None
                    continue
                rms=float(np.sqrt(np.mean(chunks[-1].flatten()**2))*32768)
                if rms<SIL_RMS:
                    if sil_t is None: sil_t=time.monotonic()
                    elif time.monotonic()-sil_t>SIL_DUR: break
                else: sil_t=None
                if e>MAX_DUR: break
        if not chunks: return None
        return self.transcribe(np.concatenate(chunks).flatten())
