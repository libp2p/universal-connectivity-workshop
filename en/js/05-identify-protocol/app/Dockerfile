FROM node:20-alpine as build
WORKDIR /en/js/05-identify-protocol/app
COPY package*.json ./
RUN npm install
COPY . .

FROM node:20-alpine
WORKDIR /en/js/05-identify-protocol/app
COPY --from=build /en/js/05-identify-protocol/app /en/js/05-identify-protocol/app

# Set environment variables for timeout and log file
ARG TIMEOUT_DURATION=10s
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG LOG_FILE=/app/stdout.log
ENV LOG_FILE=${LOG_FILE}

CMD ["node", "index.js"] 