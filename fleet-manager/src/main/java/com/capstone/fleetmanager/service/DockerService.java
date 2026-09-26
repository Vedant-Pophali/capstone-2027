package com.capstone.fleetmanager.service;

import org.springframework.stereotype.Service;
import java.io.BufferedReader;
import java.io.InputStreamReader;

@Service
public class DockerService {

    public String spinUpContainer(String vehicleId) throws Exception {
        String command = String.format("docker run -d --name vehicle_%s --network capstone-2027_default -e VEHICLE_ID=%s -e PAYLOAD_TYPE=THREAT_ALERT capstone-2027-edge-vehicle-base", vehicleId, vehicleId);
        Process process = Runtime.getRuntime().exec(command);
        
        // Read output BEFORE waitFor to prevent stream buffer deadlock
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        String containerId = reader.readLine();

        process.waitFor();
        
        if (process.exitValue() != 0) {
            BufferedReader errReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = errReader.readLine()) != null) sb.append(line);
            throw new Exception("Docker run failed: " + sb.toString());
        }

        return containerId;
    }

    public void removeContainer(String vehicleId) throws Exception {
        String command = String.format("docker rm -f vehicle_%s", vehicleId);
        Process process = Runtime.getRuntime().exec(command);
        
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        while (reader.readLine() != null) {} // drain output

        process.waitFor();
        
        if (process.exitValue() != 0) {
            throw new Exception("Docker rm failed");
        }
    }
}
