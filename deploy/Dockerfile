# Trader image (B-fast). Pinned base and uv by digest; locked dependencies; non-root.
FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
COPY --from=ghcr.io/astral-sh/uv:0.11.32@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
# review F3: the trader user and its writable output folder (the traderout volume) first
RUN useradd --uid 10001 --create-home trader && mkdir -p /app/out && chown trader:trader /app/out
# review F11: dependencies in their own layer (a code change does not reinstall them)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY trader ./trader
# L6 (security review): the forecast method note the app renders at /forecast-method
COPY docs/FORECAST_BANDS.md ./docs/FORECAST_BANDS.md
# BF-D89: the research pages' content (read-only; .md and .yaml only, checked in CI)
COPY docs/research ./docs/research
RUN uv sync --locked --no-dev && chown -R trader:trader /app/.venv
# review F22: the commit the image was built from (bigwins passes it; strategy fingerprint)
ARG BUILD_SHA=unknown
RUN printf '%s\n' "$BUILD_SHA" > /app/trader/_build_sha.txt
USER trader
