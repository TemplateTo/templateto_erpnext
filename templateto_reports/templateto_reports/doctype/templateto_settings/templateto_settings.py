"""TemplateTo Settings — Single DocType for configuration."""

import base64

import frappe
import requests
from frappe.model.document import Document

TEST_HTML = "<html><body><p>TemplateTo connection test</p></body></html>"


class TemplateToSettings(Document):
    @frappe.whitelist()
    def test_connection(self):
        """Test the TemplateTo API connection with a minimal HTML render."""
        api_key = self.get_password("api_key")
        if not api_key:
            frappe.throw("Please enter and save an API key first.")

        endpoint = (self.api_endpoint or "https://api.templateto.com").rstrip("/")
        b64_html = base64.b64encode(TEST_HTML.encode("utf-8")).decode("ascii")

        try:
            response = requests.post(
                f"{endpoint}/render/pdf/fromhtml",
                json={"base64HtmlString": b64_html},
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
        except requests.exceptions.ConnectionError:
            frappe.throw(f"Cannot reach {endpoint}. Check your network and firewall settings.")
        except requests.exceptions.Timeout:
            frappe.throw("Connection timed out after 30 seconds.")

        if response.status_code == 200 and response.content:
            frappe.msgprint(
                f"Connection successful! TemplateTo rendered a test PDF "
                f"({len(response.content)} bytes).",
                indicator="green",
                title="Success",
            )
        elif response.status_code in (401, 403):
            frappe.throw("Invalid API key. Check your key and try again.")
        else:
            frappe.throw(f"API returned HTTP {response.status_code}: {response.text[:200]}")
