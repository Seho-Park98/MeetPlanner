#!/bin/bash
# =============================================================================
# MCP Server Pre-Deploy Validation Script
# Verifies server compliance before Fly.io deployment
# =============================================================================

set -e

PORT="${PORT:-3000}"
HOST="0.0.0.0"
BASE_URL="http://localhost:${PORT}"

echo "=== MCP Server Pre-Deploy Validation ==="
echo "Target: ${BASE_URL}"
echo ""

# Check 1: Health endpoint
echo "[1/3] Checking health endpoint..."
HEALTH=$(curl -s -w "%{http_code}" -o /tmp/health.json "${BASE_URL}/health" 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo "  ✓ Health check passed"
    cat /tmp/health.json | jq .
else
    echo "  ✗ Health check failed (HTTP $HEALTH)"
    echo "  Make sure server is running on ${HOST}:${PORT}"
    exit 1
fi
echo ""

# Check 2: MCP initialize
echo "[2/3] Checking MCP initialize..."
INIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"validator","version":"1.0.0"}}}' \
    2>/dev/null || echo '{}')

PROTOCOL=$(echo "$INIT_RESPONSE" | jq -r '.result.protocolVersion // empty')
if [ -n "$PROTOCOL" ]; then
    echo "  ✓ Initialize successful (protocol: $PROTOCOL)"
else
    echo "  ✗ Initialize failed"
    echo "  Response: $INIT_RESPONSE"
    exit 1
fi
echo ""

# Check 3: tools/list with description validation
echo "[3/3] Checking tools/list (description validation)..."
TOOLS_RESPONSE=$(curl -s -X POST "${BASE_URL}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
    2>/dev/null || echo '{}')

TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | jq '.result.tools | length // 0')
TOOL_NAME=$(echo "$TOOLS_RESPONSE" | jq -r '.result.tools[0].name // empty')
TOOL_DESC=$(echo "$TOOLS_RESPONSE" | jq -r '.result.tools[0].description // "null"')

if [ "$TOOL_COUNT" -gt 0 ] && [ -n "$TOOL_NAME" ] && [ "$TOOL_DESC" != "null" ]; then
    echo "  ✓ tools/list passed"
    echo "    - Tool count: $TOOL_COUNT"
    echo "    - Tool name: $TOOL_NAME"
    echo "    - Description: (non-null, ${#TOOL_DESC} chars)"
else
    echo "  ✗ tools/list validation failed"
    echo "  - Tool count: $TOOL_COUNT"
    echo "  - Description is null or missing (PlayMCP requires non-null)"
    exit 1
fi
echo ""

echo "=== All Validations Passed ==="
echo "Server is ready for Fly.io deployment."
echo ""
echo "Deploy command: fly deploy"
echo "Check logs: fly logs"
