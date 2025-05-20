FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and switch to it
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Copy requirements first to leverage Docker cache
COPY requirements.txt requirements_dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/certs \
    && chown -R appuser:appuser /app

# Copy application code
COPY rfm/ ./rfm/
COPY ui/ ./ui/
COPY tests/ ./tests/
COPY tools/ ./tools/
COPY *.py ./

# Generate SSL certificates if not mounted
COPY tools/ssl/generate_certs.sh ./tools/ssl/generate_certs.sh
RUN chmod +x ./tools/ssl/generate_certs.sh

# Create startup script
RUN echo '#!/bin/bash\n\
# Generate certs if they don\'t exist\n\
if [ ! -f /app/certs/server.crt ] || [ ! -f /app/certs/server.key ]; then\n\
    mkdir -p /app/certs\n\
    ./tools/ssl/generate_certs.sh\n\
    mv ./tools/ssl/certs/server.crt /app/certs/\n\
    mv ./tools/ssl/certs/server.key /app/certs/\n\
fi\n\
\n\
# Start server based on environment\n\
if [ "$ENABLE_SSL" = "true" ]; then\n\
    python run_production_websocket_server.py --host 0.0.0.0 --port 8765 --ssl-cert /app/certs/server.crt --ssl-key /app/certs/server.key --enable-auth --monitor-resources\n\
else\n\
    python run_websocket_server.py --host 0.0.0.0 --port 8765\n\
fi\n' > /app/start.sh \
    && chmod +x /app/start.sh

# Switch to non-root user
USER appuser

# Set default environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=info \
    ENABLE_SSL=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 8765

# Run startup script
CMD ["/app/start.sh"]