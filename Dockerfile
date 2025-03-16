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
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY ./src/ .

# Create directories
RUN mkdir -p pipeline_outputs/feature_pipeline_output/crawled_data \
    pipeline_outputs/feature_pipeline_output/chunked_data \
    pipeline_outputs/feature_pipeline_output/embedded_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set entry point
# ENTRYPOINT ["poetry", "run", "python", "src/backend/pipelines/feature_pipeline.py"]
CMD ["--help"]