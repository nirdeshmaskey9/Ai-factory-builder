import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_DIR = os.path.join(os.path.dirname(__file__), "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def ensure_log_dir(path: Optional[str] = None) -> str:
    p = path or LOG_DIR
    os.makedirs(p, exist_ok=True)
    return p


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging for both console and rotating file."""
    ensure_log_dir()
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid dupes on reload
    for h in list(logger.handlers):
        logger.removeHandler(h)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    # Console
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File (rotating ~5MB x 3)
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
