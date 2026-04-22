from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

_INITIALIZED = False


def setup_logging(log_dir: Path, level: int = logging.INFO) -> Path:
    global _INITIALIZED
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "house_index.log"

    if _INITIALIZED:
        return log_file

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(logging.WARNING)
    root.addHandler(stream_handler)

    def _excepthook(exc_type, exc_value, exc_tb):
        logging.getLogger("house_index").exception(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_tb)
        )

    sys.excepthook = _excepthook

    _INITIALIZED = True
    logging.getLogger("house_index").info("Logging started → %s", log_file)
    return log_file
