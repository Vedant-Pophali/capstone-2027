package com.capstone.fleetmanager.service;

import com.capstone.fleetmanager.model.ChallengeResponsePair;
import com.capstone.fleetmanager.repository.CrpRepository;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Core PUF Authentication Service.
 *
 * Responsibilities:
 *   1. Issue challenges from the SQLite CRP store (join/challenge phase).
 *   2. Verify proof signatures against stored expected response hashes.
 *   3. Monitor the CRP count and emit OTA re-enrollment signals when below threshold.
 *   4. Bulk-insert CRPs received from an OTA re-enrollment batch.
 *
 * The "Cloud Verification Server" logic described in the research paper lives here.
 */
@Service
public class PufAuthService {

    private static final Logger log = LoggerFactory.getLogger(PufAuthService.class);

    /** Below this threshold, we trigger OTA re-enrollment for that vehicle. */
    private static final long OTA_THRESHOLD = 500;

    private final CrpRepository crpRepository;

    /**
     * In-memory map of active join sessions: vehicleId → issued challenge.
     * We store the challenge issued in this round so we can verify it later.
     */
    private final ConcurrentHashMap<String, String> activeSessionChallenges = new ConcurrentHashMap<>();

    public PufAuthService(CrpRepository crpRepository) {
        this.crpRepository = crpRepository;
    }

    // -------------------------------------------------------------------------
    // Phase 1: Join Request
    // -------------------------------------------------------------------------

    /**
     * Handles a vehicle join request.
     * Fetches one unused CRP from the database and returns the challenge to the vehicle.
     *
     * @return Map with keys: "status", "challenge" (or "reason" if rejected)
     */
    public Map<String, Object> requestJoin(String vehicleId) {
        Optional<ChallengeResponsePair> crpOpt = crpRepository.findFirstByVehicleIdAndStatus(vehicleId, "UNUSED");

        if (crpOpt.isEmpty()) {
            log.warn("[PufAuth] No unused CRPs available for vehicle {}. Rejecting join.", vehicleId);
            return Map.of("status", "rejected", "reason", "No CRPs available. OTA re-enrollment required.");
        }

        ChallengeResponsePair crp = crpOpt.get();
        activeSessionChallenges.put(vehicleId, crp.getChallenge());

        log.info("[PufAuth] Challenge issued to vehicle {}: {}", vehicleId, crp.getChallenge());
        return Map.of("status", "authorized", "challenge", Integer.parseInt(crp.getChallenge()));
    }

    // -------------------------------------------------------------------------
    // Phase 2: Proof Verification
    // -------------------------------------------------------------------------

    /**
     * Verifies the PUF proof (HMAC-like signature) submitted by the vehicle.
     *
     * The vehicle's signature was computed as:
     *   SHA256(JSON({"heartbeat": challenge}) + session_key)
     * where session_key = SHA256(packbits(puf_response > 0)).
     *
     * We replicate this by looking up the stored expectedResponseHash.
     * The expectedResponseHash IS the session_key (SHA-256 of packed PUF response bits).
     * So we reconstruct the expected signature and compare.
     *
     * @return true if verification passes, false otherwise.
     */
    @Transactional
    public boolean verifyProof(String vehicleId, int challenge, String submittedSignature) {
        String issuedChallenge = activeSessionChallenges.get(vehicleId);

        if (issuedChallenge == null || !issuedChallenge.equals(String.valueOf(challenge))) {
            log.warn("[PufAuth] Challenge mismatch for vehicle {}. Possible replay attack.", vehicleId);
            return false;
        }

        Optional<ChallengeResponsePair> crpOpt = crpRepository
                .findFirstByVehicleIdAndStatus(vehicleId, "UNUSED");

        if (crpOpt.isEmpty()) {
            log.warn("[PufAuth] CRP not found during verify for vehicle {}.", vehicleId);
            return false;
        }

        ChallengeResponsePair crp = crpOpt.get();
        String expectedSessionKey = crp.getExpectedResponseHash();

        // Reconstruct the expected HMAC signature as the Python edge node computed it:
        // SHA256( JSON({"heartbeat": <challenge>}) + session_key )
        String payload = "{\"heartbeat\": " + challenge + "}";
        String expectedSignature = sha256Hex(payload + expectedSessionKey);

        if (!MessageDigest.isEqual(expectedSignature.getBytes(), submittedSignature.getBytes())) {
            log.warn("[PufAuth] Signature mismatch for vehicle {}. Unauthorized.", vehicleId);
            return false;
        }

        // Atomically consume this CRP so it can never be replayed
        int updated = crpRepository.consumeChallenge(vehicleId, crp.getChallenge());
        if (updated == 0) {
            log.warn("[PufAuth] Race condition: CRP already consumed for vehicle {}.", vehicleId);
            return false;
        }

        // Clean up session state
        activeSessionChallenges.remove(vehicleId);

        log.info("[PufAuth] Vehicle {} successfully verified. CRP consumed.", vehicleId);
        checkOtaThreshold(vehicleId);
        return true;
    }

