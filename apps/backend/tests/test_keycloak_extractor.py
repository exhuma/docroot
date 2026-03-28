"""Tests for the Keycloak JWT role extractor."""

from app.extractors.keycloak import _include_client, extract_roles


def test_realm_roles_returned_as_is() -> None:
    """Ensure realm-level roles are returned without any prefix."""
    payload: dict[str, object] = {
        "realm_access": {"roles": ["editor", "viewer"]},
    }
    result = extract_roles(payload, {})
    assert result == ["editor", "viewer"]


def test_client_roles_prefixed_with_client_id() -> None:
    """Ensure client-level roles are prefixed with '<client_id>/'."""
    payload: dict[str, object] = {
        "resource_access": {
            "my-client": {"roles": ["editor", "admin"]},
        },
    }
    result = extract_roles(payload, {})
    assert result == ["my-client/editor", "my-client/admin"]


def test_realm_and_client_roles_not_merged() -> None:
    """Ensure realm roles and client roles are kept distinct."""
    payload: dict[str, object] = {
        "realm_access": {"roles": ["editor"]},
        "resource_access": {
            "my-client": {"roles": ["editor"]},
        },
    }
    result = extract_roles(payload, {})
    # Realm role "editor" and client role "my-client/editor" are different.
    assert "editor" in result
    assert "my-client/editor" in result
    assert len(result) == 2


def test_multiple_clients_all_prefixed() -> None:
    """Ensure roles from multiple clients are all prefixed correctly."""
    payload: dict[str, object] = {
        "resource_access": {
            "client-a": {"roles": ["reader"]},
            "client-b": {"roles": ["writer"]},
        },
    }
    result = extract_roles(payload, {})
    assert "client-a/reader" in result
    assert "client-b/writer" in result


def test_deduplication_preserved() -> None:
    """Ensure duplicate roles are deduplicated while preserving order."""
    payload: dict[str, object] = {
        "realm_access": {"roles": ["editor", "editor"]},
        "resource_access": {
            "my-client": {"roles": ["admin", "admin"]},
        },
    }
    result = extract_roles(payload, {})
    assert result.count("editor") == 1
    assert result.count("my-client/admin") == 1


def test_empty_payload_returns_empty_list() -> None:
    """Ensure an empty payload returns an empty list."""
    result = extract_roles({}, {})
    assert result == []


def test_missing_realm_access_key_returns_only_client_roles() -> None:
    """Ensure missing realm_access does not break extraction."""
    payload: dict[str, object] = {
        "resource_access": {
            "my-client": {"roles": ["viewer"]},
        },
    }
    result = extract_roles(payload, {})
    assert result == ["my-client/viewer"]


def test_non_list_realm_roles_ignored() -> None:
    """Ensure non-list realm_access.roles is ignored gracefully."""
    payload: dict[str, object] = {
        "realm_access": {"roles": "not-a-list"},
    }
    result = extract_roles(payload, {})
    assert result == []


def test_non_dict_client_entry_ignored() -> None:
    """Ensure non-dict resource_access entries are ignored gracefully."""
    payload: dict[str, object] = {
        "resource_access": {
            "my-client": "not-a-dict",
        },
    }
    result = extract_roles(payload, {})
    assert result == []


# ---------------------------------------------------------------------------
# Allowlist / denylist filtering
# ---------------------------------------------------------------------------


def test_allowlist_includes_only_listed_clients() -> None:
    """Ensure only whitelisted clients are extracted when allowlist set."""
    payload: dict[str, object] = {
        "resource_access": {
            "client-a": {"roles": ["reader"]},
            "client-b": {"roles": ["writer"]},
        },
    }
    ctx: dict[str, object] = {
        "client_allowlist": ["client-a"],
    }
    result = extract_roles(payload, ctx)
    assert "client-a/reader" in result
    assert "client-b/writer" not in result


def test_denylist_excludes_listed_clients() -> None:
    """Ensure denylisted clients are excluded from role extraction."""
    payload: dict[str, object] = {
        "resource_access": {
            "client-a": {"roles": ["reader"]},
            "client-b": {"roles": ["writer"]},
        },
    }
    ctx: dict[str, object] = {
        "client_denylist": ["client-b"],
    }
    result = extract_roles(payload, ctx)
    assert "client-a/reader" in result
    assert "client-b/writer" not in result


def test_allowlist_takes_precedence_over_denylist() -> None:
    """Ensure allowlist wins when a client appears in both lists."""
    payload: dict[str, object] = {
        "resource_access": {
            "client-a": {"roles": ["reader"]},
        },
    }
    ctx: dict[str, object] = {
        "client_allowlist": ["client-a"],
        "client_denylist": ["client-a"],
    }
    result = extract_roles(payload, ctx)
    assert "client-a/reader" in result


def test_empty_allowlist_uses_denylist() -> None:
    """Ensure an empty allowlist falls back to denylist filtering."""
    payload: dict[str, object] = {
        "resource_access": {
            "client-a": {"roles": ["reader"]},
            "client-b": {"roles": ["writer"]},
        },
    }
    ctx: dict[str, object] = {
        "client_allowlist": [],
        "client_denylist": ["client-a"],
    }
    result = extract_roles(payload, ctx)
    assert "client-a/reader" not in result
    assert "client-b/writer" in result


def test_realm_roles_unaffected_by_allowlist() -> None:
    """Ensure realm roles are never filtered by client allow/deny lists."""
    payload: dict[str, object] = {
        "realm_access": {"roles": ["global-admin"]},
        "resource_access": {
            "client-a": {"roles": ["local-admin"]},
        },
    }
    ctx: dict[str, object] = {
        "client_allowlist": [],
        "client_denylist": ["client-a"],
    }
    result = extract_roles(payload, ctx)
    assert "global-admin" in result
    assert "client-a/local-admin" not in result


def test_include_client_allowlist_only() -> None:
    """Ensure _include_client includes a client in allowlist."""
    assert _include_client("a", ["a", "b"], []) is True
    assert _include_client("c", ["a", "b"], []) is False


def test_include_client_denylist_only() -> None:
    """Ensure _include_client excludes a client in denylist."""
    assert _include_client("a", [], ["a"]) is False
    assert _include_client("b", [], ["a"]) is True


def test_include_client_allowlist_wins_over_denylist() -> None:
    """Ensure _include_client returns True when in both lists."""
    assert _include_client("a", ["a"], ["a"]) is True
