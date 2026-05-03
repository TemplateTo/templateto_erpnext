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

# The "templatetocloud" option is added to Print Format's pdf_generator select
# field by `setup.add_pdf_generator_option()`, which runs from both:
#   - `after_install` hook (covers fresh installs — patches are pre-marked as
#     applied during install-app and never run)
#   - The patches/v1_0/add_pdf_generator_option.py patch (covers upgrades from
#     older versions of this app)
# Both call the same idempotent helper.
after_install = "templateto_reports.setup.add_pdf_generator_option"
