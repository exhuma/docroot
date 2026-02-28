import re
from fastapi import HTTPException

NAMESPACE_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]*$")
VERSION_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
LOCALE_RE = re.compile(r"^[a-z]{2}$")


def validate_namespace(name: str) -> None:
    if not NAMESPACE_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid namespace name: {name}",
        )


def validate_project(name: str) -> None:
    if not NAMESPACE_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project name: {name}",
        )


def validate_version(name: str) -> None:
    if not VERSION_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid version: {name}",
        )


def validate_locale(name: str) -> None:
    if not LOCALE_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid locale: {name}",
        )
