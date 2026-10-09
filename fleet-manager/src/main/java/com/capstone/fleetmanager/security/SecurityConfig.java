package com.capstone.fleetmanager.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Spring Security configuration — stateless JWT-based auth.
 *
 * Single role: ADMIN — all operations require this role.
 *
 * Public endpoints (no token required):
 *   POST /api/auth/login
 *   POST /api/auth/register
 *   GET  /api/dashboard/**   (metrics dashboard — intentionally public for now)
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;

    public SecurityConfig(JwtAuthFilter jwtAuthFilter) {
        this.jwtAuthFilter = jwtAuthFilter;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        // BCrypt with strength 12 — good balance of security vs. login latency
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
                // Enable CORS so preflight OPTIONS requests are allowed
                .cors(org.springframework.security.config.Customizer.withDefaults())

                // Disable CSRF — not needed for stateless REST APIs
                .csrf(csrf -> csrf.disable())

                // Stateless session — no HttpSession, no cookies
                .sessionManagement(sm ->
                        sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                // Authorisation rules
                .authorizeHttpRequests(auth -> auth

                        // --- Public auth endpoints ---
                        .requestMatchers("/api/auth/**").permitAll()

                        // --- Dashboard: read-only, public ---
                        .requestMatchers(HttpMethod.GET, "/api/dashboard/**").permitAll()

                        // --- WebSockets ---
                        .requestMatchers("/ws/**").permitAll()

                        // --- All other endpoints require ADMIN role ---
                        .anyRequest().hasRole("ADMIN")
                )

                // Insert JWT filter before the standard username/password filter
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)

                .build();
    }
}
