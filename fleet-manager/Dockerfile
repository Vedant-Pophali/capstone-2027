FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/fleet-manager-0.0.1-SNAPSHOT.jar app.jar
# We need docker CLI inside the container if it interacts with the daemon directly
RUN apk add --no-cache docker-cli
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
