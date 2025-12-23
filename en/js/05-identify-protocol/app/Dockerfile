FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app /app

ENV KEEPALIVE_MS=30000

# Note: CMD is overridden in docker-compose.yaml for each service
# Peer IDs should be generated before building (or copy them from host)
CMD ["node", "node1.js"]
