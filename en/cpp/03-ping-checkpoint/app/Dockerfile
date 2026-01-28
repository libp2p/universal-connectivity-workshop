# Lesson 03: Ping Checkpoint
# Uses pre-built base image for fast builds

# Stage 1: Build lesson using pre-built cpp-libp2p base
FROM cpp-libp2p-base AS builder

WORKDIR /app
COPY main.cpp CMakeLists.txt ./

RUN HUNTER_DIR=$(cat /opt/hunter_path.txt) && \
    mkdir build && cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="/opt/libp2p-install;${HUNTER_DIR}" \
        -DBoost_ARCHITECTURE=-x64 && \
    cmake --build . --parallel $(nproc)

# Stage 2: Minimal runtime environment
FROM --platform=linux/amd64 ubuntu:24.04

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/build/lesson /app/lesson
RUN ldconfig 2>/dev/null || true

ENV LISTEN_PORT=9000
ENV REMOTE_PEERS=""

ARG TIMEOUT_DURATION=30s
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}

CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} /app/lesson 2>&1 | tee /app/stdout.log"]
