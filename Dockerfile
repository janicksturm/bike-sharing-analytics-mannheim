FROM ghcr.io/astral-sh/uv:python3.13-slim

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (without project itself)
RUN uv sync --frozen --no-install-project

# Copy the rest of the source
COPY . .

# Install the project
RUN uv sync --frozen

EXPOSE 8000
