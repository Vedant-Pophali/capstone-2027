package com.capstone.fleetmanager.model;

import jakarta.persistence.*;

/**
 * Represents a single hardware Challenge-Response Pair (CRP) stored for a vehicle.
 * Status lifecycle: UNUSED → CONSUMED
 * CRPs are generated offline (factory enrollment) and replenished via OTA re-enrollment.
 */
@Entity
@Table(name = "challenge_response_pairs", indexes = {
    @Index(name = "idx_crp_vehicle_status", columnList = "vehicleId, status")
})
public class ChallengeResponsePair {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String vehicleId;

    /**
     * The raw integer challenge seed sent to the vehicle.
     */
    @Column(nullable = false)
    private String challenge;

    /**
     * The SHA-256 hex digest of the expected PUF response (stored as a reference hash).
     */
    @Column(nullable = false, length = 512)
    private String expectedResponseHash;

    /**
     * "UNUSED" | "CONSUMED"
     */
    @Column(nullable = false)
    private String status = "UNUSED";

    public ChallengeResponsePair() {}

    public ChallengeResponsePair(String vehicleId, String challenge, String expectedResponseHash) {
        this.vehicleId = vehicleId;
        this.challenge = challenge;
        this.expectedResponseHash = expectedResponseHash;
        this.status = "UNUSED";
    }

    // --- Getters & Setters ---

    public Long getId() { return id; }

    public String getVehicleId() { return vehicleId; }
    public void setVehicleId(String vehicleId) { this.vehicleId = vehicleId; }

    public String getChallenge() { return challenge; }
    public void setChallenge(String challenge) { this.challenge = challenge; }

    public String getExpectedResponseHash() { return expectedResponseHash; }
    public void setExpectedResponseHash(String expectedResponseHash) {
        this.expectedResponseHash = expectedResponseHash;
    }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
