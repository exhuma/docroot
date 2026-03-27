#!/bin/sh
# Generate /usr/share/nginx/html/oidc-config.json at container
# startup from OIDC_ISSUER and OIDC_CLIENT_ID environment
# variables.  Both values default to empty string (OIDC disabled).
# The SPA fetches this file on page load instead of calling the
# backend API, keeping front-end and back-end configuration
# boundaries separate.
set -e

OIDC_CONFIG_FILE=/usr/share/nginx/html/oidc-config.json

# Escape a string value for embedding in a JSON string literal.
# Handles backslashes and double-quotes (the only characters that
# must be escaped inside a JSON string).
json_string() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

if [ -n "${OIDC_ISSUER:-}" ]; then
    ISSUER_JSON="\"$(json_string "${OIDC_ISSUER}")\""
else
    ISSUER_JSON="null"
fi

if [ -n "${OIDC_CLIENT_ID:-}" ]; then
    CLIENT_ID_JSON="\"$(json_string "${OIDC_CLIENT_ID}")\""
else
    CLIENT_ID_JSON="null"
fi

printf '{"issuer":%s,"client_id":%s}\n' \
    "${ISSUER_JSON}" "${CLIENT_ID_JSON}" \
    > "${OIDC_CONFIG_FILE}"
