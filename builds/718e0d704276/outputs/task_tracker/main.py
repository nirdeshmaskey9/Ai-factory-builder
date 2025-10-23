from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from routes.home import router as home_router
from routes.log import router as log_router
from routes.history import router as history_router
from routes.summary import router as summary_router
from database import init_db

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="task_tracker")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(home_router)
app.include_router(log_router)
app.include_router(history_router)
app.include_router(summary_router)

@app.on_event("startup")
def _startup():
    init_db()
