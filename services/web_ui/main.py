from __future__ import annotations
import asyncio, json, logging, os, sys
from typing import Any
import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
sys.path.insert(0,"/app")

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"))
logger=logging.getLogger("web_ui")
app=FastAPI(title="Kotiassistentti")
MQTT_HOST=os.getenv("MQTT_HOST","mqtt"); MQTT_PORT=int(os.getenv("MQTT_PORT","1883"))

state: dict[str,Any]={"persons_present":[],"dish_status":{},"last_face":None,"last_command":None}
ws_clients: list[WebSocket]=[]; _loop=None

def on_message(c,u,msg):
    t=msg.topic
    try: p=json.loads(msg.payload.decode())
    except: return
    if   t=="ha/presence/current": state["persons_present"]=p
    elif t=="ha/dish/status":      state["dish_status"]=p
    elif t=="ha/face/detected":    state["last_face"]=p
    elif t=="ha/voice/command":    state["last_command"]=p
    if _loop: asyncio.run_coroutine_threadsafe(broadcast(json.dumps(state)),_loop)

async def broadcast(msg):
    dead=[]
    for ws in ws_clients:
        try: await ws.send_text(msg)
        except: dead.append(ws)
    for ws in dead: ws_clients.remove(ws)

_m=mqtt.Client(client_id="web_ui"); _m.on_message=on_message

@app.on_event("startup")
async def startup():
    global _loop; _loop=asyncio.get_event_loop()
    _m.connect(MQTT_HOST,MQTT_PORT); 
    for t in ["ha/presence/current","ha/dish/status","ha/face/detected","ha/voice/command"]: _m.subscribe(t)
    _m.loop_start()

@app.websocket("/ws")
async def ws_ep(ws: WebSocket):
    await ws.accept(); ws_clients.append(ws)
    await ws.send_text(json.dumps(state))
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        if ws in ws_clients: ws_clients.remove(ws)

@app.get("/api/state")
async def get_state(): return state

@app.get("/")
async def index(): return HTMLResponse(open("/app/static/index.html").read())

if __name__=="__main__": uvicorn.run(app,host="0.0.0.0",port=8080)
