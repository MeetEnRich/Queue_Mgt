"""
app/utils/validators.py
=======================
Input-validation helpers.
"""

from __future__ import annotations

import re

# FULafia matric-number pattern: YYYY/FACULTY/DEPT/NNNN
# Examples: 2021/CP/CSC/0295, 2023/SSSE/EDU/12345
_MATRIC_RE = re.compile(r"^\d{4}/[A-Z]{2,4}/[A-Z]{2,5}/\d{3,5}$")


def validate_matric_no(matric_no: str) -> tuple[bool, str | None]:
    """Validate a student matric number against the university format.

    The expected format is ``YYYY/FACULTY/DEPT/NNNN``, e.g.
    ``2021/CP/CSC/0295``.

    Args:
        matric_no: The matric number string to check (should already be
                   stripped and upper-cased by the caller).

    Returns:
        ``(True, None)`` if valid, or ``(False, error_message)`` describing
        what is wrong.
    """
    if not matric_no:
        return False, "Matric number is required."

    if not _MATRIC_RE.match(matric_no):
        return False, (
            "Invalid matric number format. "
            "Expected pattern: YYYY/FACULTY/DEPT/NNNN "
            "(e.g. 2021/CP/CSC/0295)."
        )

    return True, None
