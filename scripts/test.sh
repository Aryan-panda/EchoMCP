#!/usr/bin/env bash
set -e

echo "=== Running EchoMCP Test Suites ==="
pytest mcp-server/tests/ -v
