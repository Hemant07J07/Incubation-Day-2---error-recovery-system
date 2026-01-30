# src/call_processor.py
import time
import yaml
import os
from src.retry import retry_on_transient
from src.circuit_breaker import CircuitBreaker
from src.logger import log_event
from src.alerts import notify_all
from src.exceptions import TransientServiceError, PermanentServiceError

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yml")
with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

# create a CB for elevenlabs using config
eleven_cfg = CONFIG.get("services", {}).get("elevenlabs", {})
eleven_cb = CircuitBreaker(
    failure_threshold=eleven_cfg.get("circuit_breaker", {}).get("failure_threshold", 3),
    recovery_timeout=eleven_cfg.get("circuit_breaker", {}).get("recovery_timeout", 30),
)

# retry decorator configured per service
retry_decorator = retry_on_transient(
    initial_delay=eleven_cfg.get("retry", {}).get("initial_delay", 5),
    backoff_factor=eleven_cfg.get("retry", {}).get("backoff_factor", 2),
    max_attempts=eleven_cfg.get("retry", {}).get("max_attempts", 3),
)

# fake client import (swap with real)
from src.services.elevenlabs_client import ElevenLabsClient
eleven_client = ElevenLabsClient(api_key=os.getenv("ELEVEN_API_KEY"))

@retry_decorator
def call_elevenlabs(text):
    # actual call that may raise TransientServiceError or PermanentServiceError
    # For demo, we call the client and assume it raises appropriate exceptions.
    try:
        return eleven_client.synthesize(text)
    except TransientServiceError:
        raise
    except PermanentServiceError:
        raise
    except Exception as e:
        # treat unknown exceptions as transient for now
        raise TransientServiceError(str(e))

def process_contact(contact, cb=eleven_cb, alerts_cfg=CONFIG.get("alerts", {})):
    service_name = "elevenlabs"
    # fail-fast if circuit open
    try:
        cb.check_or_raise()
    except Exception as e:
        log_event(service_name, "circuit_open_fail_fast", cb_state=cb.state.value, extra={"contact_id": contact.get("id")})
        # notify admin once (dedupe handled externally if needed)
        notify_all({"webhook": {"enabled": True, "url": os.getenv("WEBHOOK_URL")}}, f"[{service_name}] Circuit Open", f"Circuit is open for {service_name}")
        return False

    try:
        audio = call_elevenlabs(contact.get("message"))
    except TransientServiceError as te:
        cb.record_failure()
        log_event(service_name, "transient_failure", retry_count=CONFIG['services']['elevenlabs']['retry']['max_attempts'], cb_state=cb.state.value, extra={"contact_id": contact.get("id"), "error": str(te)})
        # after retries exhausted, alert and continue to next contact
        notify_all(CONFIG.get("alerts", {}), f"[{service_name}] Transient failure", f"Failed contact {contact.get('id')}: {str(te)}")
        return False
    except PermanentServiceError as pe:
        cb.record_failure()
        log_event(service_name, "permanent_failure", retry_count=0, cb_state=cb.state.value, extra={"contact_id": contact.get("id"), "error": str(pe)})
        notify_all(CONFIG.get("alerts", {}), f"[{service_name}] Permanent failure", f"Failed contact {contact.get('id')}: {str(pe)}")
        return False

    # success
    cb.record_success()
    log_event(service_name, "success", retry_count=0, cb_state=cb.state.value, extra={"contact_id": contact.get("id")})
    # here you would push audio to telephony system or next stage
    return True

# Example queue processor
def process_queue(queue):
    for contact in queue:
        success = process_contact(contact)
        if not success:
            # apply graceful degradation: maybe enqueue text-only fallback
            print(f"[processor] contact {contact.get('id')} failed; skipping to next.")
        else:
            print(f"[processor] contact {contact.get('id')} processed OK.")
