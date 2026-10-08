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
 * Role hierarchy:
 *   ADMIN    – all operations, including user management endpoints (future)
 *   OPERATOR – vehicle CRUD (POST / PUT / PATCH / DELETE on /api/vehicles/**)
 *   VIEWER   – read-only GET requests
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
                // Disable CSRF — not needed for stateless REST APIs
                .csrf(AbstractHttpConfigurer::disable)

                // Stateless session — no HttpSession, no cookies
                .sessionManagement(sm ->
                        sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                // Authorisation rules
                .authorizeHttpRequests(auth -> auth

                        // --- Public auth endpoints ---
                        .requestMatchers("/api/auth/**").permitAll()

                        // --- Dashboard: read-only, public ---
                        .requestMatchers(HttpMethod.GET, "/api/dashboard/**").permitAll()

                        // --- PUF auth endpoints: any authenticated user ---
                        .requestMatchers("/api/puf/**").authenticated()

                        // --- Vehicles: read = VIEWER+, write = OPERATOR+ ---
                        .requestMatchers(HttpMethod.GET, "/api/vehicles/**")
                                .hasAnyRole("VIEWER", "OPERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.POST, "/api/vehicles/**")
                                .hasAnyRole("OPERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/vehicles/**")
                                .hasAnyRole("OPERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.PATCH, "/api/vehicles/**")
                                .hasAnyRole("OPERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/vehicles/**")
                                .hasAnyRole("OPERATOR", "ADMIN")

                        // --- Anything else requires at least authentication ---
                        .anyRequest().authenticated()
                )

                // Insert JWT filter before the standard username/password filter
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)

                .build();
    }
}
