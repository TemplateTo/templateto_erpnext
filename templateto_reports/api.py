"""Whitelisted API endpoints for TemplateTo Reports."""

import frappe


@frappe.whitelist()
def test_connection():
    """Standalone API endpoint for testing connection.

    Can be called via: frappe.call('templateto_reports.api.test_connection')
    The Button in the DocType form uses the doc method instead (see templateto_settings.js).
    """
    settings = frappe.get_single("TemplateTo Settings")
    settings.test_connection()
