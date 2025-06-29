FROM node:20-alpine as build
WORKDIR /en/js/{LESSON_PATH}/app
COPY package*.json ./
RUN npm install
COPY . .

FROM node:20-alpine
WORKDIR /en/js/{LESSON_PATH}/app
COPY --from=build /en/js/{LESSON_PATH}/app /en/js/{LESSON_PATH}/app


# Set environment variables for timeout and log file
ARG TIMEOUT_DURATION=10s
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
ARG LOG_FILE=/app/stdout.log
ENV LOG_FILE=${LOG_FILE}

CMD ["node", "index.js"]
