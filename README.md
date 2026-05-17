# 🏠 Home Assistant MVP

Offline-toimiva kotiassistentti — kasvojentunnistus, puhekomennot,
astiavalvonta ja Bluetooth-kaiutin. Ei pilvipalveluita, ei maksullisia APIeja.

**Stack:** Python 3.11 · Docker Compose · MQTT · face-recognition (dlib) · YOLOv8n · faster-whisper · Piper TTS

---

## Esivalmistelut (host-koneella)

### 1. Docker + PulseAudio + Bluetooth

\`\`\`bash
sudo apt install docker.io docker-compose-plugin
sudo apt install pulseaudio pulseaudio-module-bluetooth
sudo usermod -aG docker $USER
\`\`\`

### 2. Parinna Bluetooth-kaiutin

\`\`\`bash
bluetoothctl
> scan on
> connect XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> exit

# Etsi sink-nimi → kopioi .env:iin AUDIO_OUTPUT_SINK-kohtaan
pactl list sinks short
\`\`\`

---

## Asennus

### 3. Kloonaa ja konfiguroi

\`\`\`bash
git clone https://github.com/YOUR/home-assistant-mvp.git
cd home-assistant-mvp
cp .env.example .env
nano .env
\`\`\`

Tärkeimmät .env-asetukset:

| Asetus | Esimerkki | Selitys |
|---|---|---|
| `AUDIO_OUTPUT_SINK` | `bluez_sink.XX_XX.a2dp_sink` | BT-kaiuttimen PA-sink |
| `CAMERA_SOURCE` | `webcam` tai `rtsp` | Kameran tyyppi |
| `RTSP_URL` | `rtsp://admin:pass@192.168.1.100:554/stream` | IP-kamera URL |
| `WHISPER_MODEL` | `small` | tiny/base/small/medium |
| `DISH_ROI` | `0.1,0.2,0.9,0.8` | Valvonta-alue kuvasta |
| `DISH_TIMEOUT_MINUTES` | `15` | Minuuttia ennen muistutusta |
| `QUIET_HOURS_START` | `22` | Hiljainen tila alkaa |
| `QUIET_HOURS_END` | `7` | Hiljainen tila päättyy |

### 4. Bootstrap (lataa mallit + buildaa Docker-kuvat)

\`\`\`bash
bash bootstrap.sh
\`\`\`

> ⚠️ Ensimmäinen build kestää 15–20 min — dlib käännetään lähdekoodista.

### 5. Rekisteröi kasvot

\`\`\`bash
# Interaktiivinen webkam-tallennus (ota kuvia eri valaistuksissa!)
python3 scripts/enroll_face.py --name "Jarno" --webcam --count 10

# Tai valmiista kuvista
python3 scripts/enroll_face.py --name "Jarno" --images ~/kuvat/jarno/

# Tarkista rekisteröidyt henkilöt
python3 scripts/enroll_face.py --list
\`\`\`

### 6. Käynnistä

\`\`\`bash
docker compose up -d
docker compose logs -f
# Dashboard: http://localhost:8080
\`\`\`

---

## Testaus

\`\`\`bash
# Kameratesti
docker exec ha_face python3 -c "
import cv2; c=cv2.VideoCapture(0); r,f=c.read()
print('OK' if r else 'FAIL', f.shape if r else '')
"

# TTS-testi (pitäisi kuulua BT-kaiuttimesta)
mosquitto_pub -h localhost -t ha/tts/speak \
  -m '{"text":"Hei Jarno, testi toimii."}'

# Seuraa kaikkia MQTT-tapahtumia
docker exec ha_mqtt mosquitto_sub -h localhost -t 'ha/#' -v

# Rakenna yksittäinen palvelu uudelleen
docker compose build face_service && docker compose up -d face_service
\`\`\`

---

## Puhekäskyt

| Sano | Toiminto |
|---|---|
| "laita valot päälle" | Julkaisee `ha/light/control {"action":"on"}` |
| "sammuta valot" | Julkaisee `ha/light/control {"action":"off"}` |
| "mitä näkyy tiskipöydällä" | Puhuttu vastaus astioista |
| "ketä paikalla on" | Puhuttu vastaus läsnäolijoista |

---

## Vianmääritys

**BT-kaiutin ei kuulu:**
\`\`\`bash
pactl list sinks short          # tarkista sink-nimi
# Päivitä AUDIO_OUTPUT_SINK .env:iin
docker compose restart voice_service
\`\`\`

**Kasvoja ei tunnisteta:**
\`\`\`bash
# Laske kynnystä tai rekisteröi lisää kuvia
FACE_CONFIDENCE_THRESHOLD=0.45
python3 scripts/enroll_face.py --name "Jarno" --webcam --count 5
\`\`\`

**YOLO-malli puuttuu:**
\`\`\`bash
bash scripts/download_models.sh
docker compose restart vision_service
\`\`\`

---

## Jatkokehitys

- Wake word (`openwakeword`)
- Home Assistant MQTT-silta Zigbee-valoille
- Intel OpenVINO-export ~3× nopeampi YOLO iGPU:lla
- IR-kamera pimeän kasvojentunnistukseen
- Ollama + llama3.2 älykkäämpään komennontulkintaan
