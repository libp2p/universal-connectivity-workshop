FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the checker code
COPY main.py .

# Configurable timeout duration
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG REMOTE_PEERS
ENV REMOTE_PEERS=${REMOTE_PEERS}

# Set the command to run with timeout and redirect output
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} python /app/main.py > /app/checker.log 2>&1"]