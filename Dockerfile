# nginx/Dockerfile

# 1. Użyj OpenResty (Nginx + Lua) na Alpine
FROM openresty/openresty:alpine

# 2. Zainstaluj curl (do health checków i testów)
RUN apk add --no-cache curl

# 3. Stwórz katalogi na pliki statyczne i VPN
RUN mkdir -p /usr/share/nginx/html /vpnbook /var/log/nginx

# 4. Skopiuj pliki OpenVPN i auth.txt
COPY vpnbook/*.ovpn /vpnbook/
COPY vpnbook/auth.txt     /vpnbook/

# 5. Skopiuj konfigurację nginx
COPY nginx.conf                      /usr/local/openresty/nginx/conf/nginx.conf
COPY conf.d/                         /usr/local/openresty/nginx/conf/conf.d/

# 6. Skopiuj dashboard web
COPY web/                            /usr/share/nginx/html/

# 7. Uprawnienia
RUN chmod -R 755 /usr/share/nginx/html /vpnbook

# 8. Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost/stats || exit 1

# 9. Expose port 80
EXPOSE 80

# 10. Start OpenResty (Nginx + Lua)
CMD ["openresty", "-g", "daemon off;"]
