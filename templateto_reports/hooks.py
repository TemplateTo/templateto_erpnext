app_name = "templateto_reports"
app_title = "TemplateTo Reports"
app_publisher = "TemplateTo"
app_description = (
    "Cloud-based PDF rendering for Frappe/ERPNext — replace wkhtmltopdf "
    "with zero server-side dependencies"
)
app_email = "david@templateto.com"
app_license = "MIT"
app_version = "1.0.0"
required_apps = ["frappe"]

# Register as a pdf_generator hook so users can select "templatetocloud" per Print Format.
# This is the Frappe-idiomatic integration (same pattern as Print Designer and v16 built-in Chrome).
# The monkey-patch in __init__.py handles the global "replace all wkhtmltopdf" case separately.
pdf_generator = "templateto_reports.pdf_override.get_pdf_via_hook"

# Add "templatetocloud" as an option on the Print Format's pdf_generator select field.
# On stock v15, this field only has "wkhtmltopdf". This Property Setter adds our option.
# We include "chrome" so existing Print Designer / v16 Chrome configurations aren't broken.
property_setters = [
    {
        "doctype": "Print Format",
        "fieldname": "pdf_generator",
        "property": "options",
        "value": "wkhtmltopdf\ntemplatetocloud\nchrome",
    }
]
