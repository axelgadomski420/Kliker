FROM openresty/openresty:alpine

RUN apk add --no-cache curl

RUN mkdir -p /usr/share/nginx/html /var/log/nginx

# Skopiuj wszystkie pliki .ovpn i auth.txt
COPY vpnbook/ /vpnbook/

# Skopiuj konfigurację nginx z odpowiednich ścieżek w repozytorium
COPY nginx/nginx.conf                     /usr/local/openresty/nginx/conf/nginx.conf
COPY nginx/conf.d/                        /usr/local/openresty/nginx/conf/conf.d/

# Skopiuj pliki frontend dashboard
COPY web/                                 /usr/share/nginx/html/

RUN chmod -R 755 /usr/share/nginx/html /vpnbook

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost/stats || exit 1

EXPOSE 80

CMD ["openresty", "-g", "daemon off;"]
