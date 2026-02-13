# Build context: project root
FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend .

# Vite proxy target will be overridden by env in docker-compose
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
