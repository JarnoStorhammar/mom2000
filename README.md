# Home Assistant MVP – Paikallinen kotiassistentti

Täysin offline-toimiva kotiassistentti Dockerissa.  
Kasvojentunnistus · Astiavalvonta · Puheentunnistus · TTS · MQTT

## Arkkitehtuuri

```
Camera → face_service  → MQTT → automation_service → TTS (voice_service)
       → vision_service → MQTT ↗
Mic    → voice_service  → MQTT ↗
                               ↘ web_ui (http://localhost:8080)
```

## Pikaohje

```bash
# 1. Alusta
bash bootstrap.sh

# 2. Muokkaa .env (BT-sink, kamera)
nano .env

# 3. Rekisteröi kasvot
python3 scripts/enroll_face.py --name "Jarno" --webcam

# 4. Käynnistä
docker compose up -d

# 5. Seuraa lokeja
docker compose logs -f

# Web UI
open http://localhost:8080
```

## Rakenne

| Palvelu | Vastuu |
|---|---|
| `face_service` | USB/RTSP-kamera, dlib-kasvojentunnistus, MQTT |
| `vision_service` | YOLOv8n astiavalvonta, ROI, timer-logiikka |
| `voice_service` | faster-whisper STT + Piper TTS, BT-audio |
| `automation_service` | Sääntömoottori, nalkutuslogiikka, cooldown |
| `web_ui` | FastAPI + WebSocket live-dashboard |
| `mqtt` | Mosquitto event bus |

## MQTT-topicit

| Topic | Suunta | Payload |
|---|---|---|
| `ha/face/detected` | face_service → | `{"name","confidence","timestamp"}` |
| `ha/presence/current` | face_service → | `["Jarno"]` (retained) |
| `ha/dish/alert` | vision_service → | `{"items","minutes","timestamp"}` |
| `ha/dish/status` | vision_service → | `{"plate": 3.2, ...}` (retained) |
| `ha/voice/command` | voice_service → | `{"text": "laita valot päälle"}` |
| `ha/tts/speak` | → voice_service | `{"text": "Hei Jarno!"}` |
| `ha/light/control` | → ulkoinen | `{"action": "on"}` |

## Puhekäskyt (suomi)

| Käsky | Toiminto |
|---|---|
| "laita valot päälle" | `ha/light/control` on |
| "sammuta valot" | `ha/light/control` off |
| "mitä näkyy tiskipöydällä" | Kertoo havaitut astiat |
| "ketä paikalla on" | Kertoo tunnistetut henkilöt |

## Kasvojen rekisteröinti

```bash
# Webcam (interaktiivinen)
python3 scripts/enroll_face.py --name "Jarno" --webcam --count 10

# Olemassa olevista kuvista
python3 scripts/enroll_face.py --name "Jarno" --images ~/kuvat/jarno/

# Listaa rekisteröidyt
python3 scripts/enroll_face.py --list

# Poista henkilö
python3 scripts/enroll_face.py --remove "Jarno"
```

Ota kuvia **eri valaistuksissa** (päivänvalo + keinivalo + hämärä) parhaan tarkkuuden saamiseksi.

## Astiavalvonnan säätö

Muokkaa `.env`:
```
DISH_ROI=0.1,0.2,0.9,0.8          # x1,y1,x2,y2 (0-1, kuvan suhteelliset koordinaatit)
DISH_TIMEOUT_MINUTES=15            # kuinka kauan astia saa olla
DISH_COOLDOWN_MINUTES=30           # väli muistutusten välillä
QUIET_HOURS_START=22               # hiljainen alku
QUIET_HOURS_END=7                  # hiljainen loppu
```

## Rautasuositus

| | Laite | Muisti | Suorituskyky |
|---|---|---|---|
| Budjetti | Raspberry Pi 5 8GB | 8 GB | Whisper tiny, toimii |
| **Suositus** | Intel NUC N100/i3 | 16 GB | Whisper small, hyvä |
| Tehokas | AMD Ryzen mini-PC | 32 GB | Whisper medium, nopea |

## Laajennukset (Phase 5+)

- Wake word: lisää `openwakeword`, vaihda `LISTEN_MODE=wake_word`
- Home Assistant: yhdistä MQTT-sillaksi, ohjaa Zigbee-valoja
- GPU-kiihdytys: Ultralytics OpenVINO-export Intel iGPU:lle
- LLM-komennot: Ollama + llama3.2 parempi komentojen tulkinta
- Toinen kamera eteiseen: kasvojentunnistus kotiin tullessa

## Lisenssi

MIT
