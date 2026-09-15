# Vehicle Security Operations Center Context
**Stack:** Node.js, WebSockets, Frontend (React/Astra/Fable)
**Role:** Real-time human-computer interface.
**Objectives:**
1. Maintain persistent WebSocket connections with the Go gateway.
2. Render a live visualization of the vehicle fleet.
3. Instantly update vehicle states (Safe, Threatened, Compromised) upon receiving anomaly alerts.
**Constraints:** The backend must be purely event-driven to push updates to the UI immediately.