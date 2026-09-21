package com.vehicular.audit.service;

import com.vehicular.audit.dto.SecurityEventDto;
import com.vehicular.audit.entity.SecurityEvent;
import com.vehicular.audit.repository.SecurityEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class SecurityEventService {

    private static final Logger logger = LoggerFactory.getLogger(SecurityEventService.class);
    private final SecurityEventRepository repository;

    public SecurityEventService(SecurityEventRepository repository) {
        this.repository = repository;
    }

    public SecurityEventDto saveEvent(SecurityEventDto dto) {
        logger.info("Received security event for vehicle: {}", dto.getVehicleId());
        
        SecurityEvent event = new SecurityEvent(
            dto.getVehicleId(),
            dto.getEventType(),
            dto.getTimestamp(),
            dto.getSignature(),
            dto.getDetails()
        );
        
        SecurityEvent savedEvent = repository.save(event);
        
        logger.info("Successfully persisted security event '{}' with ID: {}", savedEvent.getEventType(), savedEvent.getId());
        
        return dto;
    }
}
