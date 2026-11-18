# ---- Build stage: install dependencies into an isolated virtualenv ----
FROM python:3.14-slim AS builder

WORKDIR /app

# Upgrade pip used for the build (its bundled urllib3/msgpack have known CVEs),
# then create a venv without pip so pip never reaches the runtime image.
RUN pip install --no-cache-dir --root-user-action=ignore --upgrade pip && \
    python -m venv --without-pip /opt/venv

# Install dependencies from pyproject.toml (layer cache efficiency)
COPY pyproject.toml ./
# Create minimal package structure so pip can parse pyproject.toml deps
RUN mkdir -p jira_mcp && touch jira_mcp/__init__.py && \
    pip --python /opt/venv/bin/python install --no-cache-dir --root-user-action=ignore .

# ---- Runtime stage ----
FROM python:3.14-slim

# Apply Debian security updates, remove pip (not needed at runtime and it
# vendors packages with known CVEs), and create a non-root user.
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip uninstall -y pip && \
    groupadd --gid 1001 jira && \
    useradd --uid 1001 --gid jira --shell /bin/bash --create-home jira

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY jira_mcp/ ./jira_mcp/

# Drop to non-root user
USER jira

# Default: stdio transport (for MCP client integration)
CMD ["python", "-m", "jira_mcp.app"]
