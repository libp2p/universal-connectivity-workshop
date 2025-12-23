FROM node:22-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install --production

# Copy application files
COPY . .

# Set environment variables
ENV TIMEOUT_DURATION=30s
ENV NODE_ENV=production

# Run the Kademlia DHT lesson
CMD ["node", "index.js"]