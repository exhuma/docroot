"""FastAPI application factory for the Docroot API.

Creates and configures the FastAPI application instance. All
middleware and router registration happens here. Import
``create_app`` to instantiate the application for testing or
production.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.logging import get_logger, setup_logging
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.me import router as me_router
from app.routes.namespaces import router as namespaces_router
from app.routes.projects import router as projects_router
from app.routes.session import router as session_router
from app.routes.versions import router as versions_router
from app.settings import Settings, get_settings

_log = get_logger(__name__)


def _make_lifespan(settings: Settings):
    """Return a lifespan context manager bound to *settings*.

    :param settings: Application settings instance.
    :returns: Async context manager for the application lifespan.
    """

    @asynccontextmanager
    async def lifespan(
        application: FastAPI,
    ) -> AsyncGenerator[None, None]:
        """Run startup and shutdown tasks for the application.

        :param application: The FastAPI application instance.
        """
        setup_logging(settings.log_level)
        _log.info(
            "Docroot API starting up (log_level=%s, data_root=%s)",
            settings.log_level,
            settings.data_root,
        )
        if not settings.oauth_jwks_url:
            _log.warning(
                "DOCROOT_API_OAUTH_JWKS_URL is not set — authentication is disabled"
            )
        else:
            _log.info("JWKS endpoint: %s", settings.oauth_jwks_url)
            if not settings.oauth_verify_ssl:
                _log.warning(
                    "DOCROOT_API_OAUTH_VERIFY_SSL=false — "
                    "TLS verification for the JWKS endpoint is "
                    "DISABLED. Do not use this setting in production."
                )
        yield
        _log.info("Docroot API shutting down")

    return lifespan


def create_app(
    settings: Settings | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    :param settings: Optional settings override. When ``None``,
        settings are loaded from environment variables.
    :returns: Configured :class:`fastapi.FastAPI` instance.
    """
    if settings is None:
        settings = get_settings()

    cors_raw = settings.cors_origins
    cors_origins = (
        ["*"] if cors_raw == "*" else [o.strip() for o in cors_raw.split(",")]
    )

    application = FastAPI(
        title="Docroot API",
        lifespan=_make_lifespan(settings),
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def _log_requests(request: Request, call_next):
        """Log every incoming HTTP request and its response status.

        :param request: Incoming HTTP request.
        :param call_next: Next middleware / route handler.
        :returns: HTTP response.
        """
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        _log.info(
            "%s %s %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(me_router)
    application.include_router(session_router)
    application.include_router(namespaces_router)
    application.include_router(projects_router)
    application.include_router(versions_router)

    return application


app = create_app()
