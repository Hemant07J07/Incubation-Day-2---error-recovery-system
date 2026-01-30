# Incubation-Day-2---error-recovery-system

```
+---------------------------------------------------+
| Incubation-Day-2---error-recovery-system           |
+---------------------------------------------------+
```

## Overview
This project implements a robust **Error Recovery & Resilience System** for an AI Call Agent that integrates with external services (e.g., ElevenLabs, LLMs, CRMs). The solution focuses on **fault detection, intelligent recovery, circuit breaking, alerting**, and **graceful degradation**.

## Architecture (high level)

### ASCII Architecture Diagram
```
         +----------------------+
         |   config.yml / env   |
         +----------+-----------+
            |
            v
      +---------+---------+
      |  call_processor   |
      +----+---------+----+
           |         |
           |         |
           v         v
      +--------+--+   +--+-------------+
      |  retry()  |   | circuit_breaker |
      +-----+-----+   +--+-------------+
        |            |
        v            v
     +------+-----+   +--+-----------------+
     | external   |   |  healthcheck       |
     | services   |   |  (periodic)        |
     +------+-----+   +--+-----------------+
        |            |
        v            v
   +--------+----+   +---+-----------------+
   | alerts      |   | logger              |
   | (email/tg/  |   | (file + sheets)     |
   | webhook)    |   +---------------------+
   +-------------+
```
- **Retry logic**: [src/retry.py](src/retry.py) provides a configurable exponential backoff decorator.
- **Circuit breaker**: [src/circuit_breaker.py](src/circuit_breaker.py) tracks failure rates and blocks unhealthy services.
- **Alerting**: [src/alerts.py](src/alerts.py) sends Email, Telegram, and Webhook alerts.
- **Logging & observability**: [src/logger.py](src/logger.py) writes structured logs to a local file and optionally Google Sheets.
- **Health checks**: [src/healthcheck.py](src/healthcheck.py) runs periodic service checks and auto-recovers.
- **Call processing**: [src/call_processor.py](src/call_processor.py) orchestrates retries, circuit breaker, and fallback behavior.

## Error Categorization
Custom exceptions are used to distinguish **transient** vs **permanent** errors:
- Transient: timeouts, 503, network glitches (retryable)
- Permanent: 401, invalid payloads, quota exceeded (non-retryable)

## Retry Strategy
Retry logic is configurable in [config.yml](config.yml):
- `initial_delay`
- `backoff_factor`
- `max_attempts`

Retries only apply to transient errors.

## Circuit Breaker Behavior
Each external service has its own breaker with configurable:
- `failure_threshold`
- `recovery_timeout`

When a breaker opens, new calls **fail fast** until the recovery timeout elapses.

## Logging & Observability
Logs are structured and include:
- Timestamp
- Service name
- Error category / event type
- Retry count
- Circuit breaker state

Local logs: `logs/app.log`

Optional Google Sheets logging is enabled via the `google_sheets` section in [config.yml](config.yml).

## Alerts
Alert channels supported:
- **Email** (SMTP)
- **Telegram** bot
- **Webhook** endpoint

Configuration is in [config.yml](config.yml) with secrets loaded via environment variables.

## Health Checks
The health checker runs periodically and:
- Updates service health state
- Resets circuit breakers on recovery
- Logs health transitions

## Graceful Degradation
When a service is down:
- Current call is skipped
- Next contact in queue is processed
- System keeps operating instead of blocking

## Error Flow Walkthrough (End-to-End)
This is the exact path for failures across the system:
1. **Call starts** in `call_processor`.
2. **Retry wrapper** validates error type:
   - If transient, retry with exponential backoff.
   - If permanent, stop retries immediately.
3. **Circuit breaker** updates failure stats:
   - Opens when threshold reached; further calls fail fast.
4. **Alerts** trigger on repeated failure or breaker open.
5. **Logging** captures event, error category, retry count, and breaker state.
6. **Healthcheck** periodically probes service:
   - On success, resets breaker and resumes normal flow.

## Assignment Point Mapping
Explicit mapping to the rubric/assignment points:
- **Fault detection & classification** → Custom exceptions + transient/permanent split (see `exceptions.py`).
- **Recovery strategy** → Configurable exponential backoff retries (see `retry.py`, `config.yml`).
- **Circuit breaking** → Failure threshold + recovery timeout (see `circuit_breaker.py`).
- **Alerting** → Email, Telegram, Webhook on failure (see `alerts.py`).
- **Observability** → Structured logs + optional Google Sheets (see `logger.py`, `google_sheets_helper.py`).
- **Health monitoring** → Periodic checks and auto-recovery (see `healthcheck.py`).
- **Graceful degradation** → Skip failed call, continue queue (see `call_processor.py`).
- **Scenario compliance** → ElevenLabs 503 handling flow (see Required Scenario section).

## Required Scenario — ElevenLabs 503
Handled behavior:
1. Detect 503 as transient
2. Retry with exponential backoff (start at 5s)
3. Retry up to 3 times
4. If still failing:
   - Mark call as failed
   - Trigger alert to admin
   - Move to next contact
5. Circuit breaker opens
6. Health checks continue
7. On recovery, breaker resets and calls resume

## Tests
Pytest tests cover all alert types:
- Email
- Telegram
- Webhook

Run tests:
```
pytest
```

## Screenshots / Evidence
Place screenshots or proof in:
- `docs/screenshots/`

## Configuration
Key config file:
- [config.yml](config.yml)

### Environment Variables
- `ELEVEN_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `WEBHOOK_URL`
- `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` (optional if using Google Sheets)

---
**Deliverables included:** source code, structured logging, resilience logic, and tests covering alert channels.
