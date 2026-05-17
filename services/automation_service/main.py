"""Automation service: subscribes to all MQTT events and runs rule engine."""
from __future__ import annotations

import logging
import os
import sys
import threading

import yaml

sys.path.insert(0, "/app")

from rules import RuleEngine
from shared.utils.mqtt_client import MQTTClient

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("automation_service")


def load_config() -> dict:
    path = os.getenv("CONFIG_PATH", "/app/config/config.yaml")
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("Config not found at %s, using defaults", path)
        return {}


def main() -> None:
    config = load_config()
    mqtt = MQTTClient(
        host=os.getenv("MQTT_HOST", "mqtt"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        client_id="automation_service",
    )
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
