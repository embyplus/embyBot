# Single-stage build for Python application
FROM python:3.12-slim

# Set environment variables
ENV TZ=Asia/Shanghai \
    DOCKER_MODE=1 \
    PUID=0 \
    PGID=0 \
    UMASK=000 \
    PYTHONWARNINGS="ignore:semaphore_tracker:UserWarning" \
    WORKDIR="/app"

# Set working directory
WORKDIR ${WORKDIR}

# Copy requirements files first for better caching
COPY pyproject.toml uv.lock .python-version ./

# Install uv and application dependencies
RUN apk add --no-cache --virtual .build-deps gcc git musl-dev && \
    # Log Python version from .python-version file
    echo "Target Python version from .python-version: $(cat .python-version)" && \
    # Install uv
    wget -qO- https://astral.sh/uv/install.sh | sh && \
    # Make sure uv is in PATH
    source /root/.local/bin/env && \
    # Install project dependencies from pyproject.toml
    uv sync && \
    # Clean up
    uv cache clean && \
    apk del --purge .build-deps && \
    rm -rf /tmp/* /root/.cache /var/cache/apk/*

# Copy the rest of the application
COPY . .

# Redirect logs to stdout
RUN ln -sf /dev/stdout /app/default.log

# Define entrypoint using uv
ENTRYPOINT ["/root/.local/bin/uv", "run", "app.py"]

