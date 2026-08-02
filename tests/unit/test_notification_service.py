import asyncio

import pytest

from src.infrastructure.external.notification_clients.base import NotificationClient
from src.infrastructure.external.notification_clients.pushplus_client import PushPlusClient
from src.infrastructure.external.notification_clients.webhook_client import WebhookClient
from src.services.notification_service import NotificationService


class _OkClient(NotificationClient):
    channel_key = "ok"
    display_name = "OK"

    async def send(self, product_data, reason):
        return None


class _FailClient(NotificationClient):
    channel_key = "fail"
    display_name = "FAIL"

    async def send(self, product_data, reason):
        raise RuntimeError("boom")


def test_notification_service_collects_success_and_failure_results():
    service = NotificationService([_OkClient(enabled=True), _FailClient(enabled=True)])

    results = asyncio.run(
        service.send_notification({"商品标题": "Sony A7M4"}, "价格合适")
    )

    assert results["ok"]["success"] is True
    assert results["ok"]["message"] == "发送成功"
    assert results["fail"]["success"] is False
    assert results["fail"]["message"] == "boom"


def test_webhook_client_renders_json_templates(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

    def _fake_post(url, headers=None, json=None, data=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["data"] = data
        return _FakeResponse()

    monkeypatch.setattr("requests.post", _fake_post)

    client = WebhookClient(
        webhook_url="https://hooks.example.com/notify",
        webhook_method="POST",
        webhook_headers='{"Authorization":"Bearer token"}',
        webhook_content_type="JSON",
        webhook_query_parameters='{"task":"{{title}}"}',
        webhook_body='{"message":"{{content}}","link":"{{desktop_link}}"}',
        pcurl_to_mobile=False,
    )

    asyncio.run(
        client.send(
            {
                "商品标题": "Sony A7M4",
                "当前售价": "9999",
                "商品链接": "https://www.goofish.com/item/123",
            },
            "价格合适",
        )
    )

    assert "task=%F0%9F%9A%A8+%E6%96%B0%E6%8E%A8%E8%8D%90%21+Sony+A7M4" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer token"
    assert captured["json"]["message"].startswith("价格: 9999")
    assert captured["json"]["link"] == "https://www.goofish.com/item/123"
    assert captured["data"] is None


class _FakePushPlusResponse:
    def __init__(self, code=200, msg="success"):
        self._code = code
        self._msg = msg

    def raise_for_status(self):
        return None

    def json(self):
        return {"code": self._code, "msg": self._msg}


def test_pushplus_client_rejects_business_error(monkeypatch):
    def _fake_post(url, json=None, timeout=None):
        return _FakePushPlusResponse(code=300, msg="token invalid")

    monkeypatch.setattr("requests.post", _fake_post)

    client = PushPlusClient(token="invalid-token")
    with pytest.raises(RuntimeError, match="token invalid"):
        asyncio.run(client.send({"商品标题": "Sony A7M4"}, "价格合适"))


def test_pushplus_client_accepts_success_response(monkeypatch):
    captured = {}

    def _fake_post(url, json=None, timeout=None):
        captured["payload"] = json
        return _FakePushPlusResponse(code=200, msg="success")

    monkeypatch.setattr("requests.post", _fake_post)

    client = PushPlusClient(token="valid-token", topic="group1")
    asyncio.run(client.send({"商品标题": "Sony A7M4"}, "价格合适"))

    assert captured["payload"]["token"] == "valid-token"
    assert captured["payload"]["topic"] == "group1"
