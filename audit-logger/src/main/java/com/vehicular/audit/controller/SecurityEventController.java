package com.vehicular.audit.controller;

import com.vehicular.audit.dto.SecurityEventDto;
import com.vehicular.audit.service.SecurityEventService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/audit")
public class SecurityEventController {

    private final SecurityEventService service;

    public SecurityEventController(SecurityEventService service) {
        this.service = service;
    }

    @PostMapping("/event")
    public ResponseEntity<SecurityEventDto> createEvent(@RequestBody SecurityEventDto dto) {
        SecurityEventDto savedDto = service.saveEvent(dto);
        return new ResponseEntity<>(savedDto, HttpStatus.CREATED);
    }
}
