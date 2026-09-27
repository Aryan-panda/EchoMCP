import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from app.config import settings
from app.dependencies import get_speech_service
from app.services.speech_service import SpeechService
from app.mcp.tools import SPEAK_RESPONSE_TOOL_DEF, execute_speak_response
from app.utils.ids import generate_request_id

logger = logging.getLogger("echomcp.mcp_server")
mcp_router = APIRouter(tags=["MCP"])

def verify_mcp_auth(authorization: Optional[str]):
    """Verify Bearer token against configured MCP_AUTH_TOKEN."""
    if not settings.MCP_AUTH_TOKEN:
        return
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing Authorization header"
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != settings.MCP_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid Bearer token"
        )

@mcp_router.get("/mcp")
async def handle_mcp_get(authorization: Optional[str] = Header(None)):
    """
    GET probe for MCP Streamable HTTP transport.
    Provides transport info and confirms endpoint availability.
    """
    verify_mcp_auth(authorization)
    return {
        "transport": "streamable-http",
        "protocolVersion": "2024-11-05",
        "server": "grok-voice-bridge",
        "version": "1.0.0",
        "status": "ready"
    }

@mcp_router.post("/mcp")
async def handle_mcp_endpoint(
    request: Request,
    authorization: Optional[str] = Header(None),
    speech_service: SpeechService = Depends(get_speech_service),
):
    """
    Public Streamable HTTP MCP entry point.
    Requires Bearer token authentication and dispatches JSON-RPC 2.0 calls.
    """
    verify_mcp_auth(authorization)
    req_id = generate_request_id()

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"},
                "id": None
            }
        )

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: Body must be a JSON object"},
                "id": None
            }
        )

    jsonrpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if not method:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: Missing 'method' field"},
                "id": jsonrpc_id
            }
        )

    logger.info(f"MCP Request: method={method}, id={jsonrpc_id}")

    # Method 1: initialize handshake
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "grok-voice-bridge",
                    "version": "1.0.0"
                }
            }
        }

    # Method 2: notifications/initialized
    elif method == "notifications/initialized":
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Method 3: ping
    elif method == "ping":
        return {"jsonrpc": "2.0", "id": jsonrpc_id, "result": {}}

    # Method 4: tools/list
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "tools": [SPEAK_RESPONSE_TOOL_DEF]
            }
        }

    # Method 5: tools/call
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name != "speak_response":
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {
                    "code": -32601,
                    "message": f"Method/Tool not found: '{tool_name}'"
                }
            }

        try:
            result = await execute_speak_response(
                arguments=arguments,
                speech_service=speech_service,
                request_id=req_id
            )
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing speak_response: {e}")
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True
                }
            }

    # Default: Unknown method
    return {
        "jsonrpc": "2.0",
        "id": jsonrpc_id,
        "error": {
            "code": -32601,
            "message": f"Method not supported: '{method}'"
        }
    }
