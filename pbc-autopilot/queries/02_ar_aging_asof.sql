-- PBC-AR-01b  AR aging as of a HISTORICAL date (what auditors actually need at 31 Dec).
-- Reconstructs open balance = original amount - applications dated <= asof.
-- Part A covers invoices. Credit memos / unapplied payments: same pattern from the other side
-- of the link (nextdoc = the credit/payment) - see docs/query-design.md section 3.
-- CAVEAT: NextTransactionLineLink has no "apply date"; we use the applying document's trandate
-- as proxy. Credit memos applied later than their own date can be misdated -> tie out to GL.
SELECT
  inv.id            AS tran_id,
  inv.tranid        AS doc_no,
  inv.type          AS tran_type,
  inv.trandate      AS tran_date,
  inv.duedate       AS due_date,
  c.id              AS customer_id,
  c.entityid        AS customer_no,
  c.companyname     AS customer_name,
  inv.subsidiary    AS subsidiary_id,                                   /*OW*/
  cur.symbol        AS currency,
  ABS(inv.foreigntotal)                                  AS original_fc,
  NVL(app.applied_fc, 0)                                 AS applied_to_asof_fc,
  ABS(inv.foreigntotal) - NVL(app.applied_fc, 0)         AS open_fc_asof,
  (ABS(inv.foreigntotal) - NVL(app.applied_fc, 0)) * inv.exchangerate AS open_base_at_tran_rate,
  TO_DATE('2025-12-31','YYYY-MM-DD') - inv.duedate       AS days_past_due
FROM transaction inv
JOIN customer c   ON c.id   = inv.entity
JOIN currency cur ON cur.id = inv.currency
LEFT JOIN (
  SELECT ntl.previousdoc AS inv_id, SUM(ABS(ntl.foreignamount)) AS applied_fc
  FROM NextTransactionLineLink ntl
  JOIN transaction pay ON pay.id = ntl.nextdoc
  WHERE ntl.linktype = 'Payment'
    AND pay.trandate <= TO_DATE('2025-12-31','YYYY-MM-DD')
  GROUP BY ntl.previousdoc
) app ON app.inv_id = inv.id
WHERE inv.type = 'CustInvc'
  AND inv.posting = 'T'
  AND inv.voided  = 'F'
  AND inv.trandate <= TO_DATE('2025-12-31','YYYY-MM-DD')
  AND ABS(inv.foreigntotal) - NVL(app.applied_fc, 0) <> 0
ORDER BY c.entityid, inv.duedate;
