FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the checker code
COPY checker.py .

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy from builder
COPY --from=builder /app /app

# Configurable environment variables
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG REMOTE_ADDR
ENV REMOTE_ADDR=${REMOTE_ADDR}

# Run the checker
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} python /app/checker.py > /app/checker.log 2>&1"]