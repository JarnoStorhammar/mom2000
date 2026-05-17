"""Vision service: dish monitoring via YOLO, publishes MQTT alerts."""
from __future__ import annotations

import json
import logging
import os
import sys

sys.path.insert(0, "/app")

from dish_monitor import DishMonitor
from shared.utils.camera import CameraSource
from shared.utils.mqtt_client import MQTTClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("vision_service")

TOPIC_DISH_ALERT = "ha/dish/alert"
TOPIC_DISH_STATUS = "ha/dish/status"


def _parse_roi() -> tuple[float, float, float, float]:
    raw = os.getenv("DISH_ROI", "0.1,0.2,0.9,0.8")
    parts = [float(x) for x in raw.split(",")]
    return (parts[0], parts[1], parts[2], parts[3])


def main() -> None:
    mqtt = MQTTClient(
        host=os.getenv("MQTT_HOST", "mqtt"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        client_id="vision_service",
    )
    mqtt.connect()

    monitor = DishMonitor(
        model_path="/app/models/yolov8n.pt",
        roi=_parse_roi(),
        timeout_minutes=float(os.getenv("DISH_TIMEOUT_MINUTES", "15")),
        cooldown_minutes=float(os.getenv("DISH_COOLDOWN_MINUTES", "30")),
        quiet_start=int(os.getenv("QUIET_HOURS_START", "22")),
        quiet_end=int(os.getenv("QUIET_HOURS_END", "7")),
    )
    camera = CameraSource(
        source=os.getenv("CAMERA_SOURCE", "webcam"),
        webcam_device=int(os.getenv("WEBCAM_DEVICE", "0")),
        rtsp_url=os.getenv("RTSP_URL", ""),
    )

    logger.info("Vision service starting")
    frame_count = 0

    for frame in camera.frames(fps_limit=1):
        frame_count += 1
        alert = monitor.process_frame(frame)
        if alert:
            mqtt.publish(TOPIC_DISH_ALERT, json.dumps(alert))
        if frame_count % 60 == 0:
            mqtt.publish(TOPIC_DISH_STATUS, json.dumps(monitor.get_status()), retain=True)


if __name__ == "__main__":
    main()
