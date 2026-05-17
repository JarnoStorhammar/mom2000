#!/usr/bin/env bash
# Bootstrap: check deps, set up dirs, download models, build containers
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠ $*${NC}"; }
fail() { echo -e "${RED}✗ $*${NC}"; exit 1; }

echo -e "${GREEN}=== Home Assistant MVP Bootstrap ===${NC}"
echo ""

# 1. Required tools
for cmd in docker python3 pip3 curl pactl; do
  command -v "$cmd" &>/dev/null && ok "$cmd found" || fail "Missing: $cmd – install it first"
done

# 2. Directory structure
mkdir -p shared/models shared/embeddings shared/models/piper config
ok "Directory structure created"

# 3. .env
if [ ! -f .env ]; then
  cp .env.example .env
  warn "Created .env from .env.example – EDIT IT before starting!"
else
  ok ".env exists"
fi

# 4. Bluetooth sink hint
echo ""
echo "Available PulseAudio sinks (your BT speaker should be listed):"
pactl list sinks short 2>/dev/null || warn "PulseAudio not available yet"
echo ""
warn "Copy BT sink name → set AUDIO_OUTPUT_SINK in .env"

# 5. Download ML models (requires ultralytics + curl)
echo ""
echo "==> Downloading ML models..."
pip3 install -q ultralytics 2>/dev/null || true
bash scripts/download_models.sh
ok "ML models downloaded"

# 6. Build Docker images
echo ""
echo "==> Building Docker images (first run takes 10-20 min)..."
docker compose build
ok "Docker images built"

echo ""
echo -e "${GREEN}=== Bootstrap complete! ===${NC}"
echo ""
echo "Next steps:"
echo "  1.  Edit .env  (AUDIO_OUTPUT_SINK, camera settings)"
echo "  2.  Enroll faces:  python3 scripts/enroll_face.py --name 'Jarno' --webcam"
echo "  3.  Start:         docker compose up -d"
echo "  4.  Logs:          docker compose logs -f"
echo "  5.  Web UI:        http://localhost:8080"
echo ""
echo "Test scripts (run on host, not in container):"
echo "  python3 scripts/test_tts.py"
echo "  python3 scripts/test_camera.py"
