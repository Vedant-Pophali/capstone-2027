package com.vehicular.audit.dto;

public class SecurityEventDto {
    private String vehicleId;
    private String eventType;
    private String timestamp;
    private String signature;
    private String details;

    public SecurityEventDto() {
    }

    public SecurityEventDto(String vehicleId, String eventType, String timestamp, String signature, String details) {
        this.vehicleId = vehicleId;
        this.eventType = eventType;
        this.timestamp = timestamp;
        this.signature = signature;
        this.details = details;
    }

    public String getVehicleId() { return vehicleId; }
    public void setVehicleId(String vehicleId) { this.vehicleId = vehicleId; }
    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }
    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }
    public String getSignature() { return signature; }
    public void setSignature(String signature) { this.signature = signature; }
    public String getDetails() { return details; }
    public void setDetails(String details) { this.details = details; }
}
