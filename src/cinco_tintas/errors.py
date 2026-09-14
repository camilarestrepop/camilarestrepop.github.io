"""Problems and notices, written for the person editing the website — never a traceback."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .paths import describe


@dataclass(frozen=True, slots=True)
class Problem:
    """Something that stops the website being built."""

    where: str
    what: str
    fix: str


@dataclass(frozen=True, slots=True)
class Notice:
    """Something worth mentioning that did not stop the build."""

    where: str
    what: str


class ContentProblems(Exception):
    """Raised when the content has mistakes in it. Carries the plain-English list.

    The notices gathered along the way come with it, so a build that stops still says everything it
    noticed. One blocking mistake would otherwise hide every other hint at once.
    """

    def __init__(self, problems: list[Problem], *, notices: list[Notice] | None = None) -> None:
        super().__init__(f"{len(problems)} problem(s) in the website content")
        self.problems = list(problems)
        self.notices = list(notices or [])


@dataclass(slots=True)
class Report:
    """Collects everything worth telling the author about while the site is built."""

    problems: list[Problem] = field(default_factory=list[Problem])
    notices: list[Notice] = field(default_factory=list[Notice])

    def problem(self, *, where: Path | str, what: str, fix: str) -> None:
        self.problems.append(Problem(where=_where(where), what=what, fix=fix))

    def notice(self, *, where: Path | str, what: str) -> None:
        self.notices.append(Notice(where=_where(where), what=what))

    @property
    def ok(self) -> bool:
        return not self.problems

    def raise_if_problems(self) -> None:
        if self.problems:
            raise ContentProblems(self.problems, notices=self.notices)


def _where(where: Path | str) -> str:
    return describe(where) if isinstance(where, Path) else where


def format_problems(problems: list[Problem]) -> str:
    """Render the numbered list the build prints when the content has mistakes."""
    count = len(problems)
    thing = "one thing" if count == 1 else f"{count} things"
    lines = [
        "",
        "I could not build the website yet.",
        f"There is {thing} to fix:" if count == 1 else f"There are {thing} to fix:",
        "",
    ]
    for number, problem in enumerate(problems, start=1):
        lines.append(f"{number:>3}. {problem.where}")
        lines.append(f"     {problem.what}")
        lines.append(f"     What to do: {problem.fix}")
        lines.append("")
    lines.append("Fix those, save the files, and build again.")
    lines.append("")
    return "\n".join(lines)


def format_notices(notices: list[Notice]) -> str:
    """Render the softer 'worth knowing' list printed after a successful build."""
    if not notices:
        return ""
    lines = ["", "Worth knowing:", ""]
    for notice in notices:
        lines.append(f"  - {notice.where}")
        lines.append(f"    {notice.what}")
    lines.append("")
    return "\n".join(lines)


def format_unexpected(error: BaseException) -> str:
    """Render an unexpected failure as something a non-technical author can act on."""
    return "\n".join(
        [
            "",
            "Something went wrong inside the website builder itself.",
            "This is a bug in the program, not a mistake in your files.",
            "",
            f"  Technical detail: {type(error).__name__}: {error}",
            "",
            "Please send that line to Jack and he will fix it.",
            "",
        ]
    )
