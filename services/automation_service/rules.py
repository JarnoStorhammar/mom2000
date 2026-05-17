"""Rule engine: reacts to MQTT events, produces TTS/action responses."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, mqtt_client, config: dict) -> None:
        self.mqtt = mqtt_client
        self.cfg = config
        self.reminders = config.get("reminders", {})
        self._persons_present: list[str] = []
        self._greeting_cooldowns: dict[str, float] = {}
        self._dish_status: dict[str, float] = {}
        self._greeting_cooldown_s = float(
            config.get("face", {}).get("greeting_cooldown_minutes", 60)
        ) * 60

    def _speak(self, text: str) -> None:
        self.mqtt.publish("ha/tts/speak", json.dumps({"text": text}))

    def _fmt(self, key: str, fallback: str, **kwargs) -> str:
        try:
            return self.reminders.get(key, fallback).format(**kwargs)
        except KeyError:
            return self.reminders.get(key, fallback)

    def on_face_detected(self, topic: str, payload: str) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        name = data.get("name", "unknown")
        confidence = float(data.get("confidence", 0))
        if name == "unknown" or confidence < 0.55:
            return
        last = self._greeting_cooldowns.get(name, 0.0)
        if time.monotonic() - last > self._greeting_cooldown_s:
            self._greeting_cooldowns[name] = time.monotonic()
            self._speak(self._fmt("greeting_named", "Hei {name}!", name=name))
            logger.info("Greeted: %s", name)

    def on_presence_update(self, topic: str, payload: str) -> None:
        try:
            self._persons_present = json.loads(payload)
        except json.JSONDecodeError:
            self._persons_present = []

    def on_dish_alert(self, topic: str, payload: str) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        minutes = data.get("minutes", 0)
        person = self._persons_present[0] if self._persons_present else None
        if person:
            text = self._fmt(
                "dishes_named",
                "Hei {name}, tiskipöydällä on ollut astioita jo {minutes} minuuttia.",
                name=person,
                minutes=int(minutes),
            )
        else:
            text = self._fmt(
                "dishes_unknown",
                "Tiskipöydällä on ollut astioita jo {minutes} minuuttia.",
                minutes=int(minutes),
            )
        self._speak(text)
        logger.info("Dish reminder sent, minutes=%.1f", minutes)

    def on_voice_command(self, topic: str, payload: str) -> None:
        try:
            text = json.loads(payload).get("text", "").lower().strip()
        except json.JSONDecodeError:
            return
        logger.info("Command: %s", text)

        if any(w in text for w in ["valot päälle", "laita valot"]):
            self._speak(self._fmt("lights_on", "Laitan valot päälle."))
            self.mqtt.publish("ha/light/control", json.dumps({"action": "on"}))

        elif any(w in text for w in ["sammuta valot", "valot pois"]):
            self._speak(self._fmt("lights_off", "Sammutin valot."))
            self.mqtt.publish("ha/light/control", json.dumps({"action": "off"}))

        elif any(w in text for w in ["tiskipöydällä", "astioita", "tiskit"]):
            if self._dish_status:
                items = ", ".join(self._dish_status.keys())
                self._speak(self._fmt("dishes_query_response", "Näen: {items}.", items=items))
            else:
                self._speak("Tiskipöytä näyttää tyhjältä.")

        elif any(w in text for w in ["ketä", "kuka", "paikalla"]):
            if self._persons_present:
                names = ", ".join(self._persons_present)
                self._speak(self._fmt("present_response", "Paikalla on: {names}.", names=names))
            else:
                self._speak(self._fmt("present_empty", "Ketään ei näy."))

        else:
            self._speak(self._fmt("unknown_command", "En ymmärtänyt komentoa."))

    def on_dish_status(self, topic: str, payload: str) -> None:
        try:
            self._dish_status = json.loads(payload)
        except json.JSONDecodeError:
            pass
