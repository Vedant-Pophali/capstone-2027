package com.capstone.fleetmanager.orchestrator;

import com.capstone.fleetmanager.exception.ContainerOperationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.concurrent.TimeUnit;

/**
 * Docker-based implementation of the ContainerOrchestrator strategy.
 * Uses ProcessBuilder (not Runtime.exec) for safer subprocess management.
 * Sanitization happens at the DTO validation layer — IDs are guaranteed alphanumeric.
 */
@Component
public class DockerContainerOrchestrator implements ContainerOrchestrator {

    private static final Logger log = LoggerFactory.getLogger(DockerContainerOrchestrator.class);
    private static final long TIMEOUT_SECONDS = 60;
    private static final String IMAGE_NAME = "capstone-2027-edge-vehicle-base";
    private static final String NETWORK_NAME = "capstone-2027_default";

    @Override
    public String spinUp(String vehicleId) throws Exception {
        String containerName = "vehicle_" + vehicleId;

        log.info("Spinning up container '{}' from image '{}'", containerName, IMAGE_NAME);

        ProcessBuilder pb = new ProcessBuilder(
            "docker", "run", "-d",
            "--name", containerName,
            "--network", NETWORK_NAME,
            "-e", "VEHICLE_ID=" + vehicleId,
            "-e", "PAYLOAD_TYPE=THREAT_ALERT",
            IMAGE_NAME
        );
        pb.redirectErrorStream(false);

        Process process = pb.start();

        // Read stdout BEFORE waitFor to prevent stream buffer deadlock
        String containerId;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            containerId = reader.readLine();
        }

        boolean finished = process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new ContainerOperationException(
                "Docker run timed out after " + TIMEOUT_SECONDS + "s for vehicle " + vehicleId);
        }

        if (process.exitValue() != 0) {
            String errorOutput = readStream(process);
            throw new ContainerOperationException(
                "Docker run failed for vehicle " + vehicleId + ": " + errorOutput);
        }

        log.info("Container '{}' started with ID: {}", containerName,
                 containerId != null ? containerId.substring(0, Math.min(12, containerId.length())) : "unknown");

        return containerId;
    }

    @Override
    public void tearDown(String vehicleId) throws Exception {
        String containerName = "vehicle_" + vehicleId;

        log.info("Tearing down container '{}'", containerName);

        ProcessBuilder pb = new ProcessBuilder("docker", "rm", "-f", containerName);
        pb.redirectErrorStream(false);

        Process process = pb.start();

        // Drain stdout
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            while (reader.readLine() != null) { /* drain */ }
        }

        boolean finished = process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new ContainerOperationException(
                "Docker rm timed out after " + TIMEOUT_SECONDS + "s for vehicle " + vehicleId);
        }

        if (process.exitValue() != 0) {
            String errorOutput = readStream(process);
            throw new ContainerOperationException(
                "Docker rm failed for vehicle " + vehicleId + ": " + errorOutput);
        }

        log.info("Container '{}' removed successfully", containerName);
    }

    @Override
    public String getStatus(String vehicleId) {
        String containerName = "vehicle_" + vehicleId;

        try {
            ProcessBuilder pb = new ProcessBuilder(
                "docker", "inspect", "-f", "{{.State.Status}}", containerName
            );
            pb.redirectErrorStream(true);

            Process process = pb.start();
            String status;
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                status = reader.readLine();
            }

            boolean finished = process.waitFor(10, TimeUnit.SECONDS);
            if (!finished || process.exitValue() != 0) {
                return "not_found";
            }

            return status != null ? status.trim() : "unknown";

        } catch (Exception e) {
            log.warn("Failed to inspect container '{}': {}", containerName, e.getMessage());
            return "error";
        }
    }

    private String readStream(Process process) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append(" ");
            }
            return sb.toString().trim();
        } catch (Exception e) {
            return "Unable to read error stream";
        }
    }
}
