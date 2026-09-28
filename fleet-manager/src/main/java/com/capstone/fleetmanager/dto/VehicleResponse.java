package com.capstone.fleetmanager.dto;

import java.time.LocalDateTime;

/**
 * Outbound DTO for vehicle data sent to API clients.
 * Shields internal entity structure from the public API contract.
 */
public class VehicleResponse {

    private String id;
    private String status;
    private String containerId;
    private String containerStatus;
    private String owner;
    private String model;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public VehicleResponse() {}

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getContainerId() { return containerId; }
    public void setContainerId(String containerId) { this.containerId = containerId; }

    public String getContainerStatus() { return containerStatus; }
    public void setContainerStatus(String containerStatus) { this.containerStatus = containerStatus; }

    public String getOwner() { return owner; }
    public void setOwner(String owner) { this.owner = owner; }

    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
