# Vehicle Security Operations Center (VSOC) Dashboard Context

**Stack:** Node.js (backend), WebSockets, React (frontend)
**Role:** Real-time human-operator interface for monitoring fleet security status.

## Objectives

1. Maintain persistent WebSocket connections with the Go network gateway to receive live push events.
2. Render a live visualization of the vehicle fleet — each vehicle displayed with its current state.
3. Instantly update vehicle states (`Safe`, `Threatened`, `Compromised`) upon receiving anomaly alerts from the gateway.
4. Display PUF authentication event history — showing which vehicles successfully authenticated or triggered a re-challenge.
5. Show OTA update status per vehicle (pending, in-progress, completed, failed).

## Communication

- **Protocol:** WebSocket (inbound from Go gateway), HTTP REST (for initial state load)
- **No MQTT** — all real-time updates arrive via WebSocket push from the network gateway

## Design Principles

- The backend must be purely event-driven — no polling; all UI updates triggered by WebSocket messages.
- Frontend state should reflect real-time fleet security posture with minimal latency.
- Fleet map / vehicle grid should visually distinguish threat severity levels.

## Constraints

- The dashboard must not communicate directly with the Fleet Manager or edge vehicles.
- All data flows through the Go gateway exclusively.
- No direct database access from the frontend — all data served via the Node.js backend.
