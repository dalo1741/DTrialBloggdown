# PBC Autopilot – SuiteQL query design (v0.1 sketch)

**Status: drafted from NetSuite knowledge, NOT yet run against a sandbox.** Field names marked ⚠ are the ones I am least sure about; section 8 is the first thing to run.

## 1. Design principles (these drive the multi-tenant story)

1. **Queries return codes and raw values, never labels.** `BUILTIN.DF()` returns text in the *running user's* language, so a Swedish sandbox user and an English integration role would produce different output. Labels (sv/en) are applied in Python from a catalogue keyed by column code.
2. **Every schedule ships with a control total** that ties to the GL (aging → AR/AP control accounts; JE population → TB movement; rollforward closing → TB balance). Auditors treat this as the completeness evidence (IPE), and it is also your cheapest bug detector.
3. **Every row carries `tran_id`.** Drill-back URL = `https://{acct}.app.netsuite.com/app/accounting/transactions/transaction.nl?id={tran_id}` (account id lower-cased, `_` → `-`, e.g. `1234567-sb1`). Excel `HYPERLINK()` per row.
4. **SuiteQL REST has no bind parameters** → templates are rendered in Python (Jinja), and values must be validated/escaped there. Do not string-format user input.
5. **Templates are feature-conditional, not just parameterised.** In a non-OneWorld account `transaction.subsidiary` likely does not exist and the query fails outright (⚠ confirm). Hence the `/*OW*/` tags in the `.sql` files; in the product these become `{% if features.oneworld %}` blocks. Feature probes at onboarding: OneWorld, multi-currency, multi-book, Advanced Intercompany, FAM SuiteApp, approval routing, segments (dept/class/location).
6. **Tenant config, not code, holds**: account maps (AR/AP control, FA cost/accum-depr/expense, IC accounts), bucket definitions, JE risk rules + thresholds, primary vs secondary book, language, materiality.

## 2. Common building blocks

| Concern | Pattern |
|---|---|
| Posting only | `tal.posting='T'`, `t.voided='F'` |
| Book | `tal.accountingbook IN (SELECT id FROM accountingbook WHERE isprimary='T')` — make configurable (Swedish group often has K3 + IFRS books) |
| Period logic | Join `accountingperiod` via `t.postingperiod`; use `ap.startdate/enddate`, not `trandate`, for audit cut-offs |
| Pagination | `POST /services/rest/query/v1/suiteql` with `Prefer: transient`, `limit` ≤ 1000, loop `offset` |
| Auth | OAuth 2.0 M2M (cert) preferred; role needs REST Web Services + Log in using OAuth, plus view on the records queried; **SuiteQL honours role subsidiary restrictions**, so use a role with all subsidiaries |

## 3. AR aging (`01_`, `02_`)

**Two variants on purpose.**
- `01` current-state: `foreignamountunpaid` – fast, but it is *today's* balance, useless for a 31 Dec cut-off run in February.
- `02` as-of: original amount minus applications dated ≤ as-of, via `NextTransactionLineLink` (`previousdoc`/`nextdoc`/`linktype`/`foreignamount`). This is what the audit schedule should use.

Fields: tran_id, type, doc no, tran date, **due date**, customer id/no/name, terms, currency, open amount in transaction currency, open amount in base at transaction rate, days past due, bucket code. Buckets are config (default Not due / 1-30 / 31-60 / 61-90 / 90+); offer both **due-date** and **invoice-date** aging (Swedish auditors frequently ask for förfallodatum, some for fakturadatum).

Known gaps / traps:
- ⚠ Apply date is not on the link table; proxy = applying document's `trandate`. Credit memos applied after their own date can be mis-aged. Part B (credits/unapplied payments from the `nextdoc` side) is not yet written.
- ⚠ Unapplied payments/deposits may not populate `foreignamountunpaid` (there is a separate "amount unused" field on payments). The GL tie-out will expose this.
- **FX**: base amount at transaction rate ≠ GL, because NetSuite revalues open AR at period end. Report three columns: transaction currency, base at original rate, and (separately) the revaluation adjustment so the tie-out foots.
- Credit-memo sign: normalised with `ABS` + type, because the sign of `foreigntotal` on credit memos is easy to get wrong.
- ⚠ Status/void flags and `exchangerate` exposure on `transaction` – confirm.

## 4. AP aging (`03_`)

Same skeleton, `vendor`, types `VendBill`, `VendCred`, `VendPymt`, `VendPrep` (⚠ verify code). Differences:
- `tranid` is the **vendor's invoice number**, NetSuite's own number is `transactionnumber`. Show both.
- Bills pending approval are non-posting → excluded by `posting='T'`. Add a companion "unapproved bills at cut-off" listing (liability completeness).
- Add vendor payment terms, and optionally payment-hold flag.
- Auditors usually also want **unrecorded liabilities** (payments after year end) – separate PBC item, easy follow-on using `VendPymt` with trandate in the subsequent window.

## 5. JE listing with risk filters (`04_`)

Line-level from `transactionaccountingline` (posting lines only) joined to `transactionline`, `account`, `accountingperiod`, `employee`. Risk rules are **flags computed in an inner query**, outer query applies `risk_score >= N` – so each rule is one config entry that can be toggled per client/auditor:

weekend posting (locale-safe via `MOD(date − 1900-01-06, 7)`, avoids `TO_CHAR('D')` NLS dependence) · created after period end · adjustment period · round amounts · above threshold · no description · keywords (sv + en) · sensitive account types · reversing entries. Candidates not yet in: same user created & approved (⚠ `approvedby` exposure), entries to seldom-used accounts, user outside finance, manual vs system source (⚠ `source` column).

