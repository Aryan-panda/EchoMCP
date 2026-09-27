#!/usr/bin/env bash
set -e

echo "=== Querying EchoMCP Health Endpoints ==="

echo -n "1. MCP Liveness (/health): "
curl -s -f http://localhost:3001/health || echo "FAILED"
echo ""

echo -n "2. System Readiness (/ready): "
curl -s http://localhost:3001/ready || echo "FAILED"
echo ""

echo -n "3. System Version (/version): "
curl -s http://localhost:3001/version || echo "FAILED"
echo ""

echo -n "4. TTS Engine Status (/api/v1/tts/status): "
curl -s http://localhost:3001/api/v1/tts/status || echo "FAILED"
echo ""

echo -n "5. Frontend Web Server (http://localhost:3000): "
curl -s -I http://localhost:3000/ | head -n 1 || echo "FAILED"
echo ""
