FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies (retry with clean cache if needed)
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y gcc || \
    (apt-get clean && apt-get update && apt-get install -y gcc) && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY startup.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8082

# Health check - supports both HTTP and HTTPS
#HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#    CMD python -c "import os, urllib.request, ssl; scheme = 'https' if os.getenv('TLS_ENABLED', 'false').lower() in ('true', '1', 'yes') else 'http'; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen(f'{scheme}://localhost:8082/health', timeout=5, context=ctx if scheme == 'https' else None)"

# Run the application
CMD ["python", "startup.py"]
