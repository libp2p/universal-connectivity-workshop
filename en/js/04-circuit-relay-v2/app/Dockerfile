FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app /app


# Note: CMD is overridden in docker-compose.yaml for each service
# Default to relay.js for backward compatibility
CMD ["node", "relay.js"] 