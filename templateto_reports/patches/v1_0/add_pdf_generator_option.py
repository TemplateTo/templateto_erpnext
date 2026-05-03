"""Add `templatetocloud` (and `chrome`) as options on the Print Format
`pdf_generator` select field.

On stock Frappe v15 the field only ships with `wkhtmltopdf`. We add our option
plus `chrome` so existing Print Designer / v16 Chrome configurations aren't
broken.

Idempotent: `make_property_setter` updates the existing Property Setter if one
already exists for the field+property combo.
"""

from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    make_property_setter(
        doctype="Print Format",
        fieldname="pdf_generator",
        property="options",
        value="wkhtmltopdf\ntemplatetocloud\nchrome",
        property_type="Text",
        for_doctype=False,
    )
