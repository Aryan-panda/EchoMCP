#!/usr/bin/env bash
set -e

echo "Stopping EchoMCP containers..."
docker compose down
echo "All EchoMCP services stopped."
