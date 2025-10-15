import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_factory.config import settings
from ai_factory.logging_setup import setup_logging, ensure_log_dir
from ai_factory.routers import health as health_router
from ai_factory.routers import planner as planner_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_log_dir()
    setup_logging(settings.log_level)
    logging.getLogger(__name__).info("Starting AI Factory Router Core (Phase 1)")
    yield
    # Shutdown
    logging.getLogger(__name__).info("Shutting down AI Factory Router Core")


app = FastAPI(
    title="AI Factory Builder — Router Core",
    version="0.1.0",
    description="Phase 1: FastAPI hub that routes requests to stubs.",
    lifespan=lifespan,
)

# Routers
app.include_router(health_router.router)
app.include_router(planner_router.router)


# Root
@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Factory Builder — Router Core (Phase 1)", "docs": "/docs"}
