package com.capstone.fleetmanager.controller;

import com.capstone.fleetmanager.dto.AuthResponse;
import com.capstone.fleetmanager.dto.LoginRequest;
import com.capstone.fleetmanager.dto.RegisterRequest;
import com.capstone.fleetmanager.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Authentication REST controller — public endpoints (no token required).
 *
 * POST /api/auth/register  – create a new user account
 * POST /api/auth/login     – authenticate and receive a JWT
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserService userService;

    public AuthController(UserService userService) {
        this.userService = userService;
    }

    /**
     * Register a new user.
     *
     * <pre>
     * POST /api/auth/register
     * {
     *   "username": "alice",
     *   "password": "<your-password>",
     *   "role": "OPERATOR"
     * }
     * </pre>
     *
     * @return 201 Created with JWT on success; 400 on validation error; 409 on duplicate username
     */
    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        AuthResponse response = userService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Authenticate an existing user.
     *
     * <pre>
     * POST /api/auth/login
     * {
     *   "username": "alice",
     *   "password": "<your-password>"
     * }
     * </pre>
     *
     * @return 200 OK with JWT on success; 401 on bad credentials
     */
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        AuthResponse response = userService.login(request);
        return ResponseEntity.ok(response);
    }
}
