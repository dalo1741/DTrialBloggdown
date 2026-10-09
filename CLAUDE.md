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
- **Phase 3 (in progress):** contract templates — define new contract types
  as templates with fixed text plus `{{placeholder}}` fields (e.g.
  `{{party_name}}`, `{{start_date}}`, `{{amount}}`); create/edit/duplicate/
  delete templates in the app; "new contract" = pick a template, fill in
  fields, brand profile applied. Done when: a new contract type can be
  defined without touching code.
- **Phase 4 (not started):** TBD — likely real e-sign provider integration,
  real NetSuite SuiteTalk client, and persistent (non-in-memory) contract
  storage, per the "Nästa steg" list in `contract-tool/README.md`.

When picking up a phase, read the relevant code first, propose a plan, and
wait for approval before writing code, unless explicitly told to proceed
without that check-in.
