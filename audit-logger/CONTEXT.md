# Security Audit Ledger Context
**Stack:** Java, Spring Boot
**Role:** Immutable logging and compliance.
**Objectives:**
1. Maintain strict logs of all PUF authentication handshakes (successes and fail-safes).
2. Record all flagged Zero-Day anomalies reported by the fleet.
**Constraints:** Endpoints must be strictly internal and receive data exclusively from the Go gateway.