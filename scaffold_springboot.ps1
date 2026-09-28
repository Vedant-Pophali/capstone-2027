$rootDir = "d:\capstone-2027\fleet-manager"
$srcDir = "$rootDir\src\main\java\com\capstone\fleetmanager"
$resDir = "$rootDir\src\main\resources"

New-Item -ItemType Directory -Force -Path $srcDir\controller | Out-Null
New-Item -ItemType Directory -Force -Path $srcDir\model | Out-Null
New-Item -ItemType Directory -Force -Path $srcDir\repository | Out-Null
New-Item -ItemType Directory -Force -Path $srcDir\service | Out-Null
New-Item -ItemType Directory -Force -Path $resDir | Out-Null

$pom = @"
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.3</version>
        <relativePath/> <!-- lookup parent from repository -->
    </parent>
    <groupId>com.capstone</groupId>
    <artifactId>fleet-manager</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>fleet-manager</name>
    <description>Spring Boot Backend for Capstone Fleet CRUD</description>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"@
Set-Content -Path "$rootDir\pom.xml" -Value $pom

$appProps = @"
spring.application.name=fleet-manager
server.port=8080

spring.datasource.url=jdbc:h2:mem:fleetdb
spring.datasource.driverClassName=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=
spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
spring.h2.console.enabled=true
"@
Set-Content -Path "$resDir\application.properties" -Value $appProps

$appJava = @"
package com.capstone.fleetmanager;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class FleetManagerApplication {
    public static void main(String[] args) {
        SpringApplication.run(FleetManagerApplication.class, args);
    }
}
"@
Set-Content -Path "$srcDir\FleetManagerApplication.java" -Value $appJava

$modelJava = @"
package com.capstone.fleetmanager.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.time.LocalDateTime;

@Entity
public class Vehicle {
    @Id
    private String id;
    private String status;
    private String containerId;
    private LocalDateTime addedAt;

    public Vehicle() {}

    public Vehicle(String id, String status, String containerId) {
        this.id = id;
        this.status = status;
        this.containerId = containerId;
        this.addedAt = LocalDateTime.now();
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getContainerId() { return containerId; }
    public void setContainerId(String containerId) { this.containerId = containerId; }
    public LocalDateTime getAddedAt() { return addedAt; }
    public void setAddedAt(LocalDateTime addedAt) { this.addedAt = addedAt; }
}
"@
Set-Content -Path "$srcDir\model\Vehicle.java" -Value $modelJava

$repoJava = @"
package com.capstone.fleetmanager.repository;

import com.capstone.fleetmanager.model.Vehicle;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface VehicleRepository extends JpaRepository<Vehicle, String> {
}
"@
Set-Content -Path "$srcDir\repository\VehicleRepository.java" -Value $repoJava

$dockerServiceJava = @"
package com.capstone.fleetmanager.service;

import org.springframework.stereotype.Service;
import java.io.BufferedReader;
import java.io.InputStreamReader;

@Service
public class DockerService {

    public String spinUpContainer(String vehicleId) throws Exception {
        String command = String.format("docker run -d --name vehicle_%s -e VEHICLE_ID=%s -e PAYLOAD_TYPE=THREAT_ALERT capstone-2027-edge_vehicle", vehicleId, vehicleId);
        Process process = Runtime.getRuntime().exec(command);
        process.waitFor();
        
        if (process.exitValue() != 0) {
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) sb.append(line);
            throw new Exception("Docker run failed: " + sb.toString());
        }

        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        return reader.readLine(); // Returns container ID
    }

    public void removeContainer(String vehicleId) throws Exception {
        String command = String.format("docker rm -f vehicle_%s", vehicleId);
        Process process = Runtime.getRuntime().exec(command);
        process.waitFor();
        
        if (process.exitValue() != 0) {
            throw new Exception("Docker rm failed");
        }
    }
}
"@
Set-Content -Path "$srcDir\service\DockerService.java" -Value $dockerServiceJava

$vehicleServiceJava = @"
package com.capstone.fleetmanager.service;

import com.capstone.fleetmanager.model.Vehicle;
import com.capstone.fleetmanager.repository.VehicleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class VehicleService {

    @Autowired
    private VehicleRepository vehicleRepository;

    @Autowired
    private DockerService dockerService;

    public List<Vehicle> getAllVehicles() {
        return vehicleRepository.findAll();
    }

    public Optional<Vehicle> getVehicle(String id) {
        return vehicleRepository.findById(id);
    }

    public Vehicle addVehicle(String id) throws Exception {
        if (vehicleRepository.existsById(id)) {
            throw new IllegalArgumentException("Vehicle already exists");
        }
        
        // Loosely coupled approach: delegate to docker service to spin up container
        String containerId = dockerService.spinUpContainer(id);
        
        Vehicle vehicle = new Vehicle(id, "Healthy", containerId);
        return vehicleRepository.save(vehicle);
    }

    public void removeVehicle(String id) throws Exception {
        if (!vehicleRepository.existsById(id)) {
            throw new IllegalArgumentException("Vehicle not found");
        }
        
        // Destroy container
        dockerService.removeContainer(id);
        vehicleRepository.deleteById(id);
    }
}
"@
Set-Content -Path "$srcDir\service\VehicleService.java" -Value $vehicleServiceJava

$controllerJava = @"
package com.capstone.fleetmanager.controller;

import com.capstone.fleetmanager.model.Vehicle;
import com.capstone.fleetmanager.service.VehicleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/vehicles")
@CrossOrigin(origins = "*")
public class VehicleController {

    @Autowired
    private VehicleService vehicleService;

    @GetMapping
    public ResponseEntity<List<Vehicle>> getAll() {
        return ResponseEntity.ok(vehicleService.getAllVehicles());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Vehicle> getById(@PathVariable String id) {
        return vehicleService.getVehicle(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{id}")
    public ResponseEntity<?> addVehicle(@PathVariable String id) {
        try {
            Vehicle newVehicle = vehicleService.addVehicle(id);
            return ResponseEntity.ok(newVehicle);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> removeVehicle(@PathVariable String id) {
        try {
            vehicleService.removeVehicle(id);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
"@
Set-Content -Path "$srcDir\controller\VehicleController.java" -Value $controllerJava

$dockerfile = @"
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/fleet-manager-0.0.1-SNAPSHOT.jar app.jar
# We need docker CLI inside the container if it interacts with the daemon directly
RUN apk add --no-cache docker-cli
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
"@
Set-Content -Path "$rootDir\Dockerfile" -Value $dockerfile

Write-Host "Spring Boot microservice created at $rootDir"
