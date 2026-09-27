#!/usr/bin/env bash
set -e

echo "Starting EchoMCP system containers..."
docker compose up -d --build

echo "EchoMCP services started."
echo "Frontend:   http://localhost:3000"
echo "MCP Server: http://localhost:3001"
echo "Health:     http://localhost:3001/health"
