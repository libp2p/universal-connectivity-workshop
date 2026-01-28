#!/bin/bash
# Build the cpp-libp2p base image
# Run this once, then all lessons will build quickly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building cpp-libp2p base image..."
echo "This will take 20-40 minutes on first run, but only needs to be done once."
echo ""

docker build \
    --platform linux/amd64 \
    -t cpp-libp2p-base:latest \
    -f "${SCRIPT_DIR}/Dockerfile" \
    "${SCRIPT_DIR}"

echo ""
echo "Base image built successfully!"
echo "You can now build lessons quickly using: docker compose up --build"
