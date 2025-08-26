FROM node:22.9.0-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

FROM node:22.9.0-alpine

WORKDIR /app

COPY --from=builder /app /app

CMD ["/bin/sh", "-c", "node generate_peer_id.js && node relay.js > /app/relay.log 2>&1 & sleep 2 && cat /app/relay.log && tail -f /dev/null"] 