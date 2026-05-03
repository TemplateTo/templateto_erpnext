"""Core PDF override logic — routes HTML through TemplateTo API."""

import base64
import io

import frappe
import requests

TIMEOUT_SECONDS = 60


def get_pdf_via_hook(print_format, html, options, output, pdf_generator=None):
    """Entry point for Frappe's pdf_generator hook system.

    Called by get_print() when a Print Format's pdf_generator field is set
    to something other than "wkhtmltopdf". Returns PDF bytes if we handle it,
    or None to pass to the next hook.
    """
    if pdf_generator != "templatetocloud":
        return None  # Not ours — let other hooks (Chrome, Print Designer) handle it

    settings = _get_settings()
    if not settings:
        return None  # Not configured — fall through (get_print will use wkhtmltopdf)

    api_key = settings.get_password("api_key")
    if not api_key:
        return None

    # No _original fallback here — if the hook path fails, get_print() falls
    # through to get_pdf() (wkhtmltopdf) which our monkey-patch may also intercept.
    return _render_via_templateto(html, settings, api_key, output)


def get_pdf(html, options=None, output=None, _original=None):
    """Drop-in replacement for frappe.utils.pdf.get_pdf (monkey-patch entry point).

    Args:
        html: HTML string to convert to PDF
        options: pdfkit options dict (passed to wkhtmltopdf on fallback)
        output: pypdf PdfWriter for appending (passed through on fallback)
        _original: reference to the original frappe.utils.pdf.get_pdf
    """
    settings = _get_settings()
    if not settings or not settings.enabled:
        return _original(html, options=options, output=output)

    api_key = settings.get_password("api_key")
    if not api_key:
        return _original(html, options=options, output=output)

    try:
        return _render_via_templateto(html, settings, api_key, output)

    except requests.exceptions.RequestException as exc:
        frappe.log_error(
            title="TemplateTo Connection Error",
            message=str(exc),
        )
        if settings.fallback_enabled:
            frappe.logger("templateto").warning(
                "TemplateTo API unreachable, falling back to wkhtmltopdf"
            )
            return _original(html, options=options, output=output)
        frappe.throw(
            "TemplateTo API is unreachable and fallback is disabled. "
            "Enable fallback in TemplateTo Settings or check your connection."
        )

    except Exception as exc:
        if settings.fallback_enabled:
            frappe.logger("templateto").warning(
                f"TemplateTo error ({exc}), falling back to wkhtmltopdf"
            )
            return _original(html, options=options, output=output)
        raise


def _get_settings():
    """Load TemplateTo Settings, returning None if unavailable."""
    try:
        settings = frappe.get_single("TemplateTo Settings")
    except Exception:
        # DocType not yet created (during install)
        return None
    if not settings.api_key:
        return None
    return settings


def _render_via_templateto(html, settings, api_key, output=None):
    """Send HTML to TemplateTo API, return PDF bytes or append to output."""
    if isinstance(html, bytes):
        html_bytes = html
    else:
        html_bytes = html.encode("utf-8")

    b64_html = base64.b64encode(html_bytes).decode("ascii")
    endpoint = (settings.api_endpoint or "https://api.templateto.com").rstrip("/")

    response = requests.post(
        f"{endpoint}/render/pdf/fromhtml",
        json={"base64HtmlString": b64_html},
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        timeout=TIMEOUT_SECONDS,
    )

    if response.status_code == 200 and response.content:
        if output:
            return _append_to_output(response.content, output)
        return response.content

    if response.status_code == 200:
        frappe.log_error(
            title="TemplateTo API Error",
            message="API returned HTTP 200 but with an empty PDF response",
        )
        raise Exception("TemplateTo API returned an empty PDF response")

    if response.status_code in (401, 403):
        frappe.log_error(
            title="TemplateTo Auth Error",
            message=f"HTTP {response.status_code} — check your API key",
        )
    else:
        frappe.log_error(
            title="TemplateTo API Error",
            message=f"HTTP {response.status_code}: {response.text[:500]}",
        )
    raise Exception(f"TemplateTo API returned HTTP {response.status_code}")


def _append_to_output(pdf_bytes, output):
    """Append PDF bytes to an existing PdfWriter (mirrors original get_pdf behavior)."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    output.append_pages_from_reader(reader)
    return output
