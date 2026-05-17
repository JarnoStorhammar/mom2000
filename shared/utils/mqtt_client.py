"""Shared MQTT client with auto-reconnect."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        client_id: str = "ha_client",
    ) -> None:
        self.host = host
        self.port = port
        self._client = mqtt.Client(client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._subscriptions: list[tuple[str, Callable]] = []

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected to %s:%s", self.host, self.port)
            for topic, _ in self._subscriptions:
                client.subscribe(topic)
        else:
            logger.error("MQTT connect failed rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc):
        logger.warning("MQTT disconnected rc=%s", rc)

    def subscribe(self, topic: str, callback: Callable) -> None:
        def wrapper(client, userdata, msg):
            try:
                callback(msg.topic, msg.payload.decode("utf-8"))
            except Exception as e:
                logger.exception("MQTT callback error on %s: %s", msg.topic, e)

        self._subscriptions.append((topic, callback))
        self._client.subscribe(topic)
        self._client.message_callback_add(topic, wrapper)

    def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        self._client.publish(topic, payload, retain=retain)

    def connect(self) -> None:
        while True:
            try:
                self._client.connect(self.host, self.port, keepalive=60)
                self._client.loop_start()
                return
            except Exception as e:
                logger.warning("MQTT connect failed (%s), retry in 5s", e)
                time.sleep(5)

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