Gotchas:
- Define the **population** explicitly: type `Journal` only? Also intercompany JEs, revaluation/amortisation system journals? Auditors will ask; make it a config list of types.
- Thresholds are in **subsidiary currency** → in OneWorld with SEK/EUR/NOK entities either set per-subsidiary thresholds or convert with `BUILTIN.CONSOLIDATE`.
- Volume: a full-year population can be 100k+ lines → page by period, stream to Excel (`xlsxwriter` constant_memory), pre-filter in SQL only for cheap rules.
- ⚠ Per-line subsidiary on advanced IC journals (`transactionline.subsidiary`) vs header.

## 6. Fixed asset rollforward (`05_`)

**Two adapters, GL-based first.**
1. **GL-based (universal):** opening (periods ending before start), movements grouped by account × transaction type, closing = opening + movement, checked against TB. Python maps accounts to {cost, accumulated depreciation, depreciation expense} and movements to {additions, disposals, depreciation, transfers/other}. Default map ships with BAS ranges (11xx–12xx cost, 1119/1129/1219/1229… accumulated depreciation) – tenants override. Classification of movements by transaction type is heuristic; make it overridable and always show the unclassified residue.
2. **Register-based (per asset):** Oracle Fixed Assets Management custom records (`customrecord_ncfar_asset`, `customrecord_ncfar_assethistory`; ⚠ I am recalling field ids from memory – list them under Customization > Record Types). Many Nordic shops do **not** use FAM (spreadsheet or third-party registers), which is why GL-based is the baseline and register detail is a pluggable adapter.

## 7. Intercompany reconciliation (`06_`)

- **06a** balance matrix on IC accounts, per (subsidiary, counterparty), in subsidiary currency *and* group currency (`BUILTIN.CONSOLIDATE`, ⚠ check argument order). Python nets A→B against B→A; non-zero = reconciling item. Remaining difference after translation is usually FX or timing.
- **06b** transaction level via `transaction.intercotransaction` / `intercostatus` (⚠) to list pairs and orphans.
- Counterparty identification: IC customers/vendors carry `representingsubsidiary`; Advanced Intercompany Journals may not use entity at all (⚠ line-level counterparty field).
- IC accounts: `account.eliminate='T'` (⚠) or tenant list.
- **Single-subsidiary variant:** the item does not exist as such. Replace with a *related-party / koncernbolag* balance listing: customers/vendors flagged by a custom field (or a tenant list of entity ids) with balances and transactions in period. Same output slot in the workpaper folder.

## 8. OneWorld vs single-subsidiary – what actually changes

| Area | OneWorld | Single subsidiary |
|---|---|---|
| Subsidiary column / filter | `t.subsidiary`, role restrictions, per-sub schedules + consolidated | Column absent → query fails if left in |
| Amounts | `amount` in subsidiary currency; group view needs `BUILTIN.CONSOLIDATE` with period id | One base currency, no translation |
| AR/AP control accounts | Often one per subsidiary, same number | Single |
| Aging output | One tab/file per legal entity + group summary | One file |
| JE thresholds | Per subsidiary currency | One |
| IC reconciliation | Core item (matrix + orphans) | Replace with related-party listing |
| Multi-book | Common (local GAAP + IFRS/group) | Rare; still parameterise |
| FX revaluation | Per-subsidiary reval journals; tie-out must show them | Only foreign-currency AR/AP |
| Workpaper folder | `/{entity}/{PBC-ref}/…` | Flat |

## 9. First validation run (sandbox) – 30-minute checklist

1. `SELECT DISTINCT type FROM transaction` – confirm type codes (`CustInvc`, `VendBill`, `Journal`, `VendPrep`, `CustDep`…).
2. Select one row each of `t.foreignamountunpaid, t.exchangerate, t.voided, t.posting, t.intercotransaction, t.intercostatus, t.reversaldate, t.transactionnumber` – any "field not found" is a template fix.
3. Run `01` and tie total to the GL control query for one subsidiary; investigate the delta (expected: FX reval).
4. Run `02` for a past quarter end; compare against NetSuite's standard A/R Aging report *as of that date*.
5. Sample 5 invoices with part payments and credit memos; confirm `NextTransactionLineLink` link types and amount signs.
6. Run `04` for one period; check Σdebit = Σcredit and count against the GL Journal report.
7. Run `05` for a closed year; closing must equal TB balance per account.
8. OneWorld: run `06a`, confirm A→B nets against B→A in group currency within FX tolerance.

## 10. Bilingual labels (seed catalogue)

| key | en | sv |
|---|---|---|
| ar_aging | AR aging | Kundreskontra – åldersanalys |
| ap_aging | AP aging | Leverantörsreskontra – åldersanalys |
| je_listing | Journal entry listing | Verifikationslista (manuella verifikationer) |
| fa_rollforward | Fixed asset rollforward | Anläggningsspecifikation / förändring av anläggningstillgångar |
| ic_recon | Intercompany reconciliation | Koncerninterna mellanhavanden – avstämning |
| due_date | Due date | Förfallodatum |
| days_past_due | Days past due | Dagar efter förfallodatum |
| not_due | Not due | Ej förfallet |
| customer / vendor | Customer / Vendor | Kund / Leverantör |
| open_amount | Open amount | Öppet belopp |
| doc_no | Document no. | Dokumentnr |
| acq_cost / acc_depr | Cost / Accumulated depreciation | Anskaffningsvärde / Ackumulerade avskrivningar |

Format numbers and dates through Excel number formats (not strings) so `1 234,56` / `2025-12-31` render per locale without changing the stored value.
