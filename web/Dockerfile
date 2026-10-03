FROM node:22.22.3-bookworm-slim@sha256:e21fc383b50d5347dc7a9f1cae45b8f4e2f0d39f7ade28e4eef7d2934522b752 AS web-deps

WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci --strict-peer-deps

# C0 selects this dependency target explicitly.
CMD ["/bin/false"]

FROM web-deps AS web-build
COPY web/index.html web/tsconfig.json web/vite.config.ts web/playwright.config.ts ./
COPY web/src/ ./src/
COPY web/e2e/ ./e2e/
COPY web/public/licenses/ ./public/licenses/
RUN npm run build

FROM nginx:1.30.5-trixie@sha256:b972f831f200b19ef0767938224f9711e74cd783718738cd7405d5cabf75c442 AS web-app
RUN rm /usr/share/nginx/html/index.html /usr/share/nginx/html/50x.html
COPY --from=web-build /app/dist/ /usr/share/nginx/html/
COPY web/nginx.conf /etc/nginx/nginx.conf
USER 11002:11002
EXPOSE 8444
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
