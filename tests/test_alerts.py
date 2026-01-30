import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import alerts


def test_notify_all_email_sends(monkeypatch):
    sent = {}

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            sent["host"] = host
            sent["port"] = port

        def starttls(self):
            sent["starttls"] = True

        def login(self, user, pw):
            sent["login"] = (user, pw)

        def sendmail(self, from_addr, to_addrs, msg):
            sent["send"] = (from_addr, to_addrs, msg)

        def quit(self):
            sent["quit"] = True

    monkeypatch.setattr(alerts.smtplib, "SMTP", DummySMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    cfg = {"email": {"enabled": True, "to": ["admin@example.com"]}}
    alerts.notify_all(cfg, "Test Subject", "Test Body")

    assert sent.get("send") is not None


def test_notify_all_telegram_sends(monkeypatch):
    calls = {}

    class DummyResp:
        ok = True

    def dummy_post(url, json=None, timeout=None):
        calls["url"] = url
        calls["json"] = json
        return DummyResp()

    monkeypatch.setattr(alerts.requests, "post", dummy_post)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat123")

    cfg = {"telegram": {"enabled": True}}
    alerts.notify_all(cfg, "Test Subject", "Test Message")

    assert calls.get("url") is not None
    assert calls.get("json", {}).get("chat_id") == "chat123"


def test_notify_all_webhook_sends(monkeypatch):
    calls = {}

    class DummyResp:
        ok = True

    def dummy_post(url, json=None, timeout=None):
        calls["url"] = url
        calls["json"] = json
        return DummyResp()

    monkeypatch.setattr(alerts.requests, "post", dummy_post)
    monkeypatch.setenv("WEBHOOK_URL", "https://example.com/webhook")

    cfg = {"webhook": {"enabled": True}}
    alerts.notify_all(cfg, "Test Subject", "Test Message")

    assert calls.get("url") == "https://example.com/webhook"
    assert calls.get("json", {}).get("subject") == "Test Subject"
