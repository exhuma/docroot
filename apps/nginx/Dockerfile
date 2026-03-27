FROM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# Build-time metadata forwarded from docker build --build-arg.
ARG VITE_GITHUB_REPO_URL
ARG VITE_APP_COMMIT
ARG VITE_APP_BUILD_TIME
RUN npm run build-only

FROM nginx:1.27-alpine
# The entrypoint script runs envsubst on *.conf.template files in
# /etc/nginx/templates/ and writes them to /etc/nginx/conf.d/.
# API_HOST (default: api) and API_PORT (default: 8000) can be
# overridden at runtime — set API_HOST=localhost when the API
# container shares the same pod network namespace (k8s single-pod).
# DOCROOT_WEB_OIDC_ISSUER and DOCROOT_WEB_OIDC_CLIENT_ID are
# written to /usr/share/nginx/html/oidc-config.json by the startup
# script in /docker-entrypoint.d/ so the SPA can fetch them without
# hitting the backend API.
ENV API_HOST=api API_PORT=8000 \
    DOCROOT_WEB_OIDC_ISSUER="" DOCROOT_WEB_OIDC_CLIENT_ID=""
COPY nginx/templates/default.conf.template /etc/nginx/templates/default.conf.template
COPY nginx/docker-entrypoint.d/15-generate-oidc-config.sh \
    /docker-entrypoint.d/15-generate-oidc-config.sh
COPY --from=frontend /app/dist /usr/share/nginx/html
