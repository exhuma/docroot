"""Logging configuration for the Docroot backend.

Sets up colorful console logging via the ``gouge`` library.
Call :func:`setup_logging` once at application startup to apply
the configuration globally.

Usage::

    from app.logging import get_logger, setup_logging
    setup_logging("INFO")
    log = get_logger(__name__)
    log.info("Application started")
"""
import logging

from gouge.colourcli import Simple


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a gouge colour formatter.

    Installs a :class:`gouge.colourcli.Simple` handler on the root
    logger and sets the log level for the ``app`` logger namespace.
    Third-party loggers (uvicorn, fastapi) are left at their
    default levels to avoid duplicate output.

    :param level: Log level string (e.g. ``"DEBUG"``, ``"INFO"``,
        ``"WARNING"``, ``"ERROR"``).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    Simple.basicConfig(level=numeric_level)
    logging.getLogger("app").setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Return a :class:`logging.Logger` for the given name.

    :param name: Logger name, typically ``__name__``.
    :returns: Logger instance.
    """
    return logging.getLogger(name)
