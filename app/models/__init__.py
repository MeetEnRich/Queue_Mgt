"""
app/models/__init__.py
======================
Convenience re-exports so the rest of the app can do::

    from app.models import Office, Staff, Student, ...
"""

from app.models.office import Office
from app.models.complaint_category import ComplaintCategory
from app.models.student import Student
from app.models.staff import Staff
from app.models.complaint import Complaint
from app.models.queue_token import QueueToken
from app.models.system_setting import SystemSetting

__all__ = [
    "Office",
    "ComplaintCategory",
    "Student",
    "Staff",
    "Complaint",
    "QueueToken",
    "SystemSetting",
]
