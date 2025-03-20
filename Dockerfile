# Single-stage build for Python application
FROM python:3.12-slim

# Set environment variables
ENV TZ=Asia/Shanghai \
    DOCKER_MODE=1 \
    PUID=0 \
    PGID=0 \
    UMASK=000 \
    PYTHONWARNINGS="ignore:semaphore_tracker:UserWarning" \
    WORKDIR="/app" \
    PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR ${WORKDIR}

# Copy requirements files first for better caching
COPY pyproject.toml uv.lock .python-version ./

# Install uv and application dependencies
# Use bash explicitly to support 'source' command
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    git \
    wget \
    ca-certificates \
    bash \
    libc6-dev \
    python3-dev && \
    # Log Python version from .python-version file
    echo "Target Python version from .python-version: $(cat .python-version)" && \
    # Install uv
    wget -qO- https://astral.sh/uv/install.sh | bash && \
    # Make uv available without source
    bash -c 'export PATH="/root/.local/bin:$PATH" && \
    # Install project dependencies from pyproject.toml
    /root/.local/bin/uv sync' && \
    # Clean up build dependencies
    apt-get purge -y --auto-remove gcc git wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache

# Copy the rest of the application
COPY . .

# Redirect logs to stdout
RUN ln -sf /dev/stdout /app/default.log

# Define entrypoint using uv
ENTRYPOINT ["/root/.local/bin/uv", "run", "app.py"]

