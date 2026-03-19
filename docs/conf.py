# Sphinx configuration for Docroot documentation.

project = "Docroot"
author = "Docroot contributors"
release = "1.0-alpha1"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
]

myst_enable_extensions = ["colon_fence"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "furo"

html_theme_options = {
    "sidebar_hide_name": False,
}

exclude_patterns = ["developer", "README.md"]
