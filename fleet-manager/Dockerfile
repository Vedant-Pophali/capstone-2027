# Build stage
FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

# Run stage
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/fleet-manager-0.0.1-SNAPSHOT.jar app.jar
# We need docker CLI inside the container if it interacts with the daemon directly
RUN apk add --no-cache docker-cli
EXPOSE 8085
ENTRYPOINT ["java", "-jar", "app.jar"]
