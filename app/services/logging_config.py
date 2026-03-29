import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.services.env_config import load_project_env

load_project_env()


DEFAULT_LOG_FILE_NAME = "nba_news_agent.log"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CONFIGURED = False


def _get_log_level() -> int:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def _get_log_path() -> Path:
    log_file_path = os.getenv("LOG_FILE_PATH")
    if log_file_path:
        return Path(log_file_path)

    project_root = Path(__file__).resolve().parents[2]
    return project_root / "logs" / DEFAULT_LOG_FILE_NAME


def configure_logging() -> None:
    global _CONFIGURED

    if _CONFIGURED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(_get_log_level())

    if root_logger.handlers:
        _CONFIGURED = True
        return

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    try:
        log_path = _get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=1_000_000,
            backupCount=3,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError:
        root_logger.warning("Failed to initialize file logging", exc_info=True)

    _CONFIGURED = True
