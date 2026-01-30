# simulations/simulate_eleventlabs_503.py
import time
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # allow imports from src
from src.call_processor import process_queue, eleven_client, eleven_cb
from src.exceptions import TransientServiceError
from src.logger import log_event

# We'll monkeypatch eleven_client.synthesize to simulate 503 for N attempts, then succeed
class MockEleven:
    def __init__(self, fail_times=3):
        self.fail_times = fail_times
        self.called = 0

    def synthesize(self, text):
        self.called += 1
        print(f"[mock_eleven] call #{self.called}")
        if self.called <= self.fail_times:
            # simulate 503 transient error
            raise TransientServiceError("Simulated 503 Service Unavailable")
        return b"AUDIO_BYTES_SIMULATED"

def main():
    # Replace the real client with the mock
    mock = MockEleven(fail_times=3)
    from src import call_processor
    call_processor.eleven_client = mock

    # small queue
    queue = [
        {"id": "c1", "message": "Hello from contact 1"},
        {"id": "c2", "message": "Hello from contact 2"},
    ]

    print("Starting health checker with simple health fn (which will report healthy after 10s)...")
    # a health fn that becomes healthy after 10s
    start = time.time()
    def health_fn():
        return (time.time() - start) > 10

    # attach healthcheck on eleven_cb
    from src.healthcheck import HealthChecker
    checks = {"elevenlabs": {"fn": health_fn, "circuit_breaker": eleven_cb}}
    hc = HealthChecker(checks, interval=3)
    hc.start()

    # Process queue (first contact will hit mock fail -> retries -> CB opens)
    process_queue(queue)

    # wait to allow healthchecker to reset circuit (approx)
    print("Waiting 15 seconds for health checker to flip health...")
    time.sleep(15)

    # Process queue again; now mock will have advanced its counter and should succeed
    process_queue(queue)

    hc.stop()
    print("Simulation complete. Check logs/logs/app.log for events.")

if __name__ == "__main__":
    main()
