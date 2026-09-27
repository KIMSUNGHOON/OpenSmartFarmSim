FROM node:22.22.3-bookworm-slim@sha256:e21fc383b50d5347dc7a9f1cae45b8f4e2f0d39f7ade28e4eef7d2934522b752 AS web-deps

WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci --strict-peer-deps

# A production bundle and web server require source and a later build stage.
CMD ["/bin/false"]
