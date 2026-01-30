import json
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import yaml
from src.google_sheets_helper import append_row_to_sheet

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_PATH = os.path.join(LOG_DIR, "app.log")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yml")

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("resilience")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def log_event(service_name, event_type, retry_count=0, cb_state=None, extra=None):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        config = {}

    entry = {
        "timestamp": now_iso(),
        "service": service_name,
        "event_type": event_type,
        "retry_count": retry_count,
        "circuit_breaker": cb_state,

    }
    if extra:
        entry.update(extra)
    logger.info(json.dumps(entry))

    google_cfg = config.get("google_sheets", {})
    if google_cfg.get("enabled") and google_cfg.get("sheet_id"):
        row = [
            entry.get("timestamp"),
            entry.get("service"),
            entry.get("event_type"),
            entry.get("retry_count"),
            entry.get("circuit_breaker"),
            entry.get("contact_id"),
            entry.get("error"),
        ]
        append_row_to_sheet(google_cfg.get("sheet_id"), row)