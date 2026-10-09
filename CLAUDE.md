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
- `web/aimo_contract_form.html` - a single self-contained HTML file; runs entirely client-side (JSZip from a CDN decodes/edits/re-zips the template, which is embedded in the page as base64). No Python/LibreOffice needed. The same file runs two ways - see "Running outside Claude" below for how it detects which one it's in. **Multi-template since Phase 3** (see Roadmap below) - the CLI/desktop GUI are still single-template (the original Aimo Charge contract only); the web version's `FIELDS_CHARGE`/`SECTIONS_CHARGE` arrays are the hand-ported copy of `fields.py`/`form_fields.py` - **keep them in sync manually**, there's no shared build step between Python and this HTML file. The other templates (`FIELDS_HARDWARE`/`FIELDS_ARRENDE`, etc.) exist only in the web version, with no Python equivalent.

### The field model

- `fields.py` - the ground truth: 49 `Field` entries, each naming a `sdt_index` (the content control's position, in document order, among all `<w:sdt>` elements in `word/document.xml`) plus its `kind` (`"text"` or `"checkbox"`), default placeholder value, and `group` for mutually-exclusive checkbox sets (e.g. `betalning_manadsvis`/`kvartalsvis`/`arsvis`). A field left out of the input data keeps the template's own placeholder (`XXX`, `XX`, `DATUM`, or unchecked) rather than being blanked - this is intentional, so an unfilled field stays visibly a placeholder in the output.
- `form_fields.py` - UI-only layer on top of `fields.py`: labels, hints, section grouping, and widget kind (`text`/`email`/`numeric`/`date`/`radio`/`checkbox`) for the desktop GUI and (hand-ported) the web form.
- `form_validation.py` - pure, display-agnostic validation functions (email/date/numeric/required-field regex checks), used by `contract_form.py`. These are advisory warnings the user can override, not hard blocks.
- A handful of pricing-table fields sit immediately before a unit the template already prints as static text (` kr/mån`, ` %`, ...) - values for those must be bare numbers, not pre-formatted strings, or the unit doubles up. This is called out in `fields.py`'s module docstring.

### PDF export

`generate_contract.py --out contract.pdf` additionally requires LibreOffice (`soffice` on PATH) for the PDF conversion step. `--keep-docx` alone skips that entirely; the resulting `.docx` can be converted with Word's own **File > Save As > PDF**. The web version has no PDF export at all for the same reason (no LibreOffice available client-side) - it always stops at the `.docx` download.

### JSON export (for downstream systems, e.g. NetSuite)

The web version downloads a second file alongside the `.docx` on every successful "Generera avtal" - same base filename, `.json` instead, `{templateId, templateName, generatedAt, fields}` where `fields` is exactly what `collectData()` produced for the `.docx` fill (all filled fields, radio groups expanded into their individual boolean option ids, same as the save/resume payload's `data`). No NetSuite-specific field mapping or endpoint - this is the raw collected data as a file the user downloads alongside the contract, not a push integration. Not implemented in the CLI or desktop GUI.

### Running outside Claude

`web/aimo_contract_form.html` detects at load time whether `window.claude`
exists (`isStandalone` near the top of the inline script) and swaps in
fallbacks for both capabilities it uses, so the one file works both ways
with no build step or separate copy:

- **`downloads`** - falls back to a plain `<a download>` Blob link
  (`localDownloads`). This has no downsides outside Claude - the Artifact
  sandbox is what needed the capability in the first place, a normal page
  doesn't.
- **`db`** (save/resume, Phase 1) - falls back to `localStorage`
  (`makeLocalDb()`), mirroring the same `doc`/`collection`/`get`/`set`/
  `update`/`delete`/`orderBy`/`limit` shape the Artifact `db` capability
  uses. **Per-browser only** - saved contracts are not shared between
  colleagues the way the Artifact-hosted version's are. The "Mina avtal"
  view shows a notice when running standalone to make this explicit.

Hosted on GitHub Pages (enabled on this repo, serving from this branch,
root path) at:
`https://dalo1741.github.io/DTrialBloggdown/scripts/contract_generator/web/aimo_contract_form.html`
Pages serves the branch's tree as-is (`.nojekyll` at the repo root skips
Jekyll processing) - once this branch is merged to `main`, Pages should be
repointed there if the page is meant to stay live long-term.

### Extending to a different template

`fields.py`'s `sdt_index` values are specific to `template/Avtal_Aimo_Charge_Fee_to_Landlord_v1.2.docx`'s content controls. To adapt the **Python/CLI/desktop** side to a different contract, unzip it and walk its `<w:sdt>` elements in `word/document.xml` in document order to rebuild the field list - each one's surrounding paragraph/table-cell text identifies what it's for.

For the **web version**, see the Phase 3 roadmap notes below - it also has to handle templates built on Word's legacy Form Field mechanism, not just content controls.

## Roadmap

Tracked here so it stays visible across sessions - update status as work completes.

1. **Save and resume contracts** - done (web version only, per scope decision below)
2. **Branding and layout** - not started
3. **Contract templates** - in progress: architecture done, 2 of ~10-15 planned
   contract types added (web version only, per scope decision below) - more
   to come as templates are supplied

### Phase 1 notes (save and resume)

Scoped to `web/aimo_contract_form.html` only (not the CLI or desktop GUI) -
a few colleagues share access to the same saved contracts, via the
Artifact `db` capability (declared alongside `downloads`). No custom `db`
rules are set, so the default access rules apply: anyone admitted at
Contributor level or above can read/write; sharing the artifact link (and
at what level) is done from the page's Share menu, which Claude can't do on
your behalf.

- Collection `contracts`, one doc per saved contract: `{name, templateId,
  status: "draft"|"final", data: {...same shape as collectData()...},
  createdAt, updatedAt}`. `templateId` is a constant for now
  (`"aimo_charge_v1_2"`) so Phase 3 (contract templates) can vary it later
  without a schema change.
- "Mina avtal" is a second view (tab) in the same page, toggled with
  `setView()`; `populateForm(data)` (used by both "Fyll i exempel" and
  resuming a saved contract) resets every field first, so stale values
  from whatever was in the form don't survive a switch.
- A saved contract's status flips from "draft" to "final" automatically
  the moment `.docx` generation succeeds (if a draft is currently open) -
  no separate "mark as done" action.
- The list view does one-time `.get()` reads, not live `onSnapshot`
  subscriptions - if colleagues editing concurrently turns out to matter,
  that's the first thing to add.

### Phase 3 notes (contract templates)

Scoped to `web/aimo_contract_form.html` only, same as Phase 1 - the CLI and
desktop GUI stay single-template (Aimo Charge) until someone asks for them
to be extended too.

- **`TEMPLATES`** (in the inline script) is the registry: one entry per
  contract type, keyed by a `templateId` string (the same value Phase 1's
  saved-contract docs store). Each entry names its `mechanism`
  (`"sdt"` or `"formtext"`, see below), its own `FIELDS_*`/`SECTIONS_*`
  arrays, embedded base64 (`TEMPLATE_DOCX_BASE64_*`) and expected byte
  size, output filename, and `nameHintField` (which field seeds the
  save-draft panel's suggested name).
- A new **template picker** is the landing view inside "Formulär" whenever
  no template is active (`currentTemplateId === null`) - cards built from
  `TEMPLATES` at load time, each with a "Välj" button calling
  `selectTemplate(id)`. "Byt avtalstyp" in the topbar returns to it.
  "Nytt avtal" (from "Mina avtal") also returns to the picker now, rather
  than reopening the previous template's blank form - the user picks a
  type first, same as a brand-new contract.
- **Two fill mechanisms**, because not every Word template uses content
  controls:
  - `"sdt"` (`fillSdt`) - the original mechanism: edits native `<w:sdt>`
    content controls, addressed by `sdtIndex` (document-order position).
  - `"formtext"` (`fillFormText`) - for templates built with the older,
    pre-2010 Word "Form Field" mechanism (`FORMTEXT`/`FORMCHECKBOX`/
    `FORMDROPDOWN` fields, i.e. `w:fldChar` begin/separate/end triples
    with a `w:ffData`). Addressed by `index` (position among all such
    fields), the same idea as `sdtIndex`, because field `w:name` values in
    a template built this way are frequently blank or reused across many
    unrelated fields and so can't be trusted as a stable key. A `"dropdown"`
    field kind exists only here (`FORMDROPDOWN`'s `w:ddList`/`w:result` -
    an index into the field's own `opts` list, not free text).
    `blankPositions` on a field marks extra adjacent field slots that are
    one logical blank split across several field instances (a template
    authoring artifact) - they're force-cleared whenever that field is
    written, so nothing duplicates in the output.
  - Figuring out which mechanism (and, for `formtext`, which field index
    maps to which blank) a new template uses takes unzipping it and
    walking `word/document.xml` by hand - there's no shortcut for a
    `formtext` template given how unreliable `w:name` is; expect to
    cross-reference each field against its surrounding paragraph/table-row
    text the same way `fields.py`'s module docstring describes for `sdt`.
- **Labels are a fast pass**, not hand-polished like the original Aimo
  Charge template's: `SECTIONS_HARDWARE`/`SECTIONS_ARRENDE` mostly reuse
  the template's own wording as the field label rather than a rewritten
  one. Given ~10-15 contract types total, this was a deliberate
  speed-over-polish call - revisit specific labels on request.
- Every template's zip is loaded lazily and memoized per `templateId`
  (`getTemplateZip`/`templateZipPromises`) - only the one the user actually
  picks gets base64-decoded, not all of them up front.
- **"Fyll i exempel" needs its own `SAMPLE_DATA_*` per template** -
  `fillWithSampleData()` looks one up in `SAMPLE_DATA_BY_TEMPLATE` keyed by
  `templateId` and shows an error status if none exists for the active
  template. First version of this shipped without `SAMPLE_DATA_HARDWARE`/
  `SAMPLE_DATA_ARRENDE`, so the button silently (from the user's
  perspective) did nothing for those two until a user reported it -
  add a sample alongside any future `FIELDS_*`/`SECTIONS_*` pair, not
  after the fact.
- Fixed in passing: `fillSdt`/`fillFormText`'s XML serialization
  unconditionally prepended its own `<?xml ...?>` declaration on top of
  the one the browser's `XMLSerializer` already re-emits from the parsed
  template, producing two declarations back to back. Well-formedness
  checks (`DOMParser`, Chromium rendering) tolerated it, but LibreOffice
  rejected the file outright ("source file could not be loaded") - this
  affected the original Aimo Charge template too, not just the new ones,
  and had never been caught because the web path's output was never
  round-tripped through a strict parser before. `serializeXml()` now
  strips any existing declaration before adding its own.
- Fixed after a real user report: the Arrendeavtal template's
  `word/document.xml` (unlike the other two) ships with a UTF-8
  byte-order mark. JSZip's `.async("string")` decodes that into a
  literal U+FEFF character ahead of `<?xml ...?>` in the resulting JS
  string, which Chromium's `DOMParser` then rejects as a second XML
  declaration ("Kunde inte tolka mallens XML... XML declaration allowed
  only at the start of the document") - this only ever broke this one
  template, since it's the only one of the three with a BOM in its
  source file. `parseTemplateXml()` now strips a leading U+FEFF before
  parsing, so any future template with (or without) a BOM is handled
  the same way.
