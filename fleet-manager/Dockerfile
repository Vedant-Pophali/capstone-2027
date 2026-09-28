FROM maven:3.9.6-eclipse-temurin-17-alpine AS builder
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /build/target/fleet-manager-0.0.1-SNAPSHOT.jar app.jar
# We need docker CLI inside the container if it interacts with the daemon directly
RUN apk add --no-cache docker-cli
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
