package com.capstone.fleetmanager.repository;

import com.capstone.fleetmanager.model.ChallengeResponsePair;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

/**
 * Data access layer for CRPs.
 * Provides atomic challenge-fetch + consume operations to prevent replay attacks.
 */
public interface CrpRepository extends JpaRepository<ChallengeResponsePair, Long> {

    /**
     * Fetch exactly one unused CRP for a vehicle.
     */
    Optional<ChallengeResponsePair> findFirstByVehicleIdAndStatus(String vehicleId, String status);

    /**
     * Count remaining unused CRPs — used by the OTA threshold monitor.
     */
    long countByVehicleIdAndStatus(String vehicleId, String status);

    /**
     * Atomically mark a specific challenge as CONSUMED after successful verification.
     */
    @Modifying
    @Transactional
    @Query("UPDATE ChallengeResponsePair c SET c.status = 'CONSUMED' WHERE c.vehicleId = :vehicleId AND c.challenge = :challenge AND c.status = 'UNUSED'")
    int consumeChallenge(@Param("vehicleId") String vehicleId, @Param("challenge") String challenge);
}
