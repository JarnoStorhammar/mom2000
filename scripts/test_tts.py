import os, sys; sys.path.insert(0,".")
os.environ.setdefault("PIPER_BIN","/usr/local/bin/piper")
os.environ.setdefault("PIPER_VOICE","fi_FI-harri-medium")
os.environ.setdefault("PIPER_MODELS_DIR","shared/models/piper")
from services.voice_service.tts import TTSEngine
TTSEngine().speak("Hei Jarno, tämä on testi. Kotiassistentti toimii.")
print("TTS test complete.")
