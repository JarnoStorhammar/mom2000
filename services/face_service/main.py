"""Face service: reads camera, runs face recognition, publishes MQTT events."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime

import cv2

sys.path.insert(0, "/app")

from recognizer import FaceRecognizer
from shared.utils.camera import CameraSource
from shared.utils.mqtt_client import MQTTClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("face_service")

TOPIC_FACE_DETECTED = "ha/face/detected"
TOPIC_PERSONS_PRESENT = "ha/presence/current"


def main() -> None:
    mqtt = MQTTClient(
        host=os.getenv("MQTT_HOST", "mqtt"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        client_id="face_service",
    )
    mqtt.connect()
    logger.info("Face service starting")

    recognizer = FaceRecognizer(
        embeddings_path=os.getenv("EMBEDDINGS_PATH", "/app/embeddings"),
        confidence_threshold=float(os.getenv("FACE_CONFIDENCE_THRESHOLD", "0.55")),
    )
    camera = CameraSource(
        source=os.getenv("CAMERA_SOURCE", "webcam"),
        webcam_device=int(os.getenv("WEBCAM_DEVICE", "0")),
        rtsp_url=os.getenv("RTSP_URL", ""),
    )

    detection_interval = float(os.getenv("FACE_DETECTION_INTERVAL", "3.0"))
    last_detection = time.monotonic()
    present_names: set[str] = set()

    for frame_bgr in camera.frames(fps_limit=5):
        now = time.monotonic()
        if now - last_detection < detection_interval:
            continue
        last_detection = now

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = recognizer.recognize(frame_rgb)

        current_names: set[str] = set()
        for r in results:
            if r.name != "unknown":
                current_names.add(r.name)
            payload = json.dumps({
                "name": r.name,
                "confidence": round(r.confidence, 3),
                "timestamp": datetime.now().isoformat(),
            })
            mqtt.publish(TOPIC_FACE_DETECTED, payload)
            logger.info("Face: %s (%.2f)", r.name, r.confidence)

        if current_names != present_names:
            present_names = current_names
            mqtt.publish(
                TOPIC_PERSONS_PRESENT,
                json.dumps(sorted(present_names)),
                retain=True,
            )


if __name__ == "__main__":
    main()
