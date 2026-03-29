"""Tests for the slugify utility function."""

import pytest

from app.slugify import slugify


def test_slugify_simple_lowercase():
    """Ensure simple lowercase words pass through unchanged."""
    assert slugify("hello") == "hello"


def test_slugify_existing_slug():
    """Ensure already-slugified names are returned unchanged."""
    assert slugify("my-project") == "my-project"


def test_slugify_spaces_become_hyphens():
    """Ensure spaces are converted to hyphens."""
    assert slugify("My Amazing Project") == "my-amazing-project"


def test_slugify_mixed_case():
    """Ensure uppercase letters are lowercased."""
    assert slugify("Hello World") == "hello-world"


def test_slugify_trailing_punctuation():
    """Ensure leading and trailing hyphens are stripped."""
    assert slugify("Hello World!") == "hello-world"


def test_slugify_unicode_diacritics():
    """Ensure accented characters are transliterated to ASCII."""
    assert slugify("café") == "cafe"


def test_slugify_unicode_umlaut():
    """Ensure umlauts are transliterated to base ASCII letters."""
    assert slugify("München") == "munchen"


def test_slugify_multiple_spaces():
    """Ensure multiple consecutive spaces become a single hyphen."""
    assert slugify("hello   world") == "hello-world"


def test_slugify_underscores_preserved():
    """Ensure underscores inside a name are preserved."""
    assert slugify("my_project") == "my_project"


def test_slugify_special_chars_removed():
    """Ensure non-alphanumeric special chars become hyphens."""
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_all_special_chars_returns_empty():
    """Ensure a string of only special characters returns empty."""
    assert slugify("!!!") == ""


def test_slugify_numeric():
    """Ensure strings starting with digits are handled correctly."""
    assert slugify("42 things") == "42-things"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("My Namespace", "my-namespace"),
        ("Docs & Guides", "docs-guides"),
        ("v1.0 Release Notes", "v1-0-release-notes"),
        ("   leading spaces", "leading-spaces"),
        ("trailing spaces   ", "trailing-spaces"),
    ],
)
def test_slugify_parametrized(value: str, expected: str):
    """Ensure parametrized display names produce the expected slugs."""
    assert slugify(value) == expected
