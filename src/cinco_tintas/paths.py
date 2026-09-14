"""Where the website lives on disk.

Everything the builder reads or writes is found from the installed package, so there are no
command-line flags to get wrong: ``python -m cinco_tintas`` always builds the same folders.
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent


def _find_project_root() -> Path:
    """Return the folder that holds ``website/``.

    Both places the package runs from put it under ``src/``: this repository and the hand-off
    repository the export writes, which is a copy of the same shape. The walk is what makes the
    difference between them — a different number of folders above ``website/`` — not the layout.
    """
    for candidate in (PACKAGE_DIR, *PACKAGE_DIR.parents):
        if (candidate / "website" / "content").is_dir():
            return candidate
    return PACKAGE_DIR.parents[1]


PROJECT_ROOT = _find_project_root()

WEBSITE_DIR = PROJECT_ROOT / "website"
CONTENT_DIR = WEBSITE_DIR / "content"
THEME_DIR = WEBSITE_DIR / "theme"
TEMPLATES_DIR = THEME_DIR / "templates"
STATIC_DIR = THEME_DIR / "static"
DIST_DIR = PROJECT_ROOT / "dist"

PRODUCTS_DIRNAME = "products"
COLLECTIONS_DIRNAME = "collections"
RUNWAYS_DIRNAME = "runways"
SHARED_DIRNAME = "shared"

SITE_FILENAME = "site.md"
ABOUT_FILENAME = "about.md"
INFO_FILENAME = "info.md"


def describe(path: Path) -> str:
    """Name a file the way a person would: relative to the project when possible."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)
