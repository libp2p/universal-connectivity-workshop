FROM node:22-alpine

ARG LESSON_PATH

WORKDIR /app

# Copy package files
COPY ${LESSON_PATH}/app/package*.json ./

# Install dependencies
RUN npm install --production

# Copy application files
COPY ${LESSON_PATH}/app/ .

# Set environment variables
ENV INTERACTIVE=false
ENV TIMEOUT_DURATION=60
ENV NODE_ENV=production

# Run the application
CMD ["node", "index.js"]

