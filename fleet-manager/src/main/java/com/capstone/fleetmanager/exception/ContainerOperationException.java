package com.capstone.fleetmanager.exception;

/**
 * Thrown when a Docker/container operation fails (spinUp, tearDown, inspect).
 */
public class ContainerOperationException extends RuntimeException {

    public ContainerOperationException(String message) {
        super(message);
    }

    public ContainerOperationException(String message, Throwable cause) {
        super(message, cause);
    }
}
