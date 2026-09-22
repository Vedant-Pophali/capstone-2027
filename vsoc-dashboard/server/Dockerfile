FROM node:18-alpine

# Install Docker CLI so the server can spawn vehicle containers
RUN apk add --no-cache docker-cli

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3001

CMD ["node", "index.js"]
