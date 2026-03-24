"""Current-user identity endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import AuthContext, get_auth

router = APIRouter(prefix="/api", tags=["auth"])


class MeOut(BaseModel):
    subject: str
    roles: list[str]


@router.get("/me", response_model=MeOut)
async def get_me(
    auth: AuthContext = Depends(get_auth),
) -> MeOut:
    """Return the subject and roles of the authenticated caller.

    Delegates role extraction entirely to the server-side extractor
    so clients do not need to parse the JWT themselves.

    ---

    :param auth: Authenticated principal (required, injected).
    :returns: Subject and role list for the current token.
    :raises HTTPException: 401 if the caller is not authenticated.
    """
    return MeOut(subject=auth.subject, roles=auth.roles)
