FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy application files
COPY . .

FROM node:22-alpine

WORKDIR /app

# Copy from builder
COPY --from=builder /app /app

ENV TIMEOUT_DURATION=30s
ENV NODE_ENV=production
ENV KEEPALIVE_MS=30000

CMD ["node", "index.js"]