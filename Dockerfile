FROM alpine:3.18

# 1. Instalacja niezbędnych pakietów
RUN apk add --no-cache \
    openresty \
    openresty-openssl \
    openresty-resty \
    openvpn \
    python3 \
    py3-pip \
    supervisor \
    curl

# 2. Utworzenie struktury katalogów
RUN mkdir -p /app /vpnbook /usr/local/openresty/nginx/conf/conf.d /var/log/supervisor

WORKDIR /app

# 3. Skopiowanie plików aplikacji
COPY ai-clicker/       /app/ai-clicker/
COPY vpnbook/          /vpnbook/
COPY web/              /app/web/
COPY nginx.conf        /usr/local/openresty/nginx/conf/nginx.conf
COPY conf.d/           /usr/local/openresty/nginx/conf/conf.d/

# 4. Instalacja zależności Pythona
RUN pip3 install --no-cache-dir -r /app/ai-clicker/requirements.txt

# 5. Supervisor: plik konfiguracyjny
COPY supervisord.conf  /etc/supervisord.conf

# 6. Uprawnienia
RUN chmod -R 755 /app /vpnbook

# 7. Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost/stats || exit 1

EXPOSE 80 5000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
