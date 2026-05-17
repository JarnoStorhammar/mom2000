from __future__ import annotations
import json, logging, os, sys, time
from datetime import datetime
import cv2
sys.path.insert(0, "/app")
from shared.utils.camera import CameraSource
from shared.utils.mqtt_client import MQTTClient
from recognizer import FaceRecognizer

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("face_service")

def main():
    mqtt = MQTTClient(os.getenv("MQTT_HOST","mqtt"), int(os.getenv("MQTT_PORT","1883")), "face_service")
    mqtt.connect()
    rec = FaceRecognizer(os.getenv("EMBEDDINGS_PATH","/app/shared/embeddings"),
                         float(os.getenv("FACE_CONFIDENCE_THRESHOLD","0.55")))
    cam = CameraSource(os.getenv("CAMERA_SOURCE","webcam"),
                       int(os.getenv("WEBCAM_DEVICE","0")),
                       os.getenv("RTSP_URL",""))
    interval = float(os.getenv("FACE_DETECTION_INTERVAL","3.0"))
    last = 0.0; present: set[str] = set()
    logger.info("face_service started")
    for bgr in cam.frames(fps_limit=5):
        now = time.monotonic()
        if now - last < interval: continue
        last = now
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        current: set[str] = set()
        for r in rec.recognize(rgb):
            if r.name != "unknown": current.add(r.name)
            mqtt.publish("ha/face/detected", json.dumps({
                "name": r.name, "confidence": round(r.confidence,3),
                "timestamp": datetime.now().isoformat()}))
            logger.info("Face: %s %.2f", r.name, r.confidence)
        if current != present:
            present = current
            mqtt.publish("ha/presence/current", json.dumps(sorted(present)), retain=True)

if __name__ == "__main__": main()
