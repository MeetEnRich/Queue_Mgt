"""
app/utils/decorators.py
=======================
Custom view decorators for role-based access control.
"""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort
from flask_login import current_user, login_required


# Role hierarchy — higher roles inherit permissions of lower ones.
_ROLE_HIERARCHY: dict[str, int] = {
    "staff": 1,
    "office_admin": 2,
    "super_admin": 3,
}


def role_required(role: str) -> Callable:
    """Decorator that restricts a view to users with at least *role*.

    The hierarchy is::

        staff  →  office_admin  →  super_admin

    A ``super_admin`` can access everything.  An ``office_admin`` can access
    ``office_admin`` and ``staff`` views, and so on.

    Usage::

        @app.route("/staff/dashboard")
        @role_required("staff")
        def staff_dashboard():
            ...

    Args:
        role: Minimum role required (``'staff'``, ``'office_admin'``, or
              ``'super_admin'``).

    Returns:
        A decorator that wraps the view with both ``login_required`` and
        the role check.
    """
    min_level = _ROLE_HIERARCHY.get(role, 0)

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            user_level = _ROLE_HIERARCHY.get(current_user.role, 0)
            if user_level < min_level:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
