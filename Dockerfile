FROM python:3.11-slim

WORKDIR /app

# Install Node.js (v18 LTS)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
COPY mcp-node/package.json mcp-node/
RUN cd mcp-node && npm install --omit=dev

# Copy application code
COPY . .

# Create startup script (properly formatted)
RUN printf '#!/bin/bash\n\
set -e\n\
echo "=== MeetPlanner MCP Server Starting ==="\n\
echo "Starting FastAPI backend on port 8000..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
FASTAPI_PID=$!\n\
sleep 2\n\
echo "FastAPI started (PID: $FASTAPI_PID)"\n\
echo "Starting MCP server on port ${PORT:-3000}..."\n\
cd /app/mcp-node && exec node index.js\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports (FastAPI: 8000, MCP: 3000)
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-3000}/health || exit 1

CMD ["/app/start.sh"]
