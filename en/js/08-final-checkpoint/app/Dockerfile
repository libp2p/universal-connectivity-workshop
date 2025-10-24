FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application files
COPY . .

# Set environment variables
ENV INTERACTIVE=false
ENV TIMEOUT_DURATION=60
ENV NODE_ENV=production

# Run the application
CMD ["node", "index.js"]