    // -------------------------------------------------------------------------
    // OTA Threshold Monitor (runs every 60 seconds)
    // -------------------------------------------------------------------------

    /**
     * Scheduled check across all vehicles. If any vehicle drops below OTA_THRESHOLD,
     * a warning is logged (in a real deployment, this sends an MQTT/HTTP trigger).
     */
    @Scheduled(fixedDelay = 60_000)
    public void scheduledOtaCheck() {
        log.debug("[PufAuth] Running scheduled OTA threshold check...");
        // In a real system: query distinct vehicleIds and check each.
        // For the simulation, the checkOtaThreshold is called inline after each verify.
    }

    /**
     * Checks the remaining unused CRP count for a specific vehicle and logs an OTA warning.
     */
    public void checkOtaThreshold(String vehicleId) {
        long unused = crpRepository.countByVehicleIdAndStatus(vehicleId, "UNUSED");
        log.info("[PufAuth] Vehicle {} has {} unused CRPs remaining.", vehicleId, unused);

        if (unused < OTA_THRESHOLD) {
            log.warn("[PufAuth] ⚠ OTA TRIGGER: Vehicle {} is below threshold ({} < {}). Sending renewal signal.",
                    vehicleId, unused, OTA_THRESHOLD);
            // In the full system: publish an event or call the adapter to notify the vehicle container.
            // The VehicleEvent system already in the project can carry this signal.
        }
    }

    // -------------------------------------------------------------------------
    // OTA Re-enrollment: Bulk CRP insertion
    // -------------------------------------------------------------------------

    /**
     * Accepts a batch of new CRPs generated by the vehicle during OTA renewal
     * and persists them into the SQLite database.
     *
     * @param vehicleId   The vehicle that generated the new CRPs.
     * @param newCrpBatch List of maps, each with "challenge" (int) and "responseHash" (String).
     * @return Number of new CRPs successfully stored.
     */
    @Transactional
    public int bulkInsertOtaCrps(String vehicleId, List<Map<String, String>> newCrpBatch) {
        List<ChallengeResponsePair> toSave = new ArrayList<>();
        for (Map<String, String> entry : newCrpBatch) {
            String challenge = entry.get("challenge");
            String responseHash = entry.get("responseHash");
            if (challenge != null && responseHash != null) {
                toSave.add(new ChallengeResponsePair(vehicleId, challenge, responseHash));
            }
        }
        crpRepository.saveAll(toSave);
        log.info("[PufAuth] OTA renewal complete for vehicle {}. {} new CRPs stored.", vehicleId, toSave.size());

        // Re-check threshold after replenishment
        checkOtaThreshold(vehicleId);
        return toSave.size();
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private static String sha256Hex(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(input.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }
}
