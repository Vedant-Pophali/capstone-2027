package com.capstone.fleetmanager.exception;

/**
 * Thrown when a vehicle is looked up by ID but does not exist in the database.
 */
public class VehicleNotFoundException extends RuntimeException {

    private final String vehicleId;

    public VehicleNotFoundException(String vehicleId) {
        super("Vehicle not found: " + vehicleId);
        this.vehicleId = vehicleId;
    }

    public String getVehicleId() { return vehicleId; }
}
