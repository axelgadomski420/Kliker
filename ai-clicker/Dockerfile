# Używamy oficjalnego obrazu OpenResty (NGINX + Lua)
FROM openresty/openresty:alpine

# Instalacja niezbędnych pakietów (curl, openvpn, certyfikaty)
RUN apk add --no-cache \\
    curl \\
    openvpn \\
    ca-certificates \\
    && mkdir -p /usr/share/nginx/html /var/log/nginx /vpnbook

# Kopiowanie plików VPN
COPY --chown=nginx:nginx ../vpnbook/ /vpnbook/

# Konfiguracja NGINX
COPY --chown=nginx:nginx nginx/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY --chown=nginx:nginx nginx/conf.d/    /usr/local/openresty/nginx/conf/conf.d/

# Frontend (statyczne pliki)
COPY --chown=nginx:nginx ../web/          /usr/share/nginx/html/

# Ustawienia uprawnień
RUN chmod -R 755 /usr/share/nginx/html /vpnbook && \\
    chown -R nginx:nginx /usr/share/nginx/html /vpnbook

# Healthcheck (sprawdza dostępność /stats)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
    CMD curl -f http://localhost/stats || exit 1

# Ekspozycja portu 80 (HTTP)
EXPOSE 80

# Uruchomienie OpenResty w trybie foreground
CMD ["openresty", "-g", "daemon off;"]
