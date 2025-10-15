import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_factory.config import settings
from ai_factory.logging_setup import setup_logging, ensure_log_dir
from ai_factory.routers import health as health_router
from ai_factory.routers import planner as planner_router

# Phase 2 imports
from ai_factory.memory.memory_db import init_db
from ai_factory.memory.routers import memory_router
from ai_factory.services.middleware import MemoryLoggerMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_log_dir()
    setup_logging(settings.log_level)
    init_db()
    logging.getLogger(__name__).info("Starting AI Factory Router Core + Memory MCP (Phase 2)")
    yield
    # Shutdown
    logging.getLogger(__name__).info("Shutting down AI Factory")


app = FastAPI(
    title="AI Factory Builder — Router Core + Memory MCP",
    version="0.2.0",
    description="Phase 2: Memory MCP with SQLite event log and Chroma semantic recall.",
    lifespan=lifespan,
)

# Middleware (planner request/response logger)
app.add_middleware(MemoryLoggerMiddleware)

# Routers
app.include_router(health_router.router)
app.include_router(planner_router.router)
app.include_router(memory_router.router)


# Root
@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Factory Builder — Router Core + Memory MCP (Phase 2)", "docs": "/docs"}
