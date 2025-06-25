FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Install common dependencies for the workshop
RUN pip install cryptography base58 aiohttp

# Copy the application
COPY . .

# Final stage
FROM python:3.9-slim

# Install runtime dependencies  
RUN apt-get update && apt-get install -y \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application
COPY . .

# Configurable timeout duration
ARG TIMEOUT_DURATION=10s
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}

# Set the command to run with timeout and redirect output
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} python app/main.py > stdout.log 2>&1"]