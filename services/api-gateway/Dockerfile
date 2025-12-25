FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies (skip PostgreSQL client for now - not critical)
RUN apt-get update && apt-get install -y \
    gcc \
    ca-certificates \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ./services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ./shared /app/shared

# Copy application code
COPY ./services/api-gateway/src/ ./src/
COPY ./services/api-gateway/startup.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check - supports both HTTP and HTTPS
#HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#    CMD python -c "import os, urllib.request, ssl; scheme = 'https' if os.getenv('TLS_ENABLED', 'false').lower() in ('true', '1', 'yes') else 'http'; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen(f'{scheme}://localhost:8080/health', timeout=5, context=ctx if scheme == 'https' else None)"

# Run the application
CMD ["python", "startup.py"]
