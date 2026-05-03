"""Tests for the TemplateTo PDF override.

Mirrors test structure from TemplateTo.Odoo/report_templateto/tests/test_report_templateto.py
"""

import base64
from unittest.mock import MagicMock, patch

import frappe
import requests as req
from frappe.tests.utils import FrappeTestCase


class TestTemplateToSettings(FrappeTestCase):
    """Tests for the TemplateTo Settings DocType."""

    def setUp(self):
        self.settings = frappe.get_single("TemplateTo Settings")
        self.settings.enabled = 0
        self.settings.api_endpoint = "https://api.templateto.com"
        self.settings.fallback_enabled = 1
        self.settings.save()

    def test_disabled_by_default(self):
        """Module should be disabled on fresh install."""
        self.assertEqual(self.settings.enabled, 0)

    def test_fallback_enabled_by_default(self):
        """Fallback should be enabled by default."""
        self.assertEqual(self.settings.fallback_enabled, 1)

    def test_default_endpoint(self):
        """Default endpoint should be the production API."""
        self.assertEqual(self.settings.api_endpoint, "https://api.templateto.com")


class TestPdfOverride(FrappeTestCase):
    """Tests for the PDF rendering override."""

    def setUp(self):
        self.settings = frappe.get_single("TemplateTo Settings")
        self.settings.enabled = 1
        self.settings.api_endpoint = "https://api.templateto.com"
        self.settings.fallback_enabled = 1
        self.settings.api_key = "tt_test_fake_key_for_testing"
        self.settings.save()

    def tearDown(self):
        self.settings.enabled = 0
        self.settings.save()

    def _original_mock(self, html, options=None, output=None):
        """Mock for the original get_pdf function."""
        return b"%PDF-1.4 original"

    @patch("templateto_reports.pdf_override.requests.post")
    def test_successful_render(self, mock_post):
        """Successful API call should return PDF bytes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4 templateto"
        mock_post.return_value = mock_response

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html><body>Test</body></html>", _original=self._original_mock)

        self.assertEqual(result, b"%PDF-1.4 templateto")
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        b64_html = call_kwargs[1]["json"]["base64HtmlString"]
        decoded = base64.b64decode(b64_html).decode("utf-8")
        self.assertEqual(decoded, "<html><body>Test</body></html>")

    @patch("templateto_reports.pdf_override.requests.post")
    def test_auth_failure_with_fallback(self, mock_post):
        """401 response with fallback enabled should use wkhtmltopdf."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.content = b"Unauthorized"
        mock_post.return_value = mock_response

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")

    @patch("templateto_reports.pdf_override.requests.post")
    def test_auth_failure_without_fallback(self, mock_post):
        """401 response with fallback disabled should raise."""
        self.settings.fallback_enabled = 0
        self.settings.save()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.content = b"Unauthorized"
        mock_post.return_value = mock_response

        from templateto_reports.pdf_override import get_pdf

        with self.assertRaises(Exception):  # noqa: B017
            get_pdf("<html>Test</html>", _original=self._original_mock)

    @patch("templateto_reports.pdf_override.requests.post")
    def test_connection_error_with_fallback(self, mock_post):
        """Network error with fallback should use wkhtmltopdf."""
        mock_post.side_effect = req.exceptions.ConnectionError("Connection refused")

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")

    @patch("templateto_reports.pdf_override.requests.post")
    def test_timeout_with_fallback(self, mock_post):
        """Timeout with fallback should use wkhtmltopdf."""
        mock_post.side_effect = req.exceptions.Timeout("Timed out")

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")

    def test_disabled_uses_original(self):
        """When disabled, should call original get_pdf."""
        self.settings.enabled = 0
        self.settings.save()

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")

    def test_no_api_key_uses_original(self):
        """When no API key is set, should call original get_pdf."""
        self.settings.api_key = ""
        self.settings.save()

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")

    @patch("templateto_reports.pdf_override.requests.post")
    def test_empty_response_with_fallback(self, mock_post):
        """200 with empty body should fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b""
        mock_post.return_value = mock_response

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")

    @patch("templateto_reports.pdf_override.requests.post")
    def test_server_error_with_fallback(self, mock_post):
        """500 response with fallback should use wkhtmltopdf."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.content = b"Internal Server Error"
        mock_post.return_value = mock_response

        from templateto_reports.pdf_override import get_pdf

        result = get_pdf("<html>Test</html>", _original=self._original_mock)
        self.assertEqual(result, b"%PDF-1.4 original")


class TestPdfGeneratorHook(FrappeTestCase):
    """Tests for the per-Print-Format pdf_generator hook entry point."""

    def setUp(self):
        self.settings = frappe.get_single("TemplateTo Settings")
        self.settings.enabled = 0  # global toggle off
        self.settings.api_endpoint = "https://api.templateto.com"
        self.settings.fallback_enabled = 1
        self.settings.api_key = "tt_test_fake_key_for_testing"
        self.settings.save()

    def test_hook_returns_none_for_other_generators(self):
        """Hook should return None when pdf_generator is not 'templatetocloud'."""
        from templateto_reports.pdf_override import get_pdf_via_hook

        result = get_pdf_via_hook(
            print_format=None,
            html="<html>Test</html>",
            options=None,
            output=None,
            pdf_generator="chrome",
        )
        self.assertIsNone(result)

    @patch("templateto_reports.pdf_override.requests.post")
    def test_hook_renders_when_templatetocloud(self, mock_post):
        """Hook should render via TemplateTo when pdf_generator='templatetocloud'."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4 templateto"
        mock_post.return_value = mock_response

        from templateto_reports.pdf_override import get_pdf_via_hook

        result = get_pdf_via_hook(
            print_format=None,
            html="<html>Test</html>",
            options=None,
            output=None,
            pdf_generator="templatetocloud",
        )
        self.assertEqual(result, b"%PDF-1.4 templateto")

    def test_hook_returns_none_when_no_api_key(self):
        """Hook should return None when no API key is configured."""
        self.settings.api_key = ""
        self.settings.save()

        from templateto_reports.pdf_override import get_pdf_via_hook

        result = get_pdf_via_hook(
            print_format=None,
            html="<html>Test</html>",
            options=None,
            output=None,
            pdf_generator="templatetocloud",
        )
        self.assertIsNone(result)
