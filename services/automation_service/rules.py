"""Rule engine: reacts to MQTT events and produces TTS/action responses."""
from __future__ import annotations

import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, mqtt_client, config: dict) -> None:
        self.mqtt = mqtt_client
        self.cfg = config
        self.reminders = config.get("reminders", {})

        self._persons: list[str] = []
        self._greeting_cooldowns: dict[str, float] = {}
        self._dish_status: dict[str, float] = {}
        self._greeting_cooldown_s = (
            float(config.get("face", {}).get("greeting_cooldown_minutes", 60)) * 60
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _speak(self, text: str) -> None:
        self.mqtt.publish("ha/tts/speak", json.dumps({"text": text}))

    def _primary(self) -> Optional[str]:
        return self._persons[0] if self._persons else None

    def _fmt(self, template: str, **kwargs) -> str:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    # ── Event handlers ────────────────────────────────────────────────────────

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
            text = self._fmt(
                self.reminders.get("greeting_named", "Hei {name}!"),
                name=name,
            )
            self._speak(text)
            logger.info("Greeted: %s", name)

    def on_presence_update(self, topic: str, payload: str) -> None:
        try:
            self._persons = json.loads(payload)
        except json.JSONDecodeError:
            self._persons = []

    def on_dish_alert(self, topic: str, payload: str) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        items = data.get("items", [])
        minutes = data.get("minutes", 0)
        person = self._primary()

        if person:
            text = self._fmt(
                self.reminders.get(
                    "dishes_named",
                    "Hei {name}, astioita pöydällä {minutes} min.",
                ),
                name=person,
                minutes=int(minutes),
            )
        else:
            text = self._fmt(
                self.reminders.get(
                    "dishes_unknown",
                    "Astioita pöydällä {minutes} min.",
                ),
                minutes=int(minutes),
            )
        self._speak(text)
        logger.info("Dish reminder sent: %s", items)

    def on_voice_command(self, topic: str, payload: str) -> None:
        try:
            data = json.loads(payload)
            text = data.get("text", "").lower().strip()
        except json.JSONDecodeError:
            return

        logger.info("Command received: %s", text)

        if any(w in text for w in ["valot päälle", "laita valot"]):
            self._speak(self.reminders.get("lights_on", "Laitan valot päälle."))
            self.mqtt.publish("ha/light/control", json.dumps({"action": "on"}))

        elif any(w in text for w in ["sammuta valot", "valot pois"]):
            self._speak(self.reminders.get("lights_off", "Sammutin valot."))
            self.mqtt.publish("ha/light/control", json.dumps({"action": "off"}))

        elif any(w in text for w in ["tiskipöydällä", "astioita", "tiskit"]):
            if self._dish_status:
                items_fi = ", ".join(self._dish_status.keys())
                resp = self._fmt(
                    self.reminders.get("dishes_query_response", "Näen: {items}."),
                    items=items_fi,
                )
            else:
                resp = "Tiskipöytä näyttää tyhjältä."
            self._speak(resp)

        elif any(w in text for w in ["ketä", "kuka", "paikalla"]):
            if self._persons:
                names = ", ".join(self._persons)
                resp = self._fmt(
                    self.reminders.get("present_response", "Paikalla on: {names}."),
                    names=names,
                )
            else:
                resp = self.reminders.get("present_empty", "Ketään ei näy.")
            self._speak(resp)

        else:
            self._speak(self.reminders.get("unknown_command", "En ymmärtänyt komentoa."))

    def on_dish_status(self, topic: str, payload: str) -> None:
        try:
            self._dish_status = json.loads(payload)
        except json.JSONDecodeError:
            pass
