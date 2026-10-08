package com.capstone.fleetmanager.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * Persistent user account stored in the 'users' table.
 * <p>
 * Passwords are stored as a BCrypt hash (60-char string) — never in plain text.
 * Roles drive endpoint-level access control via Spring Security.
 * </p>
 *
 * Supported roles:
 *   ADMIN    – full read/write access, can manage users
 *   OPERATOR – can manage vehicles (create/update/delete)
 *   VIEWER   – read-only access
 */
@Entity
@Table(name = "users", uniqueConstraints = {
        @UniqueConstraint(columnNames = "username")
})
public class AppUser {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** Unique login name. Case-insensitive by convention (stored lowercase). */
    @Column(nullable = false, unique = true, length = 50)
    private String username;

    /**
     * BCrypt-hashed password (prefix $2a$12$...).
     * Stored with strength 12 rounds. Never expose this in API responses.
     */
    @Column(nullable = false, length = 60)
    private String passwordHash;

    /**
     * Role name stored as a plain string (e.g. "ADMIN", "OPERATOR", "VIEWER").
     * Spring Security will prefix it with "ROLE_" when authorising.
     */
    @Column(nullable = false, length = 20)
    private String role;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    public AppUser() {}

    public AppUser(String username, String passwordHash, String role) {
        this.username     = username;
        this.passwordHash = passwordHash;
        this.role         = role;
        this.createdAt    = LocalDateTime.now();
        this.updatedAt    = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    // --- Getters & Setters ---

    public Long getId() { return id; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
