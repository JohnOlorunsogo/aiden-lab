"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router as api_router
from app.api.websocket import websocket_endpoint, ws_manager
from app.services.database import db
from app.services.llm import llm_service
from app.services.ensp_logger_service import ensp_logger_service
from app.core.watcher import log_watcher
from app.core.analyzer import error_analyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AIDEN Labs...")
    
    await db.connect()
    logger.info("Database connected")
    
    try:
        llm_service.configure()
        logger.info(f"LLM service configured: {settings.llm_base_url}")
    except Exception as e:
        logger.warning(f"LLM service not configured: {e}")
    
    error_analyzer.register_broadcast(ws_manager.broadcast_error)
    log_watcher.register_async_callback(error_analyzer.process_new_content)
    
    if settings.ensp_logger_enabled:
        try:
            ensp_logger_service.start()
            if ensp_logger_service.is_running:
                logger.info("ENSP logger service started")
            else:
                logger.warning("ENSP logger service failed to start (may require admin privileges)")
        except Exception as e:
            logger.warning(f"Failed to start ENSP logger service: {e}")
            logger.warning("Continuing without packet capture - log monitoring will work with existing logs")
    else:
        logger.info("ENSP logger service is disabled")
    
    log_watcher.start()
    logger.info(f"Watching directory: {settings.log_watch_dir}")
    logger.info(f"Absolute path: {settings.log_watch_dir.resolve()}")
    
    yield
    
    logger.info("Shutting down AIDEN Labs...")
    
    if ensp_logger_service.is_running:
        ensp_logger_service.stop()
    
    log_watcher.stop()
    
    logger.info("Cleaning up log files...")
    ensp_logger_service.cleanup_logs()
    
    await db.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="AIDEN Labs",
    description="Log Monitoring & AI Error Analysis System for Huawei ENSP",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.websocket("/ws")(websocket_endpoint)


@app.get("/")
async def root():
    return {
        "name": "AIDEN Labs",
        "description": "Log Monitoring & AI Error Analysis System",
        "docs": "/docs",
        "websocket": "/ws"
    }
