import logging
from contextlib import asynccontextmanager
import asyncio
import time
from fastapi import FastAPI
from ai_factory.config import settings, log_openai_key_prefix, validate_config
from ai_factory.logging_setup import setup_logging, ensure_log_dir
from ai_factory.routers import health as health_router
from ai_factory.routers import planner as planner_router

# Phase 2+ imports
from ai_factory.memory.memory_db import init_db
from ai_factory.memory.routers import memory_router
from ai_factory.services.middleware import MemoryLoggerMiddleware, DebugLoggerMiddleware, SupervisorLoggerMiddleware, EvaluatorLoggerMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from ai_factory.supervisor.supervisor_router import router as supervisor_router
from ai_factory.evaluator.evaluator_router import router as evaluator_router
from ai_factory.builder.builder_router import router as builder_router
from ai_factory.deployer.deployer_router import router as deployer_router
from ai_factory.deployer.preview_router import router as deployer_preview_router
from ai_factory.router_v2.router_v2_router import router as router_v2_router
from ai_factory.evaluator_v2.evaluator_v2_router import router as evaluator_v2_router
from ai_factory.orchestrator.orchestrator_router import router as orchestrator_router
from ai_factory.orchestrator.factory_routes import router as factory_router
from ai_factory.system.health_router import router as system_health_router
from ai_factory.system.report_router import router as system_report_router
import atexit
from ai_factory.deployer.preview_service import stop_all_previews
from ai_factory.debugger.routers import debugger_router
from ai_factory.tools.system_audit import run_audit as run_system_audit
from ai_factory.config_env_validator import validate_env
from ai_factory.services.watchdog_service import start_watchdog
from ai_factory.routers import factory_info as factory_info_router
from ai_factory.system.port_finder import find_free_port
from ai_factory.ui.dashboard_router import router as dashboard_router
from ai_factory.ui.memory_ui_router import router as memory_ui_router
from ai_factory.ui.analytics_router import router as analytics_router
from ai_factory.ui.feedback_router import router as feedback_router
from ai_factory.ui.ws_router import router as ws_router
from starlette.staticfiles import StaticFiles
from ai_factory.routers.rerun_router import router as rerun_router
from ai_factory.advisor.advisor_router import router as advisor_router
from ai_factory.advisor.advisor_service import startup_probe as advisor_startup_probe
from ai_factory.advisor.trio_manager import LocalTrioManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_log_dir()
    setup_logging(settings.log_level)
    # Confirm .env visibility for Phase 11 by logging key prefix
    log_openai_key_prefix()
    init_db()
    # Ensure core directories and log creation
    from pathlib import Path
    created = []
    for p in (Path("deployments"), Path("builds"), Path("logs"), Path("tests")):
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
    # Log rotation: delete logs older than 30 days in supervisor/orchestrator
    try:
        import datetime, os
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
        for sub in ("orchestrator", "supervisor"):
            d = Path("logs") / sub
            if not d.exists():
                continue
            for f in d.iterdir():
                try:
                    stat = f.stat()
                    # On some platforms, st_mtime may be naive; rely on epoch seconds
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc)
                    if mtime < cutoff:
                        f.unlink(missing_ok=True)
                except Exception:
                    pass
    except Exception:
        pass
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Log to startup.log
    try:
        with open("logs/startup.log", "a", encoding="utf-8") as f:
            if created:
                for c in created:
                    f.write(f"{ts} created {c}\n")
            else:
                f.write(f"{ts} all core directories present\n")
    except Exception:
        pass
    # ASCII-only console output to avoid UnicodeEncodeError on some consoles
    logging.getLogger(__name__).info("AI Factory v1.3-gpt4o-builder - Live Planner Active")
    print(f"AI Factory v1.3-gpt4o-builder - Live Planner Active (Startup @ {ts})")
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
        # Health report snapshot
        try:
            with open(f"deployments/health_report_{ts}.md", "w", encoding="utf-8") as hf:
                hf.write("# Health Report\n\n")
                hf.write(json.dumps(report, ensure_ascii=False, indent=2))
        except Exception:
            pass
        # Console summary
        healthy = report.get("healthy", [])
        warns = report.get("warnings", [])
        crit = report.get("critical", [])
        if healthy:
            print(f"? [OK] Healthy components: {', '.join(healthy)}")
        if warns:
            print(f"?? [WARN] {'; '.join(warns)}")
        if crit:
            print(f"? [FAIL] {'; '.join(crit)}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Startup audit failed: {e}")
    # Advisor local trio health probe (non-fatal)
    try:
        advisor_startup_probe()
    except Exception:
        pass
    # Start watchdog loop
    try:
        start_watchdog()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Watchdog not started: {e}")
    # Config validation (warnings only)
    try:
        validate_config()
    except Exception:
        pass
    # Trio manager (auto-launch + monitor)
    try:
        tm = LocalTrioManager()
        app.state.trio_manager = tm
        tm.start()
    except Exception:
        pass
    # Additional startup self-diagnostics (migrated from deprecated on_event)
    try:
        from ai_factory.system.health_router import full_health_check
        health = full_health_check()
        if health.get("status") != "healthy":
            print("?? Warning: Startup health degraded:", health.get("summary"))
        else:
            print("?? Full health check passed on startup.")
    except Exception as e:
        print(f"[WARN] Startup diagnostics failed: {e}")
    # Advisor local trio health probe (non-fatal)
    try:
        advisor_startup_probe()
    except Exception:
        pass
    yield
    # Shutdown
    logging.getLogger(__name__).info("Shutting down AI Factory")
    try:
        from pathlib import Path
        Path("deployments").mkdir(exist_ok=True)
        with open("deployments/health.log", "a", encoding="utf-8") as f:
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            f.write(f"Factory stopped cleanly @ {ts}\n")
    except Exception:
        pass


