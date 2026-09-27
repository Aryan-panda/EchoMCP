#!/usr/bin/env bash
set -e

echo "=== Starting Cloudflare Quick Tunnel to MCP Server ==="
echo "Target: http://localhost:3001"
echo "Public endpoint: https://<subdomain>.trycloudflare.com/mcp"

cloudflared tunnel --url http://localhost:3001
