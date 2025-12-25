FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ./services/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ./shared /app/shared

# Copy application code
COPY ./services/auth-service/src/ ./src/
COPY ./services/auth-service/alembic/ ./alembic/
COPY ./services/auth-service/alembic.ini .
COPY ./services/auth-service/startup.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8085

# Health check - supports both HTTP and HTTPS
#HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#    CMD python -c "import os, urllib.request, ssl; scheme = 'https' if os.getenv('TLS_ENABLED', 'false').lower() in ('true', '1', 'yes') else 'http'; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen(f'{scheme}://localhost:8085/health', timeout=5, context=ctx if scheme == 'https' else None)"

# Run the application
CMD ["python", "startup.py"]
