FROM python:3.11-slim

# Install curl for uv installation
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Copy server code
COPY server.py .

# Create venv and install dependencies using uv
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip sync requirements.txt

# Set the entrypoint to use the virtual environment and run the server
ENTRYPOINT ["/bin/bash", "-c", "source .venv/bin/activate && uv run server.py"] 