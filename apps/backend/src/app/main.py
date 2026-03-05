"""FastAPI application factory for the Docroot API.

Creates and configures the FastAPI application instance. All
middleware and router registration happens here. Import
``create_app`` to instantiate the application for testing or
production.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.namespaces import router as namespaces_router
from app.routes.projects import router as projects_router
from app.routes.versions import router as versions_router
from app.settings import Settings, get_settings


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
        ["*"]
        if cors_raw == "*"
        else [o.strip() for o in cors_raw.split(",")]
    )

    application = FastAPI(title="Docroot API")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(namespaces_router)
    application.include_router(projects_router)
    application.include_router(versions_router)

    return application


app = create_app()
