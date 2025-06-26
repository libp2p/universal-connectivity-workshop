FROM rust:1.87 AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Cargo.toml and src directory
COPY Cargo.toml .
COPY src ./src

# Build the app
RUN cargo build

# Get the name of the application from Cargo.toml
RUN APP_NAME=$(awk '/^name = / {gsub(/"/, "", $3); print $3}' Cargo.toml) && \
    cp /app/target/debug/"$APP_NAME" /app/target/debug/checker

# Final stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/target/debug/checker /app/checker

# Configurable timeout duration
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG REMOTE_ADDR
ENV REMOTE_ADDR=${REMOTE_ADDR}

# Set the command to run with timeout and redirect output
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} /app/checker > /app/checker.log 2>&1"]