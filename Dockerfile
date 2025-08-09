# Base Python image with UV
FROM python:3.11-slim as base

LABEL authors="muhajirakbarhasibuan"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without the project)
RUN uv sync --frozen --no-install-project

# Copy source code
COPY . .

# Install the project in editable mode
RUN uv pip install -e . --no-deps

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Database population stage
FROM base as db-populate
CMD ["python", "src/database/populate.py"]

# Vanna training stage  
FROM base as vanna-train
CMD ["python", "src/vanna/training.py"]

# Main application stage
FROM base as app
EXPOSE 8000
CMD ["chainlit", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]