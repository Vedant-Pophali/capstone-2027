# Asynchronous Network Gateway Context

**Stack:** Go (Golang)
**Role:** High-speed traffic controller and message router between Edge Vehicles, Fleet Manager, Audit Logger, and VSOC Dashboard.

## Objectives

1. Ingest encrypted threat alerts and anomaly reports forwarded by the Fleet Manager after PUF authentication is verified.
2. Route threat events instantly to the VSOC Dashboard via WebSocket push / HTTP webhook.
3. Forward federated model weight deltas (from the SNN unsupervised branch) to the Flower federated learning server.
4. Relay PUF-authenticated OTA update triggers from the Fleet Manager down to the relevant vehicle container.

## Communication

- **Protocol:** HTTP/HTTPS REST and WebSocket (no MQTT)
- **Inbound:** Fleet Manager pushes verified alerts over internal Docker network
- **Outbound:** VSOC Dashboard (WebSocket), Audit Logger (internal HTTP), Flower server (HTTP)

## Design Principles

- Focus entirely on concurrency, low-latency parsing, and non-blocking I/O using Go goroutines and channels.
- Stateless: no business logic, no database access — pure routing only.
- All inbound messages must already be PUF-verified by the Fleet Manager before reaching this gateway.

## Constraints

- Endpoints must not be exposed publicly; all traffic is internal Docker network only.
- No MQTT broker integration — communication is strictly HTTP/WebSocket.
