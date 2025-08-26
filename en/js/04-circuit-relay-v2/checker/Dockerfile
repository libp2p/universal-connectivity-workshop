FROM node:22-alpine

WORKDIR /app

# Install the same dependencies the user nodes need
COPY ./app/package*.json ./
RUN npm install --omit=dev

# Copy checker script and user node files
COPY ./checker/index.js ./
COPY ./app/listener.js ./
COPY ./app/dialer.js ./

CMD ["node", "index.js"]
