package com.capstone.fleetmanager.service;

import com.capstone.fleetmanager.dto.DashboardStats;
import com.capstone.fleetmanager.repository.VehicleRepository;
import org.springframework.stereotype.Service;

/**
 * Computes aggregated fleet metrics for the dashboard.
 * Separated from VehicleService to follow Single Responsibility Principle.
 */
@Service
public class DashboardService {

    private final VehicleRepository vehicleRepository;

    public DashboardService(VehicleRepository vehicleRepository) {
        this.vehicleRepository = vehicleRepository;
    }

    public DashboardStats getStats() {
        long total = vehicleRepository.count();
        long healthy = vehicleRepository.countByStatus("Healthy");
        long compromised = vehicleRepository.countByStatus("Compromised");
        long running = vehicleRepository.countByContainerStatus("RUNNING");

        return new DashboardStats(total, healthy, compromised, running);
    }
}
