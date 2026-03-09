"""Tests for the logging setup module."""
import logging

import pytest

from app.logging import _UVICORN_LOGGERS, get_logger, setup_logging


def test_setup_logging_info():
    """Ensure setup_logging sets the 'app' logger to INFO level."""
    setup_logging("INFO")
    logger = logging.getLogger("app")
    assert logger.level == logging.INFO


def test_setup_logging_debug():
    """Ensure setup_logging sets the 'app' logger to DEBUG level."""
    setup_logging("DEBUG")
    logger = logging.getLogger("app")
    assert logger.level == logging.DEBUG


def test_setup_logging_warning():
    """Ensure setup_logging sets the 'app' logger to WARNING level."""
    setup_logging("WARNING")
    logger = logging.getLogger("app")
    assert logger.level == logging.WARNING


def test_setup_logging_unknown_falls_back_to_info():
    """Ensure an unknown log level falls back to INFO."""
    setup_logging("NOTAREAL_LEVEL")
    logger = logging.getLogger("app")
    assert logger.level == logging.INFO


def test_get_logger_returns_logger():
    """Ensure get_logger returns a Logger with the given name."""
    log = get_logger("app.test_module")
    assert isinstance(log, logging.Logger)
    assert log.name == "app.test_module"


def test_get_logger_child_of_app():
    """Ensure get_logger for 'app.x' is a child of 'app'."""
    parent = logging.getLogger("app")
    child = get_logger("app.storage")
    assert child.parent is parent


@pytest.mark.parametrize("name", _UVICORN_LOGGERS)
def test_uvicorn_logger_has_no_own_handlers(name):
    """Ensure uvicorn loggers have no handlers after setup_logging."""
    # Simulate uvicorn installing a handler before our setup runs.
    uv_log = logging.getLogger(name)
    uv_log.addHandler(logging.StreamHandler())
    uv_log.propagate = False

    setup_logging("INFO")

    assert uv_log.handlers == []
    assert uv_log.propagate is True


@pytest.mark.parametrize("name", _UVICORN_LOGGERS)
def test_uvicorn_logger_level_matches_app(name):
    """Ensure uvicorn loggers are set to the configured level."""
    setup_logging("WARNING")
    uv_log = logging.getLogger(name)
    assert uv_log.level == logging.WARNING
