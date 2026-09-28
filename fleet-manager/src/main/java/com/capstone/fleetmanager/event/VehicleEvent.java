package com.capstone.fleetmanager.event;

import com.capstone.fleetmanager.dto.VehicleResponse;
import org.springframework.context.ApplicationEvent;

/**
 * Domain event published when a vehicle's lifecycle state changes.
 * Decouples business logic from notification/broadcast concerns.
 * Any number of listeners can react without modifying the publisher.
 */
public class VehicleEvent extends ApplicationEvent {

    public enum Type {
        CREATED, DELETED, STATUS_CHANGED
    }

    private final Type type;
    private final VehicleResponse vehicle;
    private final String vehicleId;

    /** Used for CREATED and STATUS_CHANGED events (carries full vehicle data). */
    public VehicleEvent(Object source, Type type, VehicleResponse vehicle) {
        super(source);
        this.type = type;
        this.vehicle = vehicle;
        this.vehicleId = vehicle != null ? vehicle.getId() : null;
    }

    /** Used for DELETED events (only carries the ID of the removed vehicle). */
    public VehicleEvent(Object source, Type type, String vehicleId) {
        super(source);
        this.type = type;
        this.vehicle = null;
        this.vehicleId = vehicleId;
    }

    public Type getType() { return type; }
    public VehicleResponse getVehicle() { return vehicle; }
    public String getVehicleId() { return vehicleId; }
}
