# Base image with cpp-libp2p pre-built
# Build once, use for all lessons
#
# Two-stage build:
#   Stage 1 (builder) — clones and compiles cpp-libp2p with all build tools
#   Stage 2 (final)   — slim image with only cmake/clang + pre-built artifacts
#
# cpp-libp2p requires GCC 13+ or Clang 18+ for C++20 template support.
# Ubuntu 24.04 provides Clang 18 and GCC 13.

# ============================================================
# Stage 1: Build cpp-libp2p and all Hunter dependencies
# ============================================================
FROM --platform=linux/amd64 ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install all build dependencies (only needed during compilation)
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    cmake \
    git \
    curl \
    zip \
    unzip \
    tar \
    pkg-config \
    libssl-dev \
    ninja-build \
    autoconf \
    automake \
    libtool \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone cpp-libp2p at a known-good commit (separate layer for cache)
# Pinned to master @ 347eb8de (includes Sep 2025 cmake compatibility fix)
WORKDIR /opt
RUN git init cpp-libp2p && cd cpp-libp2p && \
    git remote add origin https://github.com/libp2p/cpp-libp2p.git && \
    git fetch --depth 1 origin 347eb8dedd63f5f163ae11c35c2f08e8ba21a65f && \
    git checkout FETCH_HEAD && \
    # Fix -Werror- typos to -Werror= in all cmake files (Hunter packages included)
    find . \( -name "*.cmake" -o -name "CMakeLists.txt" \) -exec sed -i 's/-Werror-/-Werror=/g' {} +

# Configure, build, and install (ninja is faster than make for parallel builds)
RUN cd /opt/cpp-libp2p && mkdir build && cd build && \
    cmake .. \
        -GNinja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER=clang \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DTESTING=OFF \
        -DEXAMPLES=OFF \
        -DCMAKE_INSTALL_PREFIX=/opt/libp2p-install \
    || (echo "=== CMAKE CONFIGURE FAILED ===" && \
        echo "=== CMakeError.log ===" && cat CMakeFiles/CMakeError.log 2>/dev/null && \
        echo "=== CMakeOutput.log (last 50 lines) ===" && tail -50 CMakeFiles/CMakeOutput.log 2>/dev/null && \
        exit 1) && \
    cmake --build . --parallel $(nproc) && \
    cmake --install .

# Record Hunter install path and clean up build artifacts
# Lessons need: Install/ (libs+headers) and Download/.../cmake/modules
# Lessons do NOT need: Build/ dirs, Source/ dirs, or the cpp-libp2p source tree
RUN HUNTER_DIR=$(find /root/.hunter/_Base -maxdepth 4 -mindepth 4 -type d -name "Install" | head -1) && \
    echo "${HUNTER_DIR}" > /opt/hunter_path.txt && \
    rm -rf /opt/cpp-libp2p && \
    find /root/.hunter/_Base -maxdepth 5 -type d -name "Build" -exec rm -rf {} + 2>/dev/null; \
    true

# ============================================================
# Stage 2: Slim base image for lesson builds
# ============================================================
FROM --platform=linux/amd64 ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install only the tools needed to compile individual lessons
# clang pulls in libstdc++-dev for C++ headers; make is needed for cmake's
# default Unix Makefiles generator used by lesson Dockerfiles
RUN apt-get update && apt-get install -y \
    clang \
    cmake \
    make \
    ninja-build \
    pkg-config \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Default to clang so lesson Dockerfiles don't need to specify compilers
ENV CC=clang CXX=clang++

# Copy pre-built cpp-libp2p installation
COPY --from=builder /opt/libp2p-install /opt/libp2p-install
COPY --from=builder /opt/hunter_path.txt /opt/hunter_path.txt

# Copy Hunter dependencies (Install dirs + cmake modules)
# Lessons reference these via CMAKE_PREFIX_PATH and cmake MODULE_PATH globs
COPY --from=builder /root/.hunter /root/.hunter

WORKDIR /app
