# Multi-stage build for jvm-libp2p application
FROM gradle:8.5-jdk21 AS builder

# Configure DNS and networking
ENV GRADLE_OPTS="-Dorg.gradle.daemon=false -Dorg.gradle.parallel=true -Dorg.gradle.caching=true"

# Set working directory
WORKDIR /app

# Copy Gradle wrapper and build files first (for layer caching)
COPY build.gradle.kts ./
COPY gradle.properties ./
COPY gradle/ ./gradle/
COPY gradlew* ./

# Download dependencies separately (cached layer)
RUN gradle dependencies --no-daemon --refresh-dependencies || true

# Copy source code
COPY src/ ./src/

# Build the application (creates fat JAR with dependencies)
RUN gradle clean build --no-daemon --stacktrace --info

# Find the built JAR (handle different naming)
RUN find build/libs -name "*.jar" -type f ! -name "*-plain.jar" -exec cp {} /app/app.jar \;

# Verify JAR exists
RUN test -f /app/app.jar && echo "JAR built successfully" || (echo "JAR not found!" && exit 1)

# Final stage - minimal JRE image
FROM eclipse-temurin:21-jre-alpine

# Install timeout utility
RUN apk --no-cache add coreutils

WORKDIR /app

# Copy the fat JAR from builder
COPY --from=builder /app/app.jar /app/app.jar

# Verify JAR in final image
RUN test -f /app/app.jar && echo "JAR copied successfully" || (echo "JAR missing in final image!" && exit 1)

# Run the application
CMD ["java", "-jar", "/app/app.jar"]
