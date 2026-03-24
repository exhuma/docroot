FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Optional build-time metadata exposed to the SPA.
# Pass with: docker build \
#   --build-arg VITE_GITHUB_REPO_URL=https://github.com/… \
#   --build-arg VITE_APP_COMMIT=$(git rev-parse --short HEAD) \
#   --build-arg VITE_APP_BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ARG VITE_GITHUB_REPO_URL
ARG VITE_APP_COMMIT
ARG VITE_APP_BUILD_TIME
RUN npm run build-only

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
