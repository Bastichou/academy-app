FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY src/ /usr/share/nginx/html/
# Renders config.js from the API_BASE env var at container startup.
COPY --chmod=0755 docker-entrypoint.d/40-api-base.sh /docker-entrypoint.d/40-api-base.sh
