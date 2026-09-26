package com.capstone.fleetmanager.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.time.LocalDateTime;

@Entity
public class Vehicle {
    @Id
    private String id;
    private String status;
    private String containerId;
    private LocalDateTime addedAt;
    
    private String owner;
    private String model;

    public Vehicle() {}

    public Vehicle(String id, String status, String containerId, String owner, String model) {
        this.id = id;
        this.status = status;
        this.containerId = containerId;
        this.owner = owner;
        this.model = model;
        this.addedAt = LocalDateTime.now();
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getContainerId() { return containerId; }
    public void setContainerId(String containerId) { this.containerId = containerId; }
    public LocalDateTime getAddedAt() { return addedAt; }
    public void setAddedAt(LocalDateTime addedAt) { this.addedAt = addedAt; }
    public String getOwner() { return owner; }
    public void setOwner(String owner) { this.owner = owner; }
    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }
}
