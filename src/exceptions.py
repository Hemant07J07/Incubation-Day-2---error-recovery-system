class BaseServiceError(Exception):
    """Base for all service errors."""
    pass

class TransientServiceError(BaseServiceError):
    """Temporary error (e.g., 502/ 503, network timeouts)."""
    pass

class PermanentServiceError(BaseServiceError):
    """Permanent errors (e.g., 401 unauthorized, invalid request)."""
    pass

class CircuitOpenError(PermanentServiceError):
    """Raised when the circuit breaker is open; fail-fast(no retries)."""
    pass