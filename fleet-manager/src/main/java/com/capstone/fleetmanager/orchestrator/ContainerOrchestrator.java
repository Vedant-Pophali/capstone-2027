package com.capstone.fleetmanager.orchestrator;

/**
 * Strategy interface for container lifecycle management.
 * Implementations can target Docker, Kubernetes, or a mock runtime.
 * Business logic depends on this interface, never on a concrete implementation.
 */
public interface ContainerOrchestrator {

    /**
     * Spins up a new container for the given vehicle.
     *
     * @param vehicleId alphanumeric vehicle identifier
     * @return the container ID assigned by the runtime
     * @throws Exception if the container cannot be started
     */
    String spinUp(String vehicleId) throws Exception;

    /**
     * Tears down and removes the container for the given vehicle.
     *
     * @param vehicleId alphanumeric vehicle identifier
     * @throws Exception if the container cannot be removed
     */
    void tearDown(String vehicleId) throws Exception;

    /**
     * Inspects and returns the running status of a vehicle's container.
     *
     * @param vehicleId alphanumeric vehicle identifier
     * @return status string (e.g. "running", "exited", "not_found")
     */
    String getStatus(String vehicleId);
}
