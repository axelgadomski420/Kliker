FROM openresty/openresty:alpine

RUN apk add --no-cache curl
RUN mkdir -p /usr/share/nginx/html /var/log/nginx

# VPN files
COPY ../vpnbook/ /vpnbook/

# Nginx config
COPY nginx/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY nginx/conf.d/    /usr/local/openresty/nginx/conf/conf.d/

# Frontend
COPY ../web/          /usr/share/nginx/html/

RUN chmod -R 755 /usr/share/nginx/html /vpnbook

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost/stats || exit 1

EXPOSE 80
CMD ["openresty","-g","daemon off;"]
