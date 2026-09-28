package com.capstone.fleetmanager.mapper;

import com.capstone.fleetmanager.dto.VehicleResponse;
import com.capstone.fleetmanager.model.Vehicle;

/**
 * Stateless mapper for converting between Vehicle entity and DTOs.
 * Keeps the JPA entity and public API contract fully decoupled.
 */
public final class VehicleMapper {

    private VehicleMapper() {
        // Utility class — no instantiation
    }

    public static VehicleResponse toResponse(Vehicle vehicle) {
        if (vehicle == null) return null;

        VehicleResponse response = new VehicleResponse();
        response.setId(vehicle.getId());
        response.setStatus(vehicle.getStatus());
        response.setContainerId(vehicle.getContainerId());
        response.setContainerStatus(vehicle.getContainerStatus());
        response.setOwner(vehicle.getOwner());
        response.setModel(vehicle.getModel());
        response.setCreatedAt(vehicle.getCreatedAt());
        response.setUpdatedAt(vehicle.getUpdatedAt());
        return response;
    }
}
