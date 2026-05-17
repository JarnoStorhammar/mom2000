from __future__ import annotations
import logging, os, sys, threading, yaml
sys.path.insert(0, "/app")
from shared.utils.mqtt_client import MQTTClient
from rules import RuleEngine

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger=logging.getLogger("automation_service")

def main():
    try:
        with open(os.getenv("CONFIG_PATH","/app/config/config.yaml")) as f: cfg=yaml.safe_load(f) or {}
    except FileNotFoundError: cfg={}
    mqtt=MQTTClient(os.getenv("MQTT_HOST","mqtt"),int(os.getenv("MQTT_PORT","1883")),"automation_service")
    mqtt.connect()
    eng=RuleEngine(mqtt,cfg)
    mqtt.subscribe("ha/face/detected",    eng.on_face_detected)
    mqtt.subscribe("ha/presence/current", eng.on_presence_update)
    mqtt.subscribe("ha/dish/alert",       eng.on_dish_alert)
    mqtt.subscribe("ha/dish/status",      eng.on_dish_status)
    mqtt.subscribe("ha/voice/command",    eng.on_voice_command)
    logger.info("automation_service running"); threading.Event().wait()

if __name__=="__main__": main()
