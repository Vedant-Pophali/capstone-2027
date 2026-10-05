# Security Audit Ledger Context

**Stack:** Java, Spring Boot
**Role:** Immutable logging and compliance trail for all security-critical events in the fleet.

## Objectives

1. Maintain strict, append-only logs of all PUF authentication handshakes — both successes and failures — including challenge hash, vehicle ID, and timestamp.
2. Record all flagged Zero-Day anomalies reported by the fleet's SNN unsupervised branch.
3. Log all OTA update events: which vehicle received an update, the firmware version delta, and the PUF re-authentication result.
4. Expose audit records for compliance review and post-incident forensic analysis.

## Communication

- **Protocol:** HTTP REST (internal only)
- **Inbound:** Receives events exclusively from the Go network gateway (not directly from edge vehicles)
- **No MQTT** — all events are pushed via HTTP POST from the gateway

## Constraints

- Endpoints must be strictly internal; never exposed outside the Docker network.
- Logs must be append-only — no update or delete operations on existing records.
- All log entries must include: `vehicleId`, `eventType`, `timestamp`, `challengeHash` (for PUF events), and `outcome`.