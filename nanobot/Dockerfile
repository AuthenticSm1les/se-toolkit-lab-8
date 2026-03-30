# Multi-stage Dockerfile for nanobot gateway
# Uses uv for dependency management

# ---
# Stage 1: Build the application
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
ARG APP_UID=1000
ARG APP_GID=1000

FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace root pyproject.toml and uv.lock from workspace context
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy nanobot project - everything from the build context
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY entrypoint.py /app/nanobot/entrypoint.py

# Copy MCP servers from workspace context
COPY --from=workspace mcp/ /app/mcp/

# Copy nanobot-websocket-channel from workspace context
COPY --from=workspace nanobot-websocket-channel/ /app/nanobot-websocket-channel/

# Sync nanobot and MCP dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot --package mcp-lms --package mcp-obs --package mcp-webchat --package nanobot-webchat --package nanobot-channel-protocol

# Copy the rest of nanobot workspace files
COPY . /app/nanobot/

# ---
# Stage 2: Runtime image
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Create non-root user with configurable UID/GID
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --system --gid ${APP_GID} appgroup \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

# Copy the application from builder
COPY --from=builder --chown=appuser:appgroup /app /app

# Set PATH to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create writable directories for nanobot runtime data
RUN mkdir -p /app/nanobot/workspace/cron /app/nanobot/workspace/memory /app/nanobot/workspace/sessions \
    && chown -R appuser:appgroup /app/nanobot/workspace

# Switch to non-root user
USER appuser

# Set working directory
WORKDIR /app

# Run the entrypoint which resolves config and starts nanobot gateway
CMD ["python", "/app/nanobot/entrypoint.py"]
