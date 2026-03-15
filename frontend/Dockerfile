# --- DEV (desarrollo con hot-reload)
FROM node:20-alpine AS dev

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

EXPOSE 5173
CMD ["npm", "run", "dev"]

# --- PRODUCTION (build + nginx, ~50MB vs ~500MB dev)
FROM node:20-alpine AS builder
WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
