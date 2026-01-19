"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router as api_router
from app.api.websocket import websocket_endpoint, ws_manager
from app.services.database import db
from app.services.gemini import gemini_service
from app.core.watcher import log_watcher
from app.core.analyzer import error_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting AIDEN Labs...")
    
    # Initialize database
    await db.connect()
    logger.info("Database connected")
    
    # Configure Gemini (if API key available)
    if settings.gemini_api_key:
        try:
            gemini_service.configure()
            logger.info("Gemini API configured")
        except Exception as e:
            logger.warning(f"Gemini API not configured: {e}")
    else:
        logger.warning("GEMINI_API_KEY not set - AI analysis disabled")
    
    # Register analyzer's broadcast to WebSocket manager
    error_analyzer.register_broadcast(ws_manager.broadcast_error)
    
    # Register analyzer as callback for watcher
    log_watcher.register_async_callback(error_analyzer.process_new_content)
    
    # Start file watcher
    log_watcher.start()
    logger.info(f"Watching directory: {settings.log_watch_dir}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AIDEN Labs...")
    log_watcher.stop()
    await db.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AIDEN Labs",
    description="Log Monitoring & AI Error Analysis System for Huawei ENSP",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AIDEN Labs",
        "description": "Log Monitoring & AI Error Analysis System",
        "docs": "/docs",
        "websocket": "/ws"
    }
