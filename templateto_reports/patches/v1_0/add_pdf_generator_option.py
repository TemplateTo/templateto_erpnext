"""Patch wrapper that calls the shared setup helper.

Runs on `bench migrate` for users upgrading from a previous version of this
app (where the after_install hook already fired). Idempotent.
"""

from templateto_reports.setup import add_pdf_generator_option


def execute():
    add_pdf_generator_option()
