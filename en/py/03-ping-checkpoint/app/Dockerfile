FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir libp2p==0.1.0

# Copy the application code
COPY main.py .

# Configurable timeout duration and remote address
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG REMOTE_ADDR
ENV REMOTE_ADDR=${REMOTE_ADDR}

# Set Python to run in unbuffered mode for immediate output
ENV PYTHONUNBUFFERED=1

# Run the application with timeout and redirect output
CMD ["/bin/sh", "-c", "sleep 5 && timeout ${TIMEOUT_DURATION} python -u main.py 2>&1 | tee stdout.log"]