FROM python:3.12-slim

# Non-root user for security
RUN groupadd --gid 1001 jira && \
    useradd --uid 1001 --gid jira --shell /bin/bash --create-home jira

WORKDIR /app

# Install dependencies from pyproject.toml (layer cache efficiency)
COPY pyproject.toml ./
# Create minimal package structure so pip can parse pyproject.toml deps
RUN mkdir -p jira_mcp && touch jira_mcp/__init__.py && \
    pip install --no-cache-dir .

# Copy application source
COPY jira_mcp/ ./jira_mcp/

# Drop to non-root user
USER jira

# Default: stdio transport (for MCP client integration)
CMD ["python", "-m", "jira_mcp.app"]
