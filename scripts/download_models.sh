#!/usr/bin/env bash
# Download YOLOv8n and Piper Finnish TTS voice model
set -euo pipefail

MODELS_DIR="shared/models"
PIPER_DIR="$MODELS_DIR/piper"
mkdir -p "$MODELS_DIR" "$PIPER_DIR"

echo "==> YOLOv8n (COCO object detection)..."
python3 -c "
from ultralytics import YOLO
import shutil, pathlib
YOLO('yolov8n.pt')  # downloads to CWD or ~/.cache
import glob, os
hits = glob.glob('yolov8n.pt') + glob.glob(str(pathlib.Path.home() / '.cache/ultralytics/yolov8n.pt'))
if hits:
    shutil.copy(hits[0], 'shared/models/yolov8n.pt')
    print('  YOLOv8n → shared/models/yolov8n.pt')
"

echo "==> Piper Finnish voice (fi_FI-harri-medium)..."
VOICE="fi_FI-harri-medium"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fi/fi_FI/harri/medium"
curl -fL -o "$PIPER_DIR/${VOICE}.onnx"      "${BASE}/${VOICE}.onnx"
curl -fL -o "$PIPER_DIR/${VOICE}.onnx.json" "${BASE}/${VOICE}.onnx.json"
echo "  Piper → $PIPER_DIR/"

echo ""
echo "✓ Models ready:"
echo "  $MODELS_DIR/yolov8n.pt"
echo "  $PIPER_DIR/${VOICE}.onnx"
