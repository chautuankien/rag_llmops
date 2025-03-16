FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry
RUN poetry config virtualenvs.create false

# Copy poetry configuration files
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Create directories
# RUN mkdir -p pipeline_outputs/feature_pipeline_output/crawled_data \
#     pipeline_outputs/feature_pipeline_output/chunked_data \
#     pipeline_outputs/feature_pipeline_output/embedded_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the PYTHONPATH to the project root
ENV PYTHONPATH=/app

# Set environment variables for the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the project files into the container
COPY . .

# Override the default command to keep the container running indefinitely
# CMD ["tail", "-f", "/dev/null"]

# Set entry point
# ENTRYPOINT ["poetry", "run", "python", "src/backend/pipelines/feature_pipeline.py"]
# CMD ["--help"]