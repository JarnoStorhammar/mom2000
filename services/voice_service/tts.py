from __future__ import annotations
import logging, os, subprocess, tempfile
from pathlib import Path

logger = logging.getLogger(__name__)
PIPER_BIN = os.getenv("PIPER_BIN","/usr/local/bin/piper")
PIPER_VOICE = os.getenv("PIPER_VOICE","fi_FI-harri-medium")
PIPER_DIR = os.getenv("PIPER_MODELS_DIR","/app/shared/models/piper")
SINK = os.getenv("AUDIO_OUTPUT_SINK","")

class TTSEngine:
    def __init__(self):
        self.model = Path(PIPER_DIR)/f"{PIPER_VOICE}.onnx"
        if not self.model.exists(): logger.warning("Piper model missing: %s", self.model)

    def speak(self, text: str):
        logger.info("TTS: %s", text)
        with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as f: wav=f.name
        try:
            r=subprocess.run([PIPER_BIN,"--model",str(self.model),"--output_file",wav],
                input=text.encode(),capture_output=True,timeout=10)
            if r.returncode!=0: raise RuntimeError(r.stderr.decode())
            cmd=["paplay",f"--device={SINK}",wav] if SINK else ["paplay",wav]
            subprocess.run(cmd,check=True,timeout=30)
        except Exception as e: logger.error("TTS: %s",e)
        finally: Path(wav).unlink(missing_ok=True)
