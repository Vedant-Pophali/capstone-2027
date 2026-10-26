package com.capstone.fleetmanager.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Centralized exception handler for all REST controllers.
 * Produces consistent, structured JSON error responses.
 */
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(VehicleNotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleVehicleNotFound(VehicleNotFoundException ex) {
        return buildResponse(HttpStatus.NOT_FOUND, "VEHICLE_NOT_FOUND", ex.getMessage());
    }

    @ExceptionHandler(ContainerOperationException.class)
    public ResponseEntity<Map<String, Object>> handleContainerOperation(ContainerOperationException ex) {
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "CONTAINER_ERROR", ex.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgument(IllegalArgumentException ex) {
        return buildResponse(HttpStatus.BAD_REQUEST, "BAD_REQUEST", ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException ex) {
        String details = ex.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getDefaultMessage() != null ? error.getDefaultMessage() : "Invalid field")
                .collect(Collectors.joining("; "));
        return buildResponse(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", details);
    }

    @ExceptionHandler(org.springframework.web.server.ResponseStatusException.class)
    public ResponseEntity<Map<String, Object>> handleResponseStatus(
            org.springframework.web.server.ResponseStatusException ex) {
        HttpStatus status = HttpStatus.valueOf(ex.getStatusCode().value());
        return buildResponse(status, status.getReasonPhrase().toUpperCase().replace(" ", "_"),
                ex.getReason() != null ? ex.getReason() : ex.getMessage());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneral(Exception ex) {
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR",
                "An unexpected error occurred: " + ex.getMessage());
    }

    private ResponseEntity<Map<String, Object>> buildResponse(HttpStatus status, String error, String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now().toString());
        body.put("status", status.value());
        body.put("error", error);
        body.put("message", message);
        return ResponseEntity.status(status).body(body);
    }
}
