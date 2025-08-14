FROM python:3.11-slim

# Link this image to a repo
LABEL org.opencontainers.image.source="https://github.com/libp2p/universal-connectivity-workshop"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy checker code
COPY *.py ./

# Configurable timeout duration
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}

ARG REMOTE_ADDR
ENV REMOTE_ADDR=${REMOTE_ADDR}

# Set the command to run with timeout and redirect output
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} python checker.py > /app/checker.log 2>&1"]