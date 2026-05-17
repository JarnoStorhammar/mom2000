"""Unit tests for shared/utils/mqtt_client.py"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from utils.mqtt_client import MQTTClient


@pytest.fixture()
def mock_paho():
    with patch("utils.mqtt_client.mqtt.Client") as MockClient:
        yield MockClient


class TestMQTTClient:
    def test_publish_calls_paho(self, mock_paho):
        client = MQTTClient(host="localhost", port=1883)
        client._client = MagicMock()
        client.publish("ha/test", "hello")
        client._client.publish.assert_called_once_with("ha/test", "hello", retain=False)

    def test_publish_with_retain(self, mock_paho):
        client = MQTTClient()
        client._client = MagicMock()
        client.publish("ha/presence/current", "[]", retain=True)
        client._client.publish.assert_called_once_with(
            "ha/presence/current", "[]", retain=True
        )

    def test_subscribe_stores_subscription(self, mock_paho):
        client = MQTTClient()
        client._client = MagicMock()
        cb = MagicMock()
        client.subscribe("ha/topic", cb)
        assert any(t == "ha/topic" for t, _ in client._subscriptions)

    def test_on_connect_resubscribes(self, mock_paho):
        client = MQTTClient()
        client._client = MagicMock()
        cb = MagicMock()
        client._subscriptions = [("ha/topic1", cb), ("ha/topic2", cb)]
        client._on_connect(client._client, None, None, rc=0)
        calls = [c[0][0] for c in client._client.subscribe.call_args_list]
        assert "ha/topic1" in calls
        assert "ha/topic2" in calls

    def test_on_connect_failed_logs_error(self, mock_paho, caplog):
        import logging
        client = MQTTClient()
        client._client = MagicMock()
        with caplog.at_level(logging.ERROR):
            client._on_connect(client._client, None, None, rc=5)
        assert any("failed" in r.message.lower() for r in caplog.records)
