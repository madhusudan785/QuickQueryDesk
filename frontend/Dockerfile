# --- QuickQueryDesk Frontend Dockerfile ---
# Multi-stage build: build static assets with Node, then serve via nginx.

# Stage 1: Build the React/Vite application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first for dependency layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy source files and build for production
COPY . .
RUN npm run build

# Stage 2: Serve with nginx (also handles API/WS reverse proxy)
FROM nginx:alpine

# Copy the built static assets from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
