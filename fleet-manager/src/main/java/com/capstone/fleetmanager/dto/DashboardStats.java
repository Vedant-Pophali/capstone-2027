package com.capstone.fleetmanager.dto;

/**
 * Aggregated fleet metrics for the dashboard summary view.
 */
public class DashboardStats {

    private long totalVehicles;
    private long healthyVehicles;
    private long compromisedVehicles;
    private long containersRunning;

    public DashboardStats() {}

    public DashboardStats(long totalVehicles, long healthyVehicles,
                          long compromisedVehicles, long containersRunning) {
        this.totalVehicles = totalVehicles;
        this.healthyVehicles = healthyVehicles;
        this.compromisedVehicles = compromisedVehicles;
        this.containersRunning = containersRunning;
    }

    public long getTotalVehicles() { return totalVehicles; }
    public void setTotalVehicles(long totalVehicles) { this.totalVehicles = totalVehicles; }

    public long getHealthyVehicles() { return healthyVehicles; }
    public void setHealthyVehicles(long healthyVehicles) { this.healthyVehicles = healthyVehicles; }

    public long getCompromisedVehicles() { return compromisedVehicles; }
    public void setCompromisedVehicles(long compromisedVehicles) { this.compromisedVehicles = compromisedVehicles; }

    public long getContainersRunning() { return containersRunning; }
    public void setContainersRunning(long containersRunning) { this.containersRunning = containersRunning; }
}
