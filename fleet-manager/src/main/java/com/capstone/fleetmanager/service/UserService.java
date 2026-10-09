package com.capstone.fleetmanager.service;

import com.capstone.fleetmanager.dto.AuthResponse;
import com.capstone.fleetmanager.dto.LoginRequest;
import com.capstone.fleetmanager.dto.RegisterRequest;
import com.capstone.fleetmanager.model.AppUser;
import com.capstone.fleetmanager.repository.UserRepository;
import com.capstone.fleetmanager.security.JwtUtil;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

/**
 * Business logic for user registration and login.
 *
 * Password policy (also enforced at the DTO layer via Bean Validation):
 *   - Minimum 6 characters
 *   - At least one uppercase letter
 *   - At least one digit
 *   - At least one special character
 *
 * Passwords are NEVER stored in plain text; only their BCrypt hash is
 * persisted in the 'users' table.
 */
@Service
public class UserService {

    private static final String PASSWORD_POLICY_REGEX =
            "^(?=.*[A-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?]).{6,}$";

    private final UserRepository  userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil         jwtUtil;

    public UserService(UserRepository userRepository,
                       PasswordEncoder passwordEncoder,
                       JwtUtil jwtUtil) {
        this.userRepository  = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtil         = jwtUtil;
    }

    /**
     * Register a new user.
     *
     * @param request validated registration payload
     * @return JWT + user info
     * @throws ResponseStatusException 409 if username already exists, 400 on policy violation
     */
    public AuthResponse register(RegisterRequest request) {
        String username = request.username().toLowerCase().trim();

        // Duplicate-username check
        if (userRepository.existsByUsername(username)) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT, "Username '" + username + "' is already taken");
        }

        // Double-check password policy at the service layer (defence-in-depth,
        // in case the DTO constraint is bypassed in tests or programmatic calls).
        if (!request.password().matches(PASSWORD_POLICY_REGEX)) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Password must be at least 6 characters and contain at least one " +
                    "uppercase letter, one digit, and one special character");
        }

        // Hash the password with BCrypt (strength 12, configured in SecurityConfig)
        String hash = passwordEncoder.encode(request.password());

        AppUser user = new AppUser(username, hash, request.role().toUpperCase());
        userRepository.save(user);

        String token = jwtUtil.generateToken(username, user.getRole());
        return new AuthResponse(token, username, user.getRole(), jwtUtil.getExpirationSeconds());
    }

    /**
     * Authenticate an existing user.
     *
     * @param request login credentials
     * @return JWT + user info
     * @throws ResponseStatusException 401 for bad credentials
     */
    public AuthResponse login(LoginRequest request) {
        String username = request.username().toLowerCase().trim();

        AppUser user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.UNAUTHORIZED, "Invalid username or password"));

        // BCrypt's matches() runs the same hash algorithm and compares — constant-time safe
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new ResponseStatusException(
                    HttpStatus.UNAUTHORIZED, "Invalid username or password");
        }

        String token = jwtUtil.generateToken(username, user.getRole());
        return new AuthResponse(token, username, user.getRole(), jwtUtil.getExpirationSeconds());
    }
}
