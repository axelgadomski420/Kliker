# Start with a base image that includes Python
FROM python:3.9-alpine

# Install system dependencies
RUN apk add --no-cache \\
    curl \\
    openvpn \\
    ca-certificates \\
    gcc \\
    python3-dev \\
    musl-dev \\
    && mkdir -p /usr/share/nginx/html /var/log/nginx /vpnbook

# Install Python dependencies
RUN pip install --no-cache-dir numpy opencv-python pyautogui

# Copy your Python script
COPY clicker.py /app/clicker.py

# Copy VPN files
COPY --chown=nginx:nginx ../vpnbook/ /vpnbook/

# Install OpenResty (NGINX + Lua) if still needed
RUN apk add --no-cache openresty

# Configure NGINX
COPY --chown=nginx:nginx nginx/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY --chown=nginx:nginx nginx/conf.d/    /usr/local/openresty/nginx/conf/conf.d/

# Frontend (static files)
COPY --chown=nginx:nginx ../web/          /usr/share/nginx/html/

# Set permissions
RUN chmod -R 755 /usr/share/nginx/html /vpnbook && \\
    chown -R nginx:nginx /usr/share/nginx/html /vpnbook

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
    CMD curl -f http://localhost/stats || exit 1

# Expose port 80
EXPOSE 80

# Command to run both your Python script and OpenResty
CMD sh -c "python /app/clicker.py & openresty -g 'daemon off;'"
