"""Unit tests for services/automation_service/rules.py"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "automation_service"))

from rules import RuleEngine

BASE_CFG = {
    "face": {"greeting_cooldown_minutes": 60},
    "reminders": {
        "greeting_named":   "Hei {name}!",
        "greeting_unknown": "Hei siellä!",
        "dishes_named":     "Hei {name}, astioita pöydällä {minutes} min.",
        "dishes_unknown":   "Astioita pöydällä {minutes} min.",
        "lights_on":        "Valot päälle.",
        "lights_off":       "Valot pois.",
        "dishes_query_response": "Näen: {items}.",
        "present_response": "Paikalla: {names}.",
        "present_empty":    "Ketään ei näy.",
        "unknown_command":  "En ymmärtänyt.",
    },
}


@pytest.fixture()
def engine(mock_mqtt):
    return RuleEngine(mqtt_client=mock_mqtt, config=BASE_CFG)


# ── Greeting ─────────────────────────────────────────────────────────────────

class TestGreeting:
    def test_greets_known_person(self, engine, mock_mqtt):
        engine.on_face_detected("ha/face/detected", json.dumps(
            {"name": "Jarno", "confidence": 0.85}
        ))
        texts = [json.loads(p)["text"] for _, p in mock_mqtt.published]
        assert any("Jarno" in t for t in texts)

    def test_no_greeting_below_threshold(self, engine, mock_mqtt):
        engine.on_face_detected("ha/face/detected", json.dumps(
            {"name": "Jarno", "confidence": 0.30}
        ))
        assert len(mock_mqtt.published) == 0

    def test_no_greeting_for_unknown(self, engine, mock_mqtt):
        engine.on_face_detected("ha/face/detected", json.dumps(
            {"name": "unknown", "confidence": 0.80}
        ))
        assert len(mock_mqtt.published) == 0

    def test_greeting_cooldown_prevents_repeat(self, engine, mock_mqtt):
        payload = json.dumps({"name": "Jarno", "confidence": 0.90})
        engine.on_face_detected("ha/face/detected", payload)
        engine.on_face_detected("ha/face/detected", payload)
        tts_calls = [p for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert len(tts_calls) == 1

    def test_greeting_fires_again_after_cooldown(self, engine, mock_mqtt):
        payload = json.dumps({"name": "Jarno", "confidence": 0.90})
        engine.on_face_detected("ha/face/detected", payload)
        # Expire the cooldown manually
        engine._greeting_cooldowns["Jarno"] = time.monotonic() - 3700
        mock_mqtt.published.clear()
        engine.on_face_detected("ha/face/detected", payload)
        tts_calls = [p for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert len(tts_calls) == 1

    def test_malformed_face_payload_does_not_raise(self, engine):
        engine.on_face_detected("ha/face/detected", "NOT_JSON")  # must not raise


# ── Dish alerts ───────────────────────────────────────────────────────────────

class TestDishAlerts:
    def test_dish_alert_named_when_person_present(self, engine, mock_mqtt):
        engine.on_presence_update("ha/presence/current", json.dumps(["Jarno"]))
        engine.on_dish_alert("ha/dish/alert", json.dumps(
            {"items": ["plate", "cup"], "minutes": 18}
        ))
        texts = [json.loads(p)["text"] for _, p in mock_mqtt.published if _ == "ha/tts/speak"]
        assert any("Jarno" in t for t in texts)
        assert any("18" in t for t in texts)

    def test_dish_alert_neutral_when_no_person(self, engine, mock_mqtt):
        engine.on_dish_alert("ha/dish/alert", json.dumps(
            {"items": ["bowl"], "minutes": 20}
        ))
        texts = [json.loads(p)["text"] for _, p in mock_mqtt.published if _ == "ha/tts/speak"]
        assert texts
        assert all("Jarno" not in t for t in texts)

    def test_malformed_dish_payload_does_not_raise(self, engine):
        engine.on_dish_alert("ha/dish/alert", "BAD")


# ── Presence ─────────────────────────────────────────────────────────────────

class TestPresence:
    def test_presence_updated(self, engine):
        engine.on_presence_update("ha/presence/current", json.dumps(["Jarno", "Testi"]))
        assert engine._persons == ["Jarno", "Testi"]

    def test_presence_cleared(self, engine):
        engine.on_presence_update("ha/presence/current", json.dumps(["Jarno"]))
        engine.on_presence_update("ha/presence/current", json.dumps([]))
        assert engine._persons == []

    def test_primary_person_returns_first(self, engine):
        engine._persons = ["Jarno", "Testi"]
        assert engine._primary() == "Jarno"

    def test_primary_person_none_when_empty(self, engine):
        engine._persons = []
        assert engine._primary() is None


# ── Voice commands ────────────────────────────────────────────────────────────

class TestVoiceCommands:
    def _cmd(self, engine, text: str):
        engine.on_voice_command("ha/voice/command", json.dumps({"text": text}))

    def test_lights_on_command(self, engine, mock_mqtt):
        self._cmd(engine, "laita valot päälle")
        topics = [t for t, _ in mock_mqtt.published]
        assert "ha/light/control" in topics
        payloads = [json.loads(p) for t, p in mock_mqtt.published if t == "ha/light/control"]
        assert any(p["action"] == "on" for p in payloads)

    def test_lights_off_command(self, engine, mock_mqtt):
        self._cmd(engine, "sammuta valot")
        payloads = [json.loads(p) for t, p in mock_mqtt.published if t == "ha/light/control"]
        assert any(p["action"] == "off" for p in payloads)

    def test_dish_query_with_status(self, engine, mock_mqtt):
        engine.on_dish_status("ha/dish/status", json.dumps({"cup": 5.0, "plate": 12.0}))
        self._cmd(engine, "mitä näkyy tiskipöydällä")
        texts = [json.loads(p)["text"] for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert texts

    def test_dish_query_empty(self, engine, mock_mqtt):
        self._cmd(engine, "mitä tiskipöydällä on")
        texts = [json.loads(p)["text"] for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert texts  # some response expected

    def test_who_is_present_with_persons(self, engine, mock_mqtt):
        engine._persons = ["Jarno"]
        self._cmd(engine, "ketä paikalla on")
        texts = [json.loads(p)["text"] for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert any("Jarno" in t for t in texts)

    def test_who_is_present_empty(self, engine, mock_mqtt):
        engine._persons = []
        self._cmd(engine, "ketä paikalla on")
        texts = [json.loads(p)["text"] for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert texts

    def test_unknown_command_responds(self, engine, mock_mqtt):
        self._cmd(engine, "kerro vitsi")
        texts = [json.loads(p)["text"] for t, p in mock_mqtt.published if t == "ha/tts/speak"]
        assert texts

    def test_malformed_command_payload(self, engine):
        engine.on_voice_command("ha/voice/command", "NOT_JSON")
