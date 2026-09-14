"""``python -m cinco_tintas`` — build the 5 Tintas website into ``dist/``.

There are no options to remember. Run it, read what it says, open ``dist/index.html``.
"""

from __future__ import annotations

import sys

from .build import build_site, describe_result
from .errors import ContentProblems, format_notices, format_problems, format_unexpected


def main() -> int:
    """Build the site. Returns 0 when it worked and 1 when there is something to fix."""
    try:
        result = build_site()
    except ContentProblems as problems:
        print(format_problems(problems.problems))
        # Whatever else was noticed still gets said: one blocking mistake must not hide the rest.
        notices = format_notices(problems.notices)
        if notices:
            print(notices)
        return 1
    except Exception as error:  # a bug in the builder must still read as plain English
        print(format_unexpected(error))
        return 1

    print(describe_result(result))
    notices = format_notices(result.report.notices)
    if notices:
        print(notices)
    return 0


if __name__ == "__main__":
    sys.exit(main())
