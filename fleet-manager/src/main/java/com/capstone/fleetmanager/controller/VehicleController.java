package com.capstone.fleetmanager.controller;

import com.capstone.fleetmanager.dto.VehicleRequest;
import com.capstone.fleetmanager.dto.VehicleResponse;
import com.capstone.fleetmanager.service.VehicleService;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST controller for vehicle CRUD operations.
 * Thin layer — delegates all business logic to VehicleService.
 * Error handling is in GlobalExceptionHandler, not here.
 */
@RestController
@RequestMapping("/api/vehicles")
public class VehicleController {

    private final VehicleService vehicleService;

    public VehicleController(VehicleService vehicleService) {
        this.vehicleService = vehicleService;
    }

    @GetMapping
    public ResponseEntity<List<VehicleResponse>> getAll() {
        return ResponseEntity.ok(vehicleService.getAllVehicles());
    }

    @GetMapping("/{id}")
    public ResponseEntity<VehicleResponse> getById(@PathVariable String id) {
        return ResponseEntity.ok(vehicleService.getVehicle(id));
    }

    @PostMapping
    public ResponseEntity<VehicleResponse> create(@Valid @RequestBody VehicleRequest request) {
        VehicleResponse created = vehicleService.createVehicle(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    public ResponseEntity<VehicleResponse> update(@PathVariable String id,
                                                   @RequestBody VehicleRequest request) {
        return ResponseEntity.ok(vehicleService.updateVehicle(id, request));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        vehicleService.deleteVehicle(id);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<VehicleResponse> updateStatus(@PathVariable String id,
                                                         @RequestBody Map<String, String> body) {
        String newStatus = body.get("status");
        if (newStatus == null || newStatus.isBlank()) {
            throw new IllegalArgumentException("Status field is required");
        }
        return ResponseEntity.ok(vehicleService.updateStatus(id, newStatus));
    }
}
