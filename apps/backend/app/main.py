import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.namespaces import router as namespaces_router
from app.routes.projects import router as projects_router
from app.routes.versions import router as versions_router

_cors_origins_raw = os.environ.get("CORS_ORIGINS", "*")
_cors_origins = (
    ["*"]
    if _cors_origins_raw == "*"
    else [o.strip() for o in _cors_origins_raw.split(",")]
)

app = FastAPI(title="Docroot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(namespaces_router)
app.include_router(projects_router)
app.include_router(versions_router)
