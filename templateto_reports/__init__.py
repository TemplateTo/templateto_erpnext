"""TemplateTo Reports — cloud-based PDF rendering for Frappe/ERPNext."""

import sys

import frappe.utils.pdf as _pdf_module

__version__ = "1.0.0"

_original_get_pdf = _pdf_module.get_pdf


def _patched_get_pdf(html, options=None, output=None):
    """Drop-in replacement for frappe.utils.pdf.get_pdf.

    Routes through TemplateTo API when enabled, falls back to wkhtmltopdf otherwise.
    """
    from templateto_reports.pdf_override import get_pdf

    return get_pdf(html, options=options, output=output, _original=_original_get_pdf)


_pdf_module.get_pdf = _patched_get_pdf

# Patch modules that imported get_pdf via direct binding (top-level
# `from frappe.utils.pdf import get_pdf`), which creates a local reference
# that survives the module-level patch above.
# Note: frappe.utils.print_utils does a lazy import inside get_print(),
# so it picks up the module-level patch automatically — no patching needed.
for _mod_name in ("frappe.utils.print_format", "frappe.email.email_body"):
    _mod = sys.modules.get(_mod_name)
    if _mod and hasattr(_mod, "get_pdf"):
        _mod.get_pdf = _patched_get_pdf
