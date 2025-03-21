FROM python:3.13-slim

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry && \
    # Configure Poetry to not create a virtual environment inside the container
    poetry config virtualenvs.create false

# Create a directory for persistent data
RUN mkdir -p /app/data

# Copy Poetry configuration files first for better layer caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY *.py .

# Set environment variable for database path
ENV DB_PATH=/app/data/message_history.db

# Use main.py as the entry point
CMD ["python", "main.py"]