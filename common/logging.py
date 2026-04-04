import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with a consistent format.

    Log level is controlled by the LOG_LEVEL env var (default: INFO).
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, level, logging.INFO))

        handler = logging.StreamHandler()
        handler.setLevel(logger.level)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
