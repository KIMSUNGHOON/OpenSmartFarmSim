FROM python:3.12.13-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2 AS backend-deps

COPY --from=ghcr.io/astral-sh/uv:0.11.14@sha256:1025398289b62de8269e70c45b91ffa37c373f38118d7da036fb8bb8efc85d97 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# C0 selects this dependency target explicitly.
CMD ["/bin/false"]

FROM python:3.12.13-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2 AS backend-app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=backend-deps /app/.venv /app/.venv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/app/ ./app/
COPY contracts/*.json /app/contracts/
COPY fixtures/*.json /app/fixtures/
COPY LICENSE /app/LICENSE
USER 11001:11010
CMD ["python", "-m", "app.api_serve", "--factory", "app.operator_config:api_service"]
