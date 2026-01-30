# src/healthcheck.py
import threading
import time
from src.logger import log_event

class HealthChecker:
    def __init__(self, checks, interval=10):
        """
        checks: dict of service_name -> {'fn': callable_healthcheck, 'circuit_breaker': cb_instance}
        interval: seconds between checks
        """
        self.checks = checks
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._stop.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        log_event("healthcheck", "started", extra={"interval": self.interval})

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=1)
        log_event("healthcheck", "stopped")

    def _run(self):
        while not self._stop.is_set():
            for svc, meta in self.checks.items():
                fn = meta.get("fn")
                cb = meta.get("circuit_breaker")
                try:
                    healthy = fn()
                    if healthy:
                        # reset circuit on success
                        if cb:
                            cb.record_success()
                        log_event(svc, "health_ok", cb_state=getattr(cb, "state", None).value if cb else None)
                    else:
                        log_event(svc, "health_bad", cb_state=getattr(cb, "state", None).value if cb else None)
                except Exception as e:
                    log_event(svc, "health_exception", extra={"error": str(e)})
            time.sleep(self.interval)
