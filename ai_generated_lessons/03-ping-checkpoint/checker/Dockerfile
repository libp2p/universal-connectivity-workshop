FROM rust:1.87 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a minimal Cargo.toml for the checker
RUN echo '[package]' > Cargo.toml && \
    echo 'name = "ping-checker"' >> Cargo.toml && \
    echo 'version = "0.1.0"' >> Cargo.toml && \
    echo 'edition = "2021"' >> Cargo.toml && \
    echo '' >> Cargo.toml && \
    echo '[dependencies]' >> Cargo.toml && \
    echo 'libp2p = { version = "0.55", features = ["ed25519", "tokio", "macros", "ping", "tcp", "noise", "yamux"] }' >> Cargo.toml && \
    echo 'tokio = { version = "1.0", features = ["full"] }' >> Cargo.toml && \
    echo 'anyhow = "1.0"' >> Cargo.toml

# Copy the checker source code
COPY . .
RUN mkdir -p src && cp ${LESSON_PATH}/checker/src/main.rs src/main.rs

# Build the checker
RUN cargo build --release

# Copy the binary with a standard name
RUN cp /app/target/release/ping-checker /app/target/release/checker

# Final stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/target/release/checker /app/checker

# Configurable timeout duration
ARG TIMEOUT_DURATION=30s
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}

# Set the command to run with timeout and redirect output
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} /app/checker > /app/stdout.log 2>&1"]