"""FastAPI web UI – live dashboard via WebSocket + MQTT bridge."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any

import paho.mqtt.client as mqtt
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

sys.path.insert(0, "/app")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("web_ui")

app = FastAPI(title="Home Assistant MVP")
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

state: dict[str, Any] = {
    "persons_present": [],
    "dish_status": {},
    "last_face": None,
    "last_command": None,
}
ws_clients: list[WebSocket] = []
_loop: asyncio.AbstractEventLoop | None = None
_mqtt = mqtt.Client(client_id="web_ui")


def _on_message(client, userdata, msg) -> None:
    global _loop
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    if topic == "ha/presence/current":
        state["persons_present"] = payload
    elif topic == "ha/dish/status":
        state["dish_status"] = payload
    elif topic == "ha/face/detected":
        state["last_face"] = payload
    elif topic == "ha/voice/command":
        state["last_command"] = payload

    if _loop:
        asyncio.run_coroutine_threadsafe(broadcast(json.dumps(state)), _loop)


async def broadcast(message: str) -> None:
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)


@app.on_event("startup")
async def startup() -> None:
    global _loop
    _loop = asyncio.get_event_loop()
    _mqtt.on_message = _on_message
    _mqtt.connect(MQTT_HOST, MQTT_PORT)
    for topic in ["ha/presence/current", "ha/dish/status", "ha/face/detected", "ha/voice/command"]:
        _mqtt.subscribe(topic)
    _mqtt.loop_start()
    logger.info("Web UI started on :8080")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    ws_clients.append(ws)
    await ws.send_text(json.dumps(state))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in ws_clients:
            ws_clients.remove(ws)


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(open("/app/static/index.html").read())


@app.get("/api/state")
async def get_state() -> dict:
    return state


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
