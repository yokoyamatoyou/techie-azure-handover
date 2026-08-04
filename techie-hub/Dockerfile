# ---------------------------------------------------
# TECHIE HUB — 統合 UI 入口 (nginx)
# ---------------------------------------------------
FROM nginx:1.27-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY config.js  /usr/share/nginx/html/config.js
COPY auth-provider-policy.js /usr/share/nginx/html/auth-provider-policy.js
COPY style.css  /usr/share/nginx/html/style.css
COPY assets/    /usr/share/nginx/html/assets/

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --spider -q http://127.0.0.1:8090/ || exit 1
