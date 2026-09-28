package com.capstone.fleetmanager.event;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Listens for VehicleEvent domain events and broadcasts them via STOMP WebSocket.
 * This class is the only place where business events meet the WebSocket layer.
 * Adding/removing notification channels requires no changes to VehicleService.
 */
@Component
public class WebSocketEventListener {

    private static final Logger log = LoggerFactory.getLogger(WebSocketEventListener.class);

    private final SimpMessagingTemplate messagingTemplate;

    public WebSocketEventListener(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    @EventListener
    public void handleVehicleEvent(VehicleEvent event) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", event.getType().name());
        payload.put("vehicleId", event.getVehicleId());
        payload.put("timestamp", LocalDateTime.now().toString());

        if (event.getVehicle() != null) {
            payload.put("vehicle", event.getVehicle());
        }

        messagingTemplate.convertAndSend("/topic/fleet", payload);

        log.info("Broadcasted {} event for vehicle {}", event.getType(), event.getVehicleId());
    }
}
