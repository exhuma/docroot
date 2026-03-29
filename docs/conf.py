# Sphinx configuration for Docroot documentation.

import tomllib
from pathlib import Path

with open(
    Path(__file__).parent.parent / "apps" / "backend" / "pyproject.toml",
    "rb",
) as _f:
    _meta = tomllib.load(_f)

project = "Docroot"
author = "Docroot contributors"
release = _meta["project"]["version"]
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

autosectionlabel_prefix_document = True

myst_enable_extensions = ["colon_fence"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "furo"

html_theme_options = {
    "sidebar_hide_name": False,
}

exclude_patterns = ["README.md"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
