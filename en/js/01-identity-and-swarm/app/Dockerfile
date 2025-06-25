    FROM node:20-alpine AS builder

    WORKDIR /en/js/{LESSON_PATH}/app
    
    COPY package.json ./
    RUN npm install
    COPY . .
    
    FROM node:20-alpine
    
    WORKDIR /app
    COPY --from=build /en/js/{LESSON_PATH}/app /en/js/{LESSON_PATH}/app
    
    ARG TIMEOUT_DURATION=10s
    ENV TIMEOUT_DURATION=${TIMEOUT_DURATION}
    ARG LOG_FILE=/app/stdout.log
    ENV LOG_FILE=${LOG_FILE}
    
    CMD ["node", "index.js"]
    