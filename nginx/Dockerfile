FROM openresty/openresty:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create directories
RUN mkdir -p /usr/share/nginx/html /var/log/nginx

# Copy VPN files (ensure vpnbook/ is a folder in your repo)
COPY vpnbook/ /vpnbook/

# Copy Nginx config
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY conf.d/      /usr/local/openresty/nginx/conf/conf.d/

# Copy static web files
COPY web/         /usr/share/nginx/html/

# Set permissions
RUN chmod -R 755 /usr/share/nginx/html /vpnbook

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost/stats || exit 1

EXPOSE 80

CMD ["openresty", "-g", "daemon off;"]
