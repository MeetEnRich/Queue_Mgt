"""
app/services/qr_service.py
===========================
QR-code generation for office registration URLs.
"""

from __future__ import annotations

import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.models.office import Office


def generate_office_qr(office: Office) -> bytes:
    """Generate a PNG QR code pointing to the office registration page.

    The encoded URL follows the pattern::

        http://localhost:5000/o/{office.slug}/register

    Args:
        office: The :class:`Office` instance to generate the QR for.

    Returns:
        Raw PNG image bytes suitable for download or ``<img>`` embedding
        via a data-URI.
    """
    url = f"http://localhost:5000/o/{office.slug}/register"

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
