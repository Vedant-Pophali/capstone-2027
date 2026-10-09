package com.capstone.fleetmanager.repository;

import com.capstone.fleetmanager.model.AppUser;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

/**
 * Spring Data JPA repository for AppUser.
 * Hibernate will create/update the 'users' table automatically via ddl-auto=update.
 */
public interface UserRepository extends JpaRepository<AppUser, Long> {

    Optional<AppUser> findByUsername(String username);

    boolean existsByUsername(String username);
}
