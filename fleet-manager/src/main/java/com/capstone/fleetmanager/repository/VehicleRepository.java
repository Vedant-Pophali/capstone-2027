package com.capstone.fleetmanager.repository;

import com.capstone.fleetmanager.model.Vehicle;
import org.springframework.data.jpa.repository.JpaRepository;

public interface VehicleRepository extends JpaRepository<Vehicle, String> {

    long countByStatus(String status);

    long countByContainerStatus(String containerStatus);
}
