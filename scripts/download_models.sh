#!/usr/bin/env bash
set -e
MODELS="shared/models"; PIPER="$MODELS/piper"; mkdir -p "$MODELS" "$PIPER"
echo "==> YOLOv8n..."
python3 -c "
from ultralytics import YOLO; import shutil,os
YOLO('yolov8n.pt')
if os.path.exists('yolov8n.pt'): shutil.move('yolov8n.pt','shared/models/yolov8n.pt')
print('yolov8n.pt ready')
"
echo "==> Piper fi_FI-harri-medium..."
V="fi_FI-harri-medium"
B="https://huggingface.co/rhasspy/piper-voices/resolve/main/fi/fi_FI/harri/medium"
curl -L --progress-bar -o "$PIPER/$V.onnx"      "$B/$V.onnx"
curl -L --progress-bar -o "$PIPER/$V.onnx.json" "$B/$V.onnx.json"
echo "Done. Models at shared/models/"
