from pydantic import BaseModel


class NamespaceOut(BaseModel):
    name: str


class ProjectOut(BaseModel):
    name: str


class VersionOut(BaseModel):
    name: str
    locales: list[str]
    is_latest: bool


class ResolveOut(BaseModel):
    version: str
    locale: str
    fallback_used: bool
