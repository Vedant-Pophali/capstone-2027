package com.capstone.fleetmanager.service;

import com.capstone.fleetmanager.dto.VehicleRequest;
import com.capstone.fleetmanager.dto.VehicleResponse;
import com.capstone.fleetmanager.event.VehicleEvent;
import com.capstone.fleetmanager.exception.ContainerOperationException;
import com.capstone.fleetmanager.exception.VehicleNotFoundException;
import com.capstone.fleetmanager.mapper.VehicleMapper;
import com.capstone.fleetmanager.model.Vehicle;
import com.capstone.fleetmanager.orchestrator.ContainerOrchestrator;
import com.capstone.fleetmanager.repository.VehicleRepository;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Core business logic for vehicle lifecycle management.
 * Depends on ContainerOrchestrator (interface) and ApplicationEventPublisher —
 * never on concrete Docker/WebSocket implementations.
 */
@Service
public class VehicleService {

    private static final Logger log = LoggerFactory.getLogger(VehicleService.class);

    private final VehicleRepository vehicleRepository;
    private final ContainerOrchestrator containerOrchestrator;
    private final ApplicationEventPublisher eventPublisher;

    // Constructor injection — no @Autowired field injection
    public VehicleService(VehicleRepository vehicleRepository,
                          ContainerOrchestrator containerOrchestrator,
                          ApplicationEventPublisher eventPublisher) {
        this.vehicleRepository = vehicleRepository;
        this.containerOrchestrator = containerOrchestrator;
        this.eventPublisher = eventPublisher;
    }

    public List<VehicleResponse> getAllVehicles() {
        return vehicleRepository.findAll()
                .stream()
                .map(VehicleMapper::toResponse)
                .collect(Collectors.toList());
    }

    public VehicleResponse getVehicle(String id) {
        Vehicle vehicle = vehicleRepository.findById(id)
                .orElseThrow(() -> new VehicleNotFoundException(id));
        return VehicleMapper.toResponse(vehicle);
    }

    public VehicleResponse createVehicle(VehicleRequest request) {
        if (vehicleRepository.existsById(request.getId())) {
            throw new IllegalArgumentException("Vehicle already exists: " + request.getId());
        }

        Vehicle vehicle = new Vehicle(request.getId(), request.getOwner(), request.getModel());

        // Delegate container creation to the orchestrator (Strategy pattern)
        try {
            String containerId = containerOrchestrator.spinUp(request.getId());
            vehicle.setContainerId(containerId);
            vehicle.setContainerStatus("RUNNING");
        } catch (Exception e) {
            log.error("Container spin-up failed for vehicle {}: {}", request.getId(), e.getMessage());
            vehicle.setContainerStatus("ERROR");
            throw new ContainerOperationException("Failed to start container for vehicle " + request.getId(), e);
        }

        Vehicle saved = vehicleRepository.save(vehicle);
        VehicleResponse response = VehicleMapper.toResponse(saved);

        // Publish event — listeners (WebSocket, logging, etc.) react independently
        eventPublisher.publishEvent(new VehicleEvent(this, VehicleEvent.Type.CREATED, response));

        log.info("Vehicle created: {}", saved.getId());
        return response;
    }

    public VehicleResponse updateVehicle(String id, VehicleRequest request) {
        Vehicle vehicle = vehicleRepository.findById(id)
                .orElseThrow(() -> new VehicleNotFoundException(id));

        if (request.getOwner() != null) vehicle.setOwner(request.getOwner());
        if (request.getModel() != null) vehicle.setModel(request.getModel());

        Vehicle saved = vehicleRepository.save(vehicle);
        return VehicleMapper.toResponse(saved);
    }

    public void deleteVehicle(String id) {
        if (!vehicleRepository.existsById(id)) {
            throw new VehicleNotFoundException(id);
        }

        // Tear down container via orchestrator
        try {
            containerOrchestrator.tearDown(id);
        } catch (Exception e) {
            log.warn("Container tear-down failed for vehicle {}: {}", id, e.getMessage());
            // Continue with DB deletion even if container removal fails
        }

        vehicleRepository.deleteById(id);

        // Publish event
        eventPublisher.publishEvent(new VehicleEvent(this, VehicleEvent.Type.DELETED, id));

        log.info("Vehicle deleted: {}", id);
    }

    public VehicleResponse updateStatus(String id, String newStatus) {
        Vehicle vehicle = vehicleRepository.findById(id)
                .orElseThrow(() -> new VehicleNotFoundException(id));

        vehicle.setStatus(newStatus);
        Vehicle saved = vehicleRepository.save(vehicle);
        VehicleResponse response = VehicleMapper.toResponse(saved);

        eventPublisher.publishEvent(new VehicleEvent(this, VehicleEvent.Type.STATUS_CHANGED, response));

        log.info("Vehicle {} status changed to: {}", id, newStatus);
        return response;
    }
}
