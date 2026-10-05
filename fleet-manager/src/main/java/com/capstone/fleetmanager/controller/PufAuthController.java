package com.capstone.fleetmanager.controller;

import com.capstone.fleetmanager.service.PufAuthService;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST controller exposing the PUF hardware authentication API.
 *
 * Endpoints consumed by edge-vehicle containers:
 *   POST /api/puf/join          — Phase 1: Request a challenge
 *   POST /api/puf/verify        — Phase 2: Submit proof, receive gate-open signal
 *   POST /api/puf/ota-renew     — OTA Re-enrollment: Submit fresh CRP batch
 *   GET  /api/puf/crp-status    — Dashboard: Check remaining CRP count for a vehicle
 */
@RestController
@RequestMapping("/api/puf")
public class PufAuthController {

    private static final Logger log = LoggerFactory.getLogger(PufAuthController.class);

    private final PufAuthService pufAuthService;

    public PufAuthController(PufAuthService pufAuthService) {
        this.pufAuthService = pufAuthService;
    }

    /**
     * Phase 1 - Join Request.
     * Body: { "vehicleId": "42" }
     * Response: { "status": "authorized", "challenge": 12345 }
     *        OR { "status": "rejected", "reason": "..." }
     */
    @PostMapping("/join")
    public ResponseEntity<Map<String, Object>> join(@RequestBody Map<String, String> body) {
        String vehicleId = body.get("vehicleId");
        if (vehicleId == null || vehicleId.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "vehicleId is required"));
        }
        log.info("[PufAuth] Join request from vehicle: {}", vehicleId);
        Map<String, Object> result = pufAuthService.requestJoin(vehicleId);
        return ResponseEntity.ok(result);
    }

    /**
     * Phase 2 - Proof Verification.
     * Body: { "vehicleId": "42", "challenge": 12345, "signature": "abc123..." }
     * Response: { "verified": true } OR { "verified": false }
     */
    @PostMapping("/verify")
    public ResponseEntity<Map<String, Object>> verify(@RequestBody Map<String, Object> body) {
        String vehicleId = (String) body.get("vehicleId");
        int challenge = ((Number) body.get("challenge")).intValue();
        String signature = (String) body.get("signature");

        if (vehicleId == null || signature == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "vehicleId and signature are required"));
        }

        boolean verified = pufAuthService.verifyProof(vehicleId, challenge, signature);
        log.info("[PufAuth] Verify result for vehicle {}: {}", vehicleId, verified);
        return ResponseEntity.ok(Map.of("verified", verified));
    }

    /**
     * OTA Re-enrollment - Bulk CRP Upload.
     * Body: {
     *   "vehicleId": "42",
     *   "crpBatch": [
     *     { "challenge": "12345", "responseHash": "sha256hex..." },
     *     ...
     *   ]
     * }
     * Response: { "stored": 5000 }
     */
    @PostMapping("/ota-renew")
    @SuppressWarnings("unchecked")
    public ResponseEntity<Map<String, Object>> otaRenew(@RequestBody Map<String, Object> body) {
        String vehicleId = (String) body.get("vehicleId");
        List<Map<String, String>> crpBatch = (List<Map<String, String>>) body.get("crpBatch");

        if (vehicleId == null || crpBatch == null || crpBatch.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "vehicleId and non-empty crpBatch are required"));
        }

        log.info("[PufAuth] OTA renewal batch received from vehicle {} ({} CRPs)", vehicleId, crpBatch.size());
        int stored = pufAuthService.bulkInsertOtaCrps(vehicleId, crpBatch);
        return ResponseEntity.ok(Map.of("stored", stored));
    }

    /**
     * Dashboard / Monitoring endpoint — check remaining CRP count.
     * GET /api/puf/crp-status?vehicleId=42
     */
    @GetMapping("/crp-status")
    public ResponseEntity<Map<String, Object>> crpStatus(@RequestParam String vehicleId) {
        pufAuthService.checkOtaThreshold(vehicleId);
        return ResponseEntity.ok(Map.of("vehicleId", vehicleId, "message", "Check server logs for CRP count."));
    }
}
