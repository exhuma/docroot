FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev
COPY src/ src/
# Invoke uvicorn from the project venv directly to avoid uv
# requiring a writable cache directory at container start-up
# (relevant for non-privileged k8s pods with a read-only rootfs).
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
