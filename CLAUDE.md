# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This repo contains two unrelated things:

1. **A blogdown/Hugo personal site** (repo root, `content/`, `themes/aafu`, `config.toml`) - a static site built with R's `blogdown` package wrapping Hugo, deployed to Netlify (`baseURL` in `config.toml` points at `dalo1.netlify.app`). The `aafu` theme lives in `themes/aafu` (a third-party Hugo theme, treat as vendored - don't edit unless asked).
2. **`scripts/`** - two independent, standalone Python tools with no connection to the blogdown site. Each is self-contained with its own `requirements.txt`.

When working on a task, check which of these it belongs to before editing - they share no code or config.

## The blogdown site

- Build with R/blogdown (`blogdown::build_site()` or `blogdown::serve_site()` from R) - there is no Node/npm build here.
- Content lives in `content/blog/` and `content/post/` as `.Rmd` or `.md` files with front matter.
- `public/` is Hugo's generated output - don't hand-edit it.
- Site config and theme options (profile, social links, color theme) are in `config.toml`.

## `scripts/sftp_sync/` - SFTP downloader

Pulls new files from an SFTP server to a local directory once a day, idempotently (skips files already copied via a local manifest; downloads land atomically via a `.part` file + rename).

```bash
cd scripts/sftp_sync
pip install -r requirements.txt
cp config.example.yaml config.yaml   # edit host/dir/auth
python3 sftp_sync.py --config config.yaml [--dry-run] [--log-file sftp_sync.log]
```

Key auth/behavior details are documented inline in `config.example.yaml` (key vs. password auth, host-key verification, retry/backoff settings).

## `scripts/contract_generator/` - Aimo charging-services contract generator

Fills in the Aimo "Avtal Laddningstjänster" Word template and exports a PDF/.docx, reproducing the original template's header banner, footer, fonts and table styling exactly - because it edits the real template's `word/document.xml` in place (via its native Word content controls) rather than recreating the document from scratch.

**Three interfaces share the same underlying field model**, so a template change must be applied to all three:
- `generate_contract.py` - CLI, takes a YAML data file (`data.example.yaml` is the schema reference)
- `contract_form.py` - Tkinter desktop GUI (stdlib only, no extra dependency beyond the base `requirements.txt`)
- `web/aimo_contract_form.html` - a single self-contained HTML file; runs entirely client-side (JSZip from a CDN decodes/edits/re-zips the template, which is embedded in the page as base64) and hands the result to the viewer via the Artifact `downloads` capability. No Python/LibreOffice needed, but it only works as a *hosted* page (via Claude Artifacts) because local `file://` pages have no download capability. Its `FIELDS`/`SECTIONS` arrays and fill logic are a hand-ported copy of `fields.py`/`form_fields.py` - **keep them in sync manually**, there's no shared build step between Python and this HTML file.

### The field model

- `fields.py` - the ground truth: 49 `Field` entries, each naming a `sdt_index` (the content control's position, in document order, among all `<w:sdt>` elements in `word/document.xml`) plus its `kind` (`"text"` or `"checkbox"`), default placeholder value, and `group` for mutually-exclusive checkbox sets (e.g. `betalning_manadsvis`/`kvartalsvis`/`arsvis`). A field left out of the input data keeps the template's own placeholder (`XXX`, `XX`, `DATUM`, or unchecked) rather than being blanked - this is intentional, so an unfilled field stays visibly a placeholder in the output.
- `form_fields.py` - UI-only layer on top of `fields.py`: labels, hints, section grouping, and widget kind (`text`/`email`/`numeric`/`date`/`radio`/`checkbox`) for the desktop GUI and (hand-ported) the web form.
- `form_validation.py` - pure, display-agnostic validation functions (email/date/numeric/required-field regex checks), used by `contract_form.py`. These are advisory warnings the user can override, not hard blocks.
- A handful of pricing-table fields sit immediately before a unit the template already prints as static text (` kr/mån`, ` %`, ...) - values for those must be bare numbers, not pre-formatted strings, or the unit doubles up. This is called out in `fields.py`'s module docstring.

### PDF export

`generate_contract.py --out contract.pdf` additionally requires LibreOffice (`soffice` on PATH) for the PDF conversion step. `--keep-docx` alone skips that entirely; the resulting `.docx` can be converted with Word's own **File > Save As > PDF**. The web version has no PDF export at all for the same reason (no LibreOffice available client-side) - it always stops at the `.docx` download.

### Extending to a different template

`fields.py`'s `sdt_index` values are specific to `template/Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx`'s content controls. To adapt this to a different contract, unzip it and walk its `<w:sdt>` elements in `word/document.xml` in document order to rebuild the field list - each one's surrounding paragraph/table-cell text identifies what it's for.

## Roadmap

Tracked here so it stays visible across sessions - update status as work completes.

1. **Save and resume contracts** - not started
2. **Branding and layout** - not started
3. **Contract templates** - not started
