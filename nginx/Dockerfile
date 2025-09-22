# nginx/Dockerfile

FROM openresty/openresty:alpine

RUN apk add --no-cache curl

# Stwórz potrzebne katalogi
RUN mkdir -p /usr/share/nginx/html /var/log/nginx

# Skopiuj VPN pliki
COPY ../vpnbook/ /vpnbook/

# Skopiuj konfiguracje nginx z katalogu nginx/
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY conf.d/    /usr/local/openresty/nginx/conf/conf.d/

# Skopiuj pliki web dashboard
COPY ../web/    /usr/share/nginx/html/

RUN chmod -R 755 /usr/share/nginx/html /vpnbook

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost/stats || exit 1

EXPOSE 80

CMD ["openresty", "-g", "daemon off;"]
