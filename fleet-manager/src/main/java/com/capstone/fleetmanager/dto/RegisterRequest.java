package com.capstone.fleetmanager.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * Payload for POST /api/auth/register
 *
 * Password rules (enforced via Bean Validation):
 *   - Minimum 6 characters
 *   - At least one uppercase letter (A-Z)
 *   - At least one digit (0-9)
 *   - At least one special character (!@#$%^&*...)
 *
 * Only one role exists: ADMIN.
 */
public record RegisterRequest(

        @NotBlank(message = "Username is required")
        @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
        String username,

        /**
         * Raw password — validated here, then immediately hashed; never persisted as-is.
         *
         * Regex breakdown:
         *   (?=.*[A-Z])   – at least one uppercase letter
         *   (?=.*\d)      – at least one digit
         *   (?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]) – at least one special char
         *   .{6,}         – minimum 6 characters total
         */
        @NotBlank(message = "Password is required")
        @Pattern(
            regexp  = "^(?=.*[A-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?]).{6,}$",
            message = "Password must be at least 6 characters and contain at least one uppercase letter, one digit, and one special character"
        )
        String password,

        /**
         * Role to assign. Only ADMIN is accepted.
         */
        @NotBlank(message = "Role is required")
        @Pattern(regexp = "ADMIN", message = "Only the ADMIN role is supported")
        String role
) {}
