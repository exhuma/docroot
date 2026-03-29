FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Never let uv download a managed Python binary; always use the
# system Python from the base image.  This prevents the
# "Could not find platform independent libraries" error in k8s
# environments where downloaded binaries may not execute.
ENV UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml .
# Install third-party dependencies first (src/ not yet present).
# --no-install-project skips the editable/wheel install of the
# project package so that this layer can be cached independently
# of source changes.
RUN uv sync --no-dev --no-install-project
# Copy the application source, then install the project package
# into the same venv.  Two-step pattern keeps the dependency
# layer cached when only application code changes.
COPY src/ src/
RUN uv sync --no-dev
# Invoke uvicorn from the project venv directly to avoid uv
# requiring a writable cache directory at container start-up
# (relevant for non-privileged k8s pods with a read-only rootfs).
# Liveness probe: checks only that the process can handle requests.
HEALTHCHECK --interval=10s --timeout=2s --retries=3 --start-period=10s \
    CMD ["python", "-c", \
         "import urllib.request; urllib.request.urlopen('http://localhost:8000/livez', timeout=2)"]
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
