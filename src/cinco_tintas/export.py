"""``python -m cinco_tintas.export`` — assemble the folder that becomes Cami's own repository.

The website is built here, in a repository full of things Cami never needs to see. This puts a
clean copy of only the parts she owns into ``handoff/``: the generator, her content, the theme, the
two READMEs written for her, and the GitHub Actions that publish the site and add a product from an
issue. That folder is a complete repository on its own — nothing above it is ever needed again.

Two rules are checked rather than hoped for:

* **No Git LFS pointers.** Pictures in this repository go through Git LFS. GitHub Pages serves an
  LFS pointer as a 34-byte text file, so a hand-off tree with one in it would publish broken
  photos. Every copied file is checked, and ``.gitattributes`` is never copied, so Cami's
  repository stores its photos as ordinary files.
* **No leftover template name.** This repository was made from a Python template, and the hand-off
  tree may not mention that template's name anywhere — including in this file, which is why
  :data:`TEMPLATE_NAME` is spelled in two pieces below.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .errors import Problem, format_unexpected
from .paths import CONTENT_DIR, PACKAGE_DIR, PROJECT_ROOT, THEME_DIR, WEBSITE_DIR, describe

HANDOFF_DIR = PROJECT_ROOT / "handoff"
HANDOFF_SOURCE_DIR = WEBSITE_DIR / "handoff"

#: How every Git LFS pointer file begins. Spelled in two pieces for the same reason as
#: :data:`TEMPLATE_NAME`: searching the exported tree for this text should find nothing at all.
LFS_POINTER_PREFIX = b"version https://" + b"git-lfs"

#: The name of the template this repository started from. Written in two pieces on purpose: this
#: file is itself copied into the hand-off tree, and the tree must not contain that word anywhere.
TEMPLATE_NAME = "my" + "project"

#: Never copied. ``.gitattributes`` is the important one: it is what routes pictures through LFS.
SKIPPED_NAMES = frozenset(
    {
        ".DS_Store",
        ".gitattributes",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
    }
)
SKIPPED_SUFFIXES = frozenset({".pyc", ".pyo"})

#: Files whose text is checked for the old template name. Anything else is a picture or a font.
TEXT_SUFFIXES = frozenset(
    {".cfg", ".css", ".html", ".ini", ".js", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
)


#: ``gitignore`` cannot live in this repository under its real name — Git would use it here.
HOISTED_RENAMES = {"gitignore": ".gitignore"}

#: The hand-off tree is useless if any of these is missing, so the export refuses instead.
REQUIRED_FILES = (
    "src/cinco_tintas/__init__.py",
    "src/cinco_tintas/__main__.py",
    "src/cinco_tintas/build.py",
    "src/cinco_tintas/content.py",
    "src/cinco_tintas/errors.py",
    "src/cinco_tintas/images.py",
    "src/cinco_tintas/intake.py",
    "src/cinco_tintas/model.py",
    "src/cinco_tintas/paths.py",
    "src/cinco_tintas/render.py",
    "src/cinco_tintas/video.py",
    "website/content/site.md",
    "website/content/about.md",
    "website/theme/templates/base.html",
    "website/theme/templates/_macros.html",
    "website/theme/static/css/site.css",
    "website/theme/static/js/site.js",
    "website/theme/static/img/bee.png",
    "website/theme/static/img/bee-cursor-32.png",
    "README.md",
    "README.es.md",
    "requirements.txt",
    "pyproject.toml",
    ".gitignore",
    ".github/workflows/deploy.yml",
    ".github/workflows/add-product.yml",
    ".github/ISSUE_TEMPLATE/add-product.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
)


def is_text(target: Path, data: bytes) -> bool:
    """Whether this file's words should be read before it is handed over.

    Suffix alone is not enough: ``gitignore`` becomes ``.gitignore``, whose suffix is empty, and that
    is the one file the export deliberately renames on the way out — so the one file most likely to
    be overlooked was the one never checked. A file with no suffix is read if its bytes are text.
    """
    if target.suffix.lower() in TEXT_SUFFIXES:
        return True
    if target.suffix:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


class ExportRefused(Exception):
    """Raised when the hand-off tree would not be safe to publish. Carries the plain-English list."""

    def __init__(self, problems: list[Problem]) -> None:
        super().__init__(f"{len(problems)} problem(s) with the hand-off export")
        self.problems = list(problems)


@dataclass(frozen=True, slots=True)
class ExportResult:
    """What the export wrote, for the summary printed at the end."""

    handoff_dir: Path
    files: list[Path]

    @property
    def total_bytes(self) -> int:
        return sum(item.stat().st_size for item in self.files)


@dataclass(slots=True)
class _Assembly:
    """Bookkeeping while the tree is copied: what was written and what went wrong."""

    files: list[Path] = field(default_factory=list[Path])
    problems: list[Problem] = field(default_factory=list[Problem])


def export(*, handoff_dir: Path = HANDOFF_DIR) -> ExportResult:
    """Empty and rebuild the hand-off tree.

    A ``.git`` folder inside it is left exactly as it is, so exporting again after the hand-off
    repository has been set up updates the files without throwing away its history or its remote.

    Raises :class:`ExportRefused` if anything about the result would publish badly. The half-made
    tree is emptied in that case, so a broken export can never be the thing that gets pushed.
    """
    if not HANDOFF_SOURCE_DIR.is_dir():
        raise ExportRefused(
            [
                Problem(
                    where=describe(HANDOFF_SOURCE_DIR),
                    what="The folder holding Cami's README files and her GitHub Actions is not there.",
                    fix="This is part of the repository; restore it from Git before exporting.",
                )
            ]
        )

    _empty(handoff_dir)
    assembly = _Assembly()
    _copy_tree(PACKAGE_DIR, handoff_dir / "src" / PACKAGE_DIR.name, assembly=assembly)
    _copy_tree(CONTENT_DIR, handoff_dir / "website" / "content", assembly=assembly)
    _copy_tree(THEME_DIR, handoff_dir / "website" / "theme", assembly=assembly)
    _copy_tree(HANDOFF_SOURCE_DIR, handoff_dir, assembly=assembly, renames=HOISTED_RENAMES)
    _check_required(handoff_dir, assembly=assembly)

    if assembly.problems:
        _empty(handoff_dir)
        raise ExportRefused(assembly.problems)
    return ExportResult(handoff_dir=handoff_dir, files=assembly.files)


def _empty(handoff_dir: Path) -> None:
    """Clear the hand-off folder, keeping any Git repository that has been set up inside it."""
    if not handoff_dir.is_dir():
        return
    for item in handoff_dir.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)


def _copy_tree(source: Path, target: Path, *, assembly: _Assembly, renames: dict[str, str] | None = None) -> None:
    """Copy one folder, checking every file on the way through.

    ``renames`` applies at this level only: it is how ``website/handoff/gitignore`` becomes the
    hand-off repository's real ``.gitignore``.
    """
    target.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        if item.name in SKIPPED_NAMES or item.suffix.lower() in SKIPPED_SUFFIXES:
            continue
        if item.is_dir():
            _copy_tree(item, target / item.name, assembly=assembly)
        elif item.is_file():
            name = (renames or {}).get(item.name, item.name)
            _copy_file(item, target / name, assembly=assembly)


def _copy_file(source: Path, target: Path, *, assembly: _Assembly) -> None:
    data = source.read_bytes()
    if data.startswith(LFS_POINTER_PREFIX):
        assembly.problems.append(
            Problem(
                where=describe(source),
                what="This is a Git LFS pointer file, not the real picture. GitHub Pages would show it as broken.",
                fix="Run  git lfs pull  in this repository, then export again.",
            )
        )
        return
    if is_text(target, data) and TEMPLATE_NAME.encode() in data:
        assembly.problems.append(
            Problem(
                where=describe(source),
                what=f'This file still mentions "{TEMPLATE_NAME}", the name of the template this repository '
                "started from. Cami's repository must not carry it.",
                fix=f'Replace "{TEMPLATE_NAME}" in that file with the right name, then export again.',
            )
        )
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    assembly.files.append(target)


def _check_required(handoff_dir: Path, *, assembly: _Assembly) -> None:
    for relative in REQUIRED_FILES:
        if not (handoff_dir / relative).is_file():
            assembly.problems.append(
                Problem(
                    where=f"handoff/{relative}",
                    what="This file is missing from the hand-off tree, which needs it to work on its own.",
                    fix="Check that website/handoff/ and website/ still contain it, then export again.",
                )
            )


def format_refusal(problems: list[Problem]) -> str:
    """The message printed when the export will not hand over a tree it does not trust."""
    lines = [
        "",
        "I did not make the hand-off folder, because it would not have worked once published.",
        "It is empty now, so nothing broken can be pushed by mistake.",
        "",
    ]
    for number, problem in enumerate(problems, start=1):
        lines.append(f"{number:>3}. {problem.where}")
        lines.append(f"     {problem.what}")
        lines.append(f"     What to do: {problem.fix}")
        lines.append("")
    return "\n".join(lines)


def describe_export(result: ExportResult) -> str:
    """The summary and the next steps, printed when the export worked."""
    megabytes = result.total_bytes / 1_000_000
    return "\n".join(
        [
            "",
            f"Done. {result.handoff_dir} holds {len(result.files)} files ({megabytes:.1f} MB).",
            "It is a complete repository on its own: no Git LFS, no trace of this repository.",
            "",
            "Next steps (Jack, in the browser and a terminal):",
            "",
            "  1. Signed in as camilarestrepop, create a PUBLIC repository named exactly",
            "     camilarestrepop.github.io — no README, no .gitignore, no licence.",
            f"  2. cd {result.handoff_dir}",
            "     git init -b main && git add -A && git commit -m '5 Tintas website'",
            "     git remote add origin https://github.com/camilarestrepop/camilarestrepop.github.io.git",
            "     then push as Cami's account.",
            "  3. In that repository: Settings -> Pages -> Build and deployment -> Source:",
            "     GitHub Actions. The first publish starts by itself; watch it under Actions.",
            "  4. Open https://camilarestrepop.github.io and click through the site.",
            "  5. Signed in as camilarestrepop — the workflow ignores an issue opened by anyone else,",
            "     so this has to be tried from Cami's own account: Issues -> New issue -> Add a product.",
            "     Check the folder appears under website/content/products/, the site redeploys,",
            "     and the piece is on shop.html. Then delete that test folder.",
            "     Nothing to set up first: the workflow recognises the form by its title as well as",
            "     by its label, and it creates the add-product label itself on that first run.",
            "  6. Send Cami the link to README.md in her repository.",
            "",
            "Exporting again later refills this folder and leaves its .git alone, so a change made",
            "here can be committed and pushed on top of what is already there.",
            "",
        ]
    )


def main() -> int:
    """Assemble the hand-off tree. Returns 0 when it worked and 1 when it refused."""
    try:
        result = export()
    except ExportRefused as refused:
        print(format_refusal(refused.problems))
        return 1
    except Exception as error:  # a bug in the exporter must still read as plain English
        print(format_unexpected(error))
        return 1

    print(describe_export(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
