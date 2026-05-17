"""Automation service: subscribes to all events and runs rule engine."""
from __future__ import annotations

import logging
import os
import sys
import threading

import yaml

sys.path.insert(0, "/app/shared")

from rules import RuleEngine
from utils.mqtt_client import MQTTClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("automation_service")

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config/config.yaml")


def load_config() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("Config not found at %s, using defaults", CONFIG_PATH)
        return {}


def main() -> None:
    config = load_config()
    mqtt = MQTTClient(host=MQTT_HOST, port=MQTT_PORT, client_id="automation_service")
    mqtt.connect()

    engine = RuleEngine(mqtt_client=mqtt, config=config)

    mqtt.subscribe("ha/face/detected", engine.on_face_detected)
    mqtt.subscribe("ha/presence/current", engine.on_presence_update)
    mqtt.subscribe("ha/dish/alert", engine.on_dish_alert)
    mqtt.subscribe("ha/dish/status", engine.on_dish_status)
    mqtt.subscribe("ha/voice/command", engine.on_voice_command)

    logger.info("Automation service running")
    threading.Event().wait()


if __name__ == "__main__":
    main()
