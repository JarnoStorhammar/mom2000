#!/usr/bin/env bash
set -e
G="\033[0;32m"; Y="\033[1;33m"; R="\033[0;31m"; N="\033[0m"
ok()  { echo -e "${G}✓ $*${N}"; }
warn(){ echo -e "${Y}⚠ $*${N}"; }
die() { echo -e "${R}✗ $*${N}"; exit 1; }

echo -e "${G}=== Home Assistant MVP Bootstrap ===${N}"
for cmd in docker pactl curl python3; do
  command -v "$cmd" &>/dev/null && ok "$cmd found" || die "Missing: $cmd"
done
docker compose version &>/dev/null || docker-compose version &>/dev/null || die "Docker Compose not found"

mkdir -p shared/models shared/embeddings config
ok "Directories ready"

if [ ! -f .env ]; then cp .env.example .env; warn "Created .env – edit AUDIO_OUTPUT_SINK!"; else ok ".env exists"; fi

echo -e "\nPulseAudio sinks (copy BT sink name → AUDIO_OUTPUT_SINK in .env):"
pactl list sinks short 2>/dev/null || echo "  (pactl unavailable – start PulseAudio)"

echo -e "\nDownloading ML models..."
bash scripts/download_models.sh

echo -e "\nBuilding Docker images (first build ~15-20 min)..."
docker compose build 2>/dev/null || docker-compose build

echo -e "\n${G}=== Done! ===${N}"
echo "  1. Edit .env            nano .env"
echo "  2. Enroll faces         python3 scripts/enroll_face.py --name 'Nimi' --webcam"
echo "  3. Start                docker compose up -d"
echo "  4. Logs                 docker compose logs -f"
echo "  5. Dashboard            http://localhost:8080"
