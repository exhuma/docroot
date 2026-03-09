"""Logging configuration for the Docroot backend.

Sets up colorful console logging via the ``gouge`` library.
Call :func:`setup_logging` once at application startup to apply
the configuration globally, including uvicorn's loggers.

Usage::

    from app.logging import get_logger, setup_logging
    setup_logging("INFO")
    log = get_logger(__name__)
    log.info("Application started")
"""
import logging

from gouge.colourcli import Simple

#: Uvicorn logger names that install their own handlers by default.
_UVICORN_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a gouge colour formatter.

    Installs a :class:`gouge.colourcli.Simple` handler on the root
    logger and sets the log level for the ``app`` logger namespace.
    Uvicorn loggers have their default handlers removed and
    propagation enabled so they also use the gouge formatter,
    ensuring visually consistent output across the whole process.

    :param level: Log level string (e.g. ``"DEBUG"``, ``"INFO"``,
        ``"WARNING"``, ``"ERROR"``).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    Simple.basicConfig(level=numeric_level)
    logging.getLogger("app").setLevel(numeric_level)

    # Remove uvicorn's own handlers and enable propagation so all
    # log records reach the root gouge handler instead.
    for name in _UVICORN_LOGGERS:
        uv_log = logging.getLogger(name)
        uv_log.handlers.clear()
        uv_log.propagate = True
        uv_log.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Return a :class:`logging.Logger` for the given name.

    :param name: Logger name, typically ``__name__``.
    :returns: Logger instance.
    """
    return logging.getLogger(name)
