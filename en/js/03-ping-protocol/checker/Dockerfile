FROM node:22-alpine AS builder

WORKDIR /app

COPY ./checker/package*.json ./
RUN npm install

COPY ./checker/ .

FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app /app

ARG TIMEOUT_DURATION=30s
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG LOG_FILE=/app/checker.log
ENV LOG_FILE=${LOG_FILE}

CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} node index.js"]