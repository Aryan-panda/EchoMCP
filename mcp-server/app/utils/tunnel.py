import re
import urllib.parse
from typing import Optional

TRYCLOUDFLARE_REGEX = re.compile(
    r"^https://[a-zA-Z0-9-]+\.(trycloudflare\.com|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/?$"
)

def validate_tunnel_url(url: str) -> bool:
    """
    Validate that an ingress URL uses secure HTTPS and has a valid domain name.
    Accepts trycloudflare.com subdomains as well as custom configured domains.
    """
    if not url:
        return False
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https":
        return False
    if not parsed.netloc:
        return False
    return bool(TRYCLOUDFLARE_REGEX.match(url))

def create_ingress_headers(
    token: str,
    forwarded_for: Optional[str] = "198.51.100.1",
    request_id: Optional[str] = None
) -> dict[str, str]:
    """
    Construct standard HTTP headers passed by Cloudflare Tunnel to local origin.
    Includes Bearer auth, HTTPS protocol forwarding, client IP, and request ID.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-For": forwarded_for or "127.0.0.1",
        "Content-Type": "application/json",
    }
    if request_id:
        headers["X-Request-ID"] = request_id
    return headers

def extract_tunnel_url_from_output(log_text: str) -> Optional[str]:
    """
    Extract public trycloudflare.com URL from cloudflared stdout/stderr log output.
    """
    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", log_text)
    if match:
        return match.group(0)
    return None
