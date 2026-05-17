from __future__ import annotations
import json, logging, os, sys, threading
sys.path.insert(0, "/app")
from shared.utils.mqtt_client import MQTTClient
from stt import STTEngine
from tts import TTSEngine

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("voice_service")

def main():
    mqtt = MQTTClient(os.getenv("MQTT_HOST","localhost"),int(os.getenv("MQTT_PORT","1883")),"voice_service")
    mqtt.connect()
    tts = TTSEngine()
    stt = STTEngine(os.getenv("WHISPER_MODEL","small"), "fi")
    def on_tts(t,p):
        try: tts.speak(json.loads(p).get("text",""))
        except Exception as e: logger.error("TTS handler: %s",e)
    mqtt.subscribe("ha/tts/speak", on_tts)
    mode = os.getenv("LISTEN_MODE","always")
    logger.info("voice_service ready mode=%s", mode)
    if mode=="always":
        logger.warning("Always-listening: all audio (incl. TV) sent to Whisper")
        while True:
            text = stt.listen_once(timeout=30)
            if text and len(text)>2:
                logger.info("Heard: %s", text)
                mqtt.publish("ha/voice/command", json.dumps({"text":text.lower()}))
    else:
        threading.Event().wait()

if __name__=="__main__": main()
