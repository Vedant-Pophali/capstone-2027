package com.capstone.fleetmanager.service;

import com.capstone.fleetmanager.model.Vehicle;
import com.capstone.fleetmanager.repository.VehicleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class VehicleService {

    @Autowired
    private VehicleRepository vehicleRepository;

    @Autowired
    private DockerService dockerService;

    public List<Vehicle> getAllVehicles() {
        return vehicleRepository.findAll();
    }

    public Optional<Vehicle> getVehicle(String id) {
        return vehicleRepository.findById(id);
    }

    public Vehicle addVehicle(Vehicle requestVehicle) throws Exception {
        if (vehicleRepository.existsById(requestVehicle.getId())) {
            throw new IllegalArgumentException("Vehicle already exists");
        }
        
        // Loosely coupled approach: delegate to docker service to spin up container
        String containerId = dockerService.spinUpContainer(requestVehicle.getId());
        
        Vehicle vehicle = new Vehicle(
            requestVehicle.getId(), 
            "Healthy", 
            containerId,
            requestVehicle.getOwner(),
            requestVehicle.getModel()
        );
        return vehicleRepository.save(vehicle);
    }

    public void removeVehicle(String id) throws Exception {
        if (!vehicleRepository.existsById(id)) {
            throw new IllegalArgumentException("Vehicle not found");
        }
        
        // Destroy container
        dockerService.removeContainer(id);
        vehicleRepository.deleteById(id);
    }
}
