# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Repository overview

This repo has two unrelated things in it:

1. **A Hugo/blogdown static site** at the repo root (`config.toml`, `content/`,
   `themes/aafu/`, `index.Rmd`, `public/` build output). This is a personal
   blog scaffold; there is no active development happening here.
2. **`contract-tool/`** — a standalone Node/TypeScript app, under active
   development. This is where almost all current work happens. Treat it as
   its own project: it has its own `package.json`, `tsconfig.json`, and
   `node_modules`, independent of the Hugo site.

Unless told otherwise, assume new work targets `contract-tool/`.

## contract-tool

A small internal tool: a web form that captures contract data and fans it
out to two independent export tracks — a PDF/e-signature document and a
NetSuite sales order/customer sync. See `contract-tool/README.md` for the
architecture diagram and the list of stubbed integrations (e-sign provider,
NetSuite SuiteTalk client, persistent storage).

Stack:
- Express + TypeScript (`src/server.ts`), `zod` for input validation.
- `pdfkit` for PDF generation (`src/pdf/renderContractPdf.ts`).
- Plain HTML/vanilla JS frontend under `public/` (dotted input names →
  nested JSON, see `public/form.js`) — no frontend framework, no bundler.
- In-memory store for contract drafts (`src/storage/contractStore.ts`);
  disk-persisted JSON for longer-lived config like the brand profile.
- No authentication yet (`/api/*` is open).

Request flow: `POST /api/contracts` validates with zod, saves the draft to
the in-memory store, then calls `emitContractSubmitted` (`src/events.ts`),
an in-process `EventEmitter`. `server.ts` registers one listener per export
track (`exportContractDocument`, `exportToNetsuite`) on that same event —
this EventEmitter fan-out is what actually implements the "independent
tracks" guarantee, since an error thrown in one listener doesn't reach the
other. Each track writes its own status back onto the contract record
(`contractExport.status` / `netsuiteExport.status`), pollable via
`GET /api/contracts/:id`. Generated PDFs and the persisted brand
profile/logo live under `data/` (gitignored).

Commands (run from `contract-tool/`):
```bash
npm install
cp .env.example .env   # only needed for real e-sign/NetSuite credentials
npm run dev          # tsx watch src/server.ts, http://localhost:3000
npm run typecheck    # tsc --noEmit
npm run build        # tsc -p tsconfig.json
npm start             # node dist/server.js (after build)
```

There is no automated test suite yet — verify changes by running `npm run
dev` and exercising the form/API manually, plus `npm run typecheck`.

Conventions to follow:
- Source comments in this codebase are written in Swedish, matching the
  existing style — keep new comments in Swedish too, and keep them rare
  (only for non-obvious "why", per general comment policy).
- Keep the two export tracks (document export, NetSuite export)
  independent: a failure in one must never block or affect the other.
- Stub out real third-party integrations the same way existing stubs do
  (`src/exporters/eSignClient.ts`, `src/netsuite/client.ts`) rather than
  wiring in real credentials/API calls unless explicitly asked.
- Validate all new external input with `zod` schemas under `src/types/`.

## Roadmap

- **Phase 1 (done):** form → validation → contract model → two independent
  export tracks (PDF/e-sign stub, NetSuite stub). In-memory storage.
- **Phase 2 (done):** branding and layout — a global, disk-persisted brand
  profile (`src/types/brandProfile.ts`, `src/storage/brandProfileStore.ts`,
  `data/brand/`) covering logo upload, primary/secondary colors, font
  (pdfkit's built-in standard fonts only), margins, header/footer text, and
  logo position (left/center/right). Configured via `/brand.html`
  (`GET`/`PUT /api/brand-profile`, `POST`/`GET /api/brand-profile/logo`) and
  applied to every generated PDF in `src/pdf/renderContractPdf.ts`. Key
  decision: an uploaded SVG logo is rasterized to PNG server-side at upload
  time (`@resvg/resvg-js`, in `brandProfileStore.saveBrandLogo`) because
  pdfkit's `doc.image()` has no native SVG support — without this, every
  contract PDF export would fail while an SVG logo was active. Verified
  end-to-end against an exported contract PDF (PNG + SVG logos, all three
  logo positions, custom colors/font/margins/header/footer text).
- **Phase 3 (done):** contract templates — `src/types/contractTemplate.ts` +
  `src/storage/templateStore.ts` (disk-persisted JSON, one file per template
  under `data/templates/`, same pattern as the brand profile). CRUD via
  `/templates.html` (`/api/templates`, `/api/templates/:id`,
  `/api/templates/:id/duplicate`). A template is a name + free-text body
  with `{{placeholder}}` fields — **the field list is auto-detected from the
  body text** (regex-extracted placeholder names, in order of first
  appearance), not declared separately; editing the body text live-updates
  the field list in the UI. "New contract" = `/new-template-contract.html`:
  pick a template → dynamically rendered form (one input per field, typed
  text/number/date) → `POST /api/templates/:id/render`, which validates
  against a zod schema built at request time from the template's fields
  (`buildFieldValuesSchema`), substitutes placeholders, and returns a
  branded PDF synchronously (`src/pdf/renderTemplatedContract.ts` — no
  NetSuite/e-sign track for this contract type, see key decision below).
  `src/pdf/pdfHeader.ts` was extracted from `renderContractPdf.ts` (shared
  `drawHeader`/`drawFooters`, used by both renderers so the brand profile
  looks identical either way). Verified end-to-end: created a template via
  the UI, confirmed live field auto-detection, generated a branded PDF
  (logo/colors/font/margins all present), and exercised duplicate/edit/
  delete — all without touching code.

  Key decisions (flagged and approved before building):
  - **Templates are a parallel system, not a replacement.** They produce a
    PDF only; they do **not** plug into `exportToNetsuite`/`eSignClient` —
    those stay scoped to the existing fixed Aimo Park `Contract` flow
    (`src/types/contract.ts`), which is untouched. The tool now has two
    contract concepts side by side (approved trade-off; Phase 3's spec never
    mentioned NetSuite/e-signing).
  - **Template body is plain text, not markup.** `{{field}}` substitution
    into paragraphs (blank-line-separated) flowed through pdfkit
    `doc.text()` — no bold/headings/tables inside a template's body, and no
    new rendering dependency.
  - **Fields are derived from the text, never hand-declared** — a template
    editor only adds a label/type override per detected placeholder key.
- **Phase 4 (not started):** TBD — likely real e-sign provider integration,
  real NetSuite SuiteTalk client, and persistent (non-in-memory) contract
  storage, per the "Nästa steg" list in `contract-tool/README.md`. Note for
  whoever picks this up: if/when Phase 4 unifies the two contract concepts
  (templated contracts currently have no NetSuite export or persistent
  "submitted contract" record — `/api/templates/:id/render` is fire-and-forget,
  nothing is stored beyond the generated PDF file), that's a bigger decision
  than Phase 4's original scope implies and should probably be flagged back
  to the user rather than assumed.

When picking up a phase, read the relevant code first, propose a plan, and
wait for approval before writing code, unless explicitly told to proceed
without that check-in.
