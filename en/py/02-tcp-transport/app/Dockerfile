FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Configurable timeout duration
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG REMOTE_ADDR
ENV REMOTE_ADDR=${REMOTE_ADDR}

# Set the command to run with timeout and redirect output
CMD ["/bin/sh", "-c", "sleep 5 && timeout ${TIMEOUT_DURATION} python /app/main.py > /app/stdout.log 2>&1"]