package com.capstone.fleetmanager.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * Payload for POST /api/auth/login
 */
public record LoginRequest(

        @NotBlank(message = "Username is required")
        String username,

        @NotBlank(message = "Password is required")
        String password
) {}
