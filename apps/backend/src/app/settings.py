"""Application settings loaded from environment variables.

Uses pydantic-settings so all configuration is validated at startup.
All variables are prefixed with DOCROOT_.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Docroot application settings.

    :param data_root: Filesystem path where namespace data is stored.
    :param oauth_jwks_url: JWKS endpoint URL. Supports file:// for
        local dev.
    :param oauth_audience: Expected JWT audience. Empty string
        disables audience validation.
    :param oauth_role_extractor: Name of the role extractor to use.
        Currently only 'keycloak' is supported.
    :param cors_origins: Comma-separated allowed CORS origins, or
        '*'.
    :param zip_max_files: Maximum number of files in an uploaded ZIP.
    :param zip_max_extracted_mb: Maximum extracted size in MB for a
        ZIP archive.
    :param log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    :param cookie_secure: Append the ``Secure`` attribute to the
        session cookie (required for HTTPS deployments).
    :param oidc_issuer: OIDC issuer URL served to the frontend
        public client (e.g. ``https://keycloak.example.com/realms/myrealm``).
        Empty string disables OIDC login button.
    :param oidc_client_id: OIDC public client ID used by the
        frontend for the authorization-code + PKCE flow.
    :param oauth_ca_bundle: Path to a PEM CA certificate or bundle
        used to verify the JWKS endpoint's TLS certificate.  Set
        this when the IDP is behind an internal or self-signed CA.
        Leave empty to use the system default trust store.
    :param oauth_verify_ssl: Set to ``False`` to disable TLS
        certificate verification when fetching the JWKS endpoint.
        **Only use in non-production / trusted-network environments.**
        A warning is logged on startup when verification is disabled.
    """

    model_config = SettingsConfigDict(
        env_prefix="DOCROOT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    data_root: str = Field(default="/data")
    oauth_jwks_url: str = Field(default="")
    oauth_audience: str = Field(default="")
    oauth_role_extractor: str = Field(default="keycloak")
    cors_origins: str = Field(default="*")
    zip_max_files: int = Field(default=500)
    zip_max_extracted_mb: int = Field(default=500)
    log_level: str = Field(default="INFO")
    cookie_secure: bool = Field(default=False)
    oidc_issuer: str = Field(default="")
    oidc_client_id: str = Field(default="")
    oauth_ca_bundle: str = Field(default="")
    oauth_verify_ssl: bool = Field(default=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance.

    Cached via :func:`functools.lru_cache` — no global variable
    is needed.

    :returns: Application settings loaded from environment.
    """
    return Settings()
