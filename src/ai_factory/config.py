import logging
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from a local .env file if present
# Force override so runtime reflects the .env during Phase 11
load_dotenv(dotenv_path=".env", override=True)


def log_openai_key_prefix() -> None:
    """Log a one-line hint that the OpenAI key is visible.

    Prints a safe prefix only (no secret leakage) so operators can
    confirm that .env was loaded successfully at startup.
    """
    key = os.getenv("OPENAI_API_KEY", "")
    logger = logging.getLogger("ai_factory.config")
    if key:
        # Prefer a stable message format requested by Phase 11
        if key.startswith("sk-proj-"):
            logger.info("✅ OpenAI key loaded (prefix: sk-proj-…)")
        else:
            # Fallback message without exposing the secret
            logger.info("✅ OpenAI key loaded (masked)")
    else:
        logger.warning("⚠️ OpenAI key missing — set OPENAI_API_KEY in .env")


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def uvicorn_log_level(self) -> str:
        return self.log_level.lower()


settings = Settings()


def validate_config() -> None:
    """Best-effort config validation with warnings only.

    - Ensures .env loaded
    - Checks for OPENAI_API_KEY, DB_PATH, and TEMPLATES_PATH
    - Logs warnings instead of raising
    """
    logger = logging.getLogger("ai_factory.config")
    # .env presence
    if not Path('.env').exists():
        logger.warning(".env file not found at project root")

    # OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY missing; model features may be limited")

    # DB_PATH
    db_path = os.getenv("DB_PATH")
    if not db_path:
        # default to internal sqlite path
        try:
            from ai_factory.memory.memory_db import DB_PATH as DEFAULT_DB
            logger.info(f"DB_PATH not set; defaulting to {DEFAULT_DB}")
        except Exception:
            logger.warning("DB_PATH missing and default could not be determined")

    # TEMPLATES_PATH
    tpath = os.getenv("TEMPLATES_PATH")
    if not tpath:
        logger.info("TEMPLATES_PATH not set; using internal ai_factory/templates")

# API port constant for local UI helpers
API_PORT = 8015
