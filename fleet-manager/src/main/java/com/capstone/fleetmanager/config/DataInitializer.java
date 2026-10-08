package com.capstone.fleetmanager.config;

import com.capstone.fleetmanager.model.AppUser;
import com.capstone.fleetmanager.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * Initializes default user account on startup if it does not already exist.
 * Ensures the system is ready to use with default credentials immediately.
 */
@Component
public class DataInitializer implements CommandLineRunner {

    private static final Logger logger = LoggerFactory.getLogger(DataInitializer.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${app.default-user.username:admin}")
    private String defaultUsername;

    @Value("${app.default-user.password}")
    private String defaultPassword;

    @Value("${app.default-user.role:ADMIN}")
    private String defaultRole;

    public DataInitializer(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {
        String normalizedUsername = defaultUsername.toLowerCase().trim();
        if (!userRepository.existsByUsername(normalizedUsername)) {
            String encodedPassword = passwordEncoder.encode(defaultPassword);
            AppUser defaultUser = new AppUser(normalizedUsername, encodedPassword, defaultRole.toUpperCase());
            userRepository.save(defaultUser);
            logger.info("Default user '{}' initialized with role '{}'.", normalizedUsername, defaultRole.toUpperCase());
        } else {
            logger.info("Default user '{}' already exists in the database.", normalizedUsername);
        }
    }
}
