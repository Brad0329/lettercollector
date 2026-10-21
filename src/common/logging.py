"""Logging utility guaranteeing zero stdout pollution for MCP stdio protocol."""
import logging
import sys


def setup_logger(name: str = "letter_collector", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger that outputs strictly to sys.stderr."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()
