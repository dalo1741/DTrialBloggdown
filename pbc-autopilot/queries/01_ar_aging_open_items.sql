-- PBC-AR-01  AR aging / Kundreskontra - open items, CURRENT state
-- Fast variant: uses NetSuite's own "unpaid" field, so it is only valid for "today".
-- For a historical cut-off (31 Dec) use 02_ar_aging_asof.sql.
-- Conventions:  literals below are example parameters (asof = 2025-12-31).
--               lines tagged /*OW*/ exist only in OneWorld accounts - strip them for single-subsidiary.
-- Output is codes/raw values only; labels (sv/en) are applied in Python.
SELECT
  t.id                                   AS tran_id,        -- drill-back key
  t.type                                 AS tran_type,
  t.tranid                               AS doc_no,
  t.trandate                             AS tran_date,
  t.duedate                              AS due_date,
  t.terms                                AS terms_id,
  c.id                                   AS customer_id,
  c.entityid                             AS customer_no,
  c.companyname                          AS customer_name,
  t.subsidiary                           AS subsidiary_id,  /*OW*/
  t.currency                             AS currency_id,
  cur.symbol                             AS currency,
  -- sign-normalised: invoices/deposits +, credit memos/payments -
  CASE WHEN t.type IN ('CustCred','CustPymt') THEN -ABS(t.foreignamountunpaid)
       ELSE ABS(t.foreignamountunpaid) END                    AS open_amount_fc,
  CASE WHEN t.type IN ('CustCred','CustPymt') THEN -ABS(t.foreignamountunpaid)
       ELSE ABS(t.foreignamountunpaid) END * t.exchangerate   AS open_amount_base_at_tran_rate,
  TO_DATE('2025-12-31','YYYY-MM-DD') - t.duedate              AS days_past_due,
  CASE
    WHEN TO_DATE('2025-12-31','YYYY-MM-DD') - t.duedate <= 0  THEN 'NOT_DUE'
    WHEN TO_DATE('2025-12-31','YYYY-MM-DD') - t.duedate <= 30 THEN 'D001_030'
    WHEN TO_DATE('2025-12-31','YYYY-MM-DD') - t.duedate <= 60 THEN 'D031_060'
    WHEN TO_DATE('2025-12-31','YYYY-MM-DD') - t.duedate <= 90 THEN 'D061_090'
    ELSE 'D090_PLUS' END                                      AS bucket
FROM transaction t
JOIN customer c   ON c.id   = t.entity
JOIN currency cur ON cur.id = t.currency
WHERE t.type IN ('CustInvc','CustCred','CustPymt','CustDep')
  AND t.posting = 'T'
  AND t.voided  = 'F'
  AND t.foreignamountunpaid <> 0
  AND t.subsidiary IN (1,2,3)                                 /*OW*/
ORDER BY c.entityid, t.duedate;

-- CONTROL (always ship with the schedule): aging total must tie to GL.
-- Differences are normally (a) period-end FX revaluation, (b) manual JEs posted straight to AR.
-- SELECT a.acctnumber, t.subsidiary /*OW*/, SUM(tal.amount) AS gl_balance
-- FROM transactionaccountingline tal
-- JOIN transaction t       ON t.id  = tal.transaction
-- JOIN account a           ON a.id  = tal.account
-- JOIN accountingperiod ap ON ap.id = t.postingperiod
-- WHERE tal.posting = 'T'
--   AND tal.accountingbook IN (SELECT id FROM accountingbook WHERE isprimary = 'T')
--   AND a.accttype = 'AcctRec'
--   AND ap.enddate <= TO_DATE('2025-12-31','YYYY-MM-DD')
-- GROUP BY a.acctnumber, t.subsidiary;
