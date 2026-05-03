"""Setup helpers — called from after_install hook AND from the v1_0 patch."""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def add_pdf_generator_option():
    """Add `templatetocloud` (and `chrome`) as options on the Print Format
    `pdf_generator` select field.

    On stock Frappe v15 the field only ships with `wkhtmltopdf`. v16 ships
    `wkhtmltopdf\\nchrome`. Either way we add our `templatetocloud` option
    alongside the existing ones.

    Idempotent: `make_property_setter` updates the existing Property Setter
    if one already exists for the field+property combo. Frappe v16 requires
    an explicit commit inside patches/setup hooks — v15 commits implicitly,
    v16 does not.
    """
    make_property_setter(
        doctype="Print Format",
        fieldname="pdf_generator",
        property="options",
        value="wkhtmltopdf\ntemplatetocloud\nchrome",
        property_type="Text",
        for_doctype=False,
    )
    frappe.db.commit()
