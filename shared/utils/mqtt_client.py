"""MQTT client with auto-reconnect."""
from __future__ import annotations
import logging, time
from typing import Callable
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, host="localhost", port=1883, client_id="ha"):
        self.host, self.port = host, port
        self._c = mqtt.Client(client_id=client_id)
        self._c.on_connect = self._on_connect
        self._c.on_disconnect = self._on_disconnect
        self._subs: list[tuple[str, Callable]] = []

    def _on_connect(self, c, u, f, rc):
        if rc == 0:
            logger.info("MQTT connected %s:%s", self.host, self.port)
            for t, _ in self._subs: c.subscribe(t)
        else:
            logger.error("MQTT connect rc=%s", rc)

    def _on_disconnect(self, c, u, rc):
        logger.warning("MQTT disconnected rc=%s", rc)

    def subscribe(self, topic: str, cb: Callable):
        def wrap(client, u, msg):
            try: cb(msg.topic, msg.payload.decode())
            except Exception as e: logger.exception("cb error %s: %s", msg.topic, e)
        self._subs.append((topic, cb))
        self._c.subscribe(topic)
        self._c.message_callback_add(topic, wrap)

    def publish(self, topic: str, payload: str, retain=False):
        self._c.publish(topic, payload, retain=retain)

    def connect(self):
        while True:
            try: self._c.connect(self.host, self.port, 60); self._c.loop_start(); return
            except Exception as e: logger.warning("MQTT retry: %s", e); time.sleep(5)

    def disconnect(self):
        self._c.loop_stop(); self._c.disconnect()
