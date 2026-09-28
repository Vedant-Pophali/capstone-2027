package com.capstone.fleetmanager.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * Inbound DTO for vehicle creation requests.
 * Decoupled from the JPA entity to allow independent API evolution.
 */
public class VehicleRequest {

    @NotBlank(message = "Vehicle ID is required")
    @Pattern(regexp = "^[a-zA-Z0-9_-]+$",
             message = "Vehicle ID must contain only letters, numbers, hyphens, and underscores")
    @Size(max = 50, message = "Vehicle ID must be 50 characters or fewer")
    private String id;

    @Size(max = 100, message = "Owner name must be 100 characters or fewer")
    private String owner;

    @Size(max = 100, message = "Model name must be 100 characters or fewer")
    private String model;

    public VehicleRequest() {}

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getOwner() { return owner; }
    public void setOwner(String owner) { this.owner = owner; }

    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }
}
