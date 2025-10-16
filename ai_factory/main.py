import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_factory.config import settings
from ai_factory.logging_setup import setup_logging, ensure_log_dir
from ai_factory.routers import health as health_router
from ai_factory.routers import planner as planner_router

# Phase 2+ imports
from ai_factory.memory.memory_db import init_db
from ai_factory.memory.routers import memory_router
from ai_factory.services.middleware import MemoryLoggerMiddleware
from ai_factory.supervisor.supervisor_router import router as supervisor_router
from ai_factory.evaluator.evaluator_router import router as evaluator_router
from ai_factory.debugger.routers import debugger_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_log_dir()
    setup_logging(settings.log_level)
    init_db()
    logging.getLogger(__name__).info("Starting AI Factory v5 — Evaluator MCP online.")
    yield
    # Shutdown
    logging.getLogger(__name__).info("Shutting down AI Factory")


app = FastAPI(
    title="AI Factory Builder - Router + Memory + Debugger + Supervisor + Evaluator",
    version="0.5.0",
    description="Phase 5: Evaluator MCP for self-assessment and feedback loop.",
    lifespan=lifespan,
)

# Middleware (planner request/response logger)
app.add_middleware(MemoryLoggerMiddleware)

# Routers
app.include_router(health_router.router)
app.include_router(planner_router.router)
app.include_router(memory_router.router)
app.include_router(debugger_router.router)
app.include_router(supervisor_router)
app.include_router(evaluator_router)


# Root
@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Factory Builder - Router + Memory + Debugger + Supervisor + Evaluator (Phase 5)", "docs": "/docs"}
