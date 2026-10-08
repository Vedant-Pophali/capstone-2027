package com.capstone.fleetmanager.dto;

/**
 * Successful authentication response returned by /api/auth/login and /api/auth/register.
 *
 * The client stores the token and sends it in future requests as:
 *   Authorization: Bearer <token>
 */
public record AuthResponse(
        String token,
        String username,
        String role,
        /** Token validity in seconds (mirrors jwt.expiration-seconds config). */
        long expiresIn
) {}
