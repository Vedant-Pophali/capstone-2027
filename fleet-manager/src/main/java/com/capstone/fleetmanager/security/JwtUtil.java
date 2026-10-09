package com.capstone.fleetmanager.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * Stateless JWT utility — generates and validates signed HS256 tokens.
 *
 * Token contents (claims):
 *   sub  – username
 *   role – ADMIN | OPERATOR | VIEWER
 *   iat  – issued-at timestamp
 *   exp  – expiry timestamp
 *
 * The secret is read from application.properties (jwt.secret).
 * In Docker Compose the secret can be injected via an environment variable.
 */
@Component
public class JwtUtil {

    private final SecretKey signingKey;
    private final long expirationSeconds;

    public JwtUtil(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.expiration-seconds:86400}") long expirationSeconds) {

        // Derive a proper HMAC-SHA256 key from the configured secret string.
        // The secret must be at least 32 bytes (256 bits) for HS256.
        this.signingKey       = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expirationSeconds = expirationSeconds;
    }

    /** Build a signed JWT for the given user. */
    public String generateToken(String username, String role) {
        Date now    = new Date();
        Date expiry = new Date(now.getTime() + expirationSeconds * 1000L);

        return Jwts.builder()
                .subject(username)
                .claim("role", role)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(signingKey)
                .compact();
    }

    /** Extract the username (subject) from a token without validating expiry. */
    public String extractUsername(String token) {
        return parseClaims(token).getSubject();
    }

    /** Extract the role claim from a valid token. */
    public String extractRole(String token) {
        return parseClaims(token).get("role", String.class);
    }

    /**
     * Fully validate the token: signature, expiry, and structure.
     *
     * @return true if the token is valid; false otherwise.
     */
    public boolean isValid(String token) {
        try {
            parseClaims(token); // throws on any invalid state
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    public long getExpirationSeconds() {
        return expirationSeconds;
    }

    // -----------------------------------------------------------------------

    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
