package com.capstone.fleetmanager.orchestrator;

import com.capstone.fleetmanager.exception.ContainerOperationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Docker-based implementation of the ContainerOrchestrator strategy.
 * Uses ProcessBuilder (not Runtime.exec) for safer subprocess management.
 * Sanitization happens at the DTO validation layer — IDs are guaranteed alphanumeric.
 *
 * Configuration (via environment variables or application.properties):
 *   ORCHESTRATOR_IMAGE_NAME   — Docker image to spin up per vehicle (default: capstone-2027-edge-vehicle-base)
 *   ORCHESTRATOR_NETWORK_NAME — Docker network to attach containers to (default: capstone-2027_default, leave blank for none)
 */
@Component
public class DockerContainerOrchestrator implements ContainerOrchestrator {

    private static final Logger log = LoggerFactory.getLogger(DockerContainerOrchestrator.class);
    private static final long TIMEOUT_SECONDS = 60;

    private final String imageName;
    private final String networkName;

    public DockerContainerOrchestrator(
            @Value("${orchestrator.image-name:capstone-2027-edge-vehicle-base}") String imageName,
            @Value("${orchestrator.network-name:capstone-2027_default}") String networkName) {
        this.imageName   = imageName;
        this.networkName = networkName;
    }

    @Override
    public String spinUp(String vehicleId) throws Exception {
        String containerName = "vehicle_" + vehicleId;

        log.info("Spinning up container '{}' from image '{}'", containerName, imageName);

        List<String> cmd = new ArrayList<>(List.of(
            "docker", "run", "-d",
            "--name", containerName
        ));

        // Only attach to a named network if one is configured
        if (networkName != null && !networkName.isBlank()) {
            cmd.add("--network");
            cmd.add(networkName);
        }

        cmd.addAll(List.of(
            "-e", "VEHICLE_ID=" + vehicleId,
            "-e", "PAYLOAD_TYPE=THREAT_ALERT",
            imageName
        ));

        ProcessBuilder pb = new ProcessBuilder(cmd);
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