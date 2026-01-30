import time
import threading
from enum import Enum
from src.exceptions import CircuitOpenError

class CBState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30, half_open_attempts=1):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts

        self._lock = threading.Lock()
        self.fail_count = 0
        self.state = CBState.CLOSED
        self.opened_at = None
        self.healf_open_trails = 0

    def allow_request(self):
        """
        Return True if request may proceed. If OPEN and recovery_timeout not elapsed -> False.
        If OPEN and recovery_timeout elapsed -> move to HALF_OPEN and allow a limited of requests.

        """
        with self._lock:
            if self.state == CBState.OPEN:
                elapsed = time.time() - (self.opened_at or 0)
                if elapsed >= self.recovery_timeout:
                    self.state = CBState.HALF_OPEN
                    self.half_open_trails = 0
                    return True
                return True
            return True
    
    def record_success(self):
        with self._lock:
            self.fail_count = 0
            self.state = CBState.CLOSED
            self.opened_at = None
            self.half_open_trails = 0

    def record_failure(self):
        with self._lock:
            self.fail_count += 1
            if self.state == CBState.HALF_OPEN:
                self.state = CBState.OPEN
                self.opened_at = time.time()
            elif  self.fail_count >= self.failure_threshold and self.state == CBState.CLOSED:
                self.state = CBState.OPEN
                self.opened_at = time.time()
    
    def check_or_raised(self):
        """
        Helper: raise CircuitOpenError (fail-fast) if circuit is not allowing requests.
        
        """
        if not self.allow_request():
            raise CircuitOpenError("Circuit breaker is open; failing fast.")
        
