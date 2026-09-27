# EchoMCP Cloudflare Tunnel Runner (PowerShell)
# Exposes local MCP Server (http://localhost:3001) over a secure, public HTTPS URL for Grok consumer connectors.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   EchoMCP — Cloudflare Tunnel Ingress for Grok MCP      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$TargetUrl = "http://localhost:3001"
Write-Host "Target Service: $TargetUrl" -ForegroundColor Yellow
Write-Host "Checking for cloudflared executable..." -ForegroundColor Gray

if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    Write-Host "Found cloudflared in PATH. Launching quick tunnel..." -ForegroundColor Green
    Write-Host "Look for the URL ending with '.trycloudflare.com' below:" -ForegroundColor Magenta
    & cloudflared tunnel --url $TargetUrl
} elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "cloudflared CLI not in PATH. Running cloudflared via Docker..." -ForegroundColor Yellow
    Write-Host "Look for the URL ending with '.trycloudflare.com' below:" -ForegroundColor Magenta
    docker run --rm -it --network host cloudflare/cloudflared:latest tunnel --url $TargetUrl
} else {
    Write-Host "ERROR: Neither 'cloudflared' nor 'docker' was found." -ForegroundColor Red
    Write-Host "To install cloudflared on Windows, run:" -ForegroundColor White
    Write-Host "  winget install Cloudflare.cloudflared" -ForegroundColor Cyan
    Write-Host "Or download from: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor Cyan
    exit 1
}
