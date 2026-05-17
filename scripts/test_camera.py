"""Display camera feed with face detection boxes. Press Q to quit."""
from __future__ import annotations
import sys
sys.path.insert(0, "services/face_service")
sys.path.insert(0, ".")

import cv2
from shared.utils.camera import CameraSource
from recognizer import FaceRecognizer

cam = CameraSource(source="webcam", webcam_device=0)
rec = FaceRecognizer(embeddings_path="shared/embeddings")
cam.open()
print("Press Q to quit")

try:
    while True:
        frame = cam.read_frame()
        if frame is None:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = rec.recognize(rgb)
        for r in results:
            top, right, bottom, left = r.location
            color = (50, 220, 80) if r.name != "unknown" else (80, 80, 220)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label = f"{r.name} {r.confidence:.2f}"
            cv2.putText(frame, label, (left, top - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.imshow("Camera test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cam.close()
    cv2.destroyAllWindows()
