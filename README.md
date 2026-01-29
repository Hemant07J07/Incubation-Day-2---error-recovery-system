# Incubation Day 2 — Resilience System

## Overview
This project implements a robust **Error Recovery & Resilience System** for an AI Call Agent that integrates with external services (e.g., ElevenLabs, LLMs, CRMs). The solution focuses on **fault detection, intelligent recovery, circuit breaking, alerting**, and **graceful degradation**.

## Architecture (high level)
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
