# nim-libp2p base image for workshop lessons
# Multi-stage build to pre-install dependencies

FROM --platform=linux/amd64 ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV CHOOSENIM_NO_ANALYTICS=1
ENV PATH="/root/.nimble/bin:${PATH}"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git gcc g++ make cmake \
    libssl-dev pkg-config ca-certificates \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Nim via choosenim
RUN curl https://nim-lang.org/choosenim/init.sh -sSf | sh -s -- -y 2.0.14

# Verify Nim installation
RUN nim --version && nimble --version

# Create a minimal project to pre-download and cache libp2p dependencies
WORKDIR /opt/nim-cache
RUN echo 'requires "libp2p >= 1.0.0"' > cache.nimble \
    && echo 'import libp2p' > cache.nim \
    && nimble install -y libp2p@#master

# Build the cache file to ensure all dependencies are compiled
RUN nim c --hints:off -d:release cache.nim || true

# Stage 2: Final base image for lessons
FROM --platform=linux/amd64 ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CHOOSENIM_NO_ANALYTICS=1
ENV PATH="/root/.nimble/bin:${PATH}"

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git gcc g++ make cmake \
    libssl-dev pkg-config ca-certificates \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy Nim installation and nimble packages from builder
COPY --from=builder /root/.choosenim /root/.choosenim
COPY --from=builder /root/.nimble /root/.nimble
COPY --from=builder /root/.cache/nim /root/.cache/nim

WORKDIR /app

# Verify Nim is working
RUN nim --version