app = FastAPI(
    title="AI Factory Builder - Cognitive Engine",
    version="v3.0-memory-mcp",
    description="v3.0-memory-mcp: Long-term memory + recall + learning.",
    lifespan=lifespan,
)

# Middleware (planner request/response logger)
app.add_middleware(MemoryLoggerMiddleware)
app.add_middleware(DebugLoggerMiddleware)
app.add_middleware(SupervisorLoggerMiddleware)
app.add_middleware(EvaluatorLoggerMiddleware)

# Global exception logging middleware
class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            try:
                import uuid
                from pathlib import Path
                Path("logs").mkdir(exist_ok=True)
                ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                err_id = uuid.uuid4().hex[:12]
                with open(f"logs/errors_{ts}.log", "a", encoding="utf-8") as f:
                    f.write(f"{err_id} {request.method} {request.url.path} -> {e}\n")
            except Exception:
                pass
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"detail": "Internal error", "error_id": err_id})

app.add_middleware(GlobalExceptionMiddleware)


@atexit.register
def graceful_shutdown():
    try:
        print("?? Cleaning up previews and processes before exit...")
        stop_all_previews()
    except Exception as e:
        print(f"[WARN] Cleanup error: {e}")

# Routers
app.include_router(health_router.router)
app.include_router(planner_router.router)
app.include_router(memory_router.router)
app.include_router(debugger_router.router)
app.include_router(supervisor_router)
app.include_router(evaluator_router)
app.include_router(builder_router)
app.include_router(deployer_router)
app.include_router(deployer_preview_router)
app.include_router(router_v2_router)
app.include_router(evaluator_v2_router)
app.include_router(orchestrator_router, prefix="/orchestrator")
app.include_router(factory_router)
app.include_router(system_health_router)
app.include_router(system_report_router)
app.include_router(factory_info_router.router)
app.include_router(dashboard_router)
app.include_router(memory_ui_router)
app.include_router(analytics_router)
app.include_router(feedback_router)
app.include_router(ws_router)
app.mount("/static", StaticFiles(directory="ai_factory/ui/static"), name="static")
app.include_router(rerun_router)
app.include_router(advisor_router)
print("?? Deployer Health route registered at /deployer/health")


# Root
@app.get("/", include_in_schema=False)
def root():
    return {"message": "AI Factory Builder v1.1 - Self-Healing Foundation", "docs": "/docs"}




@app.get("/health")
def health():
    try:
        from pathlib import Path
        active_builds = len([p for p in Path("builds").iterdir() if p.is_dir()])
    except Exception:
        active_builds = 0
    version = "v2.0-cognitive-engine"
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {"healthy": True, "timestamp": ts, "active_builds": active_builds, "version": version}


# Optional programmatic launcher with auto port recovery
if __name__ == "__main__":
    # Defer import so tests importing app don't pull uvicorn
    try:
        import uvicorn  # type: ignore
    except Exception as e:
        raise SystemExit(f"uvicorn not installed: {e}")

    # Choose a port starting from 8015 up to 8050
    try:
        port = find_free_port(8015, 8050)
    except Exception as e:
        raise SystemExit(f"No free port found in 8015-8050: {e}")

    # Log to startup.log and console
    try:
        from pathlib import Path
        Path("logs").mkdir(parents=True, exist_ok=True)
        with open("logs/startup.log", "a", encoding="utf-8") as f:
            f.write(f"selected_port {port}\n")
    except Exception:
        pass
    # Console: prefer ASCII to avoid encoding issues on some terminals
    try:
        print(f"✅ Port {port} selected — Factory online")
    except Exception:
        print(f"[OK] Port {port} selected - Factory online")

    # Propagate chosen port so internal audits use the right base URL
    try:
        import os
        os.environ["AI_FACTORY_PORT"] = str(port)
        os.environ.setdefault("AI_FACTORY_HOST", settings.host or "127.0.0.1")
    except Exception:
        pass

    uvicorn.run(app, host=settings.host or "127.0.0.1", port=port, log_level=settings.uvicorn_log_level)
