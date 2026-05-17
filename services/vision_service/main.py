from __future__ import annotations
import json, logging, os, sys
sys.path.insert(0, "/app")
from shared.utils.camera import CameraSource
from shared.utils.mqtt_client import MQTTClient
from dish_monitor import DishMonitor

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("vision_service")

def parse_roi():
    return tuple(float(x) for x in os.getenv("DISH_ROI","0.1,0.2,0.9,0.8").split(","))

def main():
    mqtt = MQTTClient(os.getenv("MQTT_HOST","mqtt"),int(os.getenv("MQTT_PORT","1883")),"vision_service")
    mqtt.connect()
    mon = DishMonitor("/app/shared/models/yolov8n.pt", parse_roi(),
        float(os.getenv("DISH_TIMEOUT_MINUTES","15")),
        float(os.getenv("DISH_COOLDOWN_MINUTES","30")),
        int(os.getenv("QUIET_HOURS_START","22")),
        int(os.getenv("QUIET_HOURS_END","7")))
    cam = CameraSource(os.getenv("CAMERA_SOURCE","webcam"),
        int(os.getenv("WEBCAM_DEVICE","0")), os.getenv("RTSP_URL",""))
    n=0; logger.info("vision_service started")
    for frame in cam.frames(fps_limit=1):
        n+=1
        a = mon.process_frame(frame)
        if a: mqtt.publish("ha/dish/alert", json.dumps(a))
        if n%60==0: mqtt.publish("ha/dish/status", json.dumps(mon.get_status()), retain=True)

if __name__=="__main__": main()
