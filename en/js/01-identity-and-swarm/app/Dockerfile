FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app /app

ARG LOG_FILE=/app/stdout.log
ENV LOG_FILE=${LOG_FILE}

CMD ["/bin/sh", "-c", "node index.js > ${LOG_FILE} 2>&1"]