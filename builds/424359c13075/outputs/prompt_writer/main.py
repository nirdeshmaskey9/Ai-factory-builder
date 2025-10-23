from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI

APP_DIR = Path(__file__).resolve().parent
app = FastAPI(title="prompt_writer", description="Generate image prompts from keywords via /generate endpoint (image)")


@app.post("/generate")
def generate(keywords: str) -> dict:
    # Create a simple artifact file to simulate generation
    artifact = APP_DIR / "generated.txt"
    artifact.write_text(f"keywords: {keywords}\n", encoding="utf-8")
    return {"status": "ok", "artifact": str(artifact)}


@app.get("/")
def root() -> dict:
    return {"message": "ImageGen home"}


@app.get("/health")
def health() -> dict:
    return {"ok": True}

