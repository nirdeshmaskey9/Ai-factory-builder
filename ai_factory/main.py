import logging
from contextlib import asynccontextmanager
import asyncio
import time
from fastapi import FastAPI
from ai_factory.config import settings, log_openai_key_prefix
from ai_factory.logging_setup import setup_logging, ensure_log_dir
from ai_factory.routers import health as health_router
from ai_factory.routers import planner as planner_router

# Phase 2+ imports
from ai_factory.memory.memory_db import init_db
from ai_factory.memory.routers import memory_router
from ai_factory.services.middleware import MemoryLoggerMiddleware
from ai_factory.supervisor.supervisor_router import router as supervisor_router
from ai_factory.evaluator.evaluator_router import router as evaluator_router
from ai_factory.builder.builder_router import router as builder_router
from ai_factory.deployer.deployer_router import router as deployer_router
from ai_factory.router_v2.router_v2_router import router as router_v2_router
from ai_factory.evaluator_v2.evaluator_v2_router import router as evaluator_v2_router
from ai_factory.orchestrator.orchestrator_router import router as orchestrator_router
from ai_factory.debugger.routers import debugger_router
from ai_factory.tools.system_audit import run_audit as run_system_audit
from ai_factory.config_env_validator import validate_env
from ai_factory.services.watchdog_service import start_watchdog


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_log_dir()
    setup_logging(settings.log_level)
    # Confirm .env visibility for Phase 11 by logging key prefix
    log_openai_key_prefix()
    init_db()
    logging.getLogger(__name__).info("Starting AI Factory v1.1 - Self-Healing Foundation online.")
    # .env runtime validation (non-fatal)
    try:
        validate_env()
    except Exception as e:
        logging.getLogger(__name__).warning(f"env validation issue: {e}")
    # Lightweight startup audit (non-blocking but awaited once)
    try:
        report = await run_system_audit()
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        from pathlib import Path
        Path("deployments").mkdir(exist_ok=True)
        with open(f"deployments/system_startup_audit_{ts}.log", "w", encoding="utf-8") as f:
            import json
            f.write(json.dumps(report, ensure_ascii=False, indent=2))
        # Console summary
        healthy = report.get("healthy", [])
        warns = report.get("warnings", [])
        crit = report.get("critical", [])
        if healthy:
            print(f"✅ [OK] Healthy components: {', '.join(healthy)}")
        if warns:
            print(f"⚠️ [WARN] {'; '.join(warns)}")
        if crit:
            print(f"❌ [FAIL] {'; '.join(crit)}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Startup audit failed: {e}")
    # Start watchdog loop
    try:
        start_watchdog()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Watchdog not started: {e}")
    yield
    # Shutdown
    logging.getLogger(__name__).info("Shutting down AI Factory")


app = FastAPI(
    title="AI Factory Builder - Router + Memory + Debugger + Supervisor + Evaluator + Builder + Deployer + RouterV2 + EvaluatorV2 + Orchestrator",
    version="1.1",
    description="v1.1: Self-Healing Foundation (auto-audit, env validation, PID tracking, watchdog).",
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
app.include_router(builder_router)
app.include_router(deployer_router)
app.include_router(router_v2_router)
app.include_router(evaluator_v2_router)
app.include_router(orchestrator_router, prefix="/orchestrator")


# Root
@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Factory Builder v1.1 - Self-Healing Foundation", "docs": "/docs"}


@app.get("/factory/info")
def factory_info():
    from ai_factory.deployer.deployer_store import get_recent
    rows = get_recent(limit=100)
    running = sum(1 for r in rows if str(getattr(r, 'status', '')).lower() == 'running')
    healthy = True
    return {"version": "1.1-self-healing", "running_deployments": running, "healthy": healthy}
