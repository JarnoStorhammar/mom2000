"""Voice service: always-listening STT + TTS output subscriber."""
from __future__ import annotations

import json
import logging
import os
import sys
import threading

sys.path.insert(0, "/app")

from shared.utils.mqtt_client import MQTTClient
from stt import STTEngine
from tts import TTSEngine

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("voice_service")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
LISTEN_MODE = os.getenv("LISTEN_MODE", "always")
TOPIC_VOICE_COMMAND = "ha/voice/command"
TOPIC_TTS_SPEAK = "ha/tts/speak"


def main() -> None:
    mqtt = MQTTClient(host=MQTT_HOST, port=MQTT_PORT, client_id="voice_service")
    mqtt.connect()
    tts = TTSEngine()
    stt = STTEngine(model_size=os.getenv("WHISPER_MODEL", "small"), language="fi")

    def on_tts_message(topic: str, payload: str) -> None:
        try:
            data = json.loads(payload)
            text = data.get("text", "")
            if text:
                tts.speak(text)
        except Exception as e:
            logger.error("TTS message error: %s", e)

    mqtt.subscribe(TOPIC_TTS_SPEAK, on_tts_message)
    logger.info("Voice service ready, listen_mode=%s", LISTEN_MODE)

    if LISTEN_MODE == "always":
        _always_listen(stt, mqtt)
    else:
        logger.info("Push-to-talk mode: awaiting external trigger")
        threading.Event().wait()


def _always_listen(stt: STTEngine, mqtt: MQTTClient) -> None:
    logger.warning("Always-listening: all audio goes to Whisper. Consider wake_word mode for privacy.")
    while True:
        text = stt.listen_once(timeout=30)
        if text and len(text) > 2:
            logger.info("Heard: %s", text)
            mqtt.publish(TOPIC_VOICE_COMMAND, json.dumps({"text": text.lower()}))


if __name__ == "__main__":
    main()
