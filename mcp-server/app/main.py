import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.health import router as health_router
from app.api.speech import router as speech_router
from app.api.audio import router as audio_router
from app.api.voices import router as voices_router
from app.mcp.server import mcp_router
from app.utils.cleanup import cleanup_expired_audio
from app.utils.ids import generate_request_id

logger = logging.getLogger("echomcp.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting EchoMCP Server v1.0.0 (Env: {settings.APP_ENV})")
    # Ensure directories exist
    settings.voices_path.mkdir(parents=True, exist_ok=True)
    settings.output_path.mkdir(parents=True, exist_ok=True)
    settings.metadata_path.mkdir(parents=True, exist_ok=True)

    if settings.AUDIO_RETENTION_ENABLED:
        logger.info(f"Audio retention enabled: {settings.AUDIO_RETENTION_DAYS} days threshold.")
        cleanup_expired_audio(settings.output_path, settings.AUDIO_RETENTION_DAYS)

    yield
    logger.info("EchoMCP Server shutting down.")

app = FastAPI(
    title="EchoMCP — Grok MCP Bridge for Custom Voice",
    version="1.0.0",
    description="Local expressive custom-voice speech bridge for Grok via Model Context Protocol.",
    lifespan=lifespan,
)

# Enable CORS for local Web Dashboard (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", generate_request_id())
    request.state.request_id = req_id
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
    return response

# Register API Routers
app.include_router(health_router)
app.include_router(speech_router)
app.include_router(audio_router)
app.include_router(voices_router)
app.include_router(mcp_router)
