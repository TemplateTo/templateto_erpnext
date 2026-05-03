# TemplateTo Reports — Frappe/ERPNext App

Replace ERPNext's built-in **wkhtmltopdf** PDF engine with **TemplateTo's Chromium-based rendering API**.

## What it does

- **Drop-in replacement**: existing Print Formats and Jinja templates work unchanged
- **Modern CSS**: full support for flexbox, grid, media queries, web fonts
- **Reliable output**: no more blank PDFs, broken headers/footers, or `ConnectionRefusedError`
- **Sync rendering**: Print button works instantly
- **Automatic fallback**: falls back to wkhtmltopdf if the API is unreachable
- **Per-Print-Format opt-in**: use TemplateTo for some formats, the default engine for others

## Why not Frappe v16's built-in Chrome?

- No need to manage a local Chromium binary on every server
- Works on shared / restricted hosting where you can't run `bench setup-chrome`
- Consistent rendering across environments (the same cloud Chrome renders every PDF)
- On Frappe v15 there is no built-in Chrome option at all — TemplateTo fills that gap

## Requirements

- Frappe v15+ (works on v16 alongside the built-in Chrome engine)
- A TemplateTo account and API key — get one at [app.templateto.com](https://app.templateto.com)
- Internet access from the Frappe server to `https://api.templateto.com`

## Installation

```bash
bench get-app https://github.com/templateto/TemplateTo.ERPNext.git
bench --site your-site install-app templateto_reports
bench restart
```

Or for local development:

```bash
bench get-app /path/to/templateto_reports
bench --site your-site install-app templateto_reports
```

## Configuration

1. Open **Settings → TemplateTo Settings**
2. Tick **Enable TemplateTo for PDF Rendering**
3. Paste your **API Key**
4. Click **Test Connection** to verify
5. Save

### Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| Enable TemplateTo | Off | Master toggle for the PDF engine |
| API Key | — | Your TemplateTo API key |
| API Endpoint | `https://api.templateto.com` | Override only if directed by support |
| Fallback to wkhtmltopdf | On | Auto-fallback on API failure |

### Per-Print-Format opt-in

Instead of (or in addition to) the global toggle, you can pick TemplateTo for a single Print Format:

1. Open the Print Format
2. Set **PDF Generator** to `templatetocloud`
3. Save — only that format uses TemplateTo

## How it works

When enabled, the app intercepts `frappe.utils.pdf.get_pdf()`:

1. Frappe renders the Print Format / Jinja template to HTML (as usual)
2. The HTML is base64-encoded and POSTed to the TemplateTo API
3. TemplateTo renders it with Chrome headless and returns the PDF bytes
4. Bytes are returned to Frappe as if wkhtmltopdf had produced them

Two integration mechanisms run side-by-side:

- **Monkey-patch** of `frappe.utils.pdf.get_pdf` (and the two modules that import it directly): replaces wkhtmltopdf globally when the master toggle is on
- **`pdf_generator` hook** named `templatetocloud`: lets users opt in per Print Format (Frappe-idiomatic, future-proof for v16's built-in Chrome)

## External service disclosure

This app sends **only the rendered HTML** to the TemplateTo API for PDF conversion. No credentials, database content, or attachments are transmitted. The app is disabled by default and requires explicit opt-in (enable + API key).

## Local development

A `docker-compose.yml` is included for spinning up an ERPNext v15 instance with this app mounted as a volume:

```bash
docker compose up -d
# wait for the init service to finish (tail logs)
# open http://localhost:8000  →  Administrator / admin
```

See `docker-compose.yml` and `init.sh` for details.

## License

MIT — see [LICENSE](LICENSE).

## Support

- Docs: [docs.templateto.com](https://docs.templateto.com)
- Email: david@templateto.com
- Issues: [GitHub Issues](https://github.com/templateto/TemplateTo.ERPNext/issues)
