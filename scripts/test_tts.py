"""Quick TTS smoke test – run from project root."""
from __future__ import annotations
import os, sys
sys.path.insert(0, "services/voice_service")
os.environ.setdefault("PIPER_MODELS_DIR", "shared/models/piper")

from tts import TTSEngine

engine = TTSEngine()
engine.speak("Hei! Tämä on testi. Ääniassistentti toimii.")
print("TTS test complete – did you hear audio?")
